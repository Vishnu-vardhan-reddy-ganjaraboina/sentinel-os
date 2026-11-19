"""Provider-neutral voice and accessibility contracts."""

from sentinel.voice.accessibility import normalize_transcript, to_speech_text
from sentinel.voice.interfaces import (
    SpeechOutput,
    SpeechRecognizer,
    SpeechResult,
    SpeechSynthesizer,
)
from sentinel.voice.providers import Pyttsx3Output, Pyttsx3Synthesizer, VoskRecognizer

__all__ = [
    "SpeechOutput",
    "SpeechRecognizer",
    "SpeechResult",
    "SpeechSynthesizer",
    "VoskRecognizer",
    "Pyttsx3Synthesizer",
    "Pyttsx3Output",
    "normalize_transcript",
    "to_speech_text",
]
