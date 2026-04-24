# Trinity — History

## Learnings

### 2026-04-24 — Static File Serving and Root Redirect

- **Purpose:** Serve the webapp from the same FastAPI container to eliminate need for separate frontend hosting.
- **Changes made:** 
  - Added `StaticFiles`, `RedirectResponse`, `FileResponse`, `Path` imports.
  - Added CORS middleware to allow webapp to call API endpoints (allow all origins for hackathon scope).
  - Added root `/` redirect to `/app/index.html` for UX (user navigates to base URL, gets webapp).
  - Mounted `/app` path to serve `src/webapp/` directory with `html=True` for index.html fallback.
- **Critical ordering:** Static mount MUST come after all API route definitions to avoid shadowing API endpoints.
- **Defensive coding:** Added `if webapp_dir.exists()` guard to prevent crashes when webapp directory is not present (dev scenarios).
- **Docker compatibility:** Existing `Dockerfile.api` already copies entire `src/` tree, so `src/webapp/` is automatically included.
- **File location:** `src/api/main.py` — webapp files live at `src/webapp/` and are accessed via `/app/*` endpoint.
- **Integration complete:** Webapp now fully integrated; users can navigate to base URL and access the complete web UI.

### 2025-07-17 — Copilot Extension Endpoint
- Added `src/api/copilot.py` with a `POST /copilot/agent` SSE-streaming endpoint and `GET /copilot/agent` discovery metadata endpoint.
- Wired the router into `src/api/main.py` via `include_router`.
- The extension calls the existing `/generate` and `/jobs/{id}` endpoints internally via `httpx` (localhost by default, configurable via `DOCTALK_API_BASE` env var).
- SSE format follows the Copilot agent protocol: `data: {"choices":[{"delta":{"content":"..."}}]}` chunks terminated by `data: [DONE]`.
- URL extraction regex covers both `learn.microsoft.com` and `docs.microsoft.com`.
- Light auth: requires `X-GitHub-Token` header to be present (no JWT validation — hackathon scope).
- `httpx` was already in requirements.txt, no dependency changes needed.

### 2025-07-17 — SSE Timeout Fix
- **Problem**: SSE stream was timing out after ~30 seconds (curl exit code 18) due to Azure Container Apps default ingress timeout (240s) and lack of keep-alive signals. Jobs take 2-5 minutes.
- **Root cause**: No data flow between status polls (3-second intervals) caused proxies/gateways to kill the connection. GitHub's SSE proxy and ACA ingress both require regular data.
- **Solution**: Added SSE keep-alive comments (`: keepalive\n\n`) every poll cycle to maintain connection.
- **Headers added**: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no` on all StreamingResponse instances to prevent proxy buffering.
- **Better timeout UX**: Changed timeout message to explain the job is still running in background and provide the job ID + API endpoint for manual status checks.
- **Production note**: Added comment in module docstring about increasing ACA ingress timeout to 600s via `az containerapp ingress update --timeout 600`.
- **Key insight**: SSE keep-alive is critical for long-running jobs behind proxies — even with proper ingress timeouts, the connection needs regular heartbeats to stay alive.

### 2025-07-18 — User Delegation SAS Tokens at API Read Time
- **Problem:** Audio playback broken — storage account has public access disabled, and the pipeline's SAS generation at write time relied on management API env vars (`AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`) not set on the worker Container App. Fallback plain blob URLs returned 409.
- **Solution:** Generate User Delegation SAS tokens in the API layer (`_add_sas_token()`) when serving job responses, not at pipeline write time.
- **Changes made in `src/api/main.py`:**
  - Added imports: `BlobServiceClient`, `generate_blob_sas`, `BlobSasPermissions` from `azure.storage.blob`; `timedelta` from `datetime`.
  - Added `_get_blob_service_client()` helper using existing `credential` (DefaultAzureCredential).
  - Added `_add_sas_token(audio_url)` — parses blob name from URL, obtains user delegation key, generates 1-hour read SAS.
  - Updated `_job_to_response()` to wrap `job.audio_url` with `_add_sas_token()`.
- **Key design points:** SAS tokens are never stored — fresh ones generated per request. Uses User Delegation SAS (no account keys needed). Graceful fallback on failure (returns original URL).
- **Prereq:** Managed identity needs **Storage Blob Delegator** role on the storage account (included in Storage Blob Data Contributor).

### 2025-01-10 — Optional Title Field for User-Provided Podcast Names
- **Purpose:** Enable webapp to pass user-provided podcast names instead of always auto-generating from URL.
- **Changes made:**
  - Added `title: str = ""` field to `GenerateRequest` model (line 41) — optional, defaults to empty string.
  - Updated `generate()` endpoint (line 75) to pass `request.title` to `Job()` constructor: `Job(url=request.url, style=request.style, title=request.title)`.
- **Integration notes:** The `Job` model already has a `title` field, and `_job_to_response` already maps it. Worker logic sets `title` during processing if empty, so user-provided titles take priority only if worker respects pre-set titles.
- **UX impact:** Users can now provide custom podcast names at submission time rather than being stuck with auto-generated titles from URL metadata.

