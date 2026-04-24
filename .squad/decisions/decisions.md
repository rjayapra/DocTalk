# Decision: M365 Copilot Agent — Granular Task Breakdown

**Author:** Morpheus (Lead/Architect)
**Date:** 2025-07-18
**Requested by:** Lucus Crawford
**Input:** COPILOT-AGENT-DESIGN.md

---

## Context

Lucus wants to build the M365 Copilot declarative agent UI described in COPILOT-AGENT-DESIGN.md. This document breaks the implementation roadmap into fine-grained, individually-assignable tasks across all three phases (MVP, v1.1, v2).

### Existing Codebase State

- **API** (`src/api/main.py`): FastAPI with `POST /generate`, `GET /jobs/{job_id}`, `GET /jobs` — already deployed on ACA
- **Models** (`src/core/models.py`): `Job` dataclass with `id`, `url`, `style`, `status`, `title`, `audio_url`, `error`, `created_at`, `updated_at`, `duration_seconds`. `QueueMessage` with `job_id`, `url`, `style`. No `level`, `summary`, or `sections` fields yet.
- **Pipeline** (`src/core/pipeline.py`): `run_pipeline()` — scrape → generate script → synthesize → upload blob
- **Script Generator** (`src/core/script_generator.py`): `SINGLE_NARRATOR_PROMPT`, `TWO_HOST_PROMPT` — no audience level support
- **Worker** (`src/worker/main.py`): Queue poller with KEDA-compatible `process_one()`
- **Infra** (`infra/`): Bicep templates for ACA, storage, etc.
- **Config** (`src/config.py`): Env-based config — no Entra ID / OAuth settings yet

### Key Design Decisions

1. **Declarative Agent + API Plugin** — no Bot Framework; Copilot orchestrates NLU
2. **OAuth 2.0 via Entra ID** — API plugin requires OAuthPluginVault auth
3. **Adaptive Cards** — response rendering for job status, audio playback
4. **Teams Toolkit** — for scaffolding, sideloading, and deployment
5. **SAS tokens** — for time-limited audio download URLs (1-hour expiry)

---

## Phase MVP: Copilot Agent + API Plugin

### Task #1 — Scaffold Teams Toolkit project structure
- **Owner:** Tank (infra)
- **Depends on:** nothing
- **Files to create:**
  - `appPackage/` directory
  - `teamsapp.yml` (Teams Toolkit project config)
  - `teamsapp.local.yml` (local dev config)
  - `env/.env.dev` (placeholder with `DOCTALK_API_URL`, `ENTRA_APP_ID`)
- **Work:**
  1. Run `npx @microsoft/teamsapp-cli init` or manually create the scaffold
  2. Configure `teamsapp.yml` with `provision` and `deploy` lifecycle stages
  3. Configure `teamsapp.local.yml` for sideload dev flow
  4. Create `env/.env.dev` with placeholder values
- **Acceptance criteria:**
  - `teamsapp.yml` and `teamsapp.local.yml` exist with valid YAML
  - `env/.env.dev` has documented placeholder keys
  - `teamsapp validate` passes (or manual YAML lint)

---

### Task #2 — Create app icon assets
- **Owner:** Tank (infra)
- **Depends on:** nothing
- **Files to create:**
  - `appPackage/color.png` (192×192)
  - `appPackage/outline.png` (32×32)
- **Work:**
  1. Create a podcast-themed icon (microphone + doc) at 192×192 for color.png
  2. Create a 32×32 monochrome outline version for outline.png
  3. Icons must meet Teams app requirements (PNG, correct dimensions, transparent background for outline)
- **Acceptance criteria:**
  - `color.png` is 192×192 PNG
  - `outline.png` is 32×32 PNG with transparent background
  - Both pass Teams Toolkit icon validation

---

### Task #3 — Write `manifest.json` (Teams app manifest)
- **Owner:** Tank (infra)
- **Depends on:** #2 (icons)
- **Files to create:**
  - `appPackage/manifest.json`
