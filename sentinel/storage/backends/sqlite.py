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

    def __init__(self, database: str | Path):
        self._database = Path(database)
        self._connection = None

        self._database.parent.mkdir(
            parents=True,
            exist_ok=True,
    )

        self._database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            self._connection = sqlite3.connect(self._database)

            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS storage(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            self._connection.commit()

        except sqlite3.Error as exc:
            raise StorageConnectionError(
                str(exc)
            ) from exc

    def exists(self, key: str) -> bool:
        cursor = self._connection.execute(
            "SELECT 1 FROM storage WHERE key=?",
            (key,),
        )

        return cursor.fetchone() is not None

    def get(self, key: str) -> Any:
        try:
            cursor = self._connection.execute(
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
        try:
            self._connection.execute(
                """
                INSERT INTO storage(key,value)
                VALUES(?,?)
                ON CONFLICT(key)
                DO UPDATE SET value=excluded.value
                """,
                (
                    key,
                    str(value),
                ),
            )

            self._connection.commit()

        except sqlite3.Error as exc:
            raise StorageWriteError(
                str(exc)
            ) from exc

    def delete(self, key: str) -> None:
        self._connection.execute(
            "DELETE FROM storage WHERE key=?",
            (key,),
        )

        self._connection.commit()

    def clear(self) -> None:
        self._connection.execute(
            "DELETE FROM storage"
        )

        self._connection.commit()

    def keys(self) -> list[str]:
        cursor = self._connection.execute(
            "SELECT key FROM storage"
        )

        return [row[0] for row in cursor.fetchall()]

    def close(self) -> None:
        self._connection.close()



    def connect(self) -> None:
        if self._connection is not None:
            return

        self._connection = sqlite3.connect(self._database)

        self._connection.execute(
           """
           CREATE TABLE IF NOT EXISTS storage(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
        )
        """
    )

        self._connection.commit()
    
    def disconnect(self) -> None:
        if self._connection is not None:
             self._connection.close()
             self._connection = None



    def _ensure_connected(self):
        if self._connection is None:
             raise StorageConnectionError(
            "Backend is not connected."
        )

    def save(self, key: str, value: Any) -> None:
        """
        Backward-compatible alias for set().
        """
        self.set(key, value)


    def load(self, key: str) -> Any:
        """
        Backward-compatible alias for get().
        """
        return self.get(key)