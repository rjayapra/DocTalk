# Testing Guide — DocTalk 🧪

> How to verify the DocTalk podcast generator across all modes and components.

---

## Automated Test Suite

DocTalk includes a pytest-based test suite for automated testing.

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test File
```bash
python -m pytest test/test_webapp.py
```

### Run with Verbose Output
```bash
python -m pytest -v
```

### Current Test Coverage
- **Webapp Integration** (`test/test_webapp.py`): 12 tests covering static file serving, CORS headers, routing, and API/static file coexistence

See [`test/README.md`](test/README.md) for detailed test documentation.

---

## Prerequisites

| Requirement | Command to verify |
|-------------|-------------------|
| Python 3.10+ | `python --version` |
| Azure CLI | `az --version` |
| Azure login | `az login` |
| Dependencies installed | `pip install -r requirements.txt` |
| `.env` configured | Copy `.env.example` → `.env`, fill values |

---

## 1. Health Check (Cloud API)

Verify the API is running and responding:

```bash
curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/health
```

**Expected response:**

```json
{
  "status": "healthy",
  "service": "doctalk-api",
  "version": "2.0.0"
}
```

---

## 2. Cloud API — End-to-End Test

### 2a. Submit a Job

```bash
curl -X POST https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/generate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://learn.microsoft.com/en-us/azure/container-apps/overview", "style": "conversation"}'
```

**Expected:** HTTP 202 with job details:

```json
{
  "id": "<job-id>",
  "url": "https://learn.microsoft.com/en-us/azure/container-apps/overview",
  "style": "conversation",
  "status": "queued",
  "title": "",
  "audio_url": "",
  "error": ""
}
```

Save the `id` value for the next step.

### 2b. Poll Job Status

```bash
curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/jobs/<job-id>
```

**Status progression:** `queued` → `processing` → `scraping` → `generating_script` → `synthesizing` → `completed`

Poll every 10–15 seconds. Full pipeline takes ~2–3 minutes.

### 2c. Verify Completed Job

When status is `completed`:

```json
{
  "id": "<job-id>",
  "status": "completed",
  "title": "Azure Container Apps overview",
  "audio_url": "https://stpodcastmkffp6.blob.core.windows.net/podcasts/<job-id>.mp3",
  "error": ""
}
```

### 2d. Download and Play Audio

```bash
# Download the MP3
curl -o podcast.mp3 "https://stpodcastmkffp6.blob.core.windows.net/podcasts/<job-id>.mp3"

# Play (Windows)
start podcast.mp3

# Play (macOS)
open podcast.mp3

# Play (Linux)
xdg-open podcast.mp3
```

### 2e. List All Jobs

```bash
curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/jobs
```

Returns an array of all recent jobs with their statuses.

---

## 3. CLI — Remote Mode (via Cloud API)

The CLI can submit jobs to the cloud API instead of running locally.

```bash
# Set the API URL
set DOCTALK_API_URL=https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io

# Generate via cloud API
python -m src.cli generate "https://learn.microsoft.com/azure/functions/functions-overview"
```

**Expected output:**

```
🌐 Submitting to DocTalk API at https://...
   Job ID: <uuid>
⏳ Waiting for completion...

✓ Podcast ready: https://stpodcastmkffp6.blob.core.windows.net/podcasts/<uuid>.mp3
```

---

## 4. CLI — Local Mode

Runs the full pipeline locally (requires Azure credentials + `.env` config):

```bash
# Force local mode (bypasses API even if DOCTALK_API_URL is set)
python -m src.cli generate --local "https://learn.microsoft.com/azure/container-apps/overview"

# Single narrator style
python -m src.cli generate --local --style single "https://learn.microsoft.com/azure/functions/functions-overview"

# Script only (no audio, no Speech Service needed)
python -m src.cli generate --script-only "https://learn.microsoft.com/azure/aks/intro-kubernetes"

# Custom output path
python -m src.cli generate --local -o my-podcast.mp3 "https://learn.microsoft.com/azure/ai-services/openai/overview"
```

### Expected Output (local mode):

