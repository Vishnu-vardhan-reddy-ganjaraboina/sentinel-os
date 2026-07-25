"""
Filesystem storage backend for Sentinel OS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentinel.storage.exceptions import (
    StorageConnectionError,
    StorageReadError,
    StorageWriteError,
)
from sentinel.storage.interfaces import StorageBackend


class FilesystemBackend(StorageBackend):
    """
    Filesystem implementation of StorageBackend.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._connected = False

    def connect(self) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            self._connected = True
        except OSError as exc:
            raise StorageConnectionError(
                f"Unable to access storage directory: {self._root}"
            ) from exc

    def disconnect(self) -> None:
        self._connected = False

    def _require_connection(self) -> None:
        if not self._connected:
            raise StorageConnectionError("Filesystem backend is not connected.")

    def _path(self, key: str) -> Path:
        return self._root / key

    def save(self, key: str, value: Any) -> None:
        self._require_connection()

        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_text(str(value), encoding="utf-8")
        except OSError as exc:
            raise StorageWriteError(
                f"Unable to save '{key}'."
            ) from exc

    def load(self, key: str) -> Any:
        self._require_connection()

        path = self._path(key)

        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageReadError(
                f"Unable to read '{key}'."
            ) from exc

    def delete(self, key: str) -> None:
        self._require_connection()

        path = self._path(key)

        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        self._require_connection()
        return self._path(key).exists()