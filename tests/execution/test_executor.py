import threading
import time

import pytest

from sentinel.execution.constants import TaskStatus
from sentinel.execution.executor import DefaultExecutor
from sentinel.execution.task import Task


def add(a: int, b: int) -> int:
    return a + b


def sleeper() -> None:
    time.sleep(2)


def fail() -> None:
    raise ValueError("boom")


def test_cancel_submitted_task() -> None:
    executor = DefaultExecutor(max_workers=1)

    task_id = executor.submit(sleeper)

    result = executor.cancel(task_id)

    assert isinstance(result, bool)

    executor.shutdown()


def test_execute_task() -> None:
    executor = DefaultExecutor()

    task = Task(callback=add, args=(2, 3))

    result = executor.execute(task)

    assert result == 5

    context = executor.get_context(task.task_id)

    assert context is not None
    assert context.status == TaskStatus.COMPLETED
    assert context.result == 5

    executor.shutdown()


def test_failed_task() -> None:
    executor = DefaultExecutor()

    task = Task(callback=fail)

    with pytest.raises(ValueError):
        executor.execute(task)

    context = executor.get_context(task.task_id)

    assert context is not None
    assert context.status == TaskStatus.FAILED

    executor.shutdown()


def test_cancel_unknown_task() -> None:
    executor = DefaultExecutor()

    assert executor.cancel("future-task") is False

    executor.shutdown()


def test_submit() -> None:
    executor = DefaultExecutor()

    task_id = executor.submit(add, 4, 6)

    context = executor.get_context(task_id)

    assert context is not None
    assert context.result == 10
    assert context.status == TaskStatus.COMPLETED

    executor.shutdown()


def test_shutdown() -> None:
    executor = DefaultExecutor()

    executor.shutdown()

    with pytest.raises(RuntimeError):
        executor.submit(add, 1, 2)


def test_executor_stats() -> None:
    executor = DefaultExecutor()

    task = Task(callback=add, args=(1, 2))

    executor.execute(task)

    stats = executor.stats()

    assert stats["submitted"] == 1
    assert stats["completed"] == 1
    assert stats["failed"] == 0
    assert stats["cancelled"] == 0
    assert stats["running"] == 0

    executor.shutdown()


def test_executor_rejects_invalid_worker_count() -> None:
    with pytest.raises((ValueError, TypeError)):
        DefaultExecutor(max_workers=0)


def test_submit_after_shutdown_is_rejected() -> None:
    executor = DefaultExecutor()
    executor.shutdown()

    with pytest.raises(RuntimeError):
        executor.submit(add, 1, 2)


def test_execute_after_shutdown_is_rejected() -> None:
    executor = DefaultExecutor()
    executor.shutdown()

    task = Task(callback=add, args=(1, 2))

    with pytest.raises(RuntimeError):
        executor.execute(task)


def test_cancel_running_task_returns_false() -> None:
    executor = DefaultExecutor(max_workers=1)

    started = threading.Event()
    release = threading.Event()

    def blocking_task() -> None:
        started.set()
        release.wait(timeout=5)

    task_id = executor.submit(blocking_task)

    assert started.wait(timeout=1)

    # ThreadPoolExecutor cannot cancel a task that has already started.
    assert executor.cancel(task_id) is False

    release.set()
    executor.shutdown()


def test_multiple_tasks_can_execute_concurrently() -> None:
    executor = DefaultExecutor(max_workers=2)

    started_a = threading.Event()
    started_b = threading.Event()
    release = threading.Event()

    def worker(started: threading.Event) -> None:
        started.set()
        release.wait(timeout=5)

    executor.submit(worker, started_a)
    executor.submit(worker, started_b)

    assert started_a.wait(timeout=1)
    assert started_b.wait(timeout=1)

    release.set()
    executor.shutdown()