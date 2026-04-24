$API_BASE = "https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io"
$URL      = "https://www.microsoft.com/en-us/microsoft-365/blog/2026/03/30/copilot-cowork-now-available-in-frontier/"
$STYLE    = "conversation"

# ── 1. Health Check ──────────────────────────────────────────────────────────
Write-Host "`n=== 1. Health Check ===" -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri "$API_BASE/health"
$health | ConvertTo-Json

# ── 2. Submit Podcast Generation Job ─────────────────────────────────────────
Write-Host "`n=== 2. Submitting Job ===" -ForegroundColor Cyan
$response = Invoke-RestMethod -Uri "$API_BASE/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body (ConvertTo-Json @{ url = $URL; style = $STYLE })

$response | ConvertTo-Json
$jobId = $response.id
Write-Host "Job ID: $jobId" -ForegroundColor Green

# ── 3. Poll Until Complete ────────────────────────────────────────────────────
Write-Host "`n=== 3. Polling Job Status ===" -ForegroundColor Cyan
$lastStatus = ""
while ($true) {
    $job = Invoke-RestMethod -Uri "$API_BASE/jobs/$jobId"
    if ($job.status -ne $lastStatus) {
        Write-Host "  Status: $($job.status)" -ForegroundColor Yellow
        $lastStatus = $job.status
    }
    if ($job.status -in @("completed", "failed")) { break }
    Start-Sleep -Seconds 5
}

Write-Host "`n=== Result ===" -ForegroundColor Cyan
$job | ConvertTo-Json

if ($job.status -eq "completed") {
    Write-Host "`nPodcast ready: $($job.audio_url)" -ForegroundColor Green
    Write-Host "Opening in browser..." -ForegroundColor Green
    Start-Process $job.audio_url
} else {
    Write-Host "`nJob failed: $($job.error)" -ForegroundColor Red
}

# ── 4. Test Copilot Agent Endpoint ───────────────────────────────────────────
Write-Host "`n=== 4. Testing Copilot Agent Endpoint ===" -ForegroundColor Cyan
$body = ConvertTo-Json -Depth 5 @{
    messages = @(
        @{ role = "user"; content = "generate $URL" }
    )
}
try {
    $agentResp = Invoke-WebRequest -Uri "$API_BASE/copilot/agent" `
        -Method POST `
        -ContentType "application/json" `
        -Headers @{ "X-GitHub-Token" = "demo-token" } `
        -Body $body
    Write-Host "Agent response (first 500 chars):"
    Write-Host ($agentResp.Content.Substring(0, [Math]::Min(500, $agentResp.Content.Length)))
} catch {
    Write-Host "Agent endpoint error: $_" -ForegroundColor Red
}

# ── 5. List Recent Jobs ───────────────────────────────────────────────────────
Write-Host "`n=== 5. Recent Jobs ===" -ForegroundColor Cyan
Invoke-RestMethod "$API_BASE/jobs" | ConvertTo-Json -Depth 5

