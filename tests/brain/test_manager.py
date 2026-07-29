from sentinel.brain.constants import BrainState
from sentinel.brain.context import BrainContext
from sentinel.brain.manager import BrainManager


def test_engine_property():
    manager = BrainManager()

    assert manager.engine is not None


def test_create_context():
    manager = BrainManager()

    context = manager.create_context(
        "ctx.1",
        user="Sentinel",
    )

    assert isinstance(context, BrainContext)
    assert context.id == "ctx.1"
    assert context.get("user") == "Sentinel"


def test_execute():
    manager = BrainManager()

    context = manager.create_context(
        "ctx.1",
        user="Sentinel",
    )

    result = manager.execute(
        "hello",
        context,
    )

    assert result["success"] is True
    assert result["request"] == "hello"


def test_state():
    manager = BrainManager()

    assert manager.state() == BrainState.IDLE

    context = manager.create_context("ctx.1")

    manager.execute(
        "hello",
        context,
    )

    assert manager.state() == BrainState.COMPLETED