- **Work:**
  1. Use Teams manifest schema v1.19+
  2. Set `id`, `version`, `name`, `description`, `icons` referencing color.png/outline.png
  3. Add `copilotAgents.declarativeAgents` array pointing to `declarativeAgent.json`
  4. Set `validDomains` to include the ACA API hostname
  5. Configure `webApplicationInfo` with Entra app ID and resource URI
- **Acceptance criteria:**
  - Valid JSON matching Teams manifest schema
  - References `declarativeAgent.json` correctly
  - `validDomains` includes the API hostname from COPILOT-AGENT-DESIGN.md

---

### Task #4 — Write OpenAPI spec: schema definitions
- **Owner:** Trinity (backend)
- **Depends on:** nothing
- **Files to create:**
  - `appPackage/openapi.yaml`
- **Work:**
  1. Create `openapi.yaml` with `openapi: 3.0.3`, `info` block (title: DocTalk API, version: 2.1.0)
  2. Set `servers` URL to the ACA API endpoint
  3. Define `components.schemas.JobResponse` matching the existing `JobResponse` Pydantic model in `src/api/main.py` (fields: `id`, `url`, `style`, `status`, `title`, `audio_url`, `error`, `created_at`, `updated_at`)
  4. Define `components.schemas.GenerateRequest` (fields: `url` required, `style` optional with enum)
- **Acceptance criteria:**
  - Schema properties exactly match existing API response shapes
  - YAML is valid and parseable
  - `$ref` paths are correct

---

### Task #5 — Write OpenAPI spec: path definitions
- **Owner:** Trinity (backend)
- **Depends on:** #4
- **Files to modify:**
  - `appPackage/openapi.yaml`
- **Work:**
  1. Add `POST /generate` path with `operationId: generatePodcast`, request body referencing `GenerateRequest`, 202 response referencing `JobResponse`
  2. Add `GET /jobs/{job_id}` path with `operationId: getJobStatus`, path parameter `job_id`, 200 response referencing `JobResponse`
  3. Add `GET /jobs` path with `operationId: listRecentPodcasts`, query parameter `limit` (integer, default 10), 200 response as array of `JobResponse`
  4. Add `summary` and `description` for each operation (critical for Copilot NLU mapping)
- **Acceptance criteria:**
  - All three operations defined with correct operationIds
  - Parameters and request bodies match existing API signatures
  - Each operation has human-readable summary/description

---

### Task #6 — Write OpenAPI spec: security/auth configuration
- **Owner:** Trinity (backend)
- **Depends on:** #5
- **Files to modify:**
  - `appPackage/openapi.yaml`
- **Work:**
  1. Add `components.securitySchemes` with OAuth2 config pointing to Entra ID endpoints
  2. Add top-level `security` requiring the OAuth2 scheme
  3. Authorization URL: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize`
  4. Token URL: `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token`
  5. Scope: `api://<app-id>/Podcasts.ReadWrite`
- **Acceptance criteria:**
  - OAuth2 security scheme defined with correct Entra ID URLs
  - All operations require the security scheme
  - Placeholder for tenant-id/app-id clearly documented

---

### Task #7 — Validate OpenAPI spec
- **Owner:** Trinity (backend)
- **Depends on:** #6
- **Files:** `appPackage/openapi.yaml` (read-only validation)
- **Work:**
  1. Install `swagger-cli` or `openapi-generator-cli`
  2. Run `swagger-cli validate appPackage/openapi.yaml`
  3. Test with `spectral lint appPackage/openapi.yaml` for best practices
  4. Verify all `$ref` pointers resolve
  5. Fix any validation errors
- **Acceptance criteria:**
  - Zero validation errors from swagger-cli
  - Zero critical warnings from Spectral (info/hints acceptable)

---

### Task #8 — Write `declarativeAgent.json`
- **Owner:** Trinity (backend)
- **Depends on:** nothing
- **Files to create:**
  - `appPackage/declarativeAgent.json`
- **Work:**
  1. Use schema `https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.3/schema.json`
  2. Set `name: "DocTalk"`, `description`, and `instructions` per the design doc
  3. Instructions must tell Copilot to: confirm URL before generating, proactively check status, present audio with summary
  4. Add 4 `conversation_starters` per design doc
  5. Add `actions` array referencing `doctalk-plugin.json`
