# Team Decisions Log

> Canonical record of architectural and operational decisions made by the DocTalk team.
> Merged and deduplicated by Scribe. Last updated: 2025-01-22.

---

## 2026-04-24: Copilot Extension Architecture (Phase 3)

**By:** Morpheus

**Context:** We need a GitHub Copilot Extension so developers can generate podcasts via `@doctalk` in Copilot Chat (VS Code, github.com, JetBrains, CLI).

**Decision:**
1. Agent-based extension (not skillset, not MCP) — simplest model for our use case
2. Calls existing DocTalk API over public HTTPS — no infra changes needed for hackathon
3. Poll-based status updates — extension polls `GET /jobs/{id}` and streams SSE updates to chat
4. GitHub App registration with agent type pointing to the API endpoint

**Consequences:**
- No changes to existing API or Worker needed
- Team can build this in a single day
- Future: could add MCP tools or skillset mode for richer integration

**Files:**
- `src/api/copilot.py` — Copilot agent implementation
- `ARCHITECTURE.md` — Updated with Phase 3 section

---

## 2026-04-24: Copilot Extension Hackathon Setup Guide

**By:** Morpheus (Lead/Architect)

**Context:** The DocTalk Copilot Extension API is deployed and functional. To enable hackathon participants and judges to easily register and test the extension, we need clear, practical documentation.

**Decision:** Created **COPILOT-EXTENSION-SETUP.md** as the canonical guide for hackathon demo participants:
- Practical, step-by-step format (GitHub App creation → installation → testing → troubleshooting)
- Minimal permissions model (no repo access required for Copilot Extension)
- Real endpoint URLs pointing to deployed `ca-doctalk-api` instance
- Ready-to-run demo script (2-minute flow with narration)
- Authentic troubleshooting for common errors (403, timeout, "agent not found")
- Security notes explaining hackathon-mode auth vs. production requirements

**Rationale:**
- Hackathon focus prioritizes speed to demo (register → test in <5 min)
- Troubleshooting section prevents common blocker issues
- Self-documenting demo script is copy-paste ready
- Future-proof with security notes for production hardening

**Consequences:**
- Participants can self-serve without asking for help
- Demo judges see a complete, professional flow
- Provides foundation for production security setup (JWT validation, etc.)
- README.md now surfaces Copilot Extension as a key feature

**Files:**
- `COPILOT-EXTENSION-SETUP.md` — Main guide
- `README.md` — Updated with Copilot Extension link

---

## 2025-07-17: Copilot Extension as Same-Service Endpoint

**By:** Trinity (Backend Dev)

**Context:** We needed a GitHub Copilot Extension agent for DocTalk. Two options: separate microservice vs. new route on the existing API.

**Decision:** Add the Copilot agent as a router (`/copilot/agent`) on the existing FastAPI app rather than a separate service.

**Rationale:**
- Zero infra cost — no new Container App, no new Dockerfile, no new deployment pipeline
- Internal calling — the agent calls `/generate` and `/jobs/{id}` via localhost, avoiding network hops and auth complexity
- `DOCTALK_API_BASE` env var allows overriding the base URL if we ever split it out

**Trade-offs:**
- The SSE polling loop holds a connection open for up to 5 minutes, tying up a uvicorn worker
- Auth is header-presence only (no JWT validation) — fine for demo, needs hardening for production

**Impact:**
- New file: `src/api/copilot.py`
- Modified: `src/api/main.py` (two lines: import + `include_router`)

---

## 2025-07-17: SSE Keep-Alive Strategy for Long-Running Jobs

**By:** Trinity (Backend Dev)

**Status:** Implemented

**Context:** The Copilot Extension endpoint uses Server-Sent Events (SSE) to stream job status updates. Podcast generation takes 2-5 minutes, but the SSE connection was dying after ~30 seconds (curl exit code 18 - partial file transfer). The job was still "queued" when the stream died, indicating connection timeout, not job failure.

**Problem:** Three timeout mechanisms were killing the connection:
1. Azure Container Apps ingress timeout (default 240s)
2. Proxy/gateway idle timeout (GitHub's SSE proxy and ACA ingress close idle connections)
3. No keep-alive signals (polling loop only sent data when job status changed)

**Decision:** Implement SSE keep-alive using standard SSE comment lines (`: keepalive\n\n`) sent on every poll iteration (every 3 seconds), even when job status hasn't changed.

Additionally:
- Set proper SSE headers: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`
- Document that ACA ingress timeout must be increased to 600s for production

**Alternatives Considered:**
1. Reduce poll interval to <1 second — would create more API load
2. WebSockets instead of SSE — not supported by Copilot Extension protocol
3. Only rely on increasing ACA timeout — still need regular data flow for proxies
4. Send fake status updates — confusing UX; keep-alive comments are the standard

**Consequences:**
- ✅ Connections stay alive for the full 5-minute poll window
- ✅ No breaking changes to API contract or message format
- ✅ Standard SSE pattern that all proxies/gateways understand
- ✅ Minimal overhead (~100 bytes/minute)
- ⚠️ Must remember to set ACA ingress timeout to 600s in production

**Implementation:**
```python
# Inside polling loop
yield ": keepalive\n\n"  # Every 3 seconds

# On StreamingResponse
headers={
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}
```

**Production Notes:** Ops team must run:
```bash
az containerapp ingress update --name doctalk-api --resource-group doctalk-rg --timeout 600
```

---

## Key Architectural Themes

### API-First, Copilot Extension Second
The main DocTalk API (`/generate`, `/jobs/{id}`) is the source of truth. The Copilot Extension is a thin SSE wrapper that polls and streams. This keeps infra simple and allows non-Copilot clients (mobile, web, CLI) to work independently.

### Hackathon Mode vs. Production Mode
Current state: minimal auth (header-presence only). Post-hackathon: implement JWT validation, increase ACA timeouts, add rate limiting.

### SSE Pattern: Keep-Alive Comments
Standard pattern for long-running streams. Comment lines (starting with `:`) are ignored by clients but keep connections alive. Works with all proxies and gateways.
