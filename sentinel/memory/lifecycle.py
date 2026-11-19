"""Retention, backup/restore and schema versioning for persistent memory."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sentinel.memory.persistent_store import PersistentMemoryStore


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    max_age: timedelta | None = None
    purge_archived_after: timedelta | None = timedelta(days=30)
    purge_deleted_after: timedelta | None = timedelta(days=7)

    def __post_init__(self) -> None:
        for name in ("max_age", "purge_archived_after", "purge_deleted_after"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, timedelta) or value.total_seconds() < 0
            ):
                raise ValueError(f"{name} must be a non-negative timedelta or None")


class MemoryLifecycle:
    """Explicit maintenance operations; no implicit background scheduler."""

    _SCHEMA_KEY = "sentinel:memory:schema_version"
    CURRENT_SCHEMA_VERSION = 1

    def __init__(self, store: PersistentMemoryStore) -> None:
        self.store = store

    def migrate(self) -> int:
        backend = self.store.backend
        with backend.atomic():
            if not backend.exists(self._SCHEMA_KEY):
                backend.set(self._SCHEMA_KEY, str(self.CURRENT_SCHEMA_VERSION))
            raw_version = backend.get(self._SCHEMA_KEY)
            try:
                version = int(raw_version)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Invalid memory schema version: {raw_version!r}"
                ) from exc
            if version > self.CURRENT_SCHEMA_VERSION or version < 1:
                raise RuntimeError(f"Unsupported memory schema version: {version!r}")
            backend.set(self._SCHEMA_KEY, str(self.CURRENT_SCHEMA_VERSION))
        return self.CURRENT_SCHEMA_VERSION

    def apply_retention(
        self, policy: RetentionPolicy, *, now: datetime | None = None
    ) -> int:
        if not isinstance(policy, RetentionPolicy):
            raise TypeError("policy must be a RetentionPolicy")
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        removed = 0
        for entry in self.store.list():
            age = current - entry.created_at
            status_age = current - entry.status_changed_at
            status = str(getattr(entry.status, "value", entry.status)).lower()
            purge = entry.expired or (
                policy.max_age is not None and age >= policy.max_age
            )
            if status == "archived" and policy.purge_archived_after is not None:
                purge = purge or status_age >= policy.purge_archived_after
            if status == "deleted" and policy.purge_deleted_after is not None:
                purge = purge or status_age >= policy.purge_deleted_after
            if purge:
                self.store.remove(entry.id)
                removed += 1
        return removed

    @staticmethod
    def backup(database: str | Path, destination: str | Path) -> Path:
        source, target = Path(database).resolve(), Path(destination).resolve()
        if source == target:
            raise ValueError("backup destination must differ from source")
        target.parent.mkdir(parents=True, exist_ok=True)
        src = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
            if dst.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise RuntimeError("Backup integrity check failed")
        finally:
            dst.close()
            src.close()
        return target

    @staticmethod
    def restore(backup: str | Path, destination: str | Path) -> Path:
        source, target = Path(backup).resolve(), Path(destination).resolve()
        if not source.is_file() or source == target:
            raise ValueError("backup must exist and differ from restore destination")
        check = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
        try:
            valid = check.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            tables = {
                row[0]
                for row in check.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not valid or "storage" not in tables:
                raise RuntimeError(
                    "Backup is not a valid Sentinel SQLite storage database"
                )
        finally:
            check.close()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".restore-tmp")
        if temporary.exists():
            temporary.unlink()
        src, dst = (
            sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True),
            sqlite3.connect(temporary),
        )
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        temporary.replace(target)
        return target

    @staticmethod
    def compact_sqlite(database: str | Path) -> None:
        """Best-effort SQLite page cleanup after logical deletion.

        This cannot guarantee physical erasure on SSDs, snapshots, backups, or
        copy-on-write filesystems. Use encryption-key destruction for crypto-erasure.
        """
        connection = sqlite3.connect(Path(database))
        try:
            connection.execute("PRAGMA secure_delete = ON")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            connection.execute("VACUUM")
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise RuntimeError("SQLite integrity check failed after compaction")
        finally:
            connection.close()
