# DocTalk 🎙️

Convert Azure documentation pages into engaging podcast-style audio — on-the-go learning powered by Azure OpenAI and Azure Speech services.

> **"Learn Azure while you commute."** — Paste a docs URL, get a podcast MP3.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎭 **Two podcast styles** | Single narrator summary **or** two-host conversational discussion (Alex & Sam) |
| 📄 **Smart content extraction** | Automatically scrapes and cleans Azure docs pages — strips nav, scripts, and boilerplate |
| 🗣️ **Natural-sounding voices** | Azure Neural TTS with expressive `chat` style — not robotic |
| 🔊 **Multi-voice SSML** | Two distinct voices for conversational mode with automatic voice-switching |
| 📝 **Script preview** | Generate and review scripts before audio synthesis (`--script-only`) |
| 🔗 **Passwordless auth** | Uses `DefaultAzureCredential` — no API keys in code |

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.10 or later |
| Azure CLI | `az login` for local authentication |
| Azure Developer CLI | `azd` for infrastructure deployment |
| Azure Subscription | With permissions to create Cognitive Services, Storage, Key Vault |

---

## Quick Start

### 1. Clone and Install

```bash
cd podcast
pip install -r requirements.txt
```

### 2. Deploy Azure Resources

```bash
azd init -e podcast-dev
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>
azd env set AZURE_LOCATION eastus2
azd provision --no-prompt
```

### 3. Configure Environment

```bash
# Auto-populate .env from deployed resource outputs
azd env get-values > .env
```

Or copy `.env.example` to `.env` and fill in values manually.

### 4. Authenticate

```bash
az login
```

### 5. Generate Your First Podcast

```bash
# Two-host conversation (default) — Alex & Sam discuss the topic
python -m src.cli generate "https://learn.microsoft.com/azure/container-apps/overview"

# Single narrator — concise summary
python -m src.cli generate --style single "https://learn.microsoft.com/azure/functions/functions-overview"

# Script only — review before synthesis
python -m src.cli generate --script-only "https://learn.microsoft.com/azure/aks/intro-kubernetes"

# Custom output path
python -m src.cli generate -o my-podcast.mp3 "https://learn.microsoft.com/azure/ai-services/openai/overview"
```

### 6. Preview Content (No Azure Resources Needed)

```bash
python -m src.cli preview "https://learn.microsoft.com/azure/ai-services/openai/overview"
```

---

## CLI Reference

```
Usage: python -m src.cli [COMMAND] [OPTIONS] URL

Commands:
  generate    Generate a podcast from an Azure documentation URL
  preview     Preview extracted content (no Azure resources needed)

Generate Options:
  --style [single|conversation]   Podcast style (default: conversation)
  --output, -o PATH               Output MP3 file path
  --script-only                   Only generate the script, no audio
  --help                          Show help
```

---

## Cloud API (Phase 2)

DocTalk is deployed as a cloud API on Azure Container Apps with async job processing.

**API Endpoint:** `https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io`

### API Usage

```bash
# Submit a podcast generation job
curl -X POST https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/generate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://learn.microsoft.com/azure/container-apps/overview"}'

# Poll job status
curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/jobs/{job_id}

# List all jobs
curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/jobs

# Health check
curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/health
```

---

## Copilot Extension (Hackathon Demo)

DocTalk is registered as a **GitHub Copilot Extension** — use it directly in Copilot Chat!

### Quick Start

1. **Register the GitHub App** — Follow [COPILOT-EXTENSION-SETUP.md](./COPILOT-EXTENSION-SETUP.md)
2. **Install on your account** — Add the DocTalk app to your personal or organization account
3. **Open Copilot Chat** — VS Code or github.com
4. **Type a command:**
   ```
   @doctalk help
   @doctalk generate https://learn.microsoft.com/azure/container-apps/overview
   ```

### Features

- 🎯 **Inline in Copilot Chat** — No context-switching
- 📡 **Real-time streaming** — See progress as the podcast is generated (SSE)
- 🎭 **Two modes** — Single narrator or two-host conversation
- 🔗 **Microsoft Learn URLs** — Auto-detects and processes Azure docs
- 📊 **Job status tracking** — Check generation progress anytime

### Documentation

See **[COPILOT-EXTENSION-SETUP.md](./COPILOT-EXTENSION-SETUP.md)** for:
- Step-by-step GitHub App registration
- Installation instructions
- Testing and troubleshooting
- Demo script for hackathon

---

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full design document with diagrams.

### Pipeline Overview

```
Phase 1 (Local):   URL ──▶ Scraper ──▶ Azure OpenAI ──▶ Azure Speech TTS ──▶ MP3 Output

Phase 2 (Cloud):   Client ──▶ FastAPI ──▶ Storage Queue ──▶ Worker ──▶ Blob Storage
                              (ACA)                        (ACA + KEDA)
```

### Azure Resources

