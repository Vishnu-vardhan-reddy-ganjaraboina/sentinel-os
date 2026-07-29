from datetime import timedelta

from sentinel.memory.constants import (
    MemoryStatus,
    MemoryType,
)
from sentinel.memory.entry import BaseMemoryEntry


def test_properties():
    entry = BaseMemoryEntry(
        memory_id="memory.one",
        content="Hello",
    )

    assert entry.id == "memory.one"
    assert entry.content == "Hello"
    assert entry.importance == 1
    assert entry.memory_type == MemoryType.WORKING
    assert entry.status == MemoryStatus.ACTIVE


def test_archive():
    entry = BaseMemoryEntry(
        "memory.one",
        "Hello",
    )

    entry.archive()

    assert entry.status == MemoryStatus.ARCHIVED


def test_delete():
    entry = BaseMemoryEntry(
        "memory.one",
        "Hello",
    )

    entry.delete()

    assert entry.status == MemoryStatus.DELETED


def test_expired():
    entry = BaseMemoryEntry(
        "memory.one",
        "Hello",
        ttl=timedelta(milliseconds=1),
    )

    import time

    time.sleep(0.01)

    assert entry.expired is True


def test_not_expired():
    entry = BaseMemoryEntry(
        "memory.one",
        "Hello",
    )

    assert entry.expired is False


def test_to_dict():
    entry = BaseMemoryEntry(
        "memory.one",
        {"value": 100},
    )

    data = entry.to_dict()

    assert data["id"] == "memory.one"
    assert data["importance"] == 1
    assert data["memory_type"] == "working"


def test_empty_id():
    import pytest

    with pytest.raises(ValueError):
        BaseMemoryEntry("", "hello")