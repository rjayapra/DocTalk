# Squad Decisions

## Active Decisions

### Decision: Teams Toolkit Project Structure

**Date:** 2025-07-17
**Author:** Tank (Infrastructure / DevOps)
**Status:** Implemented

**Context:** DocTalk needs a Teams Toolkit project scaffold to support the M365 Copilot declarative agent with API plugin architecture described in COPILOT-AGENT-DESIGN.md.

**Decision:**
- Use Teams Toolkit v1.7 schema for `teamsapp.yml` / `teamsapp.local.yml`
- Use Teams manifest schema v1.19 (required for `copilotAgents.declarativeAgents`)
- Place all Teams app package files in `appPackage/` directory
- Environment variables in `env/.env.dev` using `${{VAR}}` interpolation syntax
- Placeholder icons created as valid PNGs with documented replacement specs
- `declarativeAgent.json` referenced from manifest but not yet created (owned by agent definition task)
- `webApplicationInfo` uses Entra app ID placeholder — requires actual app registration before deployment

**Implications:**
- Agent definition files (`declarativeAgent.json`, `doctalk-plugin.json`, `openapi.yaml`) need to be created in `appPackage/`
- Entra ID app registration must be completed and IDs populated in `env/.env.dev`
- Placeholder icons must be replaced with branded artwork before publishing to Teams store

---

### Decision: Entra ID App Registration Approach

**Date:** 2025-07-21
**Author:** Tank (Infrastructure / DevOps)
**Status:** Proposed

**Context:** Task #12 requires an Entra ID app registration to enable OAuth 2.0 between M365 Copilot and the DocTalk API.

**Decision:**
- The app registration is handled via an Azure CLI script (`infra/scripts/register-entra-app.sh`), not Bicep, because Entra ID app registrations are not Azure Resource Manager resources and cannot be managed by Bicep/ARM templates.
- Client ID and tenant ID are exposed as environment variables (`ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`) and must never be hardcoded in source files.
- The app name defaults to "DocTalk API" but can be overridden via `ENTRA_APP_NAME` env var for multi-environment setups.

**Impact:**
- Other agents referencing auth config (OpenAPI spec, Teams manifest, `.env.dev`) should use `ENTRA_CLIENT_ID` and `ENTRA_TENANT_ID` env vars.
- The script should be run once per environment (dev, staging, prod) to create separate app registrations.

---

### Decision: OpenAPI Spec Structure

**Date:** 2025-07-25
**Author:** Trinity
**Status:** Implemented

**Context:** Tasks #4–#7 required creating the OpenAPI spec that the Copilot plugin references for API calls.

**Decisions:**
1. **Version 3.0.3** — widest tooling compatibility for Teams Toolkit and Copilot plugin runtime.
2. **Schema fields match `src/api/main.py:JobResponse` exactly** — 9 fields, no extras, no omissions. The `status` enum mirrors `core/models.py:JobStatus`.
3. **Style enum restricted to `[single, conversation]`** — matches the two podcast generation modes.
4. **OAuth2 authorizationCode flow** with `$ENTRA_TENANT_ID` / `$ENTRA_APP_ID` placeholders documented in the info description.
5. **operationIds** (`generatePodcast`, `getJobStatus`, `listRecentPodcasts`) match the function names in `doctalk-plugin.json`.

**Impact:**
- Plugin file references these operationIds — any rename must update both files.
- Schema changes in `main.py` must be reflected here to avoid runtime deserialization failures.

---

### Decision: Agent & Plugin Manifest Structure

**Date:** 2025-07-25
**Author:** Trinity
**Status:** Implemented

**Context:** Tasks #8–#11 required creating the M365 Copilot declarative agent and API plugin manifests.

**Decision:**
- Used exact JSON templates from COPILOT-AGENT-DESIGN.md Section 4 as the base
- Enhanced `getJobStatus` Adaptive Card with `$when` conditional rendering to gracefully handle in-progress jobs (no broken audio link when `audio_url` is null)
- Added optional list-style Adaptive Card to `listRecentPodcasts` (design doc left this open)
- All files live in `appPackage/` directory per the project structure in Section 5

**Impact:**
- Any changes to API response shapes (field names, nesting) must be reflected in the Adaptive Card templates' data binding expressions
- The `openapi.yaml` file (referenced by the plugin runtime) must exist in `appPackage/` for the plugin to function

---

### Decision: User-Delegation SAS for Audio Blob URLs

