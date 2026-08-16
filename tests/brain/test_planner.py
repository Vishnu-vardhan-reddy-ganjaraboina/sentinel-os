from sentinel.brain.constants import PlanStatus
from sentinel.brain.context import BrainContext
from sentinel.brain.planner import BrainPlanner


def test_create_plan() -> None:
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
    assert plan["steps"][0]["action"] == "execute"
    assert plan["steps"][0]["completed"] is False


def test_create_capability_plan() -> None:
    planner = BrainPlanner()

    context = BrainContext("ctx.1")
    context.update(
        capability_id="system.echo",
        capability_arguments={
            "message": "hello",
        },
    )

    plan = planner.create_plan(
        "hello",
        context,
    )

    step = plan["steps"][0]

    assert step["action"] == "execute"
    assert step["capability_id"] == "system.echo"
    assert step["arguments"] == {
        "message": "hello",
    }


def test_capability_arguments_are_copied() -> None:
    planner = BrainPlanner()

    arguments = {
        "message": "hello",
    }

    context = BrainContext("ctx.1")
    context.update(
        capability_id="system.echo",
        capability_arguments=arguments,
    )

    plan = planner.create_plan(
        "hello",
        context,
    )

    arguments["message"] = "changed"

    assert plan["steps"][0]["arguments"]["message"] == "hello"


def test_missing_capability_id_creates_generic_step() -> None:
    planner = BrainPlanner()

    plan = planner.create_plan(
        "hello",
        BrainContext("ctx.1"),
    )

    step = plan["steps"][0]

    assert step["action"] == "execute"
    assert "capability_id" not in step
    assert "arguments" not in step


def test_mark_ready() -> None:
    planner = BrainPlanner()

    plan = planner.create_plan(
        "hello",
        BrainContext("ctx.1"),
    )

    planner.mark_ready(plan)

    assert plan["status"] == PlanStatus.READY


def test_mark_completed() -> None:
    planner = BrainPlanner()

    plan = planner.create_plan(
        "hello",
        BrainContext("ctx.1"),
    )

    planner.mark_completed(plan)

    assert plan["status"] == PlanStatus.COMPLETED
    assert plan["steps"][0]["completed"] is True


def test_context_is_copied() -> None:
    planner = BrainPlanner()

    context = BrainContext("ctx.1")
    context.update(value=100)

    plan = planner.create_plan(
        "request",
        context,
    )

    context.update(value=200)

    assert plan["context"]["value"] == 100

def test_context_sources_are_recorded() -> None:
    planner = BrainPlanner()

    context = BrainContext("ctx.knowledge")

    context.update(
        memories=[
            {"id": "memory.1"},
            {"id": "memory.2"},
        ],
        knowledge=[
            {"id": "knowledge.1"},
        ],
    )

    plan = planner.create_plan(
        "hello",
        context,
    )

    assert plan["context_sources"] == {
        "memories": 2,
        "knowledge": 1,
    }


def test_context_sources_are_empty_when_not_provided() -> None:
    planner = BrainPlanner()

    context = BrainContext("ctx.empty")

    plan = planner.create_plan(
        "hello",
        context,
    )

    assert plan["context_sources"] == {
        "memories": 0,
        "knowledge": 0,
    }


def test_invalid_context_sources_are_treated_as_empty() -> None:
    planner = BrainPlanner()

    context = BrainContext("ctx.invalid")

    context.update(
        memories="invalid",
        knowledge=None,
    )

    plan = planner.create_plan(
        "hello",
        context,
    )

    assert plan["context_sources"] == {
        "memories": 0,
        "knowledge": 0,
    }