```
📄 Fetching documentation...
   Title: Azure Container Apps overview
   Content length: 8542 chars

🤖 Generating conversation script with Azure OpenAI...
   Script length: 4521 chars

🔊 Synthesizing audio with Azure Speech...
   Processing chunk 1/3...
   Processing chunk 2/3...
   Processing chunk 3/3...

✓ Podcast saved to output/azure-container-apps-overview.mp3
```

---

## 5. Content Preview (No Azure Resources Needed)

Test scraping without Azure services:

```bash
python -m src.cli preview "https://learn.microsoft.com/azure/ai-services/openai/overview"
```

**Expected:** Displays the extracted title and content text. Use this to verify URL scraping works before testing the full pipeline.

---

## 6. Infrastructure Verification

### 6a. Container Apps Status

```bash
# API container app
az containerapp show --name ca-doctalk-api-mkffp6 --resource-group rg-podcast-dev \
  --query "{status:properties.runningStatus, fqdn:properties.configuration.ingress.fqdn}" -o json

# Worker container app
az containerapp show --name ca-doctalk-worker-mkffp6 --resource-group rg-podcast-dev \
  --query "{status:properties.runningStatus, minReplicas:properties.template.scale.minReplicas, maxReplicas:properties.template.scale.maxReplicas}" -o json
```

### 6b. Worker Logs (check processing)

```bash
az containerapp logs show --name ca-doctalk-worker-mkffp6 --resource-group rg-podcast-dev --tail 50
```

Look for:
- `DocTalk Worker starting` — worker is alive
- `Processing job <id>` — job picked up from queue
- `DocTalk Worker done` — polling cycle completed

### 6c. RBAC Roles

```bash
# API identity roles
az role assignment list --assignee $(az identity show --name id-doctalk-mkffp6-api \
  --resource-group rg-podcast-dev --query principalId -o tsv) \
  --resource-group rg-podcast-dev --output table

# Worker identity roles
az role assignment list --assignee $(az identity show --name id-doctalk-mkffp6-worker \
  --resource-group rg-podcast-dev --query principalId -o tsv) \
  --resource-group rg-podcast-dev --output table
```

**Expected roles:**

| Identity | Roles |
|----------|-------|
| API | Storage Queue Data Contributor, Storage Table Data Contributor, Storage Blob Data Contributor, AcrPull |
| Worker | Storage Queue Data Contributor, Storage Table Data Contributor, Storage Blob Data Contributor, AcrPull, Cognitive Services User |

### 6d. Queue Depth (check for stuck messages)

```bash
az storage queue metadata show --name podcast-jobs \
  --account-name stpodcastmkffp6 --auth-mode login \
  --query approximateMessageCount -o tsv
```

A value of `0` means all jobs have been processed. Non-zero may indicate the worker is processing or stuck.

### 6e. Blob Storage (check generated podcasts)

```bash
az storage blob list --container-name podcasts \
  --account-name stpodcastmkffp6 --auth-mode login \
  --output table --query "[].{Name:name, Size:properties.contentLength, Created:properties.creationTime}"
```

---

## 7. Error Scenarios to Test

| Scenario | How to test | Expected behavior |
|----------|-------------|-------------------|
| **Invalid URL** | `POST /generate` with `{"url": "not-a-url"}` | Job created, fails during scraping with error message |
| **Non-Azure docs URL** | Submit `https://example.com` | Job fails — content extraction finds no docs content |
| **Single narrator style** | `{"url": "...", "style": "single"}` | Generates single-voice podcast (no Alex & Sam dialogue) |
| **API offline** | CLI with `DOCTALK_API_URL` set to bad URL | CLI shows `API call failed` error |
| **Worker scaled to 0** | Submit job when no worker replicas running | KEDA auto-scales from 0→1, job processes after ~30s delay |
| **Large doc page** | Use a long Azure docs page (e.g., Azure Functions triggers reference) | SSML chunking handles it — may take 4-5 minutes |

---

## 8. PowerShell Quick Test Script

Copy and run this to execute a full test suite:

