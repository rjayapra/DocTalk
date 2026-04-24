# Trinity — History

## Learnings

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
