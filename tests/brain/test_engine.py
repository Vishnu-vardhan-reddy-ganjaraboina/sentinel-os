import pytest

from sentinel.brain.constants import (
    BrainState,
    PlanStatus,
)
from sentinel.brain.context import BrainContext
from sentinel.brain.engine import BrainEngine


def test_initial_state():
    engine = BrainEngine()

    assert engine.state == BrainState.IDLE


def test_execute():
    engine = BrainEngine()

    context = BrainContext("ctx.1")
    context.update(user="Sentinel")

    result = engine.execute(
        "hello",
        context,
    )

    assert result["success"] is True
    assert result["request"] == "hello"
    assert result["plan"]["status"] == PlanStatus.COMPLETED
    assert result["context"]["id"] == "ctx.1"

    assert engine.state == BrainState.COMPLETED


def test_planner_property():
    engine = BrainEngine()

    assert engine.planner is not None


def test_context_data():
    engine = BrainEngine()

    context = BrainContext("ctx.1")
    context.update(user="AI")

    result = engine.execute(
        "request",
        context,
    )

    assert result["context"]["data"]["user"] == "AI"


def test_multiple_executions():
    engine = BrainEngine()

    context = BrainContext("ctx.1")

    first = engine.execute("one", context)
    second = engine.execute("two", context)

    assert first["request"] == "one"
    assert second["request"] == "two"
    assert engine.state == BrainState.COMPLETED

def test_capability_plan() -> None:
    engine = BrainEngine()

    context = BrainContext("ctx.1")
    context.update(
        capability_id="system.echo",
        capability_arguments={
            "message": "hello",
        },
    )

    result = engine.execute(
        "hello",
        context,
    )

    step = result["plan"]["steps"][0]

    assert step["action"] == "execute"
    assert step["capability_id"] == "system.echo"
    assert step["arguments"] == {
        "message": "hello",
    }
    assert step["completed"] is True

def test_execute_preserves_context_sources_in_plan() -> None:
    engine = BrainEngine()

    context = BrainContext("ctx.sources")

    context.update(
        memories=[
            {"id": "memory.1"},
        ],
        knowledge=[
            {"id": "knowledge.1"},
            {"id": "knowledge.2"},
        ],
    )

    result = engine.execute(
        "hello",
        context,
    )

    assert result["plan"]["context_sources"] == {
        "memories": 1,
        "knowledge": 2,
        "capabilities": 0,
    }

def test_engine_returns_to_failed_state_when_planner_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = BrainEngine()

    def fail_create_plan(request, context):
        raise RuntimeError("planning failed")

    monkeypatch.setattr(
        engine.planner,
        "create_plan",
        fail_create_plan,
    )

    context = BrainContext("context-1")

    with pytest.raises(RuntimeError, match="planning failed"):
        engine.execute("request", context)

    assert engine.state == BrainState.FAILED

def test_engine_state_is_failed_when_plan_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = BrainEngine()

    def fail_create_plan(request, context):
        raise ValueError("planner failure")

    monkeypatch.setattr(
        engine.planner,
        "create_plan",
        fail_create_plan,
    )

    with pytest.raises(ValueError, match="planner failure"):
        engine.execute(
            "hello",
            BrainContext("ctx.1"),
        )

    assert engine.state == BrainState.FAILED

def test_engine_completes_successfully_after_execution() -> None:
    engine = BrainEngine()

    result = engine.execute(
        "hello",
        BrainContext("ctx.1"),
    )

    assert result["success"] is True
    assert engine.state == BrainState.COMPLETED