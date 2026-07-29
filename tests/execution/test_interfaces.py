from typing import Any

import pytest

from sentinel.execution.interfaces import Executor


class DummyExecutor(Executor):

    def submit(self, callback, *args, **kwargs) -> str:
        return "task-1"

    def execute(self, callback, *args, **kwargs) -> Any:
        return callback(*args, **kwargs)

    def cancel(self, task_id: str) -> bool:
        return True

    def is_running(self, task_id: str) -> bool:
        return False

    def shutdown(self) -> None:
        pass


def test_executor_can_be_instantiated():
    executor = DummyExecutor()

    assert executor.submit(lambda: 1) == "task-1"
    assert executor.execute(lambda x: x + 1, 5) == 6
    assert executor.cancel("task-1") is True
    assert executor.is_running("task-1") is False


def test_executor_is_abstract():
    with pytest.raises(TypeError):
        Executor()