# Switch Agent History

## 2026-04-24 — UI Task Breakdown Complete
A comprehensive 39-task UI build plan has been created spanning 3 phases. Switch has been assigned testing and quality assurance tasks to support the UI implementation. See `.squad/decisions/decisions.md` for full task manifest and assignments.

## 2025-07-25 — Wave 1 Validation (Task #15 prep)

Ran full automated validation of the M365 Copilot agent package:

**All checks passed:**
- ✅ OpenAPI spec valid (3.0.3) via openapi-spec-validator
- ✅ All 3 JSON files parse correctly (manifest, declarativeAgent, doctalk-plugin)
- ✅ operationIds match across openapi.yaml ↔ plugin functions ↔ runtimes (generatePodcast, getJobStatus, listRecentPodcasts)
- ✅ manifest.json agent ID "doctalkAgent" references declarativeAgent.json correctly
- ✅ declarativeAgent.json action "doctalkPlugin" references doctalk-plugin.json
- ✅ manifest schema version is 1.19
- ✅ 10/10 unit tests passing (7 blob_utils + 3 new auth tests)

**New artifacts:**
- `tests/test_auth.py` — 3 tests covering health endpoint (no auth), 401 enforcement, dev bypass mode
- `docs/SMOKE-TEST-CHECKLIST.md` — manual sideload test procedure with pass/fail criteria

## Learnings
- `src.core.__init__.py` eagerly imports scraper/script_generator/speech_synthesizer — all deps (bs4, openai, azure-cognitiveservices-speech) must be installed even for API-only tests
- Auth middleware uses `Config.ENTRA_APP_ID` as the gate: empty string = skip auth (local dev), any value = enforce JWT
- The `DefaultAzureCredential()` is called at module scope in `main.py` — tests must import the app directly rather than lazily patching it
- Use `python3.12` explicitly on this system (python3 defaults to 3.14 which has different package paths)
