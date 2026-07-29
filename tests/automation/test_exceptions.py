import pytest

from sentinel.automation.exceptions import (
    AutomationError,
    InvalidWorkflowError,
    TriggerError,
    WorkflowAlreadyExistsError,
    WorkflowDisabledError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)
from sentinel.core.exceptions import SentinelError


def test_automation_error():
    exc = AutomationError("automation")
    assert str(exc) == "automation"


def test_not_found():
    exc = WorkflowNotFoundError("missing")
    assert isinstance(exc, AutomationError)


def test_already_exists():
    exc = WorkflowAlreadyExistsError("exists")
    assert isinstance(exc, AutomationError)


def test_trigger():
    exc = TriggerError("trigger")
    assert isinstance(exc, AutomationError)


def test_execution():
    exc = WorkflowExecutionError("failed")
    assert isinstance(exc, AutomationError)


def test_invalid():
    exc = InvalidWorkflowError("invalid")
    assert isinstance(exc, AutomationError)


def test_disabled():
    exc = WorkflowDisabledError("disabled")
    assert isinstance(exc, AutomationError)


def test_catch_base():
    with pytest.raises(AutomationError):
        raise WorkflowExecutionError("boom")


def test_catch_sentinel():
    with pytest.raises(SentinelError):
        raise WorkflowExecutionError("boom")