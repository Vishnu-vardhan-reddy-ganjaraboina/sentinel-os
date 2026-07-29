from sentinel.execution.constants import (
    CAPTURE_OUTPUT,
    DEFAULT_MAX_WORKERS,
    DEFAULT_PRIORITY,
    DEFAULT_SHELL,
    DEFAULT_TERMINATE_TIMEOUT,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_PRIORITY,
    MIN_PRIORITY,
    TEXT_MODE,
    TaskStatus,
)


def test_default_timeout():
    assert DEFAULT_TIMEOUT_SECONDS == 300


def test_default_workers():
    assert DEFAULT_MAX_WORKERS == 4


def test_default_priority():
    assert DEFAULT_PRIORITY == 5


def test_priority_limits():
    assert MIN_PRIORITY == 1
    assert MAX_PRIORITY == 10


def test_shell_default():
    assert DEFAULT_SHELL is False


def test_capture_output():
    assert CAPTURE_OUTPUT is True


def test_text_mode():
    assert TEXT_MODE is True


def test_terminate_timeout():
    assert DEFAULT_TERMINATE_TIMEOUT == 5


def test_task_status_values():
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.CANCELLED.value == "cancelled"


def test_status_is_enum():
    assert isinstance(TaskStatus.PENDING, TaskStatus)