# Morpheus — History

## Learnings

### 2025-07-18 — M365 Copilot Agent Task Breakdown

**Architecture decisions:**
- M365 Copilot declarative agent with API plugin — no Bot Framework; Copilot handles NLU, parameter extraction, response rendering
- OAuth 2.0 via Entra ID required for API plugin auth (`OAuthPluginVault`)
- Adaptive Cards for response rendering (status cards, audio download links)
- SAS tokens (1-hour expiry) for time-limited audio download URLs
- Teams Toolkit for scaffolding, sideloading, and org catalog deployment

**Codebase state observed:**
- API (`src/api/main.py`): FastAPI with `POST /generate`, `GET /jobs/{job_id}`, `GET /jobs` — no auth middleware yet
- Models (`src/core/models.py`): `Job` + `QueueMessage` — missing `level`, `summary`, `sections` fields
- Script generator (`src/core/script_generator.py`): `SINGLE_NARRATOR_PROMPT` / `TWO_HOST_PROMPT` — no audience level support
- Pipeline (`src/core/pipeline.py`): scrape → generate → synthesize → upload blob — no summary generation step
- No existing `appPackage/` directory — Teams agent is greenfield
- No existing OAuth/Entra ID integration in the API

**Key file paths:**
- Design doc: `COPILOT-AGENT-DESIGN.md`
- Task breakdown: `.squad/decisions/inbox/morpheus-ui-task-breakdown.md`
- API entry: `src/api/main.py`
- Models: `src/core/models.py`
- Script gen: `src/core/script_generator.py`
- Pipeline: `src/core/pipeline.py`
- Worker: `src/worker/main.py`
- Config: `src/config.py`

**User preferences (Lucus):**
- Wants tasks granular enough for ~30-60 min each
- Wants dependency annotations and owner assignments
- Three phases: MVP, v1.1, v2
