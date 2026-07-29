from sentinel.brain.constants import PlanStatus
from sentinel.brain.context import BrainContext
from sentinel.brain.planner import BrainPlanner


def test_create_plan():
    planner = BrainPlanner()

    context = BrainContext("ctx.1")
    context.update(user="Sentinel")

    plan = planner.create_plan(
        "hello",
        context,
    )

    assert plan["request"] == "hello"
    assert plan["context_id"] == "ctx.1"
    assert plan["status"] == PlanStatus.CREATED
    assert len(plan["steps"]) == 1


def test_mark_ready():
    planner = BrainPlanner()

    plan = planner.create_plan(
        "hello",
        BrainContext("ctx.1"),
    )

    planner.mark_ready(plan)

    assert plan["status"] == PlanStatus.READY


def test_mark_completed():
    planner = BrainPlanner()

    plan = planner.create_plan(
        "hello",
        BrainContext("ctx.1"),
    )

    planner.mark_completed(plan)

    assert plan["status"] == PlanStatus.COMPLETED
    assert plan["steps"][0]["completed"] is True


def test_context_is_copied():
    planner = BrainPlanner()

    context = BrainContext("ctx.1")
    context.update(value=100)

    plan = planner.create_plan(
        "request",
        context,
    )

    context.update(value=200)

    assert plan["context"]["value"] == 100