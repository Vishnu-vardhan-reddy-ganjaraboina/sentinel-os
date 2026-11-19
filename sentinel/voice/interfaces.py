"""Provider-neutral speech interfaces for accessible assistant I/O."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpeechResult:
    text: str
    language: str | None = None
    confidence: float | None = None

class SpeechRecognizer(ABC):
    @abstractmethod
    def transcribe(self, audio: bytes, *, language: str | None = None) -> SpeechResult:
        """Convert encoded audio bytes to text."""

class SpeechSynthesizer(ABC):
    @abstractmethod
    def synthesize(self, text: str, *, language: str | None = None) -> bytes:
        """Convert text to encoded audio bytes."""

class SpeechOutput(ABC):
    @abstractmethod
    def speak(self, text: str, *, language: str | None = None) -> None:
        """Deliver speech to an output device."""
