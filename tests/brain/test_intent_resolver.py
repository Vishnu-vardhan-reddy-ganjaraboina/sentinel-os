from __future__ import annotations

import pytest

from sentinel.brain.intent import Intent
from sentinel.brain.intent_resolver import (
    DefaultIntentResolver,
    IntentResolver,
)


def test_intent_resolver_is_abstract() -> None:
    assert IntentResolver.__abstractmethods__


def test_resolve_creates_intent() -> None:
    resolver = DefaultIntentResolver()

    intent = resolver.resolve("Open Chrome")

    assert isinstance(intent, Intent)
    assert intent.name == "user_request"
    assert intent.input == "Open Chrome"
    assert intent.capability_id is None
    assert intent.arguments == {}
    assert intent.context == {}


def test_resolve_preserves_context() -> None:
    resolver = DefaultIntentResolver()

    intent = resolver.resolve(
        "Open Chrome",
        context={
            "source": "user",
            "application": "chrome",
        },
    )

    assert intent.context == {
        "source": "user",
        "application": "chrome",
    }


def test_resolve_isolates_context() -> None:
    resolver = DefaultIntentResolver()

    context = {
        "source": "user",
    }

    intent = resolver.resolve(
        "Open Chrome",
        context=context,
    )

    context["source"] = "system"

    assert intent.context["source"] == "user"


def test_resolve_rejects_non_string_input() -> None:
    resolver = DefaultIntentResolver()

    with pytest.raises(TypeError, match="input must be a string"):
        resolver.resolve(123)  # type: ignore[arg-type]


def test_resolve_rejects_empty_input() -> None:
    resolver = DefaultIntentResolver()

    with pytest.raises(ValueError, match="input must not be empty"):
        resolver.resolve("   ")


def test_resolve_rejects_invalid_context() -> None:
    resolver = DefaultIntentResolver()

    with pytest.raises(
        TypeError,
        match="context must be a dictionary",
    ):
        resolver.resolve(
            "Open Chrome",
            context=[],  # type: ignore[arg-type]
        )
    