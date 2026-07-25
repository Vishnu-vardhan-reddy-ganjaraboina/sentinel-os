from pathlib import Path

from sentinel.storage.backends.sqlite import SQLiteBackend


def test_save_load_delete(tmp_path: Path) -> None:
    db = tmp_path / "test.db"

    backend = SQLiteBackend(db)

    backend.connect()

    backend.save("username", "vishnu")

    assert backend.exists("username")
    assert backend.load("username") == "vishnu"

    backend.delete("username")

    assert not backend.exists("username")

    backend.disconnect()