- **Acceptance criteria:**
  - Valid JSON matching v1.3 schema
  - Instructions are clear and actionable for Copilot orchestrator
  - All 4 conversation starters present
  - Action references `doctalk-plugin.json`

---

### Task #9 — Write `doctalk-plugin.json`: generatePodcast function
- **Owner:** Trinity (backend)
- **Depends on:** #4 (OpenAPI spec schemas exist)
- **Files to create:**
  - `appPackage/doctalk-plugin.json`
- **Work:**
  1. Use schema `https://developer.microsoft.com/json-schemas/copilot/plugin/v2.2/schema.json`
  2. Set `name_for_human`, `description_for_human`, `namespace: "doctalk"`
  3. Define `generatePodcast` function with Adaptive Card `static_template` showing: "🎙️ Podcast Queued" title, URL, Job ID, Status (per design doc)
  4. Add `runtimes` array with OpenApi type, `OAuthPluginVault` auth, spec pointing to `openapi.yaml`
- **Acceptance criteria:**
  - `generatePodcast` function defined with correct Adaptive Card template
  - Card renders job submission confirmation fields
  - Runtime references `openapi.yaml`

---

### Task #10 — Write `doctalk-plugin.json`: getJobStatus function
- **Owner:** Trinity (backend)
- **Depends on:** #9
- **Files to modify:**
  - `appPackage/doctalk-plugin.json`
- **Work:**
  1. Add `getJobStatus` function to the `functions` array
  2. Create Adaptive Card `static_template` showing: title ("🎙️ ${title}"), FactSet with Status + Style, and a Play/Download link using `${audio_url}`
  3. Ensure card gracefully handles in-progress state (no audio_url yet)
- **Acceptance criteria:**
  - Card shows title, status, style as FactSet
  - Audio link only renders when audio_url is present
  - Function maps to `getJobStatus` operationId

---

### Task #11 — Write `doctalk-plugin.json`: listRecentPodcasts function
- **Owner:** Trinity (backend)
- **Depends on:** #9
- **Files to modify:**
  - `appPackage/doctalk-plugin.json`
- **Work:**
  1. Add `listRecentPodcasts` function to the `functions` array
  2. Add `response_semantics` with `data_path: "$"` (array response)
  3. Optionally add a list-style Adaptive Card template showing title + status for each job
  4. Add function to `run_for_functions` in the runtime
- **Acceptance criteria:**
  - Function defined with correct operationId mapping
  - Included in `run_for_functions` array
  - Template handles array of jobs

---

### Task #12 — Register Entra ID app for API OAuth
- **Owner:** Tank (infra)
- **Depends on:** nothing
- **Files to create/modify:**
  - `infra/entra-app-registration.md` (documentation/runbook)
  - Optionally `infra/scripts/register-entra-app.sh`
- **Work:**
  1. Register new app in Entra ID (single tenant)
  2. Configure API scope: `api://<app-id>/Podcasts.ReadWrite`
  3. Set redirect URI: `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`
  4. Configure `accessTokenAcceptedVersion: 2`
  5. Document client ID, tenant ID for use in manifest and OpenAPI spec
  6. Optionally script this with `az ad app create` for repeatability
- **Acceptance criteria:**
  - App registered with correct scope and redirect URI
  - Runbook documented so any team member can replicate
  - Client ID and tenant ID captured (not hardcoded in source — use env vars)

---

### Task #13 — Add OAuth middleware to FastAPI
- **Owner:** Trinity (backend)
- **Depends on:** #12 (need Entra app ID)
- **Files to create/modify:**
  - `src/api/auth.py` (new)
  - `src/api/main.py` (modify)
  - `src/config.py` (modify)
  - `requirements.txt` (modify if needed)
