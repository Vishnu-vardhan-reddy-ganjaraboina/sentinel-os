from sentinel.brain.constants import BrainState
from sentinel.brain.context import BrainContext
from sentinel.brain.service import BrainService


def test_manager_property():
    service = BrainService()

    assert service.manager is not None


def test_create_context():
    service = BrainService()

    context = service.create_context(
        "ctx.1",
        user="Sentinel",
    )

    assert isinstance(context, BrainContext)
    assert context.id == "ctx.1"
    assert context.get("user") == "Sentinel"


def test_execute():
    service = BrainService()

    context = service.create_context(
        "ctx.1",
        user="Sentinel",
    )

    result = service.execute(
        "hello",
        context,
    )

    assert result["success"] is True
    assert result["request"] == "hello"
    assert result["plan"]["context_id"] == "ctx.1"


def test_state():
    service = BrainService()

    assert service.state() == BrainState.IDLE

    context = service.create_context("ctx.1")

    service.execute(
        "hello",
        context,
    )

    assert service.state() == BrainState.COMPLETED