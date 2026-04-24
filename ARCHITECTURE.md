# Architecture — DocTalk

> Last updated: 2025-07-27 | Status: Phase 1 Deployed (CLI), Phase 2 Deployed (API + Worker on Azure Container Apps), Wave 1 (M365 Copilot Agent)

---

## 1. Vision Statement

Enable developers and cloud practitioners to consume Azure documentation as podcast-style audio, making it easy to learn on the go — during commutes, workouts, or breaks. Accessible from **CLI**, **M365 Copilot** (Teams, Outlook, M365 Chat), and future channels via a shared API backend.

---

## 2. Architecture Evolution

| Phase | Channels | Compute | Processing |
|-------|----------|---------|------------|
| **Phase 1** | CLI | Local Python | Synchronous |
| **Phase 2 (Current)** | CLI + API | Azure Container Apps | Async with queue |
| **Phase 3 (Future)** | + M365 Copilot Agent | ACA + Declarative Agent | Async + caching |

---

## 3. Phase 2 Target Architecture

```mermaid
flowchart TB
    subgraph "Clients"
        CLI["🖥️ CLI<br/>(Python)"]
        subgraph "M365 Copilot"
            USER["👤 User<br/>(Teams / M365 Chat)"]
            COPILOT["🤖 Copilot Orchestrator"]
            AGENT["📋 DocTalk Agent<br/>(Declarative Agent v1.3)"]
            PLUGIN["🔌 API Plugin<br/>(OpenAPI 3.0 spec)"]
        end
    end

    subgraph "Azure Container Apps"
        API["🌐 DocTalk API<br/>(FastAPI)"]
        WORKER["⚙️ Worker<br/>(Background processor)"]
    end

    subgraph "Messaging"
        QUEUE["Azure Storage Queue<br/>(Job queue)"]
    end

    subgraph "AI Services"
        OAI["Azure OpenAI<br/>GPT-5.1"]
        SPE["Azure Speech<br/>Neural TTS"]
    end

    subgraph "Storage & State"
        BLOB["Blob Storage<br/>podcasts container"]
        TABLE["Table Storage<br/>job status tracking"]
    end

    subgraph "Operations"
        KV["Key Vault"]
        LOG["Log Analytics<br/>+ App Insights"]
    end

    CLI -->|POST /generate| API
    USER -->|Natural language| COPILOT
    COPILOT -->|Routes to| AGENT
    AGENT -->|Invokes| PLUGIN
    PLUGIN -->|"POST /generate | GET /jobs/:id | GET /jobs"| API
    API -->|Enqueue job| QUEUE
    API -->|Create job record| TABLE
    QUEUE -->|Dequeue| WORKER
    WORKER -->|Script gen| OAI
    WORKER -->|TTS synthesis| SPE
    WORKER -->|Upload MP3| BLOB
    WORKER -->|Update status| TABLE
    CLI -->|GET /jobs/id| API
    PLUGIN -->|Returns Adaptive Card| AGENT
    AGENT -->|Renders results| COPILOT
    COPILOT -->|Shows card + audio| USER
    API -->|Read status| TABLE
    API -->|Generate SAS URL| BLOB
    API & WORKER -.->|Auth| KV
    API & WORKER -.->|Telemetry| LOG
```

---

## 4. Async Processing Flow

```mermaid
sequenceDiagram
    participant User as 👤 User (Teams / M365 Chat)
    participant Copilot as 🤖 M365 Copilot
    participant Agent as DocTalk Agent
    participant Plugin as API Plugin
    participant API as DocTalk API
    participant Queue as Storage Queue
    participant Table as Table Storage
    participant Worker as Background Worker
    participant OAI as Azure OpenAI
    participant Speech as Azure Speech
    participant Blob as Blob Storage

    User->>Copilot: "Generate a podcast about Container Apps"
    Copilot->>Agent: Route to DocTalk agent
    Agent->>Plugin: Extract params (url, style)
    Plugin->>API: POST /generate (url, style)
    API->>Table: Create job (id, status: queued)
    API->>Queue: Enqueue (job_id, url, style)
    API-->>Plugin: 202 Accepted (job_id, status_url)
    Plugin-->>Agent: Job submitted
    Agent-->>Copilot: Render queued card
    Copilot-->>User: Adaptive Card (status: queued)

    Queue->>Worker: Dequeue message
    Worker->>Table: Update status: "scraping"
    Worker->>Worker: Scrape docs from URL
    Worker->>Table: Update status: "generating_script"
    Worker->>OAI: Generate podcast script
    Worker->>Table: Update status: "synthesizing"
    Worker->>Speech: Synthesize SSML → MP3
    Worker->>Blob: Upload MP3
    Worker->>Table: Update status: "completed" + blob_url

    Note over User: User asks "is my podcast ready?"
    User->>Copilot: "Check on my podcast"
    Copilot->>Agent: Route to DocTalk agent
    Plugin->>API: GET /jobs/{id}
    API->>Table: Read job status
    API-->>Plugin: status: completed, audio_url
    Agent-->>Copilot: Render result card
    Copilot-->>User: Adaptive Card (audio player + download link)
```

