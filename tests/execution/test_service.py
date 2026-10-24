import sys
import threading

from sentinel.execution.constants import TaskStatus
from sentinel.execution.service import ExecutionService
from sentinel.execution.task import Task


def add(a: int, b: int) -> int:
    return a + b


def test_execute_task():
    service = ExecutionService()

    task = Task(callback=add, args=(3, 4))

    result = service.execute_task(task)

    assert result == 7

    context = service.get_context(task.task_id)

    assert context is not None
    assert context.status == TaskStatus.COMPLETED


def test_submit():
    service = ExecutionService()
    completed = threading.Event()

    def add_and_signal(a: int, b: int) -> int:
        result = add(a, b)
        completed.set()
        return result

    try:
        task_id = service.submit(add_and_signal, 10, 20)

        assert completed.wait(timeout=2)

        context = service.get_context(task_id)
        assert context is not None
        assert context.result == 30
        assert context.status == TaskStatus.COMPLETED
    finally:
        service.shutdown()


def test_run_command():
    service = ExecutionService()

    result = service.run_command(
        [sys.executable, "--version"]
    )

    assert result.succeeded


def test_process():
    service = ExecutionService()

    pid = service.start_process(
        [sys.executable, "-c", "print('hello')"]
    )

    assert isinstance(pid, int)

    service.wait_for_process()

    stdout, stderr = service.read_process_output()

    assert "hello" in stdout
    assert stderr == ""


def test_shutdown():
    service = ExecutionService()

    service.shutdown()

    assert service.executor is not None

def test_shutdown_cleans_up_process_manager_when_executor_fails():
    service = ExecutionService()
    process_shutdown_called = False

    def fail_executor_shutdown():
        raise RuntimeError("executor shutdown failed")

    def track_process_shutdown():
        nonlocal process_shutdown_called
        process_shutdown_called = True

    service.executor.shutdown = fail_executor_shutdown
    service.process_manager.shutdown = track_process_shutdown

    import pytest

    with pytest.raises(RuntimeError, match="executor shutdown failed"):
        service.shutdown()

    assert process_shutdown_called


def test_shutdown_cleans_up_executor_when_process_manager_fails():
    service = ExecutionService()
    executor_shutdown_called = False

    def track_executor_shutdown():
        nonlocal executor_shutdown_called
        executor_shutdown_called = True

    def fail_process_shutdown():
        raise RuntimeError("process shutdown failed")

    service.executor.shutdown = track_executor_shutdown
    service.process_manager.shutdown = fail_process_shutdown

    import pytest

    with pytest.raises(RuntimeError, match="process shutdown failed"):
        service.shutdown()

    assert executor_shutdown_called
