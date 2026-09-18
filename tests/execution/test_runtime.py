"""
Tests for the Sentinel Execution runtime service.
"""

from __future__ import annotations

import sys
import time


from sentinel.execution.command import CommandResult
from sentinel.execution.context import ExecutionContext
from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.execution.service import ExecutionService
from sentinel.execution.task import Task
from sentinel.kernel.service import Service


def add(a: int, b: int) -> int:
    return a + b


def test_runtime_name() -> None:
    runtime = ExecutionRuntimeService()

    assert runtime.name == "execution"


def test_runtime_dependencies() -> None:
    runtime = ExecutionRuntimeService()

    assert runtime.dependencies == ()


def test_runtime_default_service() -> None:
    runtime = ExecutionRuntimeService()

    assert isinstance(
        runtime.execution,
        ExecutionService,
    )


def test_runtime_is_service() -> None:
    runtime = ExecutionRuntimeService()

    assert isinstance(runtime, Service)


def test_runtime_health_before_initialize() -> None:
    runtime = ExecutionRuntimeService()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_initialize() -> None:
    runtime = ExecutionRuntimeService()

    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_initialize_is_idempotent() -> None:
    runtime = ExecutionRuntimeService()

    runtime.initialize()
    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_shutdown() -> None:
    runtime = ExecutionRuntimeService()

    runtime.initialize()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_shutdown_is_idempotent() -> None:
    runtime = ExecutionRuntimeService()

    runtime.initialize()
    runtime.shutdown()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_initialize_after_shutdown_restarts() -> None:
    runtime = ExecutionRuntimeService()

    first_execution = runtime.execution

    runtime.initialize()
    runtime.shutdown()

    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }
    assert runtime.execution is not first_execution


def test_runtime_exposes_underlying_service_components() -> None:
    runtime = ExecutionRuntimeService()

    assert runtime.execution.executor is not None
    assert runtime.execution.command_executor is not None
    assert runtime.execution.process_manager is not None


def test_runtime_delegates_execute_task() -> None:
    runtime = ExecutionRuntimeService()

    task = Task(
        callback=add,
        args=(2, 3),
    )

    result = runtime.execute_task(task)

    assert result == 5


def test_runtime_delegates_submit() -> None:
    runtime = ExecutionRuntimeService()

    task_id = runtime.submit(
        add,
        4,
        6,
    )

    context = runtime.get_context(task_id)

    assert isinstance(context, ExecutionContext)
    assert context.result == 10


def test_runtime_delegates_cancel() -> None:
    runtime = ExecutionRuntimeService()

    result = runtime.cancel("unknown-task")

    assert result is False


def test_runtime_delegates_get_context() -> None:
    runtime = ExecutionRuntimeService()

    task = Task(
        callback=add,
        args=(5, 7),
    )

    runtime.execute_task(task)

    context = runtime.get_context(task.task_id)

    assert isinstance(context, ExecutionContext)
    assert context.result == 12


def test_runtime_delegates_run_command() -> None:
    runtime = ExecutionRuntimeService()

    result = runtime.run_command(
        [
            sys.executable,
            "--version",
        ]
    )

    assert isinstance(result, CommandResult)
    assert result.succeeded
    assert (
        "Python" in result.stdout
        or "Python" in result.stderr
    )


def test_runtime_delegates_run_command_checked() -> None:
    runtime = ExecutionRuntimeService()

    result = runtime.run_command_checked(
        [
            sys.executable,
            "--version",
        ]
    )

    assert isinstance(result, CommandResult)
    assert result.succeeded


def test_runtime_delegates_start_process() -> None:
    runtime = ExecutionRuntimeService()

    pid = runtime.start_process(
        [
            sys.executable,
            "-c",
            "print('hello')",
        ]
    )

    assert isinstance(pid, int)


def test_runtime_delegates_wait_for_process() -> None:
    runtime = ExecutionRuntimeService()

    runtime.start_process(
        [
            sys.executable,
            "-c",
            "print('hello')",
        ]
    )

    exit_code = runtime.wait_for_process()

    assert exit_code == 0


def test_runtime_delegates_read_process_output() -> None:
    runtime = ExecutionRuntimeService()

    runtime.start_process(
        [
            sys.executable,
            "-c",
            "print('hello')",
        ]
    )

    stdout, stderr = runtime.read_process_output()

    assert "hello" in stdout
    assert stderr == ""


def test_runtime_delegates_terminate_process() -> None:
    runtime = ExecutionRuntimeService()

    runtime.start_process(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(5)",
        ]
    )

    runtime.terminate_process()

    # Allow the subprocess handle to settle before the runtime object
    # is discarded.
    time.sleep(0.05)