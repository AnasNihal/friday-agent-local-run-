"""Live public-news tools backed by RSS/Atom feeds.

No API keys or search services are required. Feed failures are isolated so a
single unavailable publisher does not hide headlines from the other sources.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html
import logging
import re
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import httpx

from friday.config import config

logger = logging.getLogger("friday.tools")

WORLD_NEWS_FEEDS = (
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
    ("Google News World", "https://news.google.com/rss/search?q=world+news&hl=en-US&gl=US&ceid=US:en"),
)


def _clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def _published(value: str | None) -> tuple[str, float]:
    if not value:
        return "", 0.0
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value, 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat(), parsed.timestamp()


def parse_feed(content: bytes, source: str) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    results: list[dict[str, Any]] = []
    for entry in entries:
        title = _clean(entry.findtext("title") or entry.findtext("{http://www.w3.org/2005/Atom}title"))
        link = entry.findtext("link") or ""
        if not link:
            atom_link = entry.find("{http://www.w3.org/2005/Atom}link")
            link = atom_link.get("href", "") if atom_link is not None else ""
        published_raw = (
            entry.findtext("pubDate")
            or entry.findtext("published")
            or entry.findtext("updated")
            or entry.findtext("{http://www.w3.org/2005/Atom}published")
            or entry.findtext("{http://www.w3.org/2005/Atom}updated")
        )
        published, timestamp = _published(published_raw)
        if title and link.startswith(("http://", "https://")):
            results.append({"headline": title, "source": source, "published": published, "url": link, "_timestamp": timestamp})
    return results


def _fetch_feed(source: str, url: str) -> tuple[str, list[dict[str, Any]], str | None]:
    try:
        response = httpx.get(url, headers={"User-Agent": "FRIDAY-local/1.0"}, timeout=10, follow_redirects=True)
        response.raise_for_status()
        return source, parse_feed(response.content, source), None
    except Exception as exc:
        logger.warning("News source unavailable: %s (%s)", source, exc)
        return source, [], str(exc)


def _deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda entry: entry.get("_timestamp", 0), reverse=True):
        key = re.sub(r"[^a-z0-9]+", " ", item["headline"].lower()).strip()
        if key and key not in seen:
            seen.add(key)
            unique.append({key: value for key, value in item.items() if key != "_timestamp"})
    return unique


def get_world_news(max_results: int = 8) -> dict[str, Any]:
    """Retrieve current world headlines from multiple public RSS feeds."""
    articles: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(WORLD_NEWS_FEEDS)) as executor:
        futures = [executor.submit(_fetch_feed, source, url) for source, url in WORLD_NEWS_FEEDS]
        for future in as_completed(futures):
            source, entries, error = future.result()
            sources.append({"source": source, "success": not error, "count": len(entries), **({"error": error} if error else {})})
            articles.extend(entries)
    headlines = _deduplicate(articles)[: max(1, min(max_results, 20))]
    return {
        "success": bool(headlines),
        "message": f"Retrieved {len(headlines)} live headlines" if headlines else "Current news could not be retrieved.",
        "headlines": headlines,
        "sources": sorted(sources, key=lambda source: source["source"]),
    }


def search_web(query: str, max_results: int = 6) -> dict[str, Any]:
    """Search public Google News RSS results without scraping Google HTML."""
    encoded = quote_plus(query.strip())
    source, entries, error = _fetch_feed("Google News", f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en")
    results = _deduplicate(entries)[: max(1, min(max_results, 20))]
    return {"success": bool(results), "query": query, "results": results, **({"error": error} if error else {})}


def register(mcp):
    mcp.tool()(get_world_news)
    mcp.tool()(search_web)
