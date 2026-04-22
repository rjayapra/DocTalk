# Roadmap & Next Steps

> DocTalk — evolution from CLI tool to multi-channel podcast platform.

---

## Phase 1 — CLI Tool ✅ (Completed)

| Item | Status | Description |
|------|--------|-------------|
| 🔍 Docs scraper | ✅ Done | BeautifulSoup extraction from Azure docs URLs |
| 🤖 Script generation | ✅ Done | GPT-5.1 single-narrator + two-host conversation |
| 🔊 Speech synthesis | ✅ Done | Azure Neural TTS with SSML chunking |
| 🖥️ CLI interface | ✅ Done | Click-based `generate` and `preview` commands |
| ☁️ Azure infra | ✅ Done | Bicep + AZD provisioning (6 resources) |
| 📝 Documentation | ✅ Done | README, ARCHITECTURE, ROADMAP |

---

## Phase 2 — API Backend + Teams Bot (Next)

| Item | Description | Effort |
|------|-------------|--------|
| 🌐 **FastAPI backend** | REST API (`POST /generate`, `GET /jobs/{id}`) hosted on Azure Container Apps | Medium |
| ⚙️ **Background worker** | Queue-triggered container that runs the scrape → script → TTS pipeline | Medium |
| 📬 **Storage Queue + Table** | Job queue for async processing + Table Storage for job status tracking | Small |
| 🐳 **Containerize** | Dockerfile for API + Worker, push to Azure Container Registry | Small |
| 💬 **Teams Bot** | Bot Framework bot — paste URL, get podcast via Adaptive Card | Medium |
| 🔄 **CLI update** | CLI calls API instead of running locally; `--local` flag for offline mode | Small |
| 🏗️ **Bicep modules** | New modules: `containerapp.bicep`, `bot.bicep`, `registry.bicep` | Medium |
| 🧪 **Unit tests** | pytest for scraper, script generator, synthesizer, API endpoints | Medium |

### Architecture Summary

```
CLI / Teams Bot  →  FastAPI (Container Apps)  →  Storage Queue
                                                       ↓
                                                  Worker (Container Apps)
                                                       ↓
                                              OpenAI → Speech → Blob
                                                       ↓
                                              Notification → Client
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full diagrams and API contracts.

---

## Phase 3 — Intelligence & Reach

| Item | Description | Effort |
|------|-------------|--------|
| 🌍 **Multi-language** | Support non-English docs + localized TTS voices | Large |
| 🎨 **Voice selection** | Let users pick from Azure Neural voice catalog | Medium |
| ⏱️ **Adjustable length** | Control podcast length (5-min quick take vs. 20-min deep dive) | Small |
| 🎵 **Intro/outro music** | Add configurable background music or jingles | Small |
| 🧠 **Smart summarization** | Use RAG to combine multiple related docs into a single episode | Large |
| 📚 **Learning paths** | Auto-generate a podcast series from an Azure Learning Path URL | Large |
| 🎯 **Audience targeting** | Adjust content depth (beginner, intermediate, expert) | Medium |
| 📋 **Batch processing** | Accept a list of URLs, generate a playlist | Small |
| 📑 **RSS feed** | Podcast RSS feed from Blob Storage for standard podcast apps | Medium |
| 🔗 **Share links** | SAS URLs for sharing podcasts without auth | Small |

---

## Phase 4 — Enterprise & Scale

| Item | Description | Effort |
|------|-------------|--------|
| 👥 **Multi-tenant** | Entra ID auth + per-user podcast libraries | Large |
| ⚡ **Service Bus upgrade** | Replace Storage Queue with Service Bus for dead-lettering, sessions | Medium |
| 📈 **Usage analytics** | Dashboard showing popular topics, generation stats | Medium |
| 🔄 **Auto-refresh** | Monitor docs for updates, regenerate affected podcasts | Large |
| 📱 **Mobile companion** | React Native or PWA with offline playback | Large |
| 🌐 **Web portal** | Full web UI for browsing, searching, and playing podcasts | Large |
| 🗓️ **Scheduled digests** | Timer-triggered Function for daily/weekly podcast digests | Medium |
| 🤝 **GitHub integration** | Generate podcast from PR descriptions or ADR files | Medium |

---

## Contributing Ideas

Have an idea? File it in the backlog! Great podcast generator features are ones that:

1. **Save time** — reduce effort to go from docs → learning
2. **Improve quality** — make the audio more engaging or informative
3. **Scale access** — let more people benefit from audio learning

---

## Known Technical Debt

| Item | Description |
|------|-------------|
| `.env.example` references `gpt-4o` | Should be updated to `gpt-51` to match deployed model |
| No retry logic for OpenAI API | Should add exponential backoff for transient errors |
| Temp file cleanup on crash | If process crashes mid-synthesis, temp MP3 chunks aren't cleaned up |
| No input URL validation | Should validate that the URL is actually an Azure docs page |
| Hardcoded voice names | Voice selection should be configurable via `.env` or CLI flags |
