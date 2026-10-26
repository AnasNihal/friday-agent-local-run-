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
        profile = json.loads(path.read_text())
        if not isinstance(profile, dict):
            return {"preferred_name": "", "favorite_apps": [], "preferences": {}}
        return profile
    except (OSError, json.JSONDecodeError):
        return {"preferred_name": "", "favorite_apps": [], "preferences": {}}


def save_profile(profile: dict) -> None:
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dictionary")
    path = _path()
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(profile, indent=2) + "\n")
    temporary.replace(path)
