"""
Thread-safe filesystem storage backend for Sentinel OS.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

from sentinel.storage.constants import DEFAULT_STORAGE_DIRECTORY
from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
)
from sentinel.storage.interfaces import StorageBackend


class FilesystemStorage(StorageBackend):
    """
    Thread-safe filesystem storage backend.

    Each key is stored as an individual JSON file.
    """

    def __init__(
        self,
        directory: str | Path = DEFAULT_STORAGE_DIRECTORY,
    ) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = RLock()
        self._closed = False

    def _path(self, key: str) -> Path:
        """
        Return the file path for a storage key.

        Raises:
            ValueError:
                If the key contains invalid path characters.
        """
        if (
            "/" in key
            or "\\"
            in key
            or ".."
            in key
        ):
            raise ValueError(
                "Invalid storage key."
            )

        return self._directory / f"{key}.json"

    def exists(self, key: str) -> bool:
        self._ensure_open()

        return self._path(key).exists()


    def get(self, key: str) -> Any:
        self._ensure_open()

        path = self._path(key)

        if not path.exists():
            raise StorageKeyNotFoundError(key)

        with self._lock:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                return deepcopy(
                    json.load(file)
                )


    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        self._ensure_open()

        path = self._path(key)

        with self._lock:
            with path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    deepcopy(value),
                    file,
                    indent=4,
                )

    def delete(self, key: str) -> None:
        """
        Delete a stored key.

        Raises:
            StorageKeyNotFoundError:
                If the key does not exist.
        """
        self._ensure_open()

        path = self._path(key)

        with self._lock:
            if not path.exists():
                raise StorageKeyNotFoundError(key)

            path.unlink()


    def clear(self) -> None:
        """
        Remove all stored items.
        """
        self._ensure_open()

        with self._lock:
            for file in self._directory.glob("*.json"):
                file.unlink()


    def keys(self) -> list[str]:
        """
        Return all stored keys.
        """
        self._ensure_open()

        with self._lock:
            return sorted(
                file.stem
                for file in self._directory.glob("*.json")
            )


    def close(self) -> None:
        """
        Shutdown the storage backend.
        """
        with self._lock:
            self._closed = True


    def _ensure_open(self) -> None:
        """
        Ensure the backend is still open.

        Raises:
            StorageBackendError:
                If the backend has been closed.
        """
        if self._closed:
            raise StorageBackendError(
                "FilesystemStorage has been closed."
            )