"""
Production SQLite storage backend for Sentinel OS.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

from sentinel.storage.exceptions import (
    StorageConnectionError,
    StorageKeyNotFoundError,
    StorageReadError,
    StorageWriteError,
)
from sentinel.storage.interfaces import StorageBackend
from sentinel.storage.serializers import JsonSerializer


class SQLiteBackend(StorageBackend):
    """
    SQLite implementation of the Sentinel storage backend.

    Values are serialized as JSON before being persisted. The backend
    provides thread-safe access and transactional writes.
    """

    def __init__(
        self,
        database: str | Path,
    ) -> None:
        self._database = Path(database)
        self._connection: sqlite3.Connection | None = None
        self._lock = RLock()
        self._serializer = JsonSerializer()

        self._database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connect()

    def connect(self) -> None:
        """
        Establish the SQLite connection and initialize the schema.
        """
        with self._lock:
            if self._connection is not None:
                return

            try:
                connection = sqlite3.connect(
                    self._database,
                    check_same_thread=False,
                )

                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute("PRAGMA journal_mode = WAL")
                connection.execute("PRAGMA synchronous = NORMAL")

                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS storage (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )

                connection.commit()
                self._connection = connection

            except sqlite3.Error as exc:
                raise StorageConnectionError(
                    f"Failed to connect to SQLite database: {exc}"
                ) from exc

    def disconnect(self) -> None:
        """
        Close the SQLite connection.
        """
        with self._lock:
            if self._connection is None:
                return

            try:
                self._connection.close()
            except sqlite3.Error as exc:
                raise StorageConnectionError(
                    f"Failed to close SQLite database: {exc}"
                ) from exc
            finally:
                self._connection = None

    def close(self) -> None:
        """
        Backward-compatible alias for disconnect().
        """
        self.disconnect()

    def exists(self, key: str) -> bool:
        """
        Return whether a key exists.
        """
        self._validate_key(key)

        with self._lock:
            connection = self._ensure_connected()

            try:
                cursor = connection.execute(
                    "SELECT 1 FROM storage WHERE key = ? LIMIT 1",
                    (key,),
                )

                return cursor.fetchone() is not None

            except sqlite3.Error as exc:
                raise StorageReadError(
                    f"Failed to check key '{key}': {exc}"
                ) from exc

    def get(self, key: str) -> Any:
        """
        Retrieve and deserialize a stored value.
        """
        self._validate_key(key)

        with self._lock:
            connection = self._ensure_connected()

            try:
                cursor = connection.execute(
                    "SELECT value FROM storage WHERE key = ?",
                    (key,),
                )

                row = cursor.fetchone()

                if row is None:
                    raise StorageKeyNotFoundError(
                        f"Key '{key}' not found."
                    )

                return self._deserialize(row[0])

            except StorageKeyNotFoundError:
                raise

            except sqlite3.Error as exc:
                raise StorageReadError(
                    f"Failed to read key '{key}': {exc}"
                ) from exc

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Serialize and persist a value atomically.
        """
        self._validate_key(key)

        serialized = self._serialize(value)

        with self._lock:
            connection = self._ensure_connected()

            try:
                connection.execute(
                    """
                    INSERT INTO storage(key, value)
                    VALUES(?, ?)
                    ON CONFLICT(key)
                    DO UPDATE SET value = excluded.value
                    """,
                    (key, serialized),
                )

                connection.commit()

            except sqlite3.Error as exc:
                connection.rollback()

                raise StorageWriteError(
                    f"Failed to write key '{key}': {exc}"
                ) from exc

    def delete(self, key: str) -> None:
        """
        Delete a key if it exists.
        """
        self._validate_key(key)

        with self._lock:
            connection = self._ensure_connected()

            try:
                connection.execute(
                    "DELETE FROM storage WHERE key = ?",
                    (key,),
                )

                connection.commit()

            except sqlite3.Error as exc:
                connection.rollback()

                raise StorageWriteError(
                    f"Failed to delete key '{key}': {exc}"
                ) from exc

    def clear(self) -> None:
        """
        Remove all stored values.
        """
        with self._lock:
            connection = self._ensure_connected()

            try:
                connection.execute("DELETE FROM storage")
                connection.commit()

            except sqlite3.Error as exc:
                connection.rollback()

                raise StorageWriteError(
                    f"Failed to clear storage: {exc}"
                ) from exc

    def keys(self) -> list[str]:
        """
        Return all stored keys.
        """
        with self._lock:
            connection = self._ensure_connected()

            try:
                cursor = connection.execute(
                    "SELECT key FROM storage ORDER BY key"
                )

                return [
                    row[0]
                    for row in cursor.fetchall()
                ]

            except sqlite3.Error as exc:
                raise StorageReadError(
                    f"Failed to list storage keys: {exc}"
                ) from exc

    def save(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Backward-compatible alias for set().
        """
        self.set(key, value)

    def load(
        self,
        key: str,
    ) -> Any:
        """
        Backward-compatible alias for get().
        """
        return self.get(key)

    def _ensure_connected(self) -> sqlite3.Connection:
        """
        Return the active database connection.
        """
        if self._connection is None:
            raise StorageConnectionError(
                "SQLite backend is not connected."
            )

        return self._connection

    @staticmethod
    def _validate_key(key: str) -> None:
        """
        Validate storage keys.
        """
        if not isinstance(key, str):
            raise TypeError("Storage key must be a string.")

        if not key.strip():
            raise ValueError(
                "Storage key cannot be empty."
            )

    def _serialize(self, value: Any) -> str:
        """
        Serialize a value using the configured JSON serializer.
        """
        from io import StringIO

        stream = StringIO()
        self._serializer.dump(value, stream)

        return stream.getvalue()

    def _deserialize(self, value: str) -> Any:
        """
        Deserialize a stored JSON value.
        """
        from io import StringIO

        stream = StringIO(value)

        return self._serializer.load(stream)