"""CLI entry point for the Azure Docs Podcast Generator."""

import os
import re
import sys
import click

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config import Config
from .scraper import fetch_docs
from .script_generator import generate_script
from .speech_synthesizer import synthesize_single_narrator, synthesize_conversation


@click.group()
def cli():
    """Azure Docs Podcast Generator — Turn documentation into audio."""
    pass


@cli.command()
@click.argument("url")
@click.option(
    "--style",
    type=click.Choice(["single", "conversation"], case_sensitive=False),
    default="conversation",
    help="Podcast style: single narrator or two-host conversation.",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output MP3 file path. Defaults to output/<title>.mp3.",
)
@click.option(
    "--script-only",
    is_flag=True,
    default=False,
    help="Only generate the script without audio synthesis.",
)
def generate(url: str, style: str, output: str, script_only: bool):
    """Generate a podcast from an Azure documentation URL."""
    # Validate config
    errors = Config.validate()
    if errors:
        for err in errors:
            click.echo(click.style(f"✗ {err}", fg="red"))
        click.echo("\nCopy .env.example to .env and fill in your Azure resource details.")
        raise click.Abort()

    # Step 1: Fetch documentation
    click.echo(click.style("📄 Fetching documentation...", fg="cyan"))
    try:
        docs = fetch_docs(url)
    except Exception as e:
        click.echo(click.style(f"✗ Failed to fetch URL: {e}", fg="red"))
        raise click.Abort()

    click.echo(f"   Title: {docs['title']}")
    click.echo(f"   Content length: {len(docs['content'])} chars")

    # Step 2: Generate script
    click.echo(click.style(f"\n🤖 Generating {style} script with Azure OpenAI...", fg="cyan"))
    try:
        script = generate_script(docs, style=style)
    except Exception as e:
        click.echo(click.style(f"✗ Script generation failed: {e}", fg="red"))
        raise click.Abort()

    click.echo(f"   Script length: {len(script)} chars")

    if script_only:
        click.echo(click.style("\n📝 Generated Script:", fg="green"))
        click.echo("─" * 60)
        click.echo(script)
        click.echo("─" * 60)
        return

    # Step 3: Synthesize audio
    if not output:
        os.makedirs("output", exist_ok=True)
        safe_title = re.sub(r"[^\w\s-]", "", docs["title"])[:50].strip()
        safe_title = re.sub(r"\s+", "-", safe_title).lower()
        output = f"output/{safe_title}.mp3"

    click.echo(click.style("\n🔊 Synthesizing audio with Azure Speech...", fg="cyan"))
    try:
        if style == "single":
            result_path = synthesize_single_narrator(script, output)
        else:
            result_path = synthesize_conversation(script, output)
    except Exception as e:
        click.echo(click.style(f"✗ Audio synthesis failed: {e}", fg="red"))
        raise click.Abort()

    file_size = os.path.getsize(result_path)
    click.echo(click.style(f"\n✓ Podcast saved to: {result_path}", fg="green"))
    click.echo(f"  File size: {file_size / 1024:.1f} KB")


@cli.command()
@click.argument("url")
def preview(url: str):
    """Preview the extracted content from a documentation URL (no Azure resources needed)."""
    click.echo(click.style("📄 Fetching documentation...", fg="cyan"))
    try:
        docs = fetch_docs(url)
    except Exception as e:
        click.echo(click.style(f"✗ Failed to fetch: {e}", fg="red"))
        raise click.Abort()

    click.echo(click.style(f"\nTitle: {docs['title']}", fg="green", bold=True))
    click.echo(f"Description: {docs['description']}")
    click.echo(f"URL: {docs['url']}")
    click.echo(f"Content length: {len(docs['content'])} chars\n")
    click.echo("─" * 60)
    click.echo(docs["content"][:2000])
    if len(docs["content"]) > 2000:
        click.echo(f"\n... ({len(docs['content']) - 2000} more characters)")
    click.echo("─" * 60)


def main():
    cli()


if __name__ == "__main__":
    main()
