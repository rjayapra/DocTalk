"""Scrape and extract clean text content from Azure documentation pages."""

import re
import requests
from bs4 import BeautifulSoup


def fetch_docs(url: str) -> dict:
    """Fetch an Azure docs page and extract structured content.

    Returns dict with 'title', 'description', and 'content' keys.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AzurePodcastGenerator/1.0)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = _extract_title(soup)
    description = _extract_description(soup)
    content = _extract_content(soup)

    return {
        "title": title,
        "description": description,
        "content": content,
        "url": url,
    }


def _extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True).split("|")[0].strip()
    return "Azure Documentation"


def _extract_description(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"]
    return ""


def _extract_content(soup: BeautifulSoup) -> str:
    """Extract the main documentation content, removing nav/footer/scripts."""
    # Azure docs main content is typically in <main> or div with specific classes
    main = soup.find("main") or soup.find("div", {"id": "main-column"})
    if not main:
        main = soup.find("div", class_=re.compile(r"content|article|doc"))
    if not main:
        main = soup.find("body")

    if not main:
        return ""

    # Remove unwanted elements
    for tag in main.find_all(["script", "style", "nav", "footer", "aside", "button"]):
        tag.decompose()

    # Remove feedback/rating sections
    for div in main.find_all("div", class_=re.compile(r"feedback|rating|cookie|banner")):
        div.decompose()

    text = main.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Truncate to ~12000 chars to stay within model context limits
    if len(text) > 12000:
        text = text[:12000] + "\n\n[Content truncated for podcast generation...]"

    return text
