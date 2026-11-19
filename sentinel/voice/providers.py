"""Optional offline speech providers (install the ``voice-offline`` extra)."""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path

from sentinel.voice.interfaces import SpeechResult


class VoskRecognizer:
    """Offline recognizer for mono PCM WAV audio and a locally installed Vosk model."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        sample_rate: int = 16_000,
        language: str | None = None,
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.is_dir():
            raise FileNotFoundError(
                f"Vosk model directory not found: {self.model_path}"
            )
        if (
            isinstance(sample_rate, bool)
            or not isinstance(sample_rate, int)
            or sample_rate < 8_000
        ):
            raise ValueError("sample_rate must be an integer >= 8000")
        self.sample_rate = sample_rate
        self.language = language

    def transcribe(self, audio: bytes, *, language: str | None = None) -> SpeechResult:
        if not isinstance(audio, bytes) or not audio:
            raise ValueError("audio must be non-empty WAV bytes")
        try:
            from vosk import KaldiRecognizer, Model  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "Install sentinel-os[voice-offline] to use Vosk"
            ) from exc
        import io

        with wave.open(io.BytesIO(audio), "rb") as wav:
            if (
                wav.getnchannels() != 1
                or wav.getsampwidth() != 2
                or wav.getframerate() != self.sample_rate
            ):
                raise ValueError(
                    "audio must be mono 16-bit PCM WAV at the configured sample rate"
                )
            model = Model(str(self.model_path))
            recognizer = KaldiRecognizer(model, float(self.sample_rate))
            recognizer.SetWords(True)
            recognizer.AcceptWaveform(wav.readframes(wav.getnframes()))
            import json

            result = json.loads(recognizer.FinalResult())
        words = result.get("text", "")
        details = result.get("result", [])
        confidences = [
            float(item["conf"])
            for item in details
            if isinstance(item, dict) and "conf" in item
        ]
        confidence = sum(confidences) / len(confidences) if confidences else None
        return SpeechResult(words, language or self.language, confidence)


class Pyttsx3Synthesizer:
    """Offline speech synthesis to WAV bytes using an installed system voice."""

    def synthesize(self, text: str, *, language: str | None = None) -> bytes:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be non-empty")
        try:
            import pyttsx3  # type: ignore[import-not-found]

        except ImportError as exc:
            raise RuntimeError(
                "Install Sentinel voice dependencies to use pyttsx3"
            ) from exc
        with tempfile.TemporaryDirectory(prefix="sentinel-tts-") as directory:
            output = Path(directory) / "speech.wav"
            engine = pyttsx3.init()
            try:
                if language:
                    candidates = [
                        voice
                        for voice in engine.getProperty("voices")
                        if language.casefold()
                        in (voice.id + " " + voice.name).casefold()
                    ]
                    if not candidates:
                        raise LookupError(
                            f"No installed TTS voice matches language {language!r}"
                        )
                    engine.setProperty("voice", candidates[0].id)
                engine.save_to_file(text, str(output))
                engine.runAndWait()
            finally:
                engine.stop()
            if not output.is_file():
                raise RuntimeError("TTS engine did not produce an audio file")
            return output.read_bytes()


class Pyttsx3Output:
    """Speak through the system's default audio output."""

    def speak(self, text: str, *, language: str | None = None) -> None:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be non-empty")
        try:
            import pyttsx3
        except ImportError as exc:
            raise RuntimeError(
                "Install Sentinel voice dependencies to use pyttsx3"
            ) from exc
        engine = pyttsx3.init()
        try:
            if language:
                candidates = [
                    voice
                    for voice in engine.getProperty("voices")
                    if language.casefold() in (voice.id + " " + voice.name).casefold()
                ]
                if not candidates:
                    raise LookupError(
                        f"No installed TTS voice matches language {language!r}"
                    )
                engine.setProperty("voice", candidates[0].id)
            engine.say(text)
            engine.runAndWait()
        finally:
            engine.stop()
