"""Local notes without a cloud account."""
from datetime import datetime
from pathlib import Path
from friday.config import config

MAX_NOTE_CHARS = 12_000


def _notes() -> Path:
    path = Path(config.memory_dir) / "notes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_note(text: str) -> str:
    content = text.strip()
    if not content:
        return "I couldn't save an empty note."
    if len(content) > MAX_NOTE_CHARS:
        return f"That note is too long. Keep it under {MAX_NOTE_CHARS} characters."
    filename = _notes() / f"{datetime.now():%Y%m%d-%H%M%S-%f}.txt"
    filename.write_text(content + "\n")
    return f"Note saved locally as {filename.name}."


def read_notes() -> list[str]:
    notes = []
    for item in sorted(_notes().glob("*.txt"))[-20:]:
        try:
            with item.open("r", encoding="utf-8", errors="replace") as stream:
                notes.append(stream.read(MAX_NOTE_CHARS).strip())
        except OSError:
            continue
    return notes


def register(mcp):
    mcp.tool()(create_note)
    mcp.tool()(read_notes)
