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

## 2026-04-24 — TTK Variable Standardization Complete

### Changes Made
- Updated `manifest.json` — changed `webApplicationInfo.clientId` from `${{ENTRA_APP_ID}}` to `${{AAD_APP_CLIENT_ID}}`
- Updated `openapi.yaml` — changed all OAuth2 references:
  - authorizationUrl: `${{ENTRA_TENANT_ID}}` → `${{AAD_APP_TENANT_ID}}`
  - scope: `api://${{ENTRA_APP_ID}}/Podcasts.ReadWrite` → `api://${{AAD_APP_CLIENT_ID}}/Podcasts.ReadWrite`
  - clientId: `${{ENTRA_APP_ID}}` → `${{AAD_APP_CLIENT_ID}}`
- Verified server URL uses `${{DOCTALK_API_URL}}` for proper per-environment interpolation
- Documented decision in `.squad/decisions.md` (TTK Variable Naming Standard)

### Learnings
- TTK variable names: `AAD_APP_CLIENT_ID`, `AAD_APP_TENANT_ID` (not legacy `ENTRA_*` names)
- All appPackage placeholders must use `${{VAR_NAME}}` syntax — TTK only processes this format
- Variable consistency across files is critical: manifest → openapi → teamsapp.yml must all reference same vars
- Tank's `aadApp/create` action now outputs the standard TTK env vars that these files reference
