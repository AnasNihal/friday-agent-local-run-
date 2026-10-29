"""Minimal explicit local memory; nothing is persisted automatically."""

import json
from pathlib import Path
from friday.config import config

MAX_PROFILE_BYTES = 64 * 1024


def _default_profile() -> dict:
    return {"preferred_name": "", "favorite_apps": [], "preferences": {}}


def _normalize_profile(profile: object) -> dict:
    if not isinstance(profile, dict):
        return _default_profile()
    normalized = _default_profile()
    if isinstance(profile.get("preferred_name"), str):
        normalized["preferred_name"] = profile["preferred_name"][:200]
    if isinstance(profile.get("favorite_apps"), list):
        normalized["favorite_apps"] = [
            app[:200] for app in profile["favorite_apps"][:100]
            if isinstance(app, str)
        ]
    if isinstance(profile.get("preferences"), dict):
        normalized["preferences"] = {
            str(key)[:100]: value
            for key, value in list(profile["preferences"].items())[:100]
            if isinstance(key, str) and isinstance(value, (str, int, float, bool))
        }
    return normalized


def _path() -> Path:
    path = Path(config.memory_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / "profile.json"


def load_profile() -> dict:
    path = _path()
    if not path.exists():
        return _default_profile()
    try:
        if path.stat().st_size > MAX_PROFILE_BYTES:
            return _default_profile()
        return _normalize_profile(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return _default_profile()


def save_profile(profile: dict) -> None:
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dictionary")
    path = _path()
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(_normalize_profile(profile), indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
