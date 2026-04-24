# Decision: OAuth Middleware Implementation (Task #13)

**Author:** Trinity (Backend Developer)
**Date:** 2025-07-25
**Status:** Implemented

## Decision

Used **PyJWT + cryptography** (via `PyJWT[crypto]`) for JWT token validation instead of `python-jose[cryptography]`.

## Rationale

- PyJWT is more actively maintained and has fewer transitive dependencies
- `python-jose` hasn't had a release since 2022
- PyJWT's `[crypto]` extra bundles `cryptography`, which we need for RSA key handling
- Both achieve the same result; PyJWT is the safer long-term choice

## Auth Bypass Pattern

Auth is **skipped entirely** when `ENTRA_APP_ID` is empty (local dev). This means:
- No Bearer token required when running locally without Entra
- The `user` parameter will be `None` in handlers during local dev
- If future endpoints need user identity for business logic, they must handle the `None` case

## Impact

- All data endpoints (`/generate`, `/jobs/{id}`, `/jobs`) now require Bearer token when Entra is configured
- `/health` remains public
- No changes to existing response shapes or behavior
