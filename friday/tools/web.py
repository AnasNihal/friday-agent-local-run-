"""Secondary web tools retained from the upstream MCP surface."""

import webbrowser
import httpx


def fetch_url(url: str) -> str:
    """Fetch a small text preview from an explicitly supplied HTTP(S) URL."""
    if not url.startswith(("http://", "https://")):
        return "For safety, only HTTP(S) URLs can be fetched."
    try:
        response = httpx.get(url, follow_redirects=True, timeout=10)
        response.raise_for_status()
        return response.text[:4000]
    except Exception as exc:
        return f"Unable to fetch URL: {exc}"


def get_world_finance_news() -> dict:
    """Retained compatibility tool; use public Google News finance RSS."""
    from friday.tools.news import search_web
    result = search_web("world finance markets news")
    result["topic"] = "finance"
    return result


def open_finance_world_monitor() -> dict:
    url = "https://finance.worldmonitor.app/"
    opened = webbrowser.open(url)
    return {"success": bool(opened), "message": "Finance world monitor opened successfully" if opened else "The default browser did not accept the URL.", "url": url}


def register(mcp):
    mcp.tool()(get_world_finance_news)
    mcp.tool()(fetch_url)
    mcp.tool()(open_finance_world_monitor)
