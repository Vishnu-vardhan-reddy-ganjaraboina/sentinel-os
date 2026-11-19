import pytest

from sentinel.voice import normalize_transcript, to_speech_text


def test_normalize_transcript_unicode_and_control_characters():
    assert normalize_transcript("  cafe\u0301\x00  hello  ") == "café hello"


def test_transcript_is_bounded():
    assert normalize_transcript("abcdef", max_chars=3) == "abc"


def test_markdown_is_simplified_for_speech():
    assert (
        to_speech_text("# Hello **world** [docs](https://example.com)")
        == "Hello world docs"
    )


def test_transcript_type_and_limit_validation():
    with pytest.raises(TypeError):
        normalize_transcript(3)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        normalize_transcript("x", max_chars=0)