- **Work:**
  1. Create `src/api/auth.py` with JWT token validation using `python-jose` or `PyJWT`
  2. Validate issuer (`https://login.microsoftonline.com/{tenant}/v2.0`), audience (`api://<app-id>`), and token signature
  3. Create a FastAPI `Depends()` dependency `get_current_user` that extracts user claims
  4. Add `ENTRA_APP_ID` and `ENTRA_TENANT_ID` to `Config` class
  5. Apply auth dependency to `POST /generate`, `GET /jobs/{job_id}`, `GET /jobs` (keep `/health` public)
  6. Add `python-jose[cryptography]` or `PyJWT` + `cryptography` to `requirements.txt` if not present
- **Acceptance criteria:**
  - All data endpoints require valid Bearer token
  - `/health` remains public
  - Invalid/missing token returns 401
  - Config reads Entra settings from env vars
  - Existing tests still pass (or are updated)

---

### Task #14 — Add SAS token generation for audio URLs
- **Owner:** Trinity (backend)
- **Depends on:** nothing (enhances existing audio_url)
- **Files to modify:**
  - `src/api/main.py`
  - `src/core/pipeline.py` (possibly)
- **Work:**
  1. When returning `audio_url` in `_job_to_response()`, check if it's a blob URL
  2. Generate a user delegation SAS token with 1-hour expiry using `generate_blob_sas()`
  3. Append SAS token to the blob URL
  4. Ensure the managed identity has `Storage Blob Delegator` role
- **Acceptance criteria:**
  - `audio_url` in API responses includes a time-limited SAS token
  - SAS expires after 1 hour
  - Download works with the SAS URL
  - Empty `audio_url` (job not complete) is returned as-is

---

### Task #15 — Sideload and smoke test in Teams
- **Owner:** Switch (tester)
- **Depends on:** #1, #3, #7, #8, #9, #10, #11, #12, #13
- **Files to create:**
  - `tests/e2e/copilot-agent-smoke.md` (manual test script)
- **Work:**
  1. Run `teamsapp provision --env dev` and `teamsapp deploy --env dev`
  2. Open Teams → Apps → find DocTalk → enable
  3. Test each conversation starter
  4. Test: "Generate a podcast about Azure Container Apps" → verify 202 → Adaptive Card with job ID
  5. Test: "Check my latest podcast" → verify status card
  6. Test: "List my recent podcasts" → verify list response
  7. Test error case: invalid URL → verify graceful error
  8. Document results and any issues found
- **Acceptance criteria:**
  - Agent appears in Teams and responds to all 4 conversation starters
  - Generate flow returns Adaptive Card with job ID and status
  - Status check returns updated status
  - List shows recent jobs
  - Errors are handled gracefully (no raw JSON errors shown to user)

---

### Task #16 — Publish to org app catalog
- **Owner:** Tank (infra)
- **Depends on:** #15 (smoke test passes)
- **Files to create:**
  - `docs/publish-to-catalog.md` (runbook)
- **Work:**
  1. Package the app using `teamsapp package --env dev`
  2. Upload to org app catalog via Teams Admin Center or `teamsapp publish`
  3. Configure app policies for target user group
  4. Document the publish process as a runbook
- **Acceptance criteria:**
  - App available in org catalog
  - Target users can find and install DocTalk from catalog
  - Runbook covers the full publish flow

---

## Phase v1.1: Summarization + Audience Level

### Task #17 — Add `level` field to Job model and QueueMessage
- **Owner:** Trinity (backend)
- **Depends on:** nothing (can start in parallel with MVP)
- **Files to modify:**
  - `src/core/models.py`
- **Work:**
  1. Add `level: str = "intermediate"` field to `Job` dataclass
  2. Add `level` to `to_table_entity()` and `from_table_entity()`
  3. Add `level: str = "intermediate"` to `QueueMessage` dataclass
- **Acceptance criteria:**
  - `Job` and `QueueMessage` have `level` field with default "intermediate"
  - Table entity serialization includes `level`
  - Backward compatible (existing entities without `level` default to "intermediate")

---

### Task #18 — Add `level` parameter to API endpoints
- **Owner:** Trinity (backend)
- **Depends on:** #17
- **Files to modify:**
  - `src/api/main.py`
