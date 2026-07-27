"""
Tests for storage interfaces.
"""

import pytest

from sentinel.storage.interfaces import StorageBackend


class DummyBackend(StorageBackend):

    def exists(self, key: str) -> bool:
        return False

    def get(self, key: str):
        return None

    def set(self, key: str, value):
        pass

    def delete(self, key: str):
        pass

    def clear(self):
        pass

    def keys(self):
        return []

    def close(self):
        pass


def test_backend_can_be_instantiated():
    backend = DummyBackend()

    assert isinstance(backend, StorageBackend)


def test_storage_backend_is_abstract():
    with pytest.raises(TypeError):
        StorageBackend()