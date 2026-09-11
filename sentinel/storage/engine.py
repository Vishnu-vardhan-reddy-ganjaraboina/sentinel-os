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
        self._closed = False

    def register(
        self,
        name: str,
        backend: StorageBackend,
    ) -> None:
        """
        Register a storage backend.

        Raises:
            TypeError:
                If the backend name or backend type is invalid.

            ValueError:
                If the backend name is empty.

            StorageBackendError:
                If the engine is closed or the backend name is duplicated.
        """
        self._validate_name(name)

        if not isinstance(backend, StorageBackend):
            raise TypeError(
                "backend must implement StorageBackend"
            )

        with self._lock:
            self._ensure_open()

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
        Remove a storage backend and close it.

        Raises:
            StorageBackendError:
                If the backend does not exist or the engine is closed.
        """
        self._validate_name(name)

        with self._lock:
            self._ensure_open()

            try:
                backend = self._backends.pop(name)
            except KeyError as exc:
                raise StorageBackendError(
                    f"Unknown backend '{name}'."
                ) from exc

            if self._default_backend == name:
                self._default_backend = next(
                    iter(self._backends),
                    None,
                )

        # Close outside the engine lock so backend cleanup cannot block
        # or re-enter the engine while the registry is locked.
        try:
            backend.close()
        except Exception as exc:
            raise StorageBackendError(
                f"Failed to close backend '{name}'."
            ) from exc

    def set_default(
        self,
        name: str,
    ) -> None:
        """
        Select the default backend.
        """
        self._validate_name(name)

        with self._lock:
            self._ensure_open()

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
        if name is not None:
            self._validate_name(name)

        with self._lock:
            self._ensure_open()

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
        self.backend(backend).set(key, value)

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
            return sorted(self._backends)

    def close(self) -> None:
        """
        Close all registered backends.

        Closing is idempotent.
        """
        with self._lock:
            if self._closed:
                return

            backends = list(self._backends.values())
            self._backends.clear()
            self._default_backend = None
            self._closed = True

        errors: list[Exception] = []

        for backend in backends:
            try:
                backend.close()
            except Exception as exc:
                errors.append(exc)

        if errors:
            raise StorageBackendError(
                f"Failed to close {len(errors)} storage backend(s)."
            ) from errors[0]

    def _ensure_open(self) -> None:
        """Ensure the storage engine is available."""
        if self._closed:
            raise StorageBackendError(
                "Storage engine has been closed."
            )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate a backend name."""
        if not isinstance(name, str):
            raise TypeError(
                "Backend name must be a string."
            )

        if not name.strip():
            raise ValueError(
                "Backend name cannot be empty."
            )
