import sys

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

    task_id = service.submit(add, 10, 20)

    context = service.get_context(task_id)

    assert context is not None
    assert context.result == 30


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