**Date:** 2025-07-25
**Author:** Trinity
**Status:** Implemented (Task #14)

**Context:** Audio files are stored in Azure Blob Storage with private access. The API needs to return downloadable URLs.

**Decision:** Use **user-delegation SAS tokens** (not account keys or connection strings) for audio URL signing:

- Generated via `BlobServiceClient.get_user_delegation_key()` + `generate_blob_sas()`
- 1-hour expiry, read-only permission
- Applied in `_job_to_response()` so all API endpoints get signed URLs consistently
- Graceful fallback: if SAS generation fails, return the raw blob URL (prevents cascading 500s)

**Required Azure RBAC:**
- **Storage Blob Data Reader** — to read blobs
- **Storage Blob Delegator** — to request user delegation keys for SAS generation

**Alternatives Considered:**
- **Account-key SAS**: Rejected — violates zero-trust; account keys are shared secrets.
- **Pre-signed URLs at upload time**: Rejected — expiry would be unpredictable and long-lived tokens are a security risk.
- **Container-level public access**: Rejected — exposes all audio files without authentication.

---

### Decision: OAuth Middleware Implementation (Task #13)

**Date:** 2025-07-25
**Author:** Trinity (Backend Developer)
**Status:** Implemented

**Context:** Task #13 required protecting data endpoints with JWT token validation.

**Decision:** Use **PyJWT + cryptography** (via `PyJWT[crypto]`) for JWT token validation instead of `python-jose[cryptography]`.

**Rationale:**
- PyJWT is more actively maintained and has fewer transitive dependencies
- `python-jose` hasn't had a release since 2022
- PyJWT's `[crypto]` extra bundles `cryptography`, which we need for RSA key handling
- Both achieve the same result; PyJWT is the safer long-term choice

**Auth Bypass Pattern:** Auth is **skipped entirely** when `ENTRA_APP_ID` is empty (local dev). This means:
- No Bearer token required when running locally without Entra
- The `user` parameter will be `None` in handlers during local dev
- If future endpoints need user identity for business logic, they must handle the `None` case

**Impact:**
- All data endpoints (`/generate`, `/jobs/{id}`, `/jobs`) now require Bearer token when Entra is configured
- `/health` remains public
- No changes to existing response shapes or behavior

### Decision: User Directive — Retain OAuth/Entra ID Authentication

**Date:** 2026-04-24T20:54
**Author:** Lucus Crawford (via Copilot)
**Status:** Active

**Context:** Earlier discussion raised simplifying Wave 1 by removing OAuth and Entra ID authentication. User clarified that OAuth should be retained in the implementation.

**Decision:**
- DO NOT remove OAuth authentication
- Keep Entra ID auth in the Teams app manifest and API plugin config
- Maintain the OAuth 2.0 authorization code flow for M365 Copilot → DocTalk API

**Impact:**
- Tank and Trinity work ensures `aad.manifest.json`, `teamsapp.yml`, `manifest.json`, and `openapi.yaml` all support OAuth
- API endpoints must validate JWT tokens from Entra ID
- Users must authenticate via M365 identity to use the Copilot agent

---

### Decision: AAD Lifecycle in teamsapp.yml

**Date:** 2026-04-24T21:11
**Author:** Tank (Infrastructure / DevOps)
**Status:** Implemented

**Context:** M365 Copilot agent deployment was blocked because `teamsapp.yml` lacked `aadApp/create` and `aadApp/update` lifecycle steps. Without these, `teamsapp provision` couldn't manage the Entra app registration needed for OAuth.

**Decision:**
- Added `aadApp/create` as the first provision step — Teams Toolkit now manages Entra app registration automatically
- Created `appPackage/aad.manifest.json` for `aadApp/update` to configure scopes (`Podcasts.ReadWrite`) and Teams redirect URI
- Standardized all env vars to TTK convention (`AAD_APP_CLIENT_ID`, `AAD_APP_OBJECT_ID`, `AAD_APP_TENANT_ID`, `SECRET_AAD_APP_CLIENT_SECRET`)
- Added `deploy` section for manifest-only updates without full re-provision
- Generated real projectId (`5e4ba15d-00fd-44f7-b5bd-9de9eb9fca6c`) for idempotent Graph resource deployments

**Impact:**
- `manifest.json` must use `${{AAD_APP_CLIENT_ID}}` (not legacy `${{ENTRA_APP_ID}}`)
- `openapi.yaml` OAuth config must reference `${{AAD_APP_CLIENT_ID}}` and `${{AAD_APP_TENANT_ID}}`
- Old `ENTRA_CLIENT_ID` / `ENTRA_TENANT_ID` vars are deprecated
- `teamsapp provision` now fully manages the Entra app registration lifecycle

---

### Decision: TTK Variable Naming Standard — AAD_APP_* Prefix

**Date:** 2026-04-24T21:11
**Author:** Trinity (Backend Developer)
**Status:** Implemented

**Context:** `manifest.json` and `openapi.yaml` used inconsistent placeholder names (`ENTRA_APP_ID`, `ENTRA_TENANT_ID`) that Teams Toolkit does not natively output. TTK's `aadApp/create` action outputs `clientId`, `objectId`, `tenantId`, `clientSecret` mapped to env vars with the `AAD_APP_*` prefix.

**Decision:**
- All appPackage placeholders now use TTK `${{VAR_NAME}}` interpolation syntax (not shell `$VAR`)
- Variable names align with TTK standard outputs:
  - `AAD_APP_CLIENT_ID` (mapped from `aadApp/create` clientId output)
  - `AAD_APP_OBJECT_ID` (mapped from `aadApp/create` objectId output)
  - `AAD_APP_TENANT_ID` (mapped from `aadApp/create` tenantId output)
  - `SECRET_AAD_APP_CLIENT_SECRET` (mapped from `aadApp/create` clientSecret output)
  - `DOCTALK_API_DOMAIN` (API hostname for manifest validDomains)
  - `DOCTALK_API_URL` (full API URL for openapi.yaml servers)
- Legacy `ENTRA_*` variable names are no longer used

**Impact:**
- `manifest.json` webApplicationInfo.clientId: `${{AAD_APP_CLIENT_ID}}`
- `openapi.yaml` OAuth2 authorizationUrl: `https://login.microsoftonline.com/${{AAD_APP_TENANT_ID}}/oauth2/v2.0/authorize`
- `openapi.yaml` scope: `api://${{AAD_APP_CLIENT_ID}}/Podcasts.ReadWrite`
- `env/.env.dev` must define all six variables
- Any future appPackage files must follow this convention

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
