"""Browser actions delegated to the user's default browser."""
from urllib.parse import quote
import webbrowser


def open_url(url: str) -> str:
    if not (url.startswith("https://") or url.startswith("http://")):
        return "For safety, I can only open http or https URLs."
    webbrowser.open(url)
    return "Opening that now."


def web_search(query: str) -> str:
    return open_url("https://www.google.com/search?q=" + quote(query))


def youtube_search(query: str) -> str:
    return open_url("https://www.youtube.com/results?search_query=" + quote(query))


def register(mcp):
    mcp.tool()(open_url)
    mcp.tool()(web_search)
    mcp.tool()(youtube_search)
