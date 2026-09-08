"""Application configuration for the local-first FRIDAY assistant."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    server_name: str = os.getenv("SERVER_NAME", "FRIDAY")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base.en")
    tts_provider: str = os.getenv("TTS_PROVIDER", "piper")
    tts_voice: str = os.getenv("TTS_VOICE", "en_US-lessac-medium")
    mcp_server_port: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    world_monitor_url: str = os.getenv("WORLD_MONITOR_URL", "https://worldmonitor.app/")
    max_tool_iterations: int = int(os.getenv("MAX_TOOL_ITERATIONS", "5"))
    memory_dir: str = os.getenv("FRIDAY_MEMORY_DIR", "memory")
    debug: bool = _bool("DEBUG")
    debug_tools: bool = _bool("DEBUG_TOOLS")


config = Config()
