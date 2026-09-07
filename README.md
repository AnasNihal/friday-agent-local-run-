# Project FRIDAY — local AI voice assistant

FRIDAY is a privacy-first macOS assistant built around Ollama. The default MVP uses `qwen2.5:7b`, keeps memory on disk, exposes safe tools through FastMCP, and requires no paid API or cloud account.

## Stack

- Brain: Ollama, default model `qwen2.5:7b`
- MCP tools: FastMCP over local SSE
- STT target: local Faster Whisper (`base.en` by default)
- TTS target: local Piper (`en_US-lessac-medium` by default)
- Memory: small explicit JSON profile plus local notes

## Install

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync
ollama serve
ollama pull qwen2.5:7b
cp .env.example .env
```

No API keys are needed for the default configuration.

## Run the working MVP

Console mode is the primary debugging path and does not need a microphone, LiveKit, or TTS:

```bash
uv run agent_friday.py console
```

Try:

```text
What is my battery percentage?
Open Spotify
Search YouTube for humanoid robots
Make a note about buying coffee
What time is it?
```

The MCP server can run independently in another terminal:

```bash
uv run server.py
```

It serves the tools over local SSE on port 8000.

## Local speech-to-text

Phase 2A adds microphone input with local Faster-Whisper. Voice adapters are intentionally optional so console mode stays fast and reliable:

```bash
uv sync --extra voice
```

The default model is `base.en`; configure it with `WHISPER_MODEL`. The first transcription may download the model into Faster-Whisper's local cache. No API key is required.

Test the microphone and transcription independently:

```bash
uv run --extra voice python scripts/test_microphone.py
```

Then run voice input mode:

```bash
uv run --extra voice agent_friday.py voice-input
```

It records until a short silence, transcribes locally, and sends the text through the existing FRIDAY/Ollama/tool path. Text responses are printed; TTS is intentionally not included in this phase. Press Ctrl-C to exit.

If macOS denies input, enable Terminal under System Settings → Privacy & Security → Microphone. The recorder uses 16 kHz mono audio, `base.en`, CPU `int8` inference, and a small energy-based silence detector for a reliable Apple Silicon baseline.

## Safety

Tools are read-only or reversible by default. There is no delete-file tool, no arbitrary shell tool, and no automatic software installation. URLs are restricted to HTTP(S), and local notes/profile data are only written when explicitly requested.

## Configuration

Copy `.env.example` to `.env` to configure Ollama, Whisper, Piper, MCP, and the local memory directory. `nomic-embed-text` is intentionally not used in phase 1; semantic memory can be added later without changing the core provider boundary.