- **Work:**
  1. Add `level: str = "intermediate"` to `GenerateRequest` with validation (`beginner`, `intermediate`, `advanced`)
  2. Pass `level` through to `Job` construction in `generate()` endpoint
  3. Include `level` in queue message serialization
  4. Add `level` to `JobResponse` model
  5. Map `level` in `_job_to_response()`
- **Acceptance criteria:**
  - `POST /generate` accepts optional `level` parameter
  - Invalid levels rejected with 422
  - `level` appears in job responses
  - Default is "intermediate" when omitted

---

### Task #19 — Modify prompt templates to accept audience level
- **Owner:** Trinity (backend)
- **Depends on:** #17
- **Files to modify:**
  - `src/core/script_generator.py`
- **Work:**
  1. Update `SINGLE_NARRATOR_PROMPT` and `TWO_HOST_PROMPT` to include a `{level}` placeholder or conditional section
  2. For "beginner": add "Assume no prior Azure knowledge. Define all acronyms. Use analogies."
  3. For "advanced": add "Assume deep Azure familiarity. Focus on advanced patterns, gotchas, and best practices."
  4. For "intermediate": keep current behavior
  5. Update `generate_script()` to accept `level` parameter and inject into prompt
- **Acceptance criteria:**
  - `generate_script(docs, style, level)` produces noticeably different scripts per level
  - Default behavior unchanged when level="intermediate"
  - Prompt additions don't break existing script format

---

### Task #20 — Add `summary` field to Job model
- **Owner:** Trinity (backend)
- **Depends on:** nothing
- **Files to modify:**
  - `src/core/models.py`
- **Work:**
  1. Add `summary: str = ""` to `Job` dataclass
  2. Add `summary` to `to_table_entity()` and `from_table_entity()`
- **Acceptance criteria:**
  - `Job` has `summary` field defaulting to empty string
  - Backward compatible with existing table entities

---

### Task #21 — Generate summary during script generation
- **Owner:** Trinity (backend)
- **Depends on:** #20
- **Files to modify:**
  - `src/core/script_generator.py`
  - `src/core/pipeline.py`
- **Work:**
  1. After generating the script, make a second (cheap) OpenAI call to generate a 2–3 sentence summary
  2. Prompt: "Summarize the following podcast script in 2-3 sentences for a listener preview: {script}"
  3. Return both `script` and `summary` from `generate_script()` (change return type to `dict` or `NamedTuple`)
  4. Update `run_pipeline()` to capture `summary` and set `job.summary`
- **Acceptance criteria:**
  - Summary is 2-3 sentences, readable as a podcast preview
  - Summary is stored in `job.summary` and persisted to Table Storage
  - Pipeline still works end-to-end

---

### Task #22 — Expose `summary` in API responses
- **Owner:** Trinity (backend)
- **Depends on:** #20, #21
- **Files to modify:**
  - `src/api/main.py`
- **Work:**
  1. Add `summary: str` to `JobResponse`
  2. Map `summary` in `_job_to_response()`
- **Acceptance criteria:**
  - `GET /jobs/{id}` and `GET /jobs` include `summary` field
  - Empty string when summary not yet generated

---

### Task #23 — Update OpenAPI spec for v1.1 fields
- **Owner:** Trinity (backend)
- **Depends on:** #7, #18, #22
- **Files to modify:**
  - `appPackage/openapi.yaml`
- **Work:**
  1. Add `level` to `GenerateRequest` schema with enum constraint
  2. Add `summary` and `level` to `JobResponse` schema
  3. Bump API version to 2.2.0
  4. Re-validate spec
- **Acceptance criteria:**
  - OpenAPI spec matches new API contract
  - Spec validates cleanly

---

### Task #24 — Update Adaptive Card templates for summary + level
- **Owner:** Trinity (backend)
- **Depends on:** #23
- **Files to modify:**
  - `appPackage/doctalk-plugin.json`
- **Work:**
  1. Update `generatePodcast` card to show `${level}` if provided
  2. Update `getJobStatus` card to include `${summary}` as a TextBlock below the FactSet
  3. Add `Level` to the FactSet in status card
  4. Ensure summary only renders when non-empty
