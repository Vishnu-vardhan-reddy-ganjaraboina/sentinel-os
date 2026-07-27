"""
Storage engine for Sentinel OS.

Provides a unified interface over one or more storage backends.
"""

from __future__ import annotations

from threading import RLock
from typing import Any

from sentinel.storage.exceptions import StorageBackendError
from sentinel.storage.interfaces import StorageBackend


class StorageEngine:
    """
    Coordinates one or more storage backends.
    """

    def __init__(self) -> None:
        self._backends: dict[str, StorageBackend] = {}
        self._default_backend: str | None = None
        self._lock = RLock()

    def register(
        self,
        name: str,
        backend: StorageBackend,
    ) -> None:
        """
        Register a storage backend.
        """
        with self._lock:
            if name in self._backends:
                raise StorageBackendError(
                    f"Backend '{name}' already exists."
                )

            self._backends[name] = backend

            if self._default_backend is None:
                self._default_backend = name

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        Remove a storage backend.
        """
        with self._lock:
            try:
                backend = self._backends.pop(name)
            except KeyError as exc:
                raise StorageBackendError(
                    f"Unknown backend '{name}'."
                ) from exc

            backend.close()

            if self._default_backend == name:
                self._default_backend = (
                    next(iter(self._backends), None)
                )

    def set_default(
        self,
        name: str,
    ) -> None:
        """
        Select the default backend.
        """
        with self._lock:
            if name not in self._backends:
                raise StorageBackendError(
                    f"Unknown backend '{name}'."
                )

            self._default_backend = name

    def backend(
        self,
        name: str | None = None,
    ) -> StorageBackend:
        """
        Return a registered backend.
        """
        with self._lock:
            backend_name = (
                name
                if name is not None
                else self._default_backend
            )

            if backend_name is None:
                raise StorageBackendError(
                    "No default backend configured."
                )

            try:
                return self._backends[backend_name]
            except KeyError as exc:
                raise StorageBackendError(
                    f"Unknown backend '{backend_name}'."
                ) from exc

    def exists(
        self,
        key: str,
        *,
        backend: str | None = None,
    ) -> bool:
        """
        Check whether a key exists.
        """
        return self.backend(backend).exists(key)

    def get(
        self,
        key: str,
        *,
        backend: str | None = None,
    ) -> Any:
        """
        Retrieve a value.
        """
        return self.backend(backend).get(key)

    def set(
        self,
        key: str,
        value: Any,
        *,
        backend: str | None = None,
    ) -> None:
        """
        Store a value.
        """
        self.backend(backend).set(
            key,
            value,
        )

    def delete(
        self,
        key: str,
        *,
        backend: str | None = None,
    ) -> None:
        """
        Delete a key.
        """
        self.backend(backend).delete(key)

    def clear(
        self,
        *,
        backend: str | None = None,
    ) -> None:
        """
        Remove all keys.
        """
        self.backend(backend).clear()

    def keys(
        self,
        *,
        backend: str | None = None,
    ) -> list[str]:
        """
        Return all keys.
        """
        return self.backend(backend).keys()

    def registered_backends(self) -> list[str]:
        """
        Return registered backend names.
        """
        with self._lock:
            return sorted(self._backends.keys())

    def close(self) -> None:
        """
        Close all registered backends.
        """
        with self._lock:
            for backend in self._backends.values():
                backend.close()

            self._backends.clear()
            self._default_backend = None