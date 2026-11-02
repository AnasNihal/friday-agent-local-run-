"""Application configuration for the local-first FRIDAY assistant."""

from dataclasses import dataclass
import os
import math
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be one of: true, false, 1, 0, yes, no, on, off")


def _positive_int(name: str, default: int) -> int:
    """Read a positive integer setting with a useful error message."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


def _positive_float(name: str, default: float) -> float:
    """Read a finite positive decimal setting."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(f"{name} must be a positive number")
    return parsed


def _unit_float(name: str, default: float) -> float:
    """Read a positive decimal no greater than one."""
    parsed = _positive_float(name, default)
    if parsed > 1:
        raise ValueError(f"{name} must be greater than 0 and at most 1")
    return parsed


@dataclass(frozen=True)
class Config:
    server_name: str = os.getenv("SERVER_NAME", "FRIDAY")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base.en")
    tts_provider: str = os.getenv("TTS_PROVIDER", "piper")
    tts_voice: str = os.getenv("TTS_VOICE", "en_US-lessac-medium")
    tts_enabled: bool = _bool("TTS_ENABLED")
    piper_model: str = os.getenv("PIPER_MODEL", "voices/en_US-lessac-medium.onnx")
    stt_language: str = os.getenv("STT_LANGUAGE", "en")
    stt_device: str = os.getenv("STT_DEVICE", "cpu")
    stt_compute_type: str = os.getenv("STT_COMPUTE_TYPE", "int8")
    mic_silence_duration: float = _positive_float("MIC_SILENCE_DURATION", 0.8)
    mic_speech_timeout: float = _positive_float("MIC_SPEECH_TIMEOUT", 10.0)
    mic_max_recording_duration: float = _positive_float("MIC_MAX_RECORDING_DURATION", 20.0)
    mic_energy_threshold: float = _unit_float("MIC_ENERGY_THRESHOLD", 0.012)
    mcp_server_port: int = _positive_int("MCP_SERVER_PORT", 8000)
    world_monitor_url: str = os.getenv("WORLD_MONITOR_URL", "https://worldmonitor.app/")
    max_tool_iterations: int = _positive_int("MAX_TOOL_ITERATIONS", 5)
    memory_dir: str = os.getenv("FRIDAY_MEMORY_DIR", "memory")
    debug: bool = _bool("DEBUG")
    debug_tools: bool = _bool("DEBUG_TOOLS")


config = Config()