```powershell
$API = "https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io"

Write-Host "=== 1. Health Check ===" -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri "$API/health"
if ($health.status -eq "healthy") {
    Write-Host "  PASS: API is healthy (v$($health.version))" -ForegroundColor Green
} else {
    Write-Host "  FAIL: Unexpected status: $($health.status)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== 2. Submit Job ===" -ForegroundColor Cyan
$body = @{ url = "https://learn.microsoft.com/en-us/azure/container-apps/overview"; style = "conversation" } | ConvertTo-Json
$job = Invoke-RestMethod -Uri "$API/generate" -Method POST -Body $body -ContentType "application/json"
Write-Host "  Job ID: $($job.id)"
Write-Host "  Status: $($job.status)"

if ($job.status -ne "queued") {
    Write-Host "  FAIL: Expected 'queued', got '$($job.status)'" -ForegroundColor Red
    exit 1
}
Write-Host "  PASS: Job queued successfully" -ForegroundColor Green

Write-Host "`n=== 3. Poll Until Complete ===" -ForegroundColor Cyan
$maxWait = 300  # 5 minutes
$elapsed = 0
$interval = 10

do {
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    $result = Invoke-RestMethod -Uri "$API/jobs/$($job.id)"
    Write-Host "  [$elapsed`s] Status: $($result.status)"
} while ($result.status -notin @("completed", "failed") -and $elapsed -lt $maxWait)

if ($result.status -eq "completed") {
    Write-Host "`n  PASS: Job completed!" -ForegroundColor Green
    Write-Host "  Title: $($result.title)"
    Write-Host "  Audio: $($result.audio_url)"
} elseif ($result.status -eq "failed") {
    Write-Host "`n  FAIL: Job failed — $($result.error)" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n  FAIL: Timed out after $maxWait seconds (status: $($result.status))" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== 4. Verify Audio Accessible ===" -ForegroundColor Cyan
try {
    $audio = Invoke-WebRequest -Uri $result.audio_url -Method HEAD
    $size = [math]::Round($audio.Headers["Content-Length"] / 1MB, 2)
    Write-Host "  PASS: Audio file exists ($size MB)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Audio not accessible — $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 5. List Jobs ===" -ForegroundColor Cyan
$jobs = Invoke-RestMethod -Uri "$API/jobs"
Write-Host "  Total jobs: $($jobs.Count)"
Write-Host "  PASS: Jobs endpoint working" -ForegroundColor Green

Write-Host "`n=== All tests passed! ===" -ForegroundColor Green
```

---

## 9. Test URLs

Good Azure docs pages for testing (varying lengths and complexity):

| Page | Length | Good for testing |
|------|--------|------------------|
| [Container Apps overview](https://learn.microsoft.com/en-us/azure/container-apps/overview) | Medium | Standard two-host conversation |
| [Functions overview](https://learn.microsoft.com/en-us/azure/functions/functions-overview) | Medium | Single narrator style |
| [AKS intro](https://learn.microsoft.com/en-us/azure/aks/intro-kubernetes) | Long | SSML chunking verification |
| [OpenAI overview](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview) | Short | Quick smoke test |
| [App Service overview](https://learn.microsoft.com/en-us/azure/app-service/overview) | Medium | Another conversation test |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Health returns error | Container not running | `az containerapp show ...` to check status |
| Job stays `queued` | Worker scaled to 0, KEDA hasn't triggered | Wait 30-60s for KEDA to scale up; check worker logs |
| Job fails at `scraping` | URL unreachable or not an Azure docs page | Try a different URL; check with `preview` command first |
| Job fails at `generating_script` | OpenAI deployment issue | Check OpenAI resource health in Azure portal |
| Job fails at `synthesizing` | Speech service issue or SSML too large | Check worker logs for Speech SDK errors |
| Audio URL returns 404 | Blob upload failed | Check worker logs; verify blob container exists |
| CLI shows `API call failed` | Network issue or wrong `DOCTALK_API_URL` | Verify URL; test with curl first |
| `DefaultAzureCredential` error | Not logged in | Run `az login` |