---

## 5. API Contract

### `POST /generate`

Request a new podcast generation (async).

```json
{
  "url": "https://learn.microsoft.com/azure/container-apps/overview",
  "style": "conversation",
  "notify_teams": false
}
```

Response (`202 Accepted`):

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "status_url": "/jobs/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "estimated_wait_seconds": 90
}
```

### `GET /jobs/{job_id}`

Poll job status.

```json
{
  "job_id": "a1b2c3d4-...",
  "status": "completed",
  "title": "Azure Container Apps Overview",
  "style": "conversation",
  "duration_seconds": 312,
  "download_url": "https://stpodcast*.blob.core.windows.net/podcasts/a1b2c3d4.mp3?sv=...",
  "created_at": "2026-04-22T15:30:00Z",
  "completed_at": "2026-04-22T15:31:32Z"
}
```

### `GET /jobs`

List recent jobs.

```json
{
  "jobs": [ ... ],
  "count": 5
}
```

### Status Lifecycle

```
queued → scraping → generating_script → synthesizing → uploading → completed
                                                                  → failed
```

---

## 6. Component Design (Phase 2)

### 6.1 DocTalk API (`src/api/`)

| Aspect | Detail |
|--------|--------|
| **Framework** | FastAPI (async, auto OpenAPI docs) |
| **Hosting** | Azure Container Apps (serverless, scale to zero) |
| **Auth** | Entra ID (Managed Identity for Azure services) |
| **Endpoints** | `POST /generate`, `GET /jobs/{id}`, `GET /jobs`, `GET /health` |
| **Role** | Accept requests, enqueue jobs, serve status & download URLs |

### 6.2 Background Worker (`src/worker/`)

| Aspect | Detail |
|--------|--------|
| **Trigger** | Azure Storage Queue messages |
| **Hosting** | Azure Container Apps (separate container, auto-scale on queue depth) |
| **Pipeline** | Scrape → Script Gen → TTS → Upload → Update status |
| **Retry** | 3 retries with exponential backoff, dead-letter after failure |
| **Reuses** | Existing `scraper.py`, `script_generator.py`, `speech_synthesizer.py` |

### 6.3 M365 Copilot Agent (`appPackage/`)

| Aspect | Detail |
|--------|--------|
| **Framework** | Declarative Agent v1.3 + API Plugin v2.2 (NOT Bot Framework) |
| **Hosting** | No separate hosting — agent definition lives in `appPackage/`, API plugin calls existing FastAPI |
| **UX** | Copilot handles NLU, parameter extraction, and Adaptive Card rendering; API plugin maps to existing endpoints |
| **Auth** | Entra ID SSO via OAuthPluginVault (being simplified — may use `none` auth for dev) |
| **Functions** | `generatePodcast`, `getJobStatus`, `listRecentPodcasts` — maps to existing REST API |
| **Files** | `manifest.json`, `declarativeAgent.json`, `doctalk-plugin.json`, `openapi.yaml` |
| **Dev workflow** | Teams Toolkit for local dev, sideloading, and publish |

### 6.4 CLI (Updated — `src/cli.py`)

| Change | Detail |
|--------|--------|
| **Mode** | Calls DocTalk API instead of running pipeline locally |
| **Submit** | `POST /generate` → get job_id |
| **Poll** | `GET /jobs/{id}` every 5s with spinner |
| **Download** | Fetch MP3 from SAS URL when complete |
| **Fallback** | `--local` flag to run locally as before (no API needed) |

---

## 7. Azure Resource Architecture (Phase 2)

```mermaid
graph TB
    subgraph "Resource Group: rg-doctalk-dev"
        subgraph "Compute"
            ACA_API["Container Apps<br/>doctalk-api<br/>(FastAPI)"]
            ACA_WORKER["Container Apps<br/>doctalk-worker<br/>(Queue processor)"]
            ACR["Container Registry<br/>crdoctalk*<br/>Basic"]
        end

        subgraph "AI Services"
            OAI["Azure OpenAI<br/>oai-doctalk-*<br/>S0 + GPT-5.1"]
            SPE["Azure Speech<br/>speech-doctalk-*<br/>S0"]
        end

        subgraph "Data"
            STO["Blob Storage<br/>stdoctalk*<br/>(podcasts + queues + tables)"]
        end

        subgraph "Identity"
            ENTRA["Entra ID App<br/>(OAuth for Copilot plugin)"]
        end

        subgraph "Operations"
            KV["Key Vault<br/>kv-doctalk-*"]
            LOG["Log Analytics + App Insights"]
            CAE["Container Apps Environment"]
        end
    end

    ACA_API --> CAE
    ACA_WORKER --> CAE
    ACR -->|Image pull| ACA_API & ACA_WORKER
    ACA_API -->|Enqueue| STO
    ACA_WORKER -->|Dequeue| STO
    ACA_WORKER --> OAI & SPE
    ACA_WORKER -->|Upload MP3| STO
    ENTRA -.->|OAuth token validation| ACA_API
    ACA_API & ACA_WORKER -->|Secrets| KV
    ACA_API & ACA_WORKER -->|Logs| LOG
