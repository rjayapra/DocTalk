# Roadmap & Next Steps

> DocTalk — future enhancement ideas organized by phase.

---

## Phase 1 — Polish & Harden (Current → Next)

| Item | Description | Effort |
|------|-------------|--------|
| 🧪 **Unit tests** | Add pytest tests for scraper, script generator, and synthesizer (mock Azure calls) | Medium |
| 📦 **Blob upload** | Auto-upload generated MP3s to Azure Blob Storage after synthesis | Small |
| 🔄 **Caching layer** | Cache scraped content + generated scripts to avoid redundant API calls | Medium |
| 🏷️ **ID3 tags** | Add podcast metadata (title, description, date) to MP3 files via `mutagen` | Small |
| ⚙️ **Config validation** | Better error messages when `.env` is missing or partially configured | Small |
| 📊 **Telemetry** | Send generation events to App Insights (duration, token usage, errors) | Medium |
| 🔐 **Key Vault integration** | Store and retrieve Speech key from Key Vault (currently using env vars) | Small |

---

## Phase 2 — Web UI & Multi-Format

| Item | Description | Effort |
|------|-------------|--------|
| 🌐 **Web interface** | Streamlit or Flask web UI — paste URL, choose style, download MP3 | Medium |
| 🐳 **Containerize** | Dockerfile + deploy to Azure Container Apps for hosted access | Medium |
| 📋 **Batch processing** | Accept a list of URLs (file or CLI arg), generate a podcast playlist | Small |
| 📑 **RSS feed generation** | Generate a podcast RSS feed from Blob Storage contents | Medium |
| 🔗 **Share links** | Generate SAS URLs for sharing podcasts without authentication | Small |
| 📊 **Progress bar** | Real-time progress indicators for long-running synthesis | Small |

---

## Phase 3 — Intelligence & Personalization

| Item | Description | Effort |
|------|-------------|--------|
| 🌍 **Multi-language** | Support non-English docs + localized TTS voices | Large |
| 🎨 **Voice selection** | Let users pick from Azure Neural voice catalog | Medium |
| ⏱️ **Adjustable length** | Control podcast length (5-min quick take vs. 20-min deep dive) | Small |
| 🎵 **Intro/outro music** | Add configurable background music or jingles | Small |
| 🧠 **Smart summarization** | Use RAG to combine multiple related docs into a single episode | Large |
| 📚 **Learning paths** | Auto-generate a podcast series from an Azure Learning Path URL | Large |
| 🎯 **Audience targeting** | Adjust content depth (beginner, intermediate, expert) | Medium |

---

## Phase 4 — Enterprise & Scale

| Item | Description | Effort |
|------|-------------|--------|
| 👥 **Multi-tenant** | Auth (Entra ID) + per-user podcast libraries | Large |
| ⚡ **Async processing** | Queue-based architecture (Service Bus) for scalable generation | Large |
| 📈 **Usage analytics** | Dashboard showing popular topics, generation stats, user engagement | Medium |
| 🔄 **Auto-refresh** | Monitor docs for updates, auto-regenerate affected podcasts | Large |
| 🤝 **GitHub integration** | Generate podcast from PR descriptions or ADR files | Medium |
| 📱 **Mobile app** | Companion app with offline download + playback | Large |
| 🗓️ **Scheduled generation** | Timer-triggered Azure Function to generate daily/weekly digests | Medium |

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
