"""GitHub Copilot Extension (agent) endpoint for DocTalk.

Streams SSE responses in the Copilot agent protocol format so users can
generate podcasts directly from GitHub Copilot Chat.

PRODUCTION NOTE:
Azure Container Apps ingress timeout must be set to at least 600s to support
long-running podcast generation jobs. Default is 240s which will cause SSE
streams to be cut off prematurely. Set via:
  az containerapp ingress update --name <app> --resource-group <rg> --timeout 600
"""
import asyncio
import json
import re
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/copilot", tags=["copilot"])

# The API base URL — when running inside the same container we call ourselves
# via localhost. In production, DOCTALK_API_BASE can be overridden.
import os

DOCTALK_API_BASE = os.getenv(
    "DOCTALK_API_BASE", "http://localhost:8000"
)

# Regex for supported URLs: Microsoft docs and GitHub
_DOCS_URL_RE = re.compile(
    r"https?://(?:(?:learn|docs)\.microsoft\.com|github\.com)/[^\s)\]\"'>]+"
)

POLL_INTERVAL = 3  # seconds between status polls
MAX_POLL_TIME = 300  # 5-minute timeout

# Status → user-friendly emoji messages
_STATUS_MESSAGES = {
    "queued": "⏳ Job queued — waiting for a worker…\n",
    "processing": "⚙️ Processing…\n",
    "scraping": "📄 Scraping the documentation page…\n",
    "generating_script": "✍️ Generating the podcast script…\n",
    "synthesizing": "🔊 Synthesizing speech audio…\n",
}


def _sse_chunk(text: str) -> str:
    """Wrap *text* in the Copilot agent SSE frame."""
    payload = json.dumps({"choices": [{"delta": {"content": text}}]})
    return f"data: {payload}\n\n"


def _sse_done() -> str:
    return "data: [DONE]\n\n"


async def _stream_podcast(url: str, style: str) -> AsyncGenerator[str, None]:
    """Submit a generate request and poll until done, yielding SSE chunks.
    
    Sends periodic keep-alive comments to prevent proxy/gateway timeouts during
    long-running jobs (Azure Container Apps, GitHub SSE proxy).
    """
    yield _sse_chunk(f"🎙️ Starting podcast generation for:\n{url}\n\n")

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Submit job
        try:
            resp = await client.post(
                f"{DOCTALK_API_BASE}/generate",
                json={"url": url, "style": style},
            )
            resp.raise_for_status()
            job = resp.json()
        except Exception as exc:
            yield _sse_chunk(f"❌ Failed to submit job: {exc}\n")
            yield _sse_done()
            return

        job_id = job["id"]
        yield _sse_chunk(f"📋 Job created: `{job_id}`\n\n")

        # 2. Poll for completion
        last_status = None
        elapsed = 0
        while elapsed < MAX_POLL_TIME:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            # Send SSE keep-alive comment to prevent connection timeout
            # (Azure Container Apps/GitHub proxy require regular data flow)
            yield ": keepalive\n\n"

            try:
                resp = await client.get(f"{DOCTALK_API_BASE}/jobs/{job_id}")
                resp.raise_for_status()
                job = resp.json()
            except Exception:
                continue  # transient error — retry

            status = job.get("status", "unknown")

            # Send a status update only when status changes
            if status != last_status:
                msg = _STATUS_MESSAGES.get(status)
                if msg:
                    yield _sse_chunk(msg)
                last_status = status

            if status == "completed":
                audio_url = job.get("audio_url", "")
                title = job.get("title", "Podcast")
                yield _sse_chunk(
                    f"\n✅ **Podcast ready!**\n\n"
                    f"**{title}**\n\n"
                    f"🎧 [Listen to the podcast]({audio_url})\n"
                )
                yield _sse_done()
                return

            if status == "failed":
                error = job.get("error", "Unknown error")
                yield _sse_chunk(f"\n❌ Generation failed: {error}\n")
                yield _sse_done()
                return

        # Timeout - provide actionable guidance
        yield _sse_chunk(
            f"\n⏰ Stream timed out after {MAX_POLL_TIME}s while job was still running.\n\n"
            f"**Your job is still processing in the background.**\n\n"
            f"Check status manually:\n"
            f"```\nGET {DOCTALK_API_BASE}/jobs/{job_id}\n```\n\n"
            f"Or try again in a few minutes. Job ID: `{job_id}`\n"
        )
        yield _sse_done()


def _help_message() -> AsyncGenerator[str, None]:
    """Return usage instructions when no URL is detected."""

    async def _gen():
        yield _sse_chunk(
            "👋 **Welcome to DocTalk!**\n\n"
            "I turn Microsoft Learn / Docs pages into audio podcasts.\n\n"
            "**Usage:** Just paste a URL from `learn.microsoft.com` or "
            "`docs.microsoft.com` and I'll generate a podcast for you.\n\n"
            "**Example:**\n"
            "```\nhttps://learn.microsoft.com/en-us/azure/container-apps/overview\n```\n\n"
            "You can also add a style: `<url> style=interview`\n"
        )
        yield _sse_done()

    return _gen()


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/agent")
async def agent_metadata():
    """Discovery endpoint required by GitHub Copilot Extensions.
    
    Returns agent metadata in the format expected by GitHub's Copilot Extension
    protocol. This endpoint is called during agent discovery/configuration.
    """
    return {
        "name": "DocTalk",
        "description": "Generate audio podcasts from Microsoft Learn documentation",
        "version": "1.0.0",
    }


@router.post("/agent")
async def agent_chat(
    request: Request,
    x_github_token: str | None = Header(None),
):
    """Main Copilot agent chat endpoint.

    Receives the Copilot message payload, extracts a docs URL from the last
    user message, kicks off podcast generation, and streams SSE status
    updates back to the user.
    """
    # Light auth check — just verify the header is present
    if not x_github_token:
        raise HTTPException(status_code=401, detail="Missing X-GitHub-Token header")

    body = await request.json()
    messages = body.get("messages", [])

    # Find the last user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    if not user_message:
        return StreamingResponse(
            _help_message(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Extract URL
    match = _DOCS_URL_RE.search(user_message)
    if not match:
        return StreamingResponse(
            _help_message(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    url = match.group(0)

    # Check for style override
    style = "conversation"
    style_match = re.search(r"style\s*=\s*(\w+)", user_message, re.IGNORECASE)
    if style_match:
        style = style_match.group(1)

    # Stream SSE response with proper headers to prevent buffering/timeout
    return StreamingResponse(
        _stream_podcast(url, style),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx/proxy buffering
        },
    )
