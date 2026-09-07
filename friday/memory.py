"""Minimal explicit local memory; nothing is persisted automatically."""

import json
from pathlib import Path
from friday.config import config


def _path() -> Path:
    path = Path(config.memory_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / "profile.json"


def load_profile() -> dict:
    path = _path()
    if not path.exists():
        return {"preferred_name": "", "favorite_apps": [], "preferences": {}}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"preferred_name": "", "favorite_apps": [], "preferences": {}}


def save_profile(profile: dict) -> None:
    _path().write_text(json.dumps(profile, indent=2) + "\n")
