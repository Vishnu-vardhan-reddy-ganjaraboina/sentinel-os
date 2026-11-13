from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import sleep
from typing import Any

import pytest

from sentinel.brain.constants import BrainState, PlanStatus
from sentinel.brain.context import BrainContext
from sentinel.brain.engine import BrainEngine
from sentinel.brain.manager import BrainManager
from sentinel.brain.planner import BrainPlanner


def test_context_returns_deep_isolated_values() -> None:
    context = BrainContext("ctx.deep")
    context.update(profile={"settings": {"theme": "dark"}})

    returned = context.get("profile")
    returned["settings"]["theme"] = "changed"

    snapshot = context.data
    snapshot["profile"]["settings"]["theme"] = "also changed"

    assert context.get("profile") == {
        "settings": {"theme": "dark"}
    }


def test_context_initial_data_is_deep_copied() -> None:
    initial = {"profile": {"name": "Sentinel"}}
    context = BrainContext("ctx.initial", initial)

    initial["profile"]["name"] = "changed"

    assert context.get("profile")["name"] == "Sentinel"


def test_engine_serializes_concurrent_execution() -> None:
    engine = BrainEngine()
    context = BrainContext("ctx.concurrent")

    active = 0
    maximum_active = 0
    counter_lock = Lock()

    def controlled_plan(
        request: Any,
        context: Any,
    ) -> dict[str, Any]:
        nonlocal active, maximum_active

        with counter_lock:
            active += 1
            maximum_active = max(maximum_active, active)

        sleep(0.03)

        with counter_lock:
            active -= 1

        return {
            "request": request,
            "context_id": context.id,
            "context": context.data,
            "context_sources": {},
            "recommendation": None,
            "status": PlanStatus.CREATED,
            "steps": [{"completed": False}],
        }

    engine.planner.create_plan = controlled_plan  # type: ignore[method-assign]

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda number: engine.execute(
                    f"request-{number}",
                    context,
                ),
                range(16),
            )
        )

    assert len(results) == 16
    assert all(result["success"] for result in results)
    assert maximum_active == 1
    assert engine.state == BrainState.COMPLETED


def test_engine_rejects_invalid_context() -> None:
    engine = BrainEngine()

    with pytest.raises(TypeError):
        engine.execute("request", object())  # type: ignore[arg-type]


def test_manager_rejects_invalid_context() -> None:
    manager = BrainManager()

    with pytest.raises(TypeError):
        manager.execute("request", object())  # type: ignore[arg-type]


def test_planner_rejects_invalid_context() -> None:
    planner = BrainPlanner()

    with pytest.raises(TypeError):
        planner.create_plan("request", object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("plan", "expected_error"),
    [
        (None, TypeError),
        ({}, ValueError),
        ({"status": PlanStatus.READY}, ValueError),
        ({"status": PlanStatus.READY, "steps": None}, TypeError),
        ({"status": PlanStatus.READY, "steps": ["invalid"]}, TypeError),
    ],
)
def test_planner_rejects_malformed_plans(
    plan: Any,
    expected_error: type[Exception],
) -> None:
    planner = BrainPlanner()

    with pytest.raises(expected_error):
        planner.mark_completed(plan)


def test_planner_deep_copies_capability_arguments() -> None:
    planner = BrainPlanner()
    arguments = {"payload": {"message": "original"}}

    context = BrainContext("ctx.arguments")
    context.update(
        capability_id="system.echo",
        capability_arguments=arguments,
    )

    plan = planner.create_plan("request", context)
    arguments["payload"]["message"] = "changed"

    assert plan["steps"][0]["arguments"] == {
        "payload": {"message": "original"}
    }


def test_planner_deep_copies_context_snapshot() -> None:
    planner = BrainPlanner()
    context = BrainContext("ctx.snapshot")
    context.update(profile={"name": "Sentinel"})

    plan = planner.create_plan("request", context)
    plan["context"]["profile"]["name"] = "changed"

    assert context.get("profile") == {"name": "Sentinel"}

def test_context_update_is_thread_safe() -> None:
    context = BrainContext("concurrent")

    def update(value: int) -> None:
        context.update(**{f"value_{value}": value})

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(update, range(100)))

    expected = {f"value_{value}": value for value in range(100)}
    assert context.data == expected
