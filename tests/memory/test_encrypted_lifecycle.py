import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from sentinel.memory import (
    BaseMemoryEntry,
    EncryptedStorageBackend,
    MemoryLifecycle,
    PersistentMemoryStore,
    RetentionPolicy,
)
from sentinel.storage.backends.sqlite import SQLiteBackend


def test_encrypted_backend_hides_plaintext_and_round_trips(tmp_path):
    database = tmp_path / "memory.db"
    key = EncryptedStorageBackend.generate_key()
    raw = SQLiteBackend(database)
    encrypted = EncryptedStorageBackend(raw, key)
    store = PersistentMemoryStore(encrypted)
    store.add(BaseMemoryEntry("one", {"secret": "private phrase"}, ttl=None))
    raw_value = raw.get("sentinel:memory:entry:one")
    assert "private phrase" not in raw_value
    assert store.get("one").content == {"secret": "private phrase"}
    raw.close()


def test_wrong_key_fails_closed(tmp_path):
    db = tmp_path / "memory.db"
    first = SQLiteBackend(db)
    key = EncryptedStorageBackend.generate_key()
    EncryptedStorageBackend(first, key).set("k", "value")
    wrong = EncryptedStorageBackend.generate_key()
    with pytest.raises(ValueError, match="failed authentication"):
        EncryptedStorageBackend(first, wrong).get("k")
    first.close()


def test_key_rotation_preserves_values(tmp_path):
    backend = SQLiteBackend(tmp_path / "memory.db")
    old_key, new_key = (
        EncryptedStorageBackend.generate_key(),
        EncryptedStorageBackend.generate_key(),
    )
    encrypted = EncryptedStorageBackend(backend, old_key)
    encrypted.set("a", "alpha")
    encrypted.set("b", "beta")
    encrypted.rotate_key(new_key)
    assert encrypted.get("a") == "alpha"
    assert EncryptedStorageBackend(backend, new_key).get("b") == "beta"
    backend.close()


def test_schema_migration_retention_and_backup_restore(tmp_path):
    db = tmp_path / "source.db"
    backend = SQLiteBackend(db)
    store = PersistentMemoryStore(backend)
    lifecycle = MemoryLifecycle(store)
    assert lifecycle.migrate() == 1
    store.add(BaseMemoryEntry("keep", "recent", ttl=None))
    old = BaseMemoryEntry("old", "stale", ttl=None)
    old._created_at = datetime.now(UTC) - timedelta(days=40)
    store.add(old)
    removed = lifecycle.apply_retention(
        RetentionPolicy(
            max_age=timedelta(days=30),
            purge_archived_after=None,
            purge_deleted_after=None,
        )
    )
    assert removed == 1
    backup = lifecycle.backup(db, tmp_path / "backup.db")
    backend.close()
    restored = lifecycle.restore(backup, tmp_path / "restored.db")
    restored_backend = SQLiteBackend(restored)
    restored_store = PersistentMemoryStore(restored_backend)
    assert restored_store.exists("keep")
    assert not restored_store.exists("old")
    restored_backend.close()


def test_retention_rejects_naive_clock(tmp_path):
    backend = SQLiteBackend(tmp_path / "memory.db")
    lifecycle = MemoryLifecycle(PersistentMemoryStore(backend))
    with pytest.raises(ValueError, match="timezone-aware"):
        lifecycle.apply_retention(RetentionPolicy(), now=datetime.now())
    backend.close()


def test_encrypted_memory_factory_and_startup_retention(tmp_path):
    from sentinel.memory.runtime import MemoryRuntimeService
    from sentinel.memory.service import MemoryService

    service = MemoryService.with_encrypted_sqlite(
        tmp_path / "encrypted.db", EncryptedStorageBackend.generate_key()
    )
    service.create("expired", "temporary", ttl=timedelta(0))
    runtime = MemoryRuntimeService(service)
    runtime.initialize()
    assert not service.exists("expired")
    assert runtime.retention_removed_on_last_start == 1
    runtime.shutdown()


def test_sqlite_compaction_keeps_database_valid(tmp_path):
    db = tmp_path / "memory.db"
    backend = SQLiteBackend(db)
    PersistentMemoryStore(backend).add(BaseMemoryEntry("x", "y", ttl=None))
    backend.close()
    MemoryLifecycle.compact_sqlite(db)
    check = SQLiteBackend(db)
    assert check.exists("sentinel:memory:entry:x")
    check.close()


def test_archive_retention_uses_archive_timestamp_not_creation_time(tmp_path):
    backend = SQLiteBackend(tmp_path / "memory.db")
    store = PersistentMemoryStore(backend)
    entry = BaseMemoryEntry("archived", "content", ttl=None)
    entry._created_at = datetime.now(UTC) - timedelta(days=100)
    entry.archive()
    store.add(entry)
    lifecycle = MemoryLifecycle(store)
    removed = lifecycle.apply_retention(
        RetentionPolicy(
            max_age=None,
            purge_archived_after=timedelta(days=30),
            purge_deleted_after=None,
        )
    )
    assert removed == 0
    assert store.exists("archived")
    backend.close()


def test_encrypted_backup_restore_preserves_ciphertext_and_key(tmp_path):
    source = tmp_path / "encrypted-source.db"
    backup = tmp_path / "encrypted-backup.db"
    restored = tmp_path / "encrypted-restored.db"
    key = EncryptedStorageBackend.generate_key()
    raw = SQLiteBackend(source)
    encrypted = EncryptedStorageBackend(raw, key)
    store = PersistentMemoryStore(encrypted)
    store.add(BaseMemoryEntry("private", {"note": "restore-drill-secret"}, ttl=None))

    MemoryLifecycle.backup(source, backup)
    raw.close()
    MemoryLifecycle.restore(backup, restored)

    restored_raw = SQLiteBackend(restored)
    ciphertext = restored_raw.get("sentinel:memory:entry:private")
    assert "restore-drill-secret" not in ciphertext
    restored_store = PersistentMemoryStore(EncryptedStorageBackend(restored_raw, key))
    assert restored_store.get("private").content == {"note": "restore-drill-secret"}
    with pytest.raises(ValueError, match="failed authentication"):
        PersistentMemoryStore(
            EncryptedStorageBackend(
                restored_raw, EncryptedStorageBackend.generate_key()
            )
        ).get("private")
    restored_raw.close()


def test_restore_rejects_corrupt_backup_without_replacing_destination(tmp_path):
    corrupt = tmp_path / "corrupt.db"
    destination = tmp_path / "existing.db"
    corrupt.write_bytes(b"not a sqlite database")
    destination.write_bytes(b"preserve-existing-target")

    with pytest.raises(sqlite3.DatabaseError):
        MemoryLifecycle.restore(corrupt, destination)

    assert destination.read_bytes() == b"preserve-existing-target"
