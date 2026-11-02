"""Optional local Piper speech synthesis and system audio playback."""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from friday.config import config

MAX_SPEECH_CHARACTERS = 4_000


class TTSError(RuntimeError):
    """A user-actionable local text-to-speech error."""


def synthesize(text: str, output_path: str | Path) -> Path:
    """Render speech to a WAV file using the configured local Piper model."""
    if not isinstance(text, str) or not text.strip():
        raise TTSError("There is no text to speak.")
    if len(text) > MAX_SPEECH_CHARACTERS:
        raise TTSError(f"Speech is limited to {MAX_SPEECH_CHARACTERS} characters.")

    binary = shutil.which(__import__("os").getenv("PIPER_BIN", "piper"))
    if not binary:
        raise TTSError("Piper is unavailable. Install it or set PIPER_BIN.")
    model = Path(config.piper_model).expanduser()
    if not model.is_file():
        raise TTSError(f"Piper model not found: {model}")

    destination = Path(output_path)
    try:
        result = subprocess.run(
            [binary, "--model", str(model), "--output_file", str(destination)],
            input=text.strip(),
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TTSError(f"Piper could not synthesize speech: {exc}") from exc
    if result.returncode != 0 or not destination.is_file() or destination.stat().st_size == 0:
        detail = result.stderr.strip()[:300]
        raise TTSError("Piper did not create an audio file." + (f" {detail}" if detail else ""))
    return destination
