"""
Production filesystem storage backend for Sentinel OS.
"""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

from sentinel.storage.constants import DEFAULT_STORAGE_DIRECTORY
from sentinel.storage.exceptions import (
    StorageBackendError,
    StorageKeyNotFoundError,
    StorageReadError,
    StorageSerializationError,
    StorageWriteError,
)
from sentinel.storage.interfaces import StorageBackend


class FilesystemBackend(StorageBackend):
    """
    Thread-safe filesystem storage backend.

    Each key is stored as an individual JSON file.

    Writes are performed atomically using a temporary file followed
    by an atomic filesystem replacement.
    """

    def __init__(
        self,
        root: str | Path = DEFAULT_STORAGE_DIRECTORY,
    ) -> None:
        self._root = Path(root)
        self._lock = RLock()
        self._closed = False

        try:
            self._root.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as exc:
            raise StorageWriteError(
                f"Unable to create storage directory: {self._root}"
            ) from exc

    def connect(self) -> None:
        with self._lock:
            if self._closed:
                raise StorageBackendError(
                    "Filesystem backend has been closed."
                )

            try:
                self._root.mkdir(
                    parents=True,
                    exist_ok=True,
                )
            except OSError as exc:
                raise StorageWriteError(
                    f"Unable to access storage directory: {self._root}"
                ) from exc

    def disconnect(self) -> None:
        with self._lock:
            self._closed = True

    def close(self) -> None:
        self.disconnect()

    def exists(self, key: str) -> bool:
        self._validate_key(key)
        self._ensure_open()

        with self._lock:
            try:
                return self._path(key).exists()
            except OSError as exc:
                raise StorageReadError(
                    f"Unable to check '{key}'."
                ) from exc

    def get(self, key: str) -> Any:
        self._validate_key(key)
        self._ensure_open()

        path = self._path(key)

        with self._lock:
            if not path.exists():
                raise StorageKeyNotFoundError(
                    f"Key '{key}' does not exist."
                )

            try:
                with path.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    value = json.load(file)

                return deepcopy(value)

            except json.JSONDecodeError as exc:
                raise StorageSerializationError(
                    f"Invalid JSON for key '{key}'."
                ) from exc

            except OSError as exc:
                raise StorageReadError(
                    f"Unable to read '{key}'."
                ) from exc

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        self._validate_key(key)
        self._ensure_open()

        path = self._path(key)

        with self._lock:
            temporary_path: Path | None = None

            try:
                fd, temporary_name = tempfile.mkstemp(
                    dir=self._root,
                    prefix=f".{key}.",
                    suffix=".tmp",
                    text=True,
                )

                temporary_path = Path(temporary_name)

                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        deepcopy(value),
                        file,
                        indent=4,
                    )
                    file.flush()
                    os.fsync(file.fileno())

                os.replace(
                    temporary_path,
                    path,
                )

                temporary_path = None

            except (TypeError, ValueError) as exc:
                raise StorageSerializationError(
                    f"Unable to serialize key '{key}'."
                ) from exc

            except OSError as exc:
                raise StorageWriteError(
                    f"Unable to write '{key}'."
                ) from exc

            finally:
                if temporary_path is not None:
                    try:
                        temporary_path.unlink(
                            missing_ok=True
                        )
                    except OSError:
                        pass

    def delete(self, key: str) -> None:
        self._validate_key(key)
        self._ensure_open()

        path = self._path(key)

        with self._lock:
            if not path.exists():
                raise StorageKeyNotFoundError(
                    f"Key '{key}' does not exist."
                )

            try:
                path.unlink()
            except OSError as exc:
                raise StorageWriteError(
                    f"Unable to delete '{key}'."
                ) from exc

    def clear(self) -> None:
        self._ensure_open()

        with self._lock:
            try:
                for path in self._root.glob("*.json"):
                    path.unlink()
            except OSError as exc:
                raise StorageWriteError(
                    "Unable to clear filesystem storage."
                ) from exc

    def keys(self) -> list[str]:
        self._ensure_open()

        with self._lock:
            try:
                return sorted(
                    path.stem
                    for path in self._root.glob("*.json")
                    if path.is_file()
                )
            except OSError as exc:
                raise StorageReadError(
                    "Unable to list filesystem storage."
                ) from exc

    def save(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.set(key, value)

    def load(
        self,
        key: str,
    ) -> Any:
        return self.get(key)

    def _path(self, key: str) -> Path:
        return self._root / f"{key}.json"

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("Storage key must be a string.")

        if not key.strip():
            raise ValueError("Storage key cannot be empty.")

        if (
            "/" in key
            or "\\" in key
            or ".." in key
            or "\x00" in key
        ):
            raise ValueError("Invalid storage key.")

    def _ensure_open(self) -> None:
        if self._closed:
            raise StorageBackendError(
                "Filesystem backend has been closed."
            )