- **Acceptance criteria:**
  - Level shown in both generate and status cards
  - Summary displayed in status card when available
  - Cards render correctly with and without optional fields

---

### Task #25 — Write unit tests for level parameter
- **Owner:** Switch (tester)
- **Depends on:** #18, #19
- **Files to create:**
  - `tests/test_level_parameter.py`
- **Work:**
  1. Test `POST /generate` with each level value (beginner, intermediate, advanced)
  2. Test `POST /generate` with invalid level → 422
  3. Test `POST /generate` without level → defaults to intermediate
  4. Test that `generate_script()` produces different prompts per level
  5. Test Job model serialization with level
- **Acceptance criteria:**
  - All tests pass
  - Coverage for all three levels plus default and invalid cases

---

### Task #26 — Write unit tests for summary generation
- **Owner:** Switch (tester)
- **Depends on:** #21, #22
- **Files to create:**
  - `tests/test_summary.py`
- **Work:**
  1. Test that pipeline populates `job.summary` after script generation
  2. Test `GET /jobs/{id}` includes `summary` field
  3. Test backward compatibility — job without summary returns empty string
  4. Mock OpenAI call to test summary generation logic
- **Acceptance criteria:**
  - All tests pass
  - Mocked tests don't require live Azure services

---

### Task #27 — E2E test: v1.1 agent features in Teams
- **Owner:** Switch (tester)
- **Depends on:** #24, #25, #26
- **Files to modify:**
  - `tests/e2e/copilot-agent-smoke.md` (extend)
- **Work:**
  1. Sideload updated agent
  2. Test: "Create a beginner-level episode on Azure Functions" → verify level parameter passed
  3. Test: completed job shows summary in Adaptive Card
  4. Test: level appears in status card
  5. Verify backward compat — old jobs without summary/level still display correctly
- **Acceptance criteria:**
  - Level selection works end-to-end
  - Summary appears in completed job cards
  - No regression on MVP functionality

---

## Phase v2: Interactive Playback

### Task #28 — Add `sections` field to Job model
- **Owner:** Trinity (backend)
- **Depends on:** nothing
- **Files to modify:**
  - `src/core/models.py`
- **Work:**
  1. Add `sections: str = ""` to Job (JSON-serialized list, stored as string in Table Storage)
  2. Define section structure: `[{"title": "...", "timestamp": 0.0}]`
  3. Add serialization/deserialization helpers
  4. Update `to_table_entity()` and `from_table_entity()`
- **Acceptance criteria:**
  - Sections round-trip through Table Storage
  - Empty/missing sections default gracefully

---

### Task #29 — Extract sections during script generation
- **Owner:** Trinity (backend)
- **Depends on:** #28
- **Files to modify:**
  - `src/core/script_generator.py`
  - `src/core/pipeline.py`
- **Work:**
  1. After generating the script, use OpenAI to extract topic sections with approximate timestamps
  2. Prompt: "Extract the main sections/topics from this podcast script as JSON array with title and approximate timestamp_seconds"
  3. Store parsed sections in `job.sections`
  4. Update pipeline to capture sections
- **Acceptance criteria:**
  - Sections extracted with reasonable titles and timestamps
  - Sections stored in job record
  - Pipeline handles extraction failure gracefully (empty sections, not a crash)

---

### Task #30 — Store generated scripts in Blob Storage
- **Owner:** Trinity (backend)
- **Depends on:** nothing
- **Files to modify:**
  - `src/core/pipeline.py`
- **Work:**
  1. After generating the script, upload it to Blob Storage as `{job_id}.txt`
  2. Add `script_url` field to Job model
  3. Store blob URL in job record
  4. This enables RAG-style Q&A in the ask endpoint
- **Acceptance criteria:**
  - Script text uploaded alongside audio
  - `script_url` populated in job record
  - Blob naming is consistent (`{job_id}.txt` next to `{job_id}.mp3`)

---

