from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from sentinel.brain.context import BrainContext
from sentinel.brain.engine import BrainEngine
from sentinel.brain.planner import BrainPlanner


def test_context_update_is_thread_safe() -> None:
    context = BrainContext("concurrent")

    def update(value: int) -> None:
        context.update(value=value)

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(update, range(100)))

    assert context.get("value") in range(100)


def test_context_returns_deep_isolated_data() -> None:
    context = BrainContext(
        "isolation",
        data={
            "nested": {
                "values": [1, 2, 3],
            }
        },
    )

    snapshot = context.data
    snapshot["nested"]["values"].append(4)

    assert context.get("nested") == {
        "values": [1, 2, 3],
    }


def test_context_get_returns_deep_isolated_value() -> None:
    context = BrainContext(
        "isolation",
        data={
            "nested": {
                "values": [1, 2, 3],
            }
        },
    )

    value = context.get("nested")
    value["values"].append(4)

    assert context.get("nested") == {
        "values": [1, 2, 3],
    }


def test_planner_deep_copies_capability_arguments() -> None:
    planner = BrainPlanner()

    arguments = {
        "payload": {
            "items": [1, 2, 3],
        }
    }

    context = BrainContext("planner")
    context.update(
        capability_id="system.echo",
        capability_arguments=arguments,
    )

    plan = planner.create_plan("echo", context)

    arguments["payload"]["items"].append(4)

    assert plan["steps"][0]["arguments"] == {
        "payload": {
            "items": [1, 2, 3],
        }
    }


def test_planner_deep_copies_context() -> None:
    planner = BrainPlanner()

    context = BrainContext(
        "planner",
        data={
            "nested": {
                "values": [1, 2, 3],
            }
        },
    )

    plan = planner.create_plan("request", context)

    context.update(
        nested={
            "values": [9],
        }
    )

    assert plan["context"] == {
        "nested": {
            "values": [1, 2, 3],
        }
    }


def test_engine_concurrent_execution_keeps_valid_final_state() -> None:
    engine = BrainEngine()

    def execute(index: int) -> dict:
        return engine.execute(
            f"request-{index}",
            BrainContext(f"context-{index}"),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(execute, range(32)))

    assert len(results) == 32
    assert all(result["success"] is True for result in results)
    assert engine.state.name == "COMPLETED"


def test_engine_rejects_invalid_context() -> None:
    engine = BrainEngine()

    with pytest.raises(TypeError, match="context must be a Context"):
        engine.execute(
            "request",
            None,  # type: ignore[arg-type]
        )


def test_planner_rejects_invalid_plan() -> None:
    planner = BrainPlanner()

    with pytest.raises(TypeError):
        planner.mark_ready(None)  # type: ignore[arg-type]


def test_planner_rejects_plan_without_status() -> None:
    planner = BrainPlanner()

    with pytest.raises(ValueError, match="status"):
        planner.mark_ready({"steps": []})


def test_planner_rejects_plan_without_steps() -> None:
    planner = BrainPlanner()

    with pytest.raises(ValueError, match="steps"):
        planner.mark_ready({"status": "created"})
