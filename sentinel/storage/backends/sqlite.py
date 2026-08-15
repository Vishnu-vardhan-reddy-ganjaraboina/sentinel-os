"""
SQLite storage backend for Sentinel OS.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sentinel.storage.exceptions import (
    StorageConnectionError,
    StorageKeyNotFoundError,
    StorageReadError,
    StorageWriteError,
)
from sentinel.storage.interfaces import StorageBackend


class SQLiteBackend(StorageBackend):
    """
    SQLite implementation of StorageBackend.
    """

    def __init__(
        self,
        database: str | Path,
    ) -> None:
        self._database = Path(database)
        self._connection: sqlite3.Connection | None = None

        self._database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connect()

    def exists(
        self,
        key: str,
    ) -> bool:
        connection = self._ensure_connected()

        cursor = connection.execute(
            "SELECT 1 FROM storage WHERE key=?",
            (key,),
        )

        return cursor.fetchone() is not None

    def get(
        self,
        key: str,
    ) -> Any:
        connection = self._ensure_connected()

        try:
            cursor = connection.execute(
                "SELECT value FROM storage WHERE key=?",
                (key,),
            )

            row = cursor.fetchone()

            if row is None:
                raise StorageKeyNotFoundError(
                    f"Key '{key}' not found."
                )

            return row[0]

        except sqlite3.Error as exc:
            raise StorageReadError(
                str(exc)
            ) from exc

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        connection = self._ensure_connected()

        try:
            connection.execute(
                """
                INSERT INTO storage(key, value)
                VALUES(?, ?)
                ON CONFLICT(key)
                DO UPDATE SET value=excluded.value
                """,
                (
                    key,
                    str(value),
                ),
            )

            connection.commit()

        except sqlite3.Error as exc:
            raise StorageWriteError(
                str(exc)
            ) from exc

    def delete(
        self,
        key: str,
    ) -> None:
        connection = self._ensure_connected()

        connection.execute(
            "DELETE FROM storage WHERE key=?",
            (key,),
        )

        connection.commit()

    def clear(self) -> None:
        connection = self._ensure_connected()

        connection.execute(
            "DELETE FROM storage"
        )

        connection.commit()

    def keys(self) -> list[str]:
        connection = self._ensure_connected()

        cursor = connection.execute(
            "SELECT key FROM storage"
        )

        return [row[0] for row in cursor.fetchall()]

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def connect(self) -> None:
        """
        Connect to the SQLite database.
        """
        if self._connection is not None:
            return

        try:
            connection = sqlite3.connect(self._database)

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS storage(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            connection.commit()

            self._connection = connection

        except sqlite3.Error as exc:
            raise StorageConnectionError(
                str(exc)
            ) from exc

    def disconnect(self) -> None:
        """
        Disconnect from the SQLite database.
        """
        self.close()

    def _ensure_connected(self) -> sqlite3.Connection:
        """
        Return the active database connection.

        Raises:
            StorageConnectionError:
                If the backend is not connected.
        """
        if self._connection is None:
            raise StorageConnectionError(
                "Backend is not connected."
            )

        return self._connection

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