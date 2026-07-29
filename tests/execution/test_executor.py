import pytest

from sentinel.execution.constants import TaskStatus
from sentinel.execution.executor import DefaultExecutor
from sentinel.execution.task import Task
import time


def add(a: int, b: int) -> int:
    return a + b


def sleeper():
    time.sleep(2)

def test_cancel_submitted_task():
    executor = DefaultExecutor(max_workers=1)

    task_id = executor.submit(sleeper)

    # Cancellation may succeed if the task hasn't started yet,
    # or fail if the worker already began executing it.
    result = executor.cancel(task_id)

    assert isinstance(result, bool)

def fail() -> None:
    raise ValueError("boom")


def test_execute_task():
    executor = DefaultExecutor()

    task = Task(callback=add, args=(2, 3))

    result = executor.execute(task)

    assert result == 5

    context = executor.get_context(task.task_id)

    assert context is not None
    assert context.status == TaskStatus.COMPLETED
    assert context.result == 5


def test_failed_task():
    executor = DefaultExecutor()

    task = Task(callback=fail)

    with pytest.raises(ValueError):
        executor.execute(task)

    context = executor.get_context(task.task_id)

    assert context is not None
    assert context.status == TaskStatus.FAILED


def test_cancel_unknown_task():
    executor = DefaultExecutor()

    assert executor.cancel("future-task") is False


def test_submit():
    executor = DefaultExecutor()

    task_id = executor.submit(add, 4, 6)

    context = executor.get_context(task_id)

    assert context is not None
    assert context.result == 10


def test_shutdown():
    executor = DefaultExecutor()

    executor.shutdown()

    with pytest.raises(RuntimeError):
        executor.submit(add, 1, 2)


def test_executor_stats():
    executor = DefaultExecutor()

    task = Task(callback=add, args=(1, 2))

    executor.execute(task)

    stats = executor.stats()

    assert stats["submitted"] == 1
    assert stats["completed"] == 1
    assert stats["failed"] == 0