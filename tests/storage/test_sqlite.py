from pathlib import Path

import pytest

from sentinel.storage.backends.sqlite import SQLiteBackend
from sentinel.storage.exceptions import (
    StorageConnectionError,
    StorageKeyNotFoundError,
)


def test_save_load_delete(tmp_path: Path) -> None:
    db = tmp_path / "test.db"

    backend = SQLiteBackend(db)

    backend.save("username", "vishnu")

    assert backend.exists("username")
    assert backend.load("username") == "vishnu"

    backend.delete("username")

    assert not backend.exists("username")

    backend.disconnect()


def test_complex_value_round_trip(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    value = {
        "name": "Sentinel",
        "version": 1,
        "enabled": True,
        "items": [1, 2, 3],
    }

    backend.set("config", value)

    assert backend.get("config") == value

    backend.disconnect()


def test_update_existing_key(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    backend.set("counter", 1)
    backend.set("counter", 2)

    assert backend.get("counter") == 2

    backend.disconnect()


def test_missing_key(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    with pytest.raises(StorageKeyNotFoundError):
        backend.get("missing")

    backend.disconnect()


def test_empty_key_rejected(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    with pytest.raises(ValueError):
        backend.set("", "value")

    with pytest.raises(ValueError):
        backend.get("   ")

    backend.disconnect()


def test_non_string_key_rejected(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    with pytest.raises(TypeError):
        backend.set(123, "value")  # type: ignore[arg-type]

    backend.disconnect()


def test_disconnect_prevents_operations(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    backend.disconnect()

    with pytest.raises(StorageConnectionError):
        backend.get("anything")


def test_reconnect(tmp_path: Path) -> None:
    db = tmp_path / "test.db"

    backend = SQLiteBackend(db)

    backend.set("name", "Sentinel")
    backend.disconnect()

    backend.connect()

    assert backend.get("name") == "Sentinel"

    backend.disconnect()


def test_persistence_across_instances(tmp_path: Path) -> None:
    db = tmp_path / "test.db"

    first = SQLiteBackend(db)
    first.set("name", "Sentinel")
    first.disconnect()

    second = SQLiteBackend(db)

    assert second.get("name") == "Sentinel"

    second.disconnect()


def test_keys(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    backend.set("b", 2)
    backend.set("a", 1)

    assert backend.keys() == ["a", "b"]

    backend.disconnect()


def test_clear(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    backend.set("a", 1)
    backend.set("b", 2)

    backend.clear()

    assert backend.keys() == []

    backend.disconnect()