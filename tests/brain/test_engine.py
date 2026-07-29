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