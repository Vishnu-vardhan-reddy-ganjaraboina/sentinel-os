import pytest

from sentinel.core.exceptions import SentinelError
from sentinel.memory.exceptions import (
    InvalidMemoryError,
    MemoryAlreadyExistsError,
    MemoryError,
    MemoryExpiredError,
    MemoryNotFoundError,
    MemoryStorageError,
)


def test_memory_error():
    exc = MemoryError("memory")
    assert str(exc) == "memory"


def test_not_found():
    exc = MemoryNotFoundError("missing")
    assert isinstance(exc, MemoryError)


def test_already_exists():
    exc = MemoryAlreadyExistsError("exists")
    assert isinstance(exc, MemoryError)


def test_invalid():
    exc = InvalidMemoryError("invalid")
    assert isinstance(exc, MemoryError)


def test_expired():
    exc = MemoryExpiredError("expired")
    assert isinstance(exc, MemoryError)


def test_storage():
    exc = MemoryStorageError("storage")
    assert isinstance(exc, MemoryError)


def test_catch_memory():
    with pytest.raises(MemoryError):
        raise MemoryExpiredError("expired")


def test_catch_sentinel():
    with pytest.raises(SentinelError):
        raise MemoryStorageError("storage")