"""Accessible response formatting and input normalization."""
from __future__ import annotations

import re
import unicodedata


def normalize_transcript(text: str, *, max_chars: int = 8_000) -> str:
    if not isinstance(text, str):
        raise TypeError("transcript must be a string")
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars < 1:
        raise ValueError("max_chars must be a positive integer")
    cleaned = unicodedata.normalize("NFC", text)
    cleaned = "".join(
        ch for ch in cleaned
        if ch in "\n\t" or unicodedata.category(ch)[0] != "C"
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()[:max_chars]


def to_speech_text(text: str) -> str:
    """Remove common Markdown decoration while retaining readable content."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    value = re.sub(r"```.*?```", " code block omitted ", text, flags=re.DOTALL)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"^[#>*-]+\s*", "", value, flags=re.MULTILINE)
    value = re.sub(r"[*_~]{1,3}", "", value)
    return re.sub(r"\s+", " ", value).strip()
