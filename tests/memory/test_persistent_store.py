import json
from datetime import UTC, datetime, timedelta

import pytest

from sentinel.memory.constants import MemoryStatus, MemoryType
from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.manager import MemoryManager
from sentinel.memory.persistent_store import PersistentMemoryStore
from sentinel.storage.backends.sqlite import SQLiteBackend


def make_store(tmp_path):
    backend = SQLiteBackend(tmp_path / "sentinel-memory.sqlite3")
    return PersistentMemoryStore(backend), backend


def test_memory_survives_backend_reopen(tmp_path):
    store, backend = make_store(tmp_path)
    manager = MemoryManager(store=store)
    created = manager.create(
        "profile.preference",
        {"theme": "dark", "languages": ["en", "te"]},
        importance=4,
        memory_type=MemoryType.LONG_TERM,
        ttl=timedelta(hours=3),
    )
    original_created_at = created.created_at
    backend.close()

    reopened_backend = SQLiteBackend(tmp_path / "sentinel-memory.sqlite3")
    reopened = PersistentMemoryStore(reopened_backend)
    restored = MemoryManager(store=reopened).get("profile.preference")

    assert restored.content == {
        "theme": "dark",
        "languages": ["en", "te"],
    }
    assert restored.importance == 4
    assert restored.memory_type is MemoryType.LONG_TERM
    assert restored.created_at == original_created_at
    reopened_backend.close()


def test_duplicate_add_is_rejected(tmp_path):
    store, backend = make_store(tmp_path)
    manager = MemoryManager(store=store)
    manager.create("same", "first")

    with pytest.raises(MemoryAlreadyExistsError):
        manager.create("same", "second")
    backend.close()


def test_missing_remove_raises(tmp_path):
    store, backend = make_store(tmp_path)
    with pytest.raises(MemoryNotFoundError):
        store.remove("missing")
    backend.close()


def test_archive_and_delete_lifecycle_persist(tmp_path):
    store, backend = make_store(tmp_path)
    manager = MemoryManager(store=store)
    manager.create("archived", "one")
    manager.create("deleted", "two")

    manager.archive("archived")
    manager.delete("deleted")

    assert store.get("archived").status is MemoryStatus.ARCHIVED
    assert store.get("deleted").status is MemoryStatus.DELETED
    backend.close()

    reopened_backend = SQLiteBackend(tmp_path / "sentinel-memory.sqlite3")
    reopened = PersistentMemoryStore(reopened_backend)
    assert reopened.get("archived").status is MemoryStatus.ARCHIVED
    assert reopened.get("deleted").status is MemoryStatus.DELETED
    reopened_backend.close()


def test_expiry_is_not_reset_by_restart(tmp_path):
    store, backend = make_store(tmp_path)
    expired_at = datetime.now(UTC) - timedelta(minutes=5)
    record = {
        "id": "expired",
        "content": "old",
        "memory_type": MemoryType.SHORT_TERM.value,
        "importance": 1,
        "status": MemoryStatus.ACTIVE.value,
        "created_at": (expired_at - timedelta(seconds=60)).isoformat(),
        "last_accessed": expired_at.isoformat(),
        "ttl_seconds": 60,
        "expired": True,
    }
    backend.set("sentinel:memory:entry:expired", json.dumps(record))
    restored = store.get("expired")
    assert restored.expired
    backend.close()


def test_search_and_clear_only_touch_memory_namespace(tmp_path):
    store, backend = make_store(tmp_path)
    backend.set("application:setting", "preserve")
    manager = MemoryManager(store=store)
    manager.create("one", "Sentinel assistant")
    manager.create("two", "unrelated")

    assert [entry.id for entry in manager.search("sentinel")] == ["one"]
    assert backend.exists("application:setting")
    store.clear()
    assert len(store) == 0
    assert backend.get("application:setting") == "preserve"
    backend.close()


def test_non_json_content_is_rejected(tmp_path):
    store, backend = make_store(tmp_path)
    with pytest.raises(TypeError, match="JSON-serializable"):
        store.add(
            __import__("sentinel.memory.entry", fromlist=["BaseMemoryEntry"])
            .BaseMemoryEntry("not-json", object())
        )
    assert len(store) == 0
    backend.close()


def test_upsert_replaces_persisted_content(tmp_path):
    store, backend = make_store(tmp_path)
    manager = MemoryManager(store=store)
    manager.create("replace", "before")
    manager.upsert("replace", "after")
    assert store.get("replace").content == "after"
    backend.close()


def test_concurrent_get_does_not_overwrite_another_store_update(
    tmp_path, monkeypatch
):
    from contextlib import contextmanager
    from threading import Event, Thread

    from sentinel.memory.entry import BaseMemoryEntry

    database = tmp_path / "shared-memory.sqlite3"
    first_backend = SQLiteBackend(database)
    second_backend = SQLiteBackend(database)

    first_store = PersistentMemoryStore(first_backend)
    second_store = PersistentMemoryStore(second_backend)

    first_store.add(BaseMemoryEntry("shared", "original"))

    read_completed = Event()
    continue_get = Event()
    writer_attempting = Event()
    writer_finished = Event()
    results = []
    errors = []

    original_get = first_backend.get

    def paused_get(key):
        value = original_get(key)
        if key == "sentinel:memory:entry:shared":
            read_completed.set()
            if not continue_get.wait(timeout=10):
                raise TimeoutError("Timed out waiting to resume persistent get")
        return value

    monkeypatch.setattr(first_backend, "get", paused_get)

    original_atomic = second_backend.atomic

    @contextmanager
    def observed_atomic():
        writer_attempting.set()
        with original_atomic():
            yield

    monkeypatch.setattr(second_backend, "atomic", observed_atomic)

    def read_from_first_store():
        try:
            results.append(first_store.get("shared"))
        except Exception as exc:
            errors.append(exc)

    def update_from_second_store():
        try:
            second_store.upsert(
                BaseMemoryEntry("shared", "updated by second store")
            )
        except Exception as exc:
            errors.append(exc)
        finally:
            writer_finished.set()

    reader = Thread(target=read_from_first_store, daemon=True)
    writer = Thread(target=update_from_second_store, daemon=True)

    try:
        reader.start()
        assert read_completed.wait(timeout=10)

        writer.start()
        assert writer_attempting.wait(timeout=10)
        assert not writer_finished.wait(timeout=0.2), (
            "Second store should wait while the first transaction is active"
        )
    finally:
        continue_get.set()
        reader.join(timeout=10)
        if writer.ident is not None:
            writer.join(timeout=10)

    try:
        assert not reader.is_alive(), "Persistent get thread did not finish"
        assert not writer.is_alive(), "Persistent update thread did not finish"
        assert not errors, f"Concurrent operation raised: {errors}"
        assert results

        persisted = second_store.get("shared")
        assert persisted.content == "updated by second store"
    finally:
        first_backend.close()
        second_backend.close()