### Task #31 — Create `POST /ask` endpoint
- **Owner:** Trinity (backend)
- **Depends on:** #30
- **Files to create/modify:**
  - `src/api/main.py` (add endpoint)
  - `src/api/ask.py` (new, RAG logic)
- **Work:**
  1. Create `POST /ask` accepting `{ job_id, question }`
  2. Retrieve the stored script from Blob Storage
  3. Send script + question to Azure OpenAI as context
  4. Prompt: "Based on this podcast script about Azure documentation, answer the user's question: {question}\n\nScript:\n{script}"
  5. Return `{ answer, sources: [{section, timestamp}] }`
  6. Apply same OAuth auth dependency
- **Acceptance criteria:**
  - Endpoint returns contextual answers based on podcast content
  - References relevant sections when possible
  - Handles missing job_id (404) and missing script (400) gracefully
  - Auth required

---

### Task #32 — Add `askQuestion` function to API plugin
- **Owner:** Trinity (backend)
- **Depends on:** #31
- **Files to modify:**
  - `appPackage/doctalk-plugin.json`
  - `appPackage/openapi.yaml`
- **Work:**
  1. Add `POST /ask` to OpenAPI spec with request/response schemas
  2. Add `askQuestion` function to plugin with Adaptive Card template
  3. Card shows answer text and optional section references
  4. Add to `run_for_functions` in runtime
- **Acceptance criteria:**
  - OpenAPI spec includes `/ask` endpoint
  - Plugin function defined with appropriate card template
  - Spec validates cleanly

---

### Task #33 — Update agent instructions for Q&A flow
- **Owner:** Trinity (backend)
- **Depends on:** #32
- **Files to modify:**
  - `appPackage/declarativeAgent.json`
- **Work:**
  1. Update `instructions` to guide Copilot on when to use `askQuestion` vs `getJobStatus`
  2. Add instruction: "When the user asks a follow-up question about a podcast they've generated, use the askQuestion action with the relevant job_id"
  3. Add new conversation starter: "What does this podcast say about scaling?"
- **Acceptance criteria:**
  - Instructions clearly differentiate between status checks and Q&A
  - Copilot correctly routes follow-up questions to askQuestion

---

### Task #34 — Update Adaptive Card for sections display
- **Owner:** Trinity (backend)
- **Depends on:** #28, #29
- **Files to modify:**
  - `appPackage/doctalk-plugin.json`
