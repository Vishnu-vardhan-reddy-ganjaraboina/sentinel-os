"""
Unit tests for the Scheduler service.
"""

from __future__ import annotations

import time

import pytest

from sentinel.infrastructure.scheduler import Scheduler
from sentinel.kernel.exceptions import (
    DuplicateTaskError,
    TaskNotFoundError,
)

# ----------------------------------------------------------------------
# Initialization
# ----------------------------------------------------------------------


def test_scheduler_initializes() -> None:
    scheduler = Scheduler()

    scheduler.initialize()

    assert scheduler._thread is not None
    assert scheduler._thread.is_alive()

    scheduler.shutdown()


# ----------------------------------------------------------------------
# Add Task
# ----------------------------------------------------------------------


def test_add_task() -> None:
    scheduler = Scheduler()

    scheduler.add_task(
        "cleanup",
        10,
        lambda: None,
    )

    task = scheduler.get_task("cleanup")

    assert task.name == "cleanup"
    assert task.interval == 10
    assert task.enabled is True


def test_duplicate_task() -> None:
    scheduler = Scheduler()

    scheduler.add_task(
        "cleanup",
        10,
        lambda: None,
    )

    with pytest.raises(DuplicateTaskError):
        scheduler.add_task(
            "cleanup",
            5,
            lambda: None,
        )


def test_invalid_interval() -> None:
    scheduler = Scheduler()

    with pytest.raises(ValueError):
        scheduler.add_task(
            "cleanup",
            0,
            lambda: None,
        )

    with pytest.raises(ValueError):
        scheduler.add_task(
            "cleanup",
            -1,
            lambda: None,
        )


# ----------------------------------------------------------------------
# Remove Task
# ----------------------------------------------------------------------


def test_remove_task() -> None:
    scheduler = Scheduler()

    scheduler.add_task(
        "cleanup",
        10,
        lambda: None,
    )

    scheduler.remove_task("cleanup")

    with pytest.raises(TaskNotFoundError):
        scheduler.get_task("cleanup")


def test_remove_unknown_task() -> None:
    scheduler = Scheduler()

    with pytest.raises(TaskNotFoundError):
        scheduler.remove_task("unknown")


# ----------------------------------------------------------------------
# Enable / Disable
# ----------------------------------------------------------------------


def test_disable_task() -> None:
    scheduler = Scheduler()

    scheduler.add_task(
        "cleanup",
        10,
        lambda: None,
    )

    scheduler.disable_task("cleanup")

    assert scheduler.get_task("cleanup").enabled is False


def test_enable_task() -> None:
    scheduler = Scheduler()

    scheduler.add_task(
        "cleanup",
        10,
        lambda: None,
    )

    scheduler.disable_task("cleanup")
    scheduler.enable_task("cleanup")

    assert scheduler.get_task("cleanup").enabled is True


# ----------------------------------------------------------------------
# Snapshot
# ----------------------------------------------------------------------


def test_get_tasks() -> None:
    scheduler = Scheduler()

    scheduler.add_task(
        "one",
        1,
        lambda: None,
    )

    scheduler.add_task(
        "two",
        2,
        lambda: None,
    )

    tasks = scheduler.get_tasks()

    assert len(tasks) == 2
    assert "one" in tasks
    assert "two" in tasks


# ----------------------------------------------------------------------
# Scheduler Execution
# ----------------------------------------------------------------------


def test_task_execution() -> None:
    scheduler = Scheduler()

    executed = []

    def callback() -> None:
        executed.append(True)

    scheduler.add_task(
        "job",
        0.2,
        callback,
    )

    scheduler.initialize()

    time.sleep(0.8)

    scheduler.shutdown()

    assert len(executed) >= 1


# ----------------------------------------------------------------------
# Exception Isolation
# ----------------------------------------------------------------------


def test_failed_task_does_not_stop_scheduler() -> None:
    scheduler = Scheduler()

    executed = []

    def bad_task() -> None:
        raise RuntimeError("Failure")

    def good_task() -> None:
        executed.append(True)

    scheduler.add_task(
        "bad",
        0.2,
        bad_task,
    )

    scheduler.add_task(
        "good",
        0.2,
        good_task,
    )

    scheduler.initialize()

    time.sleep(0.8)

    scheduler.shutdown()

    assert len(executed) >= 1


# ----------------------------------------------------------------------
# Shutdown
# ----------------------------------------------------------------------


def test_shutdown_stops_thread() -> None:
    scheduler = Scheduler()

    scheduler.initialize()

    scheduler.shutdown()

    assert scheduler._thread is None


# ----------------------------------------------------------------------
# Unknown Task
# ----------------------------------------------------------------------


def test_get_unknown_task() -> None:
    scheduler = Scheduler()

    with pytest.raises(TaskNotFoundError):
        scheduler.get_task("missing")