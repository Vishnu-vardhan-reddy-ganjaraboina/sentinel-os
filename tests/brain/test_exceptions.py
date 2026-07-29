import pytest

from sentinel.brain.exceptions import (
    BrainError,
    ContextError,
    EngineError,
    ExecutionError,
    InvalidPlanError,
    PlanningError,
)
from sentinel.core.exceptions import SentinelError


def test_brain_error():
    exc = BrainError("brain")
    assert str(exc) == "brain"


def test_context_error():
    exc = ContextError("context")
    assert isinstance(exc, BrainError)


def test_planning_error():
    exc = PlanningError("planning")
    assert isinstance(exc, BrainError)


def test_execution_error():
    exc = ExecutionError("execution")
    assert isinstance(exc, BrainError)


def test_engine_error():
    exc = EngineError("engine")
    assert isinstance(exc, BrainError)


def test_invalid_plan():
    exc = InvalidPlanError("invalid")
    assert isinstance(exc, BrainError)


def test_catch_brain():
    with pytest.raises(BrainError):
        raise PlanningError("failed")


def test_catch_sentinel():
    with pytest.raises(SentinelError):
        raise EngineError("failed")