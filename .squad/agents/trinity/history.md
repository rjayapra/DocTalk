# Trinity Agent History

## 2026-04-24 — UI Task Breakdown Complete
A comprehensive 39-task UI build plan has been created spanning 3 phases. Trinity has been assigned key backend/integration tasks to support the UI implementation. See `.squad/decisions/decisions.md` for full task manifest and assignments.

## Learnings

- **Adaptive Card conditional rendering**: Use `$when` with expressions like `${audio_url != null && audio_url != ''}` to gracefully handle in-progress states where fields like `audio_url` aren't populated yet. This avoids broken links in the card.
- **Plugin function ↔ runtime mapping**: Every function in the `functions` array must also appear in the runtime's `run_for_functions` array — if they diverge, Copilot silently ignores unmapped functions.
- **Design doc is authoritative**: The COPILOT-AGENT-DESIGN.md Section 4 contains exact JSON templates for all agent/plugin files. Always use it as the source of truth for schema versions, field names, and structure.

## 2026-07-25 — Tasks #8–#11: Agent & Plugin Manifests Created

Created `appPackage/declarativeAgent.json` (v1.3 schema) and `appPackage/doctalk-plugin.json` (v2.2 schema) per design doc Section 4:
- **declarativeAgent.json**: Instructions tell Copilot to confirm URL before generating, proactively check status, and present audio with summary. 4 conversation starters. References doctalk-plugin.json.
- **doctalk-plugin.json**: 3 functions — `generatePodcast` (Adaptive Card: queued title, URL, job ID, status), `getJobStatus` (FactSet with status/style, conditional play/download link with `$when` for in-progress graceful handling), `listRecentPodcasts` (data_path: `$`, list-style card).
- All 3 functions registered in `run_for_functions`. OpenApi runtime with OAuthPluginVault auth pointing to openapi.yaml.

## 2025-07-25 — Task #14: SAS Token Generation for Audio URLs

Added `src/api/blob_utils.py` with `add_sas_to_url()` helper that generates user-delegation SAS tokens (1-hour expiry) for blob audio URLs using managed identity. Integrated into `_job_to_response()` in `src/api/main.py`. Empty/non-blob URLs pass through unchanged. Gracefully falls back to the original URL on any error. Added 7 unit tests in `tests/test_blob_utils.py` — all passing.

## Learnings

- **User delegation SAS**: Use `BlobServiceClient.get_user_delegation_key()` + `generate_blob_sas()` for keyless SAS generation. Requires `Storage Blob Delegator` role on the managed identity.
- **Graceful fallback**: SAS generation should never break the API — catch all exceptions and return the raw URL if signing fails. This prevents auth issues from cascading into 500 errors.

## 2025-07-25 — Tasks #4–#7: OpenAPI Spec Created & Validated

Created `appPackage/openapi.yaml` (OpenAPI 3.0.3):
- **Info**: DocTalk API v2.1.0 with production server URL.
- **Schemas**: `JobResponse` (9 fields matching `src/api/main.py` exactly: id, url, style, status, title, audio_url, error, created_at, updated_at) and `GenerateRequest` (url required, style optional with enum [single, conversation]).
- **Paths**: POST /generate (generatePodcast, 202), GET /jobs/{job_id} (getJobStatus, 200/404), GET /jobs (listRecentPodcasts, 200 array). All operations have human-readable summary + description for Copilot NLU.
- **Security**: OAuth2 authorizationCode flow with `$ENTRA_TENANT_ID` and `$ENTRA_APP_ID` placeholders. Scope: `api://$ENTRA_APP_ID/Podcasts.ReadWrite`. Top-level security block requires oauth2.
- **Validation**: YAML parses cleanly, all $ref pointers resolve, operationIds match plugin expectations.

## Learnings

- **JobResponse shape**: The API returns 9 string fields (id, url, style, status, title, audio_url, error, created_at, updated_at). The `status` field uses the JobStatus enum (queued, processing, completed, failed). Keep the OpenAPI spec in sync with `src/api/main.py:JobResponse` and `src/core/models.py:Job`.
- **Entra ID placeholders**: Use `$ENTRA_TENANT_ID` and `$ENTRA_APP_ID` as literal placeholders in OpenAPI auth URLs — these get replaced at deployment time.

## 2025-07-25 — Task #13: OAuth Middleware Added to FastAPI

Created `src/api/auth.py` with Entra ID JWT validation using PyJWT + cryptography:
- **JWKS caching**: Fetches keys from `login.microsoftonline.com/{tenant}/discovery/v2.0/keys` with 1-hour TTL. Automatic cache refresh on kid miss (handles key rotation).
- **Token validation**: Checks RS256 signature, issuer (`https://login.microsoftonline.com/{tenant}/v2.0`), audience (`api://{app-id}`), expiry, and required claims (oid).
- **`get_current_user` dependency**: Extracts oid, name, email from validated token. Returns user claims dict.
- **Local dev bypass**: When `ENTRA_APP_ID` is empty, auth is skipped entirely — dependency returns `None`.
- Applied to `POST /generate`, `GET /jobs/{job_id}`, `GET /jobs`. `GET /health` remains public.
- Added `ENTRA_APP_ID` and `ENTRA_TENANT_ID` to `src/config.py`.
- Added `PyJWT[crypto]` to `requirements.txt`.

## Learnings

- **PyJWT vs python-jose**: PyJWT with `[crypto]` extra (includes cryptography) is lighter and better maintained than python-jose. Use `jwt.algorithms.RSAAlgorithm.from_jwk()` to convert JWKS JSON to public key objects.
- **JWKS key rotation**: Always attempt a cache refresh when a kid is not found before returning 401 — Entra ID rotates signing keys periodically.
- **Auth bypass pattern**: Using `HTTPBearer(auto_error=False)` + checking config at the top of the dependency is the cleanest way to make auth optional for local dev without conditional route registration.
