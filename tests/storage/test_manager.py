from pathlib import Path

from sentinel.storage.backends.sqlite import SQLiteBackend
from sentinel.storage.manager import StorageManager


def test_storage_manager(tmp_path: Path) -> None:
    backend = SQLiteBackend(tmp_path / "test.db")

    manager = StorageManager(backend)

    manager.connect()

    manager.save("name", "Sentinel")

    assert manager.exists("name")
    assert manager.load("name") == "Sentinel"

    manager.delete("name")

    assert not manager.exists("name")

    manager.disconnect()