# DocTalk — Smoke Test Checklist

> **Purpose:** Manual validation before publishing the M365 Copilot declarative agent.
> Run through every scenario below after sideloading. Mark each row Pass / Fail.

---

## Prerequisites

| # | Requirement | Details |
|---|-------------|---------|
| 1 | **M365 tenant** | A Microsoft 365 developer or enterprise tenant with Copilot license |
| 2 | **Teams Toolkit** | VS Code + M365 Agents Toolkit extension v6.9+ (or CLI `teamsapp`) installed |
| 3 | **Entra app registration** | Run `infra/scripts/register-entra-app.sh` — note the Client ID and Tenant ID |
| 4 | **Environment variables** | Populate `env/.env.dev` with `ENTRA_APP_ID`, `ENTRA_TENANT_ID`, `AZURE_STORAGE_ACCOUNT_NAME` |
| 5 | **API running** | DocTalk API deployed or running locally (`uvicorn src.api.main:app`) |
| 6 | **Azure resources** | Storage Account (table `podcastjobs`, queue `podcast-jobs`, container `podcasts`) provisioned |

---

## Step-by-step Sideload Instructions

1. Open the project in VS Code.
2. Press **F5** or run `Teams: Provision` then `Teams: Deploy` via the Teams Toolkit sidebar.
3. Toolkit will package `appPackage/` and sideload into your M365 tenant.
4. Open **Microsoft Teams** → **Copilot** → look for **DocTalk** in the agent picker (bottom-left).
5. Select the DocTalk agent. You should see the four conversation starters.

---

## Test Scenarios — Conversation Starters

### Scenario 1: "Generate a podcast about Azure Container Apps"

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1.1 | Click the conversation starter | Copilot asks for URL confirmation or generates directly | |
| 1.2 | Provide a valid docs URL | `generatePodcast` API called, Adaptive Card appears | |
| 1.3 | Verify Adaptive Card | Shows "🎙️ Podcast Queued" with URL, Job ID, Status=queued | |
| 1.4 | Wait ~60s, ask "check status" | `getJobStatus` called, card updates with progress | |

### Scenario 2: "Create a beginner-level episode on Azure Functions"

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 2.1 | Click the conversation starter | Copilot helps find docs URL, then calls `generatePodcast` | |
| 2.2 | Verify Adaptive Card renders | Shows queued job with correct URL and style | |

### Scenario 3: "What podcasts have I generated recently?"

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 3.1 | Click the conversation starter | `listRecentPodcasts` called | |
| 3.2 | Verify Adaptive Card | Shows "🎧 Recent Podcasts" heading | |
| 3.3 | Verify list content | Previously generated jobs appear with status and titles | |

### Scenario 4: "Check the status of my latest podcast"

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 4.1 | Click the conversation starter | `getJobStatus` called for most recent job | |
| 4.2 | If completed | Card shows title, FactSet (Status/Style), and ▶️ Play link | |
| 4.3 | If in progress | Card shows "⏳ Audio is still being generated…" | |
| 4.4 | Click Play link (if completed) | Audio file downloads/plays — SAS token valid | |

---

## Adaptive Card Rendering Validation

| Card | Key Elements to Verify | Pass/Fail |
|------|----------------------|-----------|
| `generatePodcast` | "🎙️ Podcast Queued" title, URL, Job ID, Status fields | |
| `getJobStatus` — completed | Title, FactSet (Status + Style), "▶️ Play / Download" link visible | |
| `getJobStatus` — in progress | Title, FactSet, "⏳ Audio is still being generated…" shown, no broken Play link | |
| `listRecentPodcasts` | "🎧 Recent Podcasts" heading, subtitle text | |

---

## Auth Flow Verification

| # | Test | Expected Result | Pass/Fail |
|---|------|-----------------|-----------|
| A1 | First API call triggers OAuth consent | Copilot shows OAuth popup / consent card | |
| A2 | Grant consent | Token acquired, API call succeeds | |
| A3 | Subsequent calls use cached token | No repeated consent prompts | |
| A4 | Revoke app consent in Entra portal | Next API call triggers re-consent | |
| A5 | Verify token audience | JWT `aud` claim matches `api://<ENTRA_APP_ID>` | |

---

## Error Scenarios

| # | Scenario | How to Trigger | Expected Behavior | Pass/Fail |
|---|----------|---------------|-------------------|-----------|
| E1 | **Bad URL** | Submit `not-a-url` as the docs URL | API returns validation error, Copilot shows friendly message | |
| E2 | **Unreachable URL** | Submit `https://example.com/nonexistent-page` | Job fails gracefully, status=failed with error message | |
| E3 | **API timeout** | Stop the API server, then try a command | Copilot shows connection error, no crash | |
| E4 | **Missing permissions** | Remove Storage RBAC roles from managed identity | SAS generation fails, fallback URL returned (no 500) | |
| E5 | **Expired SAS token** | Wait >1 hour, click old Play link | Download fails; re-check status to get fresh SAS | |
| E6 | **Rate limit** | Submit many jobs rapidly | Queue accepts all; no lost jobs | |
| E7 | **Invalid auth** | Modify ENTRA_APP_ID to wrong value | 401 returned, Copilot re-prompts for auth | |

---

## Pass / Fail Criteria

**PASS:** All numbered scenarios complete without 5xx errors. Adaptive Cards render correctly.
Auth flow completes without manual intervention. Error scenarios fail gracefully with user-friendly messages.

**FAIL:** Any 5xx error from the API. Broken Adaptive Card rendering (missing fields, layout errors).
Auth loop (repeated consent prompts). Silent failures (job stuck without error message).

---

*Last updated: 2025-07-25 — Switch (QA)*
