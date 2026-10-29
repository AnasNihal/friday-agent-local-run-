"""Small dependency-light client for Ollama's local HTTP API."""

from __future__ import annotations
from typing import Any, Iterable
import httpx
from friday.config import config


class OllamaError(RuntimeError):
    pass


def _error(exc: Exception) -> OllamaError:
    return OllamaError(
        "Could not connect to Ollama. Start it with `ollama serve`, "
        f"then make sure `{config.ollama_model}` is installed. ({exc})"
    )


def list_models() -> list[str]:
    try:
        response = httpx.get(f"{config.ollama_base_url}/api/tags", timeout=3)
        response.raise_for_status()
        return [item["name"] for item in response.json().get("models", [])]
    except Exception as exc:
        raise _error(exc) from exc


def check_ready() -> tuple[bool, str]:
    try:
        models = list_models()
        installed = {name.split(":", 1)[0] for name in models}
        wanted = config.ollama_model.split(":", 1)[0]
        if config.ollama_model not in models and wanted not in installed:
            return False, f"Model {config.ollama_model} is not installed. Run: ollama pull {config.ollama_model}"
        return True, f"Ollama available; {config.ollama_model} available"
    except OllamaError:
        return False, "Ollama is not running. Start it with: ollama serve"


def chat_message(messages: Iterable[dict[str, Any]], *, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": config.ollama_model, "messages": list(messages), "stream": False, "options": {"temperature": 0.4}}
    if tools:
        payload["tools"] = tools
    try:
        response = httpx.post(f"{config.ollama_base_url}/api/chat", json=payload, timeout=180)
        response.raise_for_status()
        body = response.json()
        message = body.get("message") if isinstance(body, dict) else None
        if not isinstance(message, dict):
            raise ValueError("Ollama returned no message object")
        if not isinstance(message.get("content", ""), str):
            raise ValueError("Ollama returned invalid message content")
        if not isinstance(message.get("tool_calls", []), list):
            raise ValueError("Ollama returned invalid tool calls")
        return message
    except Exception as exc:
        raise _error(exc) from exc


def chat(messages: Iterable[dict[str, str]], *, stream: bool = False) -> str:
    return str(chat_message(messages)["content"]).strip()
