"""Read-only file awareness tools."""
from pathlib import Path

MAX_SEARCH_ENTRIES = 5_000


def list_directory(path: str = ".") -> list[str] | str:
    try:
        target = Path(path).expanduser().resolve()
        if not target.is_dir():
            return f"I couldn't read that directory: {target} is not a directory."
        return [item.name for item in sorted(target.iterdir())[:100]]
    except OSError as exc:
        return f"I couldn't read that directory: {exc}"


def search_files(query: str, path: str = ".") -> list[str] | str:
    query = query.strip()[:200]
    if not query:
        return "Please provide a file name or part of a file name to search for."
    try:
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            return f"I couldn't search that path: {root} is not a directory."
        matches = []
        for index, item in enumerate(root.rglob("*")):
            if index >= MAX_SEARCH_ENTRIES:
                break
            if item.is_file() and query.casefold() in item.name.casefold():
                matches.append(str(item))
                if len(matches) == 100:
                    break
        return matches
    except OSError as exc:
        return f"I couldn't search that path: {exc}"


def open_file(path: str, max_chars: int = 12000) -> str:
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 0:
        return "The maximum file preview length must be a non-negative integer."
    max_chars = min(max_chars, 12_000)
    try:
        with Path(path).expanduser().open("r", encoding="utf-8", errors="replace") as stream:
            return stream.read(max_chars)
    except OSError as exc:
        return f"I couldn't open that file: {exc}"


def register(mcp):
    mcp.tool()(list_directory)
    mcp.tool()(search_files)
    mcp.tool()(open_file)