```

### New Resources (Phase 2 additions)

| Resource | Service | SKU | Purpose | Est. Cost |
|----------|---------|-----|---------|-----------|
| Container Apps Env | `Microsoft.App/managedEnvironments` | Consumption | Serverless container hosting | ~$0 (scale to zero) |
| API Container | `Microsoft.App/containerApps` | Consumption | FastAPI endpoint | ~$2–5/mo |
| Worker Container | `Microsoft.App/containerApps` | Consumption | Queue-triggered processor | ~$1–3/mo |
| Container Registry | `Microsoft.ContainerRegistry/registries` | Basic | Docker image storage | ~$5/mo |
| Entra ID App | `Microsoft.Graph/applications` | Free | OAuth for Copilot API plugin | Free |
| **Phase 2 Additional** | | | | **~$8–13/mo** |
| **Total (Phase 1 + 2)** | | | | **~$18–38/mo** |

---

## 8. M365 Copilot Agent User Experience

### Conversation Starters

When a user opens DocTalk in M365 Copilot, they see these suggested prompts:

- "Generate a podcast about Azure Container Apps"
- "Create a beginner-level episode on Azure Functions"
- "What podcasts have I generated recently?"
- "Check the status of my latest podcast"

### Interaction Flow

```
┌─────────────────────────────────────────────┐
│ 🤖 M365 Copilot (Teams / M365 Chat)        │
├─────────────────────────────────────────────┤
│                                             │
│  You:                                       │
│  ┌─────────────────────────────────────┐    │
│  │ Generate a podcast about Azure      │    │
│  │ Container Apps                      │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  DocTalk (via Copilot):                     │
│  ┌─────────────────────────────────────┐    │
│  │ 🎙️ Podcast Queued                  │    │
│  │                                     │    │
│  │ URL: https://learn.microsoft.com/   │    │
│  │      azure/container-apps/overview  │    │
│  │ Job ID: a1b2c3d4-...               │    │
│  │ Status: queued                      │    │
│  └─────────────────────── Adaptive Card┘    │
│                                             │
│  You:                                       │
│  ┌─────────────────────────────────────┐    │
│  │ Check on my podcast                 │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  DocTalk (via Copilot):                     │
│  ┌─────────────────────────────────────┐    │
│  │ 🎙️ Azure Container Apps Overview   │    │
│  │                                     │    │
│  │ Status: completed                   │    │
│  │ Style: conversation                 │    │
│  │                                     │    │
│  │ [▶️ Play / Download Podcast]        │    │
│  └─────────────────── Adaptive Card    ┘    │
│                                             │
└─────────────────────────────────────────────┘
```

> **Note:** Copilot handles NLU (natural language understanding), parameter extraction, and response rendering. The API plugin defines Adaptive Card templates that Copilot uses to display structured results.

---

## 9. Phase 1 Component Design (Current — Unchanged)

### 9.1 Scraper (`src/scraper.py`)

| Aspect | Detail |
|--------|--------|
| **Input** | Azure docs URL (learn.microsoft.com) |
| **Output** | `{title, description, content, url}` dict |
| **Method** | HTTP GET + BeautifulSoup HTML parsing |
| **Content extraction** | Targets `<main>` or article divs; strips nav, scripts, footer, feedback sections |
| **Truncation** | Caps at 12,000 chars to fit model context window |
| **Error handling** | HTTP timeout (30s), raise on non-200 status |

### 9.2 Script Generator (`src/script_generator.py`)

| Aspect | Detail |
|--------|--------|
| **Input** | Scraped docs dict + style (`single` / `conversation`) |
| **Output** | Podcast script as plain text |
| **Model** | Azure OpenAI GPT-5.1 (deployment: `gpt-51`) |
| **Auth** | `DefaultAzureCredential` → Bearer token provider |
| **Single narrator** | ~600–1000 words, conversational tone, key takeaways |
| **Two-host** | Alex (expert) + Sam (curious co-host), ~1000–1500 words |
| **Temperature** | 0.7 (balanced creativity/accuracy) |
| **Max tokens** | 4000 completion tokens |

### 9.3 Speech Synthesizer (`src/speech_synthesizer.py`)

| Aspect | Detail |
|--------|--------|
| **Input** | Script text + output file path |
| **Output** | MP3 file (16kHz, 128kbps mono) |
| **Voices** | `en-US-AndrewMultilingualNeural` (narrator/Alex), `en-US-EmmaMultilingualNeural` (Sam) |
| **SSML style** | `chat` express-as with neutral prosody rate |
| **Voice limit** | Azure Speech max 50 `<voice>` elements per request |
| **Mitigation** | Merges consecutive same-speaker lines; chunks into ≤48 segments with MP3 concatenation |
| **Auth** | AAD token with resource ID (`aad#<resource-id>#<token>`) or subscription key |

