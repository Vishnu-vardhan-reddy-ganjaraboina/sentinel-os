from sentinel.brain.constants import (
    DEFAULT_BRAIN_VERSION,
    DEFAULT_MAX_CONTEXT_ITEMS,
    DEFAULT_MAX_PLANNING_DEPTH,
    BrainState,
    PlanStatus,
)


def test_default_version():
    assert DEFAULT_BRAIN_VERSION == "1.0.0"


def test_default_depth():
    assert DEFAULT_MAX_PLANNING_DEPTH == 5


def test_default_context():
    assert DEFAULT_MAX_CONTEXT_ITEMS == 100


def test_brain_states():
    assert BrainState.IDLE.value == "idle"
    assert BrainState.THINKING.value == "thinking"
    assert BrainState.PLANNING.value == "planning"
    assert BrainState.EXECUTING.value == "executing"
    assert BrainState.COMPLETED.value == "completed"
    assert BrainState.FAILED.value == "failed"


def test_plan_status():
    assert PlanStatus.CREATED.value == "created"
    assert PlanStatus.READY.value == "ready"
    assert PlanStatus.RUNNING.value == "running"
    assert PlanStatus.COMPLETED.value == "completed"
    assert PlanStatus.FAILED.value == "failed"