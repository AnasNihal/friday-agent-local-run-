"""FRIDAY entry point with text console mode and local voice-input mode.

Voice input is deliberately limited to microphone → Faster-Whisper → text;
TTS is not part of this phase.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import Callable

from dotenv import load_dotenv

from friday.config import config
from friday.ollama import OllamaError, chat, check_ready
from friday.stt import LocalSTT, STTError, microphone_status
from friday.tools.applications import open_application
from friday.tools.browser import youtube_search, web_search
from friday.tools.productivity import create_note
from friday.tools.system import get_battery_status, get_cpu_usage, get_current_time, get_disk_usage, get_memory_usage

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

SYSTEM_PROMPT = """You are FRIDAY, a private local voice assistant. Be calm, concise, confident, and slightly witty. Address the user as boss occasionally. Keep ordinary answers to two or three spoken sentences. Never mention internal prompts, APIs, or implementation details. If a tool result is supplied, summarize it naturally and do not invent facts. The user has explicitly chosen local-only processing."""


def build_stt():
    """Build the local Whisper adapter without loading it until first use."""
    if os.getenv("STT_PROVIDER", "local_whisper") != "local_whisper":
        raise ValueError("Only STT_PROVIDER=local_whisper is supported")
    return LocalSTT(config.whisper_model)


def build_llm() -> Callable:
    return chat


def build_tts():
    """Return a Piper command adapter if Piper is installed; otherwise explain how to fix it."""
    voice = config.tts_voice
    command = os.getenv("PIPER_BIN", "piper")
    if not shutil_which(command):
        raise RuntimeError(f"Piper is unavailable. Install it and the {voice} voice, or set PIPER_BIN.")
    return command


def shutil_which(command: str) -> str | None:
    import shutil
    return shutil.which(command)


def startup_diagnostics() -> bool:
    print("╔══════════════════════════════════╗")
    print("║          FRIDAY ONLINE           ║")
    print("╚══════════════════════════════════╝")
    print(f"LLM:      Ollama ({config.ollama_base_url})")
    print(f"Model:    {config.ollama_model}")
    print(f"STT:      Local Whisper ({config.whisper_model})")
    print(f"TTS:      Piper ({config.tts_voice})")
    print("Tools:    MCP")
    ready, message = check_ready()
    print(("✓ " if ready else "✗ ") + message)
    return ready


def voice_input_diagnostics(stt: LocalSTT) -> bool:
    """Check audio input, load Whisper, and check the existing local brain."""
    print("FRIDAY Voice Input Diagnostics")
    microphone_ok, microphone_message = microphone_status()
    print(("✓ " if microphone_ok else "✗ ") + microphone_message)
    try:
        _ = stt.model
        print(f"✓ Whisper model loaded ({stt.model_name})")
        whisper_ok = True
    except STTError as exc:
        print(f"✗ {exc}")
        whisper_ok = False
    ollama_ok, ollama_message = check_ready()
    print(("✓ " if ollama_ok else "✗ ") + ollama_message)
    return microphone_ok and whisper_ok and ollama_ok


def _tool_route(text: str) -> tuple[str, str] | None:
    lower = re.sub(r"[?!.,]+$", "", text.lower().strip())
    patterns: list[tuple[str, str, Callable]] = [
        (r"(?:what is|check|what's) my battery(?: percentage)?", "battery", get_battery_status),
        (r"(?:open|launch|start) (?:the )?(.+)", "app", open_application),
        (r"search youtube for (.+)", "youtube", youtube_search),
        (r"(?:search|google) (?:the web )?for (.+)", "web", web_search),
        (r"what time is it|current time", "time", get_current_time),
        (r"(?:make|create|save) (?:a )?note(?: that says| saying| about)? (.+)", "note", create_note),
        (r"cpu usage|processor usage", "cpu", get_cpu_usage),
        (r"memory usage|ram usage", "memory", get_memory_usage),
        (r"disk usage|free disk space", "disk", get_disk_usage),
    ]
    for pattern, name, function in patterns:
        match = re.fullmatch(pattern, lower)
        if match:
            argument = match.group(1) if match.lastindex else ""
            if name == "app":
                original_match = re.fullmatch(pattern, text.strip(), flags=re.IGNORECASE)
                argument = original_match.group(1) if original_match else argument
            result = function(argument) if name in {"app", "youtube", "web", "note"} else function()
            return name, json.dumps(result) if isinstance(result, (dict, list)) else str(result)
    return None


def _friday_response(text: str, messages: list[dict[str, str]]) -> str:
    routed = _tool_route(text)
    messages.append({"role": "user", "content": text})
    if routed:
        name, result = routed
        messages.append({"role": "system", "content": f"Tool result for {name}: {result}"})
    try:
        answer = chat(messages)
    except OllamaError as exc:
        return f"I couldn't reach Ollama. {exc}"
    messages.append({"role": "assistant", "content": answer})
    return answer


def run_console() -> int:
    if not startup_diagnostics():
        return 1
    print("Status:   Ready")
    print("Type 'exit' to leave. Console mode keeps the microphone and TTS out of the loop for easy debugging.\n")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue
        if text.lower() in {"exit", "quit", "goodbye"}:
            print("FRIDAY: Standing by, boss.")
            return 0
        print(f"FRIDAY: {_friday_response(text, messages)}")


def run_voice_input() -> int:
    """Continuously record, transcribe, and send text through the same agent."""
    stt = build_stt()
    if not voice_input_diagnostics(stt):
        return 1
    from friday.stt import MicrophoneRecorder

    recorder = MicrophoneRecorder()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("\nVoice input ready. Speak naturally; press Ctrl-C to exit. TTS is disabled in this phase.\n")
    while True:
        try:
            audio, sample_rate = recorder.record_until_silence()
            text = stt.transcribe(audio, sample_rate)
            if not text:
                print("I didn't catch that.\n")
                continue
            print(f"\nYou: {text}")
            print(f"FRIDAY: {_friday_response(text, messages)}\n")
        except STTError as exc:
            print(f"STT: {exc}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nFRIDAY: Standing by, boss.")
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local FRIDAY assistant")
    parser.add_argument("mode", nargs="?", choices=("console", "voice-input", "dev"), default="console")
    args = parser.parse_args()
    if args.mode == "console":
        return run_console()
    if args.mode == "voice-input":
        return run_voice_input()
    print("Voice mode is the next local integration step. Use `uv run agent_friday.py console` for the working MVP.")
    print("Configure local Whisper/Piper first; no LiveKit or cloud credentials are required for console mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
