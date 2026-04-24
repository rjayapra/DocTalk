# Morpheus — History

## Learnings

### 2026-04-24 — Copilot Extension Setup Guide (Hackathon)

- Created comprehensive **COPILOT-EXTENSION-SETUP.md** as a practical, step-by-step guide for hackathon participants.
- Included all critical sections: GitHub App creation with minimal permissions, endpoint configuration, installation flow, testing scenarios, troubleshooting with real error messages, and a ready-to-run 2-minute demo script.
- Key insight: For hackathon demos, simplicity wins — the guide focuses on "register → install → test" flow without deep OAuth/JWT details (saved for post-hackathon production setup).
- SSE streaming format is: `data: {"choices": [{"delta": {"content": "text"}}]}\n\n` followed by `data: [DONE]\n\n` — critical for real-time status updates in Copilot Chat.
- Updated README.md with Copilot Extension section to surface the setup guide and demo quick-start.
- Current API endpoint uses basic `X-GitHub-Token` header check (no JWT validation) — sufficient for hackathon, but production must validate tokens against GitHub's public key.

### 2026-04-24 — Copilot Extension Design (Phase 3)

- **GitHub Copilot Extensions** use a simple agent protocol: a server receives a POST with `messages` array (OpenAI chat format) and `X-GitHub-Token` header, and streams back SSE responses in OpenAI-compatible delta format.
- The canonical example is [copilot-extensions/blackbeard-extension](https://github.com/copilot-extensions/blackbeard-extension) — ~50 lines of JS. The pattern is: parse messages → call Copilot LLM or custom logic → stream SSE back.
- Extensions can call `https://api.githubcopilot.com/chat/completions` with the user's token for LLM responses — useful for freeform chat fallback.
- GitHub has also introduced MCP (Model Context Protocol) as an alternative/complement to agent-based extensions. MCP is broader but agent protocol is simpler for our use case.
- For DocTalk: separate ACA app is the right deployment model. SSE long-polling (waiting for podcast generation) has a fundamentally different scaling profile than the short request/response API.
- Designed full Phase 3 architecture with DESIGN.md and updated ARCHITECTURE.md.
