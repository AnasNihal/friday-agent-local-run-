"""Local notes without a cloud account."""
from datetime import datetime
from pathlib import Path
from friday.config import config


def _notes() -> Path:
    path = Path(config.memory_dir) / "notes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_note(text: str) -> str:
    filename = _notes() / f"{datetime.now():%Y%m%d-%H%M%S}.txt"
    filename.write_text(text.strip() + "\n")
    return f"Note saved locally as {filename.name}."


def read_notes() -> list[str]:
    return [item.read_text(errors="replace").strip() for item in sorted(_notes().glob("*.txt"))[-20:]]


def register(mcp):
    mcp.tool()(create_note)
    mcp.tool()(read_notes)
