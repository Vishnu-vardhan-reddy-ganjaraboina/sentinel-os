from sentinel.execution.constants import TaskStatus
from sentinel.execution.context import ExecutionContext


def test_initial_state():
    context = ExecutionContext(task_id="task-1")

    assert context.task_id == "task-1"
    assert context.status == TaskStatus.PENDING
    assert context.duration is None
    assert context.is_finished is False


def test_mark_running():
    context = ExecutionContext(task_id="task-1")

    context.mark_running()

    assert context.status == TaskStatus.RUNNING
    assert context.started_at is not None


def test_mark_completed():
    context = ExecutionContext(task_id="task-1")

    context.mark_running()
    context.mark_completed(result=123)

    assert context.status == TaskStatus.COMPLETED
    assert context.result == 123
    assert context.finished_at is not None
    assert context.duration is not None
    assert context.is_finished is True


def test_mark_failed():
    context = ExecutionContext(task_id="task-1")

    error = RuntimeError("boom")

    context.mark_running()
    context.mark_failed(error)

    assert context.status == TaskStatus.FAILED
    assert context.error is error
    assert context.is_finished is True


def test_mark_cancelled():
    context = ExecutionContext(task_id="task-1")

    context.mark_cancelled()

    assert context.status == TaskStatus.CANCELLED
    assert context.finished_at is not None
    assert context.is_finished is True