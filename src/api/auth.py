"""Entra ID (Azure AD) JWT token validation for FastAPI."""
import time
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import Config

# Module-level JWKS cache
_jwks_cache: dict[str, Any] = {"keys": [], "fetched_at": 0.0}
_JWKS_CACHE_TTL = 3600  # 1 hour

bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwks_url() -> str:
    tenant = Config.ENTRA_TENANT_ID
    return f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"


def _get_signing_keys() -> list[dict[str, Any]]:
    """Fetch and cache JWKS signing keys from Entra ID."""
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < _JWKS_CACHE_TTL:
        return _jwks_cache["keys"]

    resp = httpx.get(_get_jwks_url(), timeout=10)
    resp.raise_for_status()
    keys = resp.json().get("keys", [])
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def _find_key(token: str) -> dict[str, Any]:
    """Find the signing key matching the token's kid header."""
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Token missing kid header")

    keys = _get_signing_keys()
    for key in keys:
        if key.get("kid") == kid:
            return key

    # Key not found — refresh cache once in case of key rotation
    _jwks_cache["fetched_at"] = 0.0
    keys = _get_signing_keys()
    for key in keys:
        if key.get("kid") == kid:
            return key

    raise HTTPException(status_code=401, detail="Token signing key not found")


def _decode_token(token: str) -> dict[str, Any]:
    """Validate and decode a JWT token using Entra ID JWKS."""
    key_data = _find_key(token)
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

    tenant = Config.ENTRA_TENANT_ID
    app_id = Config.ENTRA_APP_ID

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=f"api://{app_id}",
            issuer=f"https://login.microsoftonline.com/{tenant}/v2.0",
            options={"require": ["exp", "iss", "aud", "oid"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any] | None:
    """FastAPI dependency — validates Bearer token and returns user claims.

    When ENTRA_APP_ID is not configured, auth is skipped (local dev mode).
    """
    if not Config.ENTRA_APP_ID:
        return None

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(credentials.credentials)
    return {
        "oid": payload.get("oid", ""),
        "name": payload.get("name", ""),
        "email": payload.get("preferred_username", payload.get("email", "")),
    }
