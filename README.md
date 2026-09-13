# Project FRIDAY — Local AI Voice Assistant

**A privacy-first, local-only AI agent that turns natural-language instructions into real actions on your machine.**

FRIDAY is a privacy-first macOS assistant built around [Ollama](https://ollama.com). It runs entirely on your machine, keeps memory on disk, exposes safe tools through FastMCP, and requires no paid API or cloud account.

`ai` · `ai-agents` · `automation` · `local-first` · `python`

---

## Table of Contents

- [Overview](#overview)
- [Stack](#stack)
- [Project Structure](#project-structure)
- [Install](#install)
- [Run the Working MVP](#run-the-working-mvp)
- [Local Speech-to-Text](#local-speech-to-text)
- [World Intelligence](#world-intelligence)
- [Safety](#safety)
- [Configuration](#configuration)
- [License](#license)

---

## Overview

FRIDAY is designed around a simple boundary: **everything runs locally by default.**

- The reasoning model runs through Ollama on your machine.
- Tools are exposed over a local MCP server, not a remote API.
- Speech-to-text and text-to-speech targets are local models, not cloud services.
- Memory is a plain JSON profile plus local notes — inspectable, editable, and yours.

The default MVP uses `qwen2.5:7b` and needs no API keys to run.

## Stack

| Component | Default |
|---|---|
| **Brain** | Ollama, model `qwen2.5:7b` |
| **MCP tools** | FastMCP over local SSE |
| **STT** | Local Faster-Whisper (`base.en`) |
| **TTS** | Local Piper (`en_US-lessac-medium`) |
| **Memory** | Explicit JSON profile + local notes |

## Project Structure

```
friday-agent-local-run/
│
├── friday/              # Core agent package
├── scripts/             # Utility scripts (e.g. microphone test)
├── tests/               # Test suite
│
├── agent_friday.py      # Main entry point (console / voice-input modes)
├── server.py            # Standalone MCP tool server
├── main.py              # Application entry point
│
├── .env.example         # Environment variable template
├── .python-version      # Pinned Python version
├── pyproject.toml       # Project metadata & dependencies
├── uv.lock              # Locked dependency versions
└── README.md
```

## Install

**Prerequisites:** Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone the repository
git clone https://github.com/AnasNihal/friday-agent-local-run-.git
cd friday-agent-local-run-

# Install dependencies
uv sync

# Start Ollama and pull the default model
ollama serve
ollama pull qwen2.5:7b

# Set up environment variables
cp .env.example .env
```

No API keys are needed for the default configuration.

## Run the Working MVP

Console mode is the primary debugging path — it needs no microphone, LiveKit, or TTS:

```bash
uv run agent_friday.py console
```

Try prompts like:

```text
What is my battery percentage?
Open Spotify
Search YouTube for humanoid robots
Make a note about buying coffee
What time is it?
```

The MCP server can also run independently in another terminal:

```bash
uv run server.py
```

It serves tools over local SSE on port `8000`.

## Local Speech-to-Text

Phase 2A adds microphone input via local Faster-Whisper. Voice adapters are optional so console mode stays fast and dependency-light:

```bash
uv sync --extra voice
```

The default model is `base.en`, configurable with `WHISPER_MODEL`. The first transcription may download the model into Faster-Whisper's local cache — no API key required.

**Test the microphone and transcription independently:**

```bash
uv run --extra voice python scripts/test_microphone.py
```

**Run voice input mode:**

```bash
uv run --extra voice agent_friday.py voice-input
```

This records until a short silence, transcribes locally, and sends the text through the existing FRIDAY → Ollama → tool pipeline. Text responses are printed; TTS is intentionally not included in this phase. Press `Ctrl-C` to exit.

**Tool-call diagnostics:**

```bash
DEBUG_TOOLS=true uv run agent_friday.py console
```

This logs the model-selected tool, its arguments, the actual tool result, and the final response generation. Live system questions are never answered from model knowledge — if Ollama declines a tool call, FRIDAY falls back to a deterministic safety path and still returns the real tool result.

> **macOS microphone permissions:** if input is denied, enable Terminal under `System Settings → Privacy & Security → Microphone`. The recorder uses 16 kHz mono audio, `base.en`, CPU `int8` inference, and energy-based silence detection — a reliable baseline on Apple Silicon.

## World Intelligence

FRIDAY can retrieve live world headlines without an API key:

```text
What's happening around the world?
Give me today's world news.
Open the world monitor.
What are the latest technology headlines?
```

Headlines are aggregated from BBC World, Al Jazeera, NPR World, and Google News RSS. Sources can fail independently — results report which feeds succeeded and include only retrieved headlines. Internet access is required for current news.

The default monitor is `https://worldmonitor.app/`, configurable via `WORLD_MONITOR_URL`, and opens in the system default browser.

- `search_browser` — opens an encoded Google search
- `search_web` — retrieves public Google News RSS results without scraping Google HTML

**Inspect multi-tool orchestration:**

```bash
DEBUG_TOOLS=true uv run agent_friday.py console
```

The tool-call loop is capped by `MAX_TOOL_ITERATIONS` (default `5`) and supports chained sequences such as `get_world_news` → `open_world_monitor` → final briefing.

## Safety

FRIDAY's tools are read-only or reversible by default:

- No delete-file tool
- No arbitrary shell execution tool
- No automatic software installation
- URLs restricted to HTTP(S) only
- Local notes and profile data are written only when explicitly requested

## Configuration

Copy `.env.example` to `.env` to configure Ollama, Whisper, Piper, MCP, and the local memory directory.

> `nomic-embed-text` is intentionally not used in phase 1. Semantic memory can be added later without changing the core provider boundary.

## License

No license has been published yet. All rights are reserved by the author until a license is added.

---

Built by [AnasNihal](https://github.com/AnasNihal) — a privacy-focused local AI agent redesigned to run entirely on your own machine, models, and tools.
