from sentinel.execution.constants import DEFAULT_PRIORITY
from sentinel.execution.task import Task


def add(a: int, b: int) -> int:
    return a + b


def test_task_creation():
    task = Task(
        callback=add,
        args=(2, 3),
    )

    assert task.name == "add"
    assert task.priority == DEFAULT_PRIORITY
    assert task.execute() == 5


def test_custom_name():
    task = Task(
        callback=add,
        name="addition",
    )

    assert task.name == "addition"


def test_invalid_priority():
    import pytest

    with pytest.raises(ValueError):
        Task(
            callback=add,
            priority=100,
        )


def test_invalid_timeout():
    import pytest

    with pytest.raises(ValueError):
        Task(
            callback=add,
            timeout=0,
        )


def test_invalid_callback():
    import pytest

    with pytest.raises(TypeError):
        Task(callback=123)  # type: ignore


def test_to_dict():
    task = Task(callback=add)

    data = task.to_dict()

    assert data["name"] == "add"
    assert "task_id" in data
    assert "created_at" in data


def test_str():
    task = Task(callback=add)

    assert "Task(" in str(task)