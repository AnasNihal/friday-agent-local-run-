"""Local microphone capture and Faster-Whisper speech recognition.

This module deliberately owns all audio/STT concerns. Importing it does not
load a model or require microphone permissions, which keeps console mode
independent from voice input.
"""

from __future__ import annotations

from dataclasses import dataclass
import queue
import time
from typing import Any

from friday.config import config


class STTError(RuntimeError):
    """A user-actionable local STT or microphone error."""


@dataclass(frozen=True)
class MicrophoneSettings:
    sample_rate: int = 16_000
    channels: int = 1
    block_duration: float = 0.064
    silence_duration: float = 0.8
    speech_timeout: float = 10.0
    max_recording_duration: float = 20.0
    energy_threshold: float = 0.012


def microphone_status() -> tuple[bool, str]:
    """Return whether a default input device can be queried."""
    try:
        import sounddevice as sd

        device = sd.query_devices(kind="input")
        if not device:
            return False, "No microphone input device was found."
        return True, str(device.get("name", "Microphone detected"))
    except ImportError:
        return False, "Install microphone support with: uv sync --extra voice"
    except Exception as exc:
        message = str(exc)
        if "permission" in message.lower() or "denied" in message.lower():
            return False, (
                "Microphone access denied. Enable it in System Settings → "
                "Privacy & Security → Microphone → Terminal."
            )
        return False, f"Microphone unavailable: {message}"


class MicrophoneRecorder:
    """Record one utterance using energy-based start/stop detection.

    This is intentionally a small reliable fallback rather than a second VAD
    stack. It waits for speech, then stops after a short quiet period. The
    interface can later accept Silero without changing the agent.
    """

    def __init__(self, settings: MicrophoneSettings | None = None) -> None:
        self.settings = settings or MicrophoneSettings()

    def record_until_silence(self) -> tuple[Any, int]:
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise STTError("Install microphone support with: uv sync --extra voice") from exc

        settings = self.settings
        blocksize = max(1, int(settings.sample_rate * settings.block_duration))
        chunks: queue.Queue[Any] = queue.Queue()
        callback_error: list[BaseException] = []

        def callback(indata, _frames, _time, status):
            if status:
                # Dropouts are recoverable; recording still produces audio.
                pass
            chunks.put(indata[:, 0].copy())

        try:
            with sd.InputStream(
                samplerate=settings.sample_rate,
                channels=settings.channels,
                dtype="float32",
                blocksize=blocksize,
                callback=callback,
            ):
                started = False
                quiet_for = 0.0
                started_at = time.monotonic()
                last_log = 0.0
                recorded: list[Any] = []
                while True:
                    try:
                        chunk = chunks.get(timeout=settings.block_duration + 1.0)
                    except queue.Empty as exc:
                        raise STTError("The microphone stopped returning audio.") from exc
                    level = float(np.sqrt(np.mean(np.square(chunk))))
                    now = time.monotonic()
                    if not started:
                        if level >= settings.energy_threshold:
                            started = True
                            recorded.append(chunk)
                            started_at = now
                            quiet_for = 0.0
                        elif now - started_at >= settings.speech_timeout:
                            raise STTError("I did not hear speech. Check the microphone and try again.")
                        elif now - last_log >= 1.0:
                            print("🎤 Listening...", flush=True)
                            last_log = now
                    else:
                        recorded.append(chunk)
                        quiet_for = 0.0 if level >= settings.energy_threshold else quiet_for + settings.block_duration
                        if quiet_for >= settings.silence_duration:
                            break
                        if now - started_at >= settings.max_recording_duration:
                            break
                if not recorded:
                    raise STTError("No speech was recorded.")
                audio = np.concatenate(recorded).astype("float32", copy=False)
                return audio, settings.sample_rate
        except STTError:
            raise
        except Exception as exc:
            message = str(exc)
            if "permission" in message.lower() or "denied" in message.lower():
                raise STTError(
                    "Microphone access denied. Enable it in System Settings → "
                    "Privacy & Security → Microphone → Terminal."
                ) from exc
            raise STTError(f"Could not record from the microphone: {message}") from exc


class LocalSTT:
    """Lazy-loaded Faster-Whisper recognizer with a stable transcription API."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or config.whisper_model
        self._model: Any = None

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise STTError("Install local Whisper with: uv sync --extra voice") from exc
            try:
                self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
            except Exception as exc:
                raise STTError(
                    f"Could not load Whisper model {self.model_name!r}. "
                    "The first load may download it locally; check disk space and try again."
                ) from exc
        return self._model

    def transcribe(self, audio: Any, sample_rate: int = 16_000) -> str:
        """Transcribe a mono float32 waveform captured at ``sample_rate``."""
        if sample_rate != 16_000:
            raise STTError("LocalSTT expects 16 kHz microphone audio.")
        try:
            segments, _info = self.model.transcribe(
                audio,
                language="en",
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            raise STTError(f"Whisper transcription failed: {exc}") from exc


def transcribe_microphone(stt: LocalSTT | None = None) -> str:
    """Record one utterance and transcribe it; useful for manual diagnostics."""
    audio, sample_rate = MicrophoneRecorder().record_until_silence()
    return (stt or LocalSTT()).transcribe(audio, sample_rate)
