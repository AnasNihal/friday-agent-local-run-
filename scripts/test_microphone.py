"""Manual microphone + local Whisper check.

Run with: uv run --extra voice python scripts/test_microphone.py
"""

from __future__ import annotations

from friday.config import config
from friday.stt import LocalSTT, MicrophoneRecorder, STTError, microphone_status


def main() -> int:
    ok, message = microphone_status()
    if not ok:
        print(f"✗ {message}")
        return 1
    print(f"✓ {message}")
    print(f"Whisper model: {config.whisper_model}")
    try:
        stt = LocalSTT()
        print("Loading Whisper locally (first run may download the model)...")
        _ = stt.model
        print("Recording...\nSpeak now.")
        audio, sample_rate = MicrophoneRecorder().record_until_silence()
        text = stt.transcribe(audio, sample_rate)
        print(f"\nTranscription:\n{text or '[no speech detected]'}")
        return 0
    except STTError as exc:
        print(f"✗ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