### 9.4 CLI (`src/cli.py`)

| Command | Description | Azure Resources Needed |
|---------|-------------|------------------------|
| `generate <url>` | Full pipeline: scrape → script → audio | ✅ OpenAI + Speech |
| `generate --script-only <url>` | Scrape + script generation only | ✅ OpenAI only |
| `preview <url>` | Preview extracted content | ❌ None |

---

## 10. Azure Resource Architecture (Phase 1 — Current)

```mermaid
graph TB
    subgraph "Resource Group: rg-podcast-dev"
        OAI["Azure OpenAI<br/>oai-podcast-*<br/>S0 + GPT-5.1"]
        SPE["Azure Speech<br/>speech-podcast-*<br/>S0"]
        STO["Blob Storage<br/>stpodcast*<br/>Standard_LRS"]
        KV["Key Vault<br/>kv-podcast-*<br/>Standard"]
        LOG["Log Analytics<br/>log-podcast-*<br/>PerGB2018"]
        AI["App Insights<br/>appi-podcast-*"]
    end

    OAI -->|Diagnostics| LOG
    SPE -->|Diagnostics| LOG
    STO -->|Metrics| LOG
    KV -->|Audit logs| LOG
    AI -->|Workspace| LOG
```

### Infrastructure as Code

| File | Scope | Resources |
|------|-------|-----------|
| `infra/main.bicep` | Subscription | Resource group, module orchestration, outputs |
| `infra/modules/openai.bicep` | Resource Group | OpenAI account + GPT-5.1 deployment + diagnostics |
| `infra/modules/speech.bicep` | Resource Group | Speech Services account + diagnostics |
| `infra/modules/storage.bicep` | Resource Group | Storage account + `podcasts` container + diagnostics |
| `infra/modules/keyvault.bicep` | Resource Group | Key Vault (RBAC mode, soft-delete) + diagnostics |
| `infra/modules/monitoring.bicep` | Resource Group | Log Analytics workspace + Application Insights |

### Naming Convention

