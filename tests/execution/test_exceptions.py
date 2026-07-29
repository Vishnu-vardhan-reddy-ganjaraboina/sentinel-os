import pytest

from sentinel.core.exceptions import SentinelError
from sentinel.execution.exceptions import (
    CommandError,
    ExecutionError,
    ExecutionTimeoutError,
    ProcessError,
    TaskCancelledError,
    TaskError,
)


def test_execution_error_inheritance():
    exc = ExecutionError("execution failed")

    assert isinstance(exc, SentinelError)
    assert str(exc) == "execution failed"


def test_task_error():
    exc = TaskError("task failed")

    assert isinstance(exc, ExecutionError)
    assert str(exc) == "task failed"


def test_command_error():
    exc = CommandError("command failed")

    assert isinstance(exc, ExecutionError)
    assert str(exc) == "command failed"


def test_process_error():
    exc = ProcessError("process failed")

    assert isinstance(exc, ExecutionError)
    assert str(exc) == "process failed"


def test_timeout_error():
    exc = ExecutionTimeoutError("timeout")

    assert isinstance(exc, ExecutionError)
    assert str(exc) == "timeout"


def test_task_cancelled_error():
    exc = TaskCancelledError("cancelled")

    assert isinstance(exc, ExecutionError)
    assert str(exc) == "cancelled"


def test_catch_execution_error():
    with pytest.raises(ExecutionError):
        raise CommandError("boom")


def test_catch_sentinel_error():
    with pytest.raises(SentinelError):
        raise TaskError("boom")