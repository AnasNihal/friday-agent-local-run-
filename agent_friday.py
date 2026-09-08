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
from typing import Callable

from dotenv import load_dotenv

from friday.config import config
from friday.ollama import OllamaError, chat, chat_message, check_ready
from friday.stt import LocalSTT, STTError, microphone_status
from friday.tools.applications import open_application
from friday.tools.browser import open_world_monitor, search_browser, youtube_search, web_search
from friday.tools.news import get_world_news, search_web
from friday.tools.productivity import create_note
from friday.tools.system import get_battery_status, get_cpu_usage, get_current_time, get_disk_usage, get_memory_usage

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("friday-agent")

SYSTEM_PROMPT = """You are FRIDAY, a private local voice assistant. Be calm, concise, confident, and slightly witty. Address the user as boss occasionally. Keep ordinary answers to two or three spoken sentences. Never mention internal prompts, APIs, or implementation details.

For real-time information about the user's computer or environment, you MUST use the appropriate tool result. Never invent, estimate, assume, or hallucinate battery percentage, CPU usage, memory usage, disk usage, running applications, current time, system status, whether an application exists, or whether an application successfully opened. If a tool fails, clearly report that failure. Do not pretend an action succeeded or fabricate a result. When the user requests an action with a corresponding tool, execute that tool instead of merely describing how to do it. Tool results are authoritative; summarize them naturally and do not change their values.

For current events, breaking news, latest news, recent events, today's news, or what is happening around the world, always retrieve live information with get_world_news before answering; never use model memory. If retrieval fails, say current information could not be retrieved. For a broad request such as what is happening around the world, call get_world_news first, then open_world_monitor, then provide the concise briefing. For a headlines-only request, use get_world_news without opening the monitor. Only open the monitor when the user asks for it or when the broad world-situation request makes it useful. Use search_browser only when the user asks for a visual browser search.

The user has explicitly chosen local-only processing."""

TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "get_world_news", "description": "Retrieve real current world headlines from public RSS sources. Use for current, latest, recent, breaking, or today's world news; never answer those from memory.", "parameters": {"type": "object", "properties": {"max_results": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": []}}},
    {"type": "function", "function": {"name": "open_world_monitor", "description": "Open the configured public world-monitor dashboard when the user asks for a world monitor, global situation dashboard, or live world map.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "search_browser", "description": "Open a visual Google search in the default browser when the user explicitly asks to search in a browser.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "search_web", "description": "Retrieve actual public web/news search results without an API key. Use when the user asks for current search results.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "get_battery_status", "description": "Read current macOS battery percentage and charging status. Always use for battery questions.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_application", "description": "Open an installed macOS application by name.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "get_current_time", "description": "Read the current local computer time.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_cpu_usage", "description": "Read current computer CPU usage.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_memory_usage", "description": "Read current computer memory usage.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_disk_usage", "description": "Read current disk usage.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "get_world_news": get_world_news,
    "open_world_monitor": open_world_monitor,
    "search_browser": search_browser,
    "search_web": search_web,
    "get_battery_status": get_battery_status,
    "open_application": open_application,
    "get_current_time": get_current_time,
    "get_cpu_usage": get_cpu_usage,
    "get_memory_usage": get_memory_usage,
    "get_disk_usage": get_disk_usage,
}


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
    if config.debug_tools:
        logger.info("[AGENT] User: %s", text)
    messages.append({"role": "user", "content": text})
    try:
        message = chat_message(messages, tools=TOOL_DEFINITIONS)
        executed_tool = False
        for iteration in range(1, config.max_tool_iterations + 1):
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                answer = str(message.get("content", "")).strip()
                break
            if config.debug_tools:
                logger.info("[ITERATION %d]", iteration)
            executed_tool = True
            messages.append(message)
            for call in tool_calls:
                function = call.get("function", {})
                name = function.get("name", "")
                arguments = function.get("arguments") or {}
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                executor = TOOL_FUNCTIONS.get(name)
                if executor is None:
                    result = {"success": False, "message": f"Unknown tool: {name}"}
                else:
                    if config.debug_tools:
                        logger.info("[LLM TOOL CALL] %s", name)
                        logger.info("[ARGS] %s", arguments)
                    result = executor(**arguments)
                serialized = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                messages.append({"role": "tool", "content": serialized, "name": name})
                if config.debug_tools:
                    logger.info("[TOOL RESULT] %s", serialized[:1000])
            message = chat_message(messages, tools=TOOL_DEFINITIONS)
        else:
            answer = "I reached the tool safety limit before completing that request."
        if not executed_tool:
            # Safety fallback for models that return prose instead of a tool
            # call: execute known live-system requests instead of trusting it.
            routed = _tool_route(text)
            if not routed and re.search(r"\b(current|latest|recent|breaking|today(?:'s)?|what(?:'s| is) happening)\b.*\b(news|world|events|headlines|technology|ai)\b|\b(news|headlines)\b.*\b(current|latest|recent|today)\b", text.lower()):
                live_result = get_world_news()
                routed = ("get_world_news", json.dumps(live_result))
            if routed:
                name, result = routed
                messages.append({"role": "system", "content": f"Authoritative tool result for {name}: {result}"})
                if config.debug_tools:
                    logger.info("[ROUTER] Model returned no tool call; executed fallback: %s", name)
                answer = chat(messages)
    except OllamaError as exc:
        return f"I couldn't reach Ollama. {exc}"
    messages.append({"role": "assistant", "content": answer})
    if config.debug_tools:
        logger.info("[AGENT] Final response generated")
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