```
{resource-abbreviation}-doctalk-{uniqueHash6}
```

Where `uniqueHash6 = take(uniqueString(subscription().id, environmentName, location), 6)`.

---

## 11. Security Design

| Principle | Phase 1 | Phase 2 |
|-----------|---------|---------|
| **No secrets in code** | `DefaultAzureCredential` | Managed Identity on Container Apps |
| **RBAC authorization** | Key Vault RBAC mode | + AcrPull, Storage Queue Data roles |
| **TLS 1.2+** | Storage account | + Container Apps ingress HTTPS-only |
| **No public blob access** | `allowBlobPublicAccess: false` | Time-limited SAS tokens for downloads |
| **Soft delete** | Key Vault (7-day) | Unchanged |
| **Diagnostic logging** | All resources → Log Analytics | + Container Apps system/console logs |
| **Network isolation** | User's local machine | Container Apps VNet (optional) |
| **Copilot agent auth** | N/A | Entra ID SSO via OAuthPluginVault (OAuth 2.0 authorization code flow) |

---

## 12. Cost Estimate (Monthly)

### Phase 1 — CLI Only (Current)

| Resource | Est. Cost | Assumptions |
|----------|-----------|-------------|
| Azure OpenAI (GPT-5.1) | ~$5–15 | ~50 generations, ~2K tokens each |
| Azure Speech (Neural TTS) | ~$2–5 | ~250 min neural TTS |
| Blob Storage | <$1 | ~250 MB stored |
| Key Vault + Log Analytics | <$2 | Minimal usage |
| **Phase 1 Total** | **~$10–25** | |

### Phase 2 — API + M365 Copilot Agent

| Resource | Est. Cost | Assumptions |
|----------|-----------|-------------|
| Container Apps (API) | ~$2–5 | Scale-to-zero, ~100 requests/mo |
| Container Apps (Worker) | ~$1–3 | Scale-to-zero, ~50 jobs/mo |
| Container Registry (Basic) | ~$5 | Image storage |
| Entra ID App Registration | Free | OAuth for Copilot API plugin |
| Storage Queues + Tables | <$1 | Job management |
| **Phase 2 Additional** | **~$8–13** | |
| **Combined Total** | **~$18–38** | |

---

## 13. Limitations & Constraints

| Constraint | Detail | Mitigation |
|------------|--------|------------|
| Content truncation | Scraper caps at 12K chars | Summarization; could add pagination |
| SSML voice limit | Max 50 `<voice>` elements | Auto-chunking with MP3 concatenation |
| Public pages only | Some docs require auth | Error message; could add login support |
| English only | TTS voices are English | Multilingual voice support (Phase 3) |
| No caching | Regenerates every time | Blob-based caching by URL hash (Phase 2) |
| Queue visibility timeout | Long TTS jobs may exceed 30s default | Set 5-min visibility timeout |
| Cold start | Container Apps scale-to-zero | First request ~5–10s latency; acceptable for small team |

---

## 14. Technology Choices & Trade-offs

| Decision | Choice | Alternative | Rationale |
|----------|--------|-------------|-----------|
| API framework | FastAPI | Flask, Django | Async-native, auto OpenAPI docs, lightweight |
| Compute | Container Apps | Functions, App Service | Scale-to-zero, queue triggers, no VM management |
| Job queue | Storage Queue | Service Bus | Simpler, cheaper, sufficient for small team scale |
| Job state | Table Storage | Cosmos DB, SQL | Cheap, serverless, key-value is enough |
| Copilot integration | Declarative Agent + API Plugin | Bot Framework SDK | Zero backend code — Copilot handles NLU/rendering, API plugin maps to existing REST API |
| Container registry | ACR Basic | Docker Hub | Azure-native, private, Managed Identity pull |
| LLM | Azure OpenAI GPT-5.1 | GPT-4.1, Claude | Best Azure integration, managed, passwordless |
| TTS | Azure Speech Neural | ElevenLabs | Native Azure, SSML multi-voice, chat style |
| Scraping | BeautifulSoup | Playwright | Lightweight, no browser needed |
| IaC | Bicep + AZD | Terraform | Azure-native, simplified provisioning |
| Auth | DefaultAzureCredential | API keys | Zero-secret dev, Managed Identity in prod |
