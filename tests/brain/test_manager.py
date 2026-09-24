from __future__ import annotations

from typing import Any

import pytest

from sentinel.brain.constants import BrainState
from sentinel.brain.intent import Intent
from sentinel.brain.intent_resolver import IntentResolver
from sentinel.brain.manager import BrainManager


class StubIntentResolver(IntentResolver):
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def resolve(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        self.calls.append((input, context))

        return Intent(
            name="stub_intent",
            input=input,
            context=context or {},
        )


def test_manager_creates_default_intent_resolver() -> None:
    manager = BrainManager()

    assert isinstance(
        manager.intent_resolver,
        IntentResolver,
    )


def test_intent_resolver_property() -> None:
    resolver = StubIntentResolver()

    manager = BrainManager(
        intent_resolver=resolver,
    )

    assert manager.intent_resolver is resolver


def test_resolve_intent() -> None:
    resolver = StubIntentResolver()

    manager = BrainManager(
        intent_resolver=resolver,
    )

    context = {
        "source": "test",
    }

    intent = manager.resolve_intent(
        input="open calculator",
        context=context,
    )

    assert isinstance(intent, Intent)
    assert intent.name == "stub_intent"
    assert intent.input == "open calculator"
    assert intent.context == context

    assert resolver.calls == [
        (
            "open calculator",
            context,
        )
    ]


def test_custom_intent_resolver() -> None:
    resolver = StubIntentResolver()

    manager = BrainManager(
        intent_resolver=resolver,
    )

    intent = manager.resolve_intent(
        input="test request",
    )

    assert intent.name == "stub_intent"
    assert intent.input == "test request"


def test_manager_creates_context() -> None:
    manager = BrainManager()

    context = manager.create_context(
        "test-context",
        user="vishnu",
        source="test",
    )

    assert context.id == "test-context"
    assert context.get("user") == "vishnu"
    assert context.get("source") == "test"


def test_manager_exposes_engine() -> None:
    manager = BrainManager()

    assert manager.engine is not None


def test_manager_initial_state() -> None:
    manager = BrainManager()

    assert manager.state() == BrainState.IDLE