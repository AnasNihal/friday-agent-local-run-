"""Read-only file awareness tools."""
from pathlib import Path


def list_directory(path: str = ".") -> list[str] | str:
    try:
        target = Path(path).expanduser().resolve()
        if not target.is_dir():
            return f"I couldn't read that directory: {target} is not a directory."
        return [item.name for item in sorted(target.iterdir())[:100]]
    except OSError as exc:
        return f"I couldn't read that directory: {exc}"


def search_files(query: str, path: str = ".") -> list[str] | str:
    query = query.strip()
    if not query:
        return "Please provide a file name or part of a file name to search for."
    try:
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            return f"I couldn't search that path: {root} is not a directory."
        return [str(item) for item in root.rglob(f"*{query}*") if item.is_file()][:100]
    except OSError as exc:
        return f"I couldn't search that path: {exc}"


def open_file(path: str, max_chars: int = 12000) -> str:
    if max_chars < 0:
        return "The maximum file preview length cannot be negative."
    try:
        return Path(path).expanduser().read_text(errors="replace")[:max_chars]
    except OSError as exc:
        return f"I couldn't open that file: {exc}"


def register(mcp):
    mcp.tool()(list_directory)
    mcp.tool()(search_files)
    mcp.tool()(open_file)
