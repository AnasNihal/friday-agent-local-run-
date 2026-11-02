"""Lightweight diagnostics for FRIDAY's optional local services."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import socket

from friday.config import config
from friday.ollama import check_ready
from friday.stt import microphone_status


def collect_health() -> list[dict[str, str]]:
    """Return service readiness without loading speech models or opening audio."""
    ollama_ok, ollama_message = check_ready()
    microphone_ok, microphone_message = microphone_status()
    piper_binary = shutil.which(os.getenv("PIPER_BIN", "piper"))
    piper_model = Path(config.piper_model).expanduser()
    try:
        with socket.create_connection(("127.0.0.1", config.mcp_server_port), timeout=0.4):
            mcp_message = f"MCP service is responding on port {config.mcp_server_port}"
            mcp_status = "ready"
    except OSError:
        mcp_message = f"MCP service is not responding on port {config.mcp_server_port}"
        mcp_status = "optional"

    return [
        {"name": "Ollama", "status": "ready" if ollama_ok else "unavailable", "message": ollama_message},
        {
            "name": "Voice input dependencies",
            "status": "ready" if importlib.util.find_spec("faster_whisper") else "optional",
            "message": "Faster-Whisper is installed" if importlib.util.find_spec("faster_whisper") else "Install with: uv sync --extra voice",
        },
        {"name": "Microphone", "status": "ready" if microphone_ok else "optional", "message": microphone_message},
        {
            "name": "Piper speech output",
            "status": "ready" if piper_binary and piper_model.is_file() else "optional",
            "message": "Piper and its model are available" if piper_binary and piper_model.is_file() else f"Set PIPER_BIN and PIPER_MODEL (model exists: {piper_model.is_file()})",
        },
        {"name": "MCP server", "status": mcp_status, "message": mcp_message},
    ]
