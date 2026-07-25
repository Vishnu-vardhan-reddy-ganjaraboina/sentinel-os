"""
SQLite storage backend for Sentinel OS.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sentinel.storage.exceptions import (
    StorageConnectionError,
    StorageReadError,
    StorageWriteError,
)
from sentinel.storage.interfaces import StorageBackend


class SQLiteBackend(StorageBackend):
    """
    SQLite implementation of the StorageBackend interface.
    """

    def __init__(self, database: str | Path) -> None:
        self._database = Path(database)
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        """
        Connect to the SQLite database.
        """
        try:
            self._database.parent.mkdir(parents=True, exist_ok=True)

            self._connection = sqlite3.connect(self._database)

            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS storage (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            self._connection.commit()

        except sqlite3.Error as exc:
            raise StorageConnectionError(
                f"Unable to connect to database: {self._database}"
            ) from exc

    def disconnect(self) -> None:
        """
        Close the database connection.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def save(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Save or update a key/value pair.
        """
        if self._connection is None:
            raise StorageConnectionError("Database is not connected.")

        try:
            self._connection.execute(
                """
                INSERT INTO storage(key, value)
                VALUES (?, ?)
                ON CONFLICT(key)
                DO UPDATE SET value = excluded.value
                """,
                (key, str(value)),
            )

            self._connection.commit()

        except sqlite3.Error as exc:
            raise StorageWriteError(
                f"Failed to save '{key}'."
            ) from exc

    def load(
        self,
        key: str,
    ) -> Any:
        """
        Load a value.
        """
        if self._connection is None:
            raise StorageConnectionError("Database is not connected.")

        try:
            cursor = self._connection.execute(
                "SELECT value FROM storage WHERE key = ?",
                (key,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return row[0]

        except sqlite3.Error as exc:
            raise StorageReadError(
                f"Failed to load '{key}'."
            ) from exc

    def delete(
        self,
        key: str,
    ) -> None:
        """
        Delete a key.
        """
        if self._connection is None:
            raise StorageConnectionError("Database is not connected.")

        self._connection.execute(
            "DELETE FROM storage WHERE key = ?",
            (key,),
        )

        self._connection.commit()

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check if a key exists.
        """
        if self._connection is None:
            raise StorageConnectionError("Database is not connected.")

        cursor = self._connection.execute(
            "SELECT 1 FROM storage WHERE key = ?",
            (key,),
        )

        return cursor.fetchone() is not None