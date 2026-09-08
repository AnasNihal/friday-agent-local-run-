"""Browser actions delegated to the user's default browser."""
from urllib.parse import quote_plus, urlparse
import webbrowser

from friday.config import config


def _validated_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    return url.strip() if parsed.scheme in {"http", "https"} and parsed.netloc else None


def open_url(url: str) -> str:
    validated = _validated_url(url)
    if not validated:
        return "For safety, I can only open http or https URLs."
    opened = webbrowser.open(validated)
    return {"success": bool(opened), "message": "Opening that now." if opened else "The default browser did not accept the URL.", "url": validated}


def web_search(query: str) -> str:
    return search_browser(query)


def youtube_search(query: str) -> str:
    return open_url("https://www.youtube.com/results?search_query=" + quote_plus(query))


def search_browser(query: str) -> dict:
    """Open a safely encoded Google search in the default browser."""
    url = "https://www.google.com/search?q=" + quote_plus(query.strip())
    result = open_url(url)
    if isinstance(result, dict):
        result["query"] = query
        return result
    return {"success": False, "message": result, "query": query, "url": url}


def open_world_monitor() -> dict:
    """Open the configured public world-monitor dashboard."""
    url = _validated_url(config.world_monitor_url)
    if not url:
        return {"success": False, "message": "WORLD_MONITOR_URL must be an http(s) URL", "url": config.world_monitor_url}
    opened = webbrowser.open(url)
    return {"success": bool(opened), "message": "World monitor opened successfully" if opened else "The default browser did not accept the world monitor URL.", "url": url}


def register(mcp):
    mcp.tool()(open_url)
    mcp.tool()(web_search)
    mcp.tool()(youtube_search)
    mcp.tool()(search_browser)
    mcp.tool()(open_world_monitor)