| Resource | Service | SKU | Purpose |
|----------|---------|-----|---------|
| Azure OpenAI | `Microsoft.CognitiveServices/accounts` | S0 | GPT-5.1 model for script generation |
| Azure Speech | `Microsoft.CognitiveServices/accounts` | S0 | Neural TTS with multi-voice SSML |
| Blob Storage | `Microsoft.Storage/storageAccounts` | Standard_LRS | Store generated podcast MP3s |
| Container Registry | `Microsoft.ContainerRegistry/registries` | Basic | Docker images for API + Worker |
| Container Apps (API) | `Microsoft.App/containerApps` | Consumption | FastAPI backend with external ingress |
| Container Apps (Worker) | `Microsoft.App/containerApps` | Consumption | KEDA queue-triggered worker (scale 0→5) |
| Key Vault | `Microsoft.KeyVault/vaults` | Standard | Secrets management |
| Log Analytics | `Microsoft.OperationalInsights/workspaces` | PerGB2018 | Centralized logging |
| App Insights | `Microsoft.Insights/components` | — | Monitoring & APM |

---

## Project Structure

```
podcast/
├── .azure/
│   └── deployment-plan.md          # Azure deployment plan (source of truth)
├── infra/                          # Bicep infrastructure-as-code
│   ├── main.bicep                  # Subscription-scoped orchestrator
│   ├── main.parameters.json        # Deployment parameters
│   └── modules/
│       ├── monitoring.bicep        # Log Analytics + Application Insights
│       ├── keyvault.bicep          # Azure Key Vault
│       ├── openai.bicep            # Azure OpenAI + GPT-5.1 deployment
│       ├── speech.bicep            # Azure Speech Services
│       ├── storage.bicep           # Blob + Queue + Table Storage
│       ├── registry.bicep          # Azure Container Registry
│       ├── container-app-env.bicep # Container Apps Environment
│       ├── container-app-api.bicep # API Container App
│       ├── container-app-worker.bicep # Worker Container App (KEDA)
│       └── identity.bicep          # Managed Identities + RBAC
├── src/
│   ├── core/                       # Shared pipeline modules
│   │   ├── pipeline.py             # Full scrape→script→TTS→blob pipeline
│   │   ├── scraper.py              # Azure docs URL scraper
│   │   ├── script_generator.py     # Azure OpenAI script generation
│   │   └── speech_synthesizer.py   # Azure Speech SSML synthesis
│   ├── api/
│   │   └── main.py                 # FastAPI backend (POST /generate, GET /jobs)
│   ├── worker/
│   │   └── main.py                 # Queue consumer with KEDA scaling
│   ├── cli.py                      # Click-based CLI (local + remote modes)
│   └── config.py                   # Environment variable configuration
├── output/                         # Generated podcast MP3 files (local mode)
├── Dockerfile.api                  # API container image
├── Dockerfile.worker               # Worker container image
├── azure.yaml                      # Azure Developer CLI configuration
├── requirements.txt                # Python dependencies
├── .dockerignore                   # Build context exclusions
├── ARCHITECTURE.md                 # Architecture document with diagrams
├── ROADMAP.md                      # Project roadmap
└── README.md                       # This file
```

---

## Authentication

| Environment | Method | Setup |
|-------------|--------|-------|
| **Local development** | `DefaultAzureCredential` | Run `az login` — picks up CLI credentials |
| **CI/CD** | Service Principal | Set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` |
| **Production (Azure-hosted)** | Managed Identity | Assign `ManagedIdentityCredential` — no secrets to manage |

> **Security note**: The app uses passwordless authentication via `azure-identity`. No API keys are stored in code. For Speech Service, the app constructs an AAD token using the resource ID.

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | ✅ | — | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | — | `gpt-51` | Model deployment name |
| `AZURE_SPEECH_REGION` | ✅ | `eastus2` | Azure region for Speech Service |
| `AZURE_SPEECH_RESOURCE_ID` | — | — | Speech resource ID (for AAD token auth) |
| `AZURE_SPEECH_KEY` | — | — | Speech subscription key (alternative to AAD) |
| `AZURE_STORAGE_ACCOUNT_NAME` | — | — | Storage account for podcast uploads |
| `AZURE_STORAGE_CONTAINER_NAME` | — | `podcasts` | Blob container name |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `AZURE_OPENAI_ENDPOINT is required` | Missing `.env` config | Run `azd env get-values > .env` |
| `Unsupported parameter: max_tokens` | Old model API parameter | Ensure `max_completion_tokens` is used (fixed in code) |
| `SSML must contain a maximum of 50 voice elements` | Too many dialogue lines | Fixed — code merges same-speaker lines and chunks SSML |
| `Speech synthesis canceled: Error 1007` | SSML voice limit exceeded | Fixed — automatic chunking with MP3 concatenation |
| `WinError 32: file in use` | Speech SDK file lock on temp files | Fixed — uses `tempfile.mkdtemp()` with retry cleanup |
| Unicode errors on Windows console | Emoji characters in output | Fixed — `sys.stdout.reconfigure(encoding="utf-8")` |
| `AuthenticationError` | Not logged in to Azure | Run `az login` |
| Empty content extracted | Page requires authentication | Some docs pages require sign-in; try a public page |

---

## License

This project is for internal use. See your organization's licensing policies.
