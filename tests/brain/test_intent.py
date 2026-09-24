from __future__ import annotations

import pytest

from sentinel.brain.intent import Intent


def test_intent_creates_with_required_fields() -> None:
    intent = Intent(
        name="open_application",
        input="Open Chrome",
    )

    assert intent.name == "open_application"
    assert intent.input == "Open Chrome"
    assert intent.capability_id is None
    assert dict(intent.arguments) == {}
    assert dict(intent.context) == {}


def test_intent_creates_with_capability_and_arguments() -> None:
    intent = Intent(
        name="open_application",
        input="Open Chrome",
        capability_id="system.open_application",
        arguments={
            "application": "chrome",
        },
        context={
            "source": "user",
        },
    )

    assert intent.capability_id == "system.open_application"
    assert intent.arguments["application"] == "chrome"
    assert intent.context["source"] == "user"


def test_intent_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        Intent(
            name="",
            input="Open Chrome",
        )


def test_intent_rejects_non_string_name() -> None:
    with pytest.raises(TypeError, match="name must be a string"):
        Intent(
            name=123,  # type: ignore[arg-type]
            input="Open Chrome",
        )


def test_intent_rejects_non_string_input() -> None:
    with pytest.raises(TypeError, match="input must be a string"):
        Intent(
            name="open_application",
            input=123,  # type: ignore[arg-type]
        )


def test_intent_rejects_empty_capability_id() -> None:
    with pytest.raises(
        ValueError,
        match="capability_id must not be empty",
    ):
        Intent(
            name="open_application",
            input="Open Chrome",
            capability_id="",
        )


def test_intent_to_dict() -> None:
    intent = Intent(
        name="open_application",
        input="Open Chrome",
        capability_id="system.open_application",
        arguments={
            "application": "chrome",
        },
        context={
            "source": "user",
        },
    )

    assert intent.to_dict() == {
        "name": "open_application",
        "input": "Open Chrome",
        "capability_id": "system.open_application",
        "arguments": {
            "application": "chrome",
        },
        "context": {
            "source": "user",
        },
    }