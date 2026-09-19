from __future__ import annotations

import pytest

from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.callers import ControlCallerType


def test_control_context_stores_identity() -> None:
    context = ControlContext(
        caller_id="local-cli",
        caller_type="cli",
    )

    assert context.caller_id == "local-cli"
    assert context.caller_type == "cli"
    assert context.metadata == {}


def test_control_context_stores_metadata() -> None:
    context = ControlContext(
        caller_id="local-cli",
        caller_type="cli",
        metadata={
            "session": "test-session",
            "source": "terminal",
        },
    )

    assert context.metadata == {
        "session": "test-session",
        "source": "terminal",
    }


def test_control_context_copies_metadata() -> None:
    metadata = {
        "source": "terminal",
    }

    context = ControlContext(
        caller_id="local-cli",
        caller_type="cli",
        metadata=metadata,
    )

    metadata["source"] = "changed"

    assert context.metadata == {
        "source": "terminal",
    }


def test_control_context_rejects_empty_caller_id() -> None:
    with pytest.raises(ValueError, match="caller_id must not be empty"):
        ControlContext(
            caller_id="",
            caller_type="cli",
        )


def test_control_context_rejects_whitespace_caller_id() -> None:
    with pytest.raises(ValueError, match="caller_id must not be empty"):
        ControlContext(
            caller_id="   ",
            caller_type="cli",
        )


def test_control_context_rejects_empty_caller_type() -> None:
    with pytest.raises(ValueError, match="caller_type must not be empty"):
        ControlContext(
            caller_id="local-cli",
            caller_type="",
        )


def test_control_context_is_immutable() -> None:
    context = ControlContext(
        caller_id="local-cli",
        caller_type="cli",
    )

    with pytest.raises(AttributeError):
        context.caller_id = "other"  # type: ignore[misc]

def test_context_accepts_caller_type_enum() -> None:
    context = ControlContext(
        caller_id="test",
        caller_type=ControlCallerType.AI_AGENT,
    )

    assert context.caller_type is ControlCallerType.AI_AGENT


def test_context_accepts_caller_type_enum() -> None:
    context = ControlContext(
        caller_id="test",
        caller_type=ControlCallerType.AI_AGENT,
    )

    assert context.caller_type is ControlCallerType.AI_AGENT


def test_context_preserves_unknown_caller_type() -> None:
    context = ControlContext(
        caller_id="test",
        caller_type="system_agent",
    )

    assert context.caller_type == "system_agent"