- **Work:**
  1. Update `getJobStatus` Adaptive Card to include a sections list
  2. Each section shows title and timestamp
  3. Sections rendered as a numbered list or ColumnSet
  4. Handle case where sections is empty (don't show section heading)
- **Acceptance criteria:**
  - Sections visible in completed job card
  - Graceful handling when no sections available
  - Card doesn't break for old jobs without sections

---

### Task #35 — Expose `sections` in API responses
- **Owner:** Trinity (backend)
- **Depends on:** #28
- **Files to modify:**
  - `src/api/main.py`
  - `appPackage/openapi.yaml`
- **Work:**
  1. Add `sections` to `JobResponse` (as list of objects with `title` and `timestamp`)
  2. Map sections in `_job_to_response()` (deserialize from JSON string)
  3. Update OpenAPI spec with sections schema
- **Acceptance criteria:**
  - API returns sections array in job responses
  - Empty array when no sections
  - OpenAPI spec matches

---

### Task #36 — Playback speed options (documentation/guidance)
- **Owner:** Trinity (backend)
- **Depends on:** #34
- **Files to create:**
  - `docs/playback-speed.md`
- **Work:**
  1. Document that Adaptive Cards don't support native audio playback controls
  2. Options: (a) re-encode audio at different speeds server-side, (b) embed a lightweight web player via URL
  3. If option (a): add `GET /jobs/{job_id}/audio?speed=1.5` endpoint that returns re-encoded audio
  4. If option (b): create a simple HTML page hosted on the API that plays audio with speed control
  5. Recommend approach and document trade-offs
- **Acceptance criteria:**
  - Decision documented with trade-offs
  - If implementing: endpoint or page works with speed parameter
  - Design doc updated with chosen approach

---

### Task #37 — Write unit tests for ask endpoint
- **Owner:** Switch (tester)
- **Depends on:** #31
- **Files to create:**
  - `tests/test_ask_endpoint.py`
- **Work:**
  1. Test `POST /ask` with valid job_id and question → answer returned
  2. Test with non-existent job_id → 404
  3. Test with job that has no script → 400
  4. Test auth required → 401 without token
  5. Mock Azure OpenAI responses
- **Acceptance criteria:**
  - All tests pass
  - Error cases covered
  - Mocked — no live services required

---

### Task #38 — Write unit tests for sections extraction
- **Owner:** Switch (tester)
- **Depends on:** #29, #35
- **Files to create:**
  - `tests/test_sections.py`
- **Work:**
  1. Test sections extraction from a sample script
  2. Test sections serialization/deserialization in Job model
  3. Test API response includes sections
  4. Test backward compat — old jobs return empty sections
  5. Mock OpenAI for section extraction
- **Acceptance criteria:**
  - All tests pass
  - Covers happy path, empty sections, and malformed extraction

---

### Task #39 — E2E test: v2 interactive features in Teams
- **Owner:** Switch (tester)
- **Depends on:** #32, #33, #34, #37, #38
- **Files to modify:**
  - `tests/e2e/copilot-agent-smoke.md` (extend)
- **Work:**
  1. Sideload updated agent
  2. Generate a podcast → wait for completion
  3. Ask: "What does this podcast say about scaling?" → verify answer via askQuestion
  4. Verify sections appear in completed job card
  5. Test follow-up conversation flow
  6. Test error: ask question about non-existent job
- **Acceptance criteria:**
  - Q&A flow works end-to-end
  - Sections display correctly
  - Agent correctly routes follow-up questions
  - No regression on v1.1 features

---

## Dependency Graph Summary

```
Phase MVP:
  #1 (scaffold) ──┐
  #2 (icons)   ───┤──→ #3 (manifest)
                   │
  #4 (schemas) ──→ #5 (paths) ──→ #6 (auth) ──→ #7 (validate)
                   │
  #8 (agent json)  │
  #9 (plugin gen) ─┤──→ #10 (plugin status)
                   │──→ #11 (plugin list)
  #12 (Entra ID) ──┤──→ #13 (OAuth middleware)
  #14 (SAS tokens) │
                   └──→ #15 (smoke test) ──→ #16 (publish)

Phase v1.1:
  #17 (level model) ──→ #18 (level API) ──→ #25 (level tests)
  #17 ──→ #19 (level prompts) ──→ #25
  #20 (summary model) ──→ #21 (summary gen) ──→ #22 (summary API) ──→ #26 (summary tests)
  #18, #22 ──→ #23 (OpenAPI update) ──→ #24 (card update) ──→ #27 (E2E test)

Phase v2:
  #28 (sections model) ──→ #29 (sections extract) ──→ #34 (sections card)
  #28 ──→ #35 (sections API)
  #30 (script blob) ──→ #31 (ask endpoint) ──→ #32 (ask plugin) ──→ #33 (agent instructions)
  #31 ──→ #37 (ask tests)
  #29, #35 ──→ #38 (sections tests)
  #32, #33, #34, #37, #38 ──→ #39 (E2E test)
  #36 (playback speed) — independent research task
```

---

## Owner Summary

| Owner | Tasks |
|-------|-------|
| **Tank (infra)** | #1, #2, #3, #12, #16 |
| **Trinity (backend)** | #4, #5, #6, #7, #8, #9, #10, #11, #13, #14, #17, #18, #19, #20, #21, #22, #23, #24, #28, #29, #30, #31, #32, #33, #34, #35, #36 |
| **Switch (tester)** | #15, #25, #26, #27, #37, #38, #39 |

---

## Parallelism Opportunities

**Can start immediately (no dependencies):**
- Tank: #1, #2, #12
- Trinity: #4, #8, #14, #17, #20, #28, #30

**After MVP core is done, v1.1 can start in parallel:**
- Trinity can begin #17–#22 while Switch tests MVP (#15)
