"""Authenticated encryption adapter for Sentinel storage values.

Key material is injected by the application and is never stored in the database.
Storage key names remain visible; applications should use opaque identifiers.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from sentinel.storage.interfaces import StorageBackend


class EncryptedStorageBackend(StorageBackend):
    """Encrypt string values using Fernet before delegating to a backend."""

    _FORMAT = "sentinel-fernet:v1:"

    def __init__(self, backend: StorageBackend, key: bytes | str) -> None:
        if not isinstance(backend, StorageBackend):
            raise TypeError("backend must implement StorageBackend")
        if isinstance(key, str):
            key = key.encode("ascii")
        if not isinstance(key, bytes):
            raise TypeError("key must be bytes or a Fernet key string")
        try:
            self._fernet = Fernet(key)
        except (ValueError, TypeError) as exc:
            raise ValueError("key must be a valid URL-safe Fernet key") from exc
        self._backend = backend

    @staticmethod
    def generate_key() -> bytes:
        return Fernet.generate_key()

    @property
    def backend(self) -> StorageBackend:
        return self._backend

    def connect(self) -> None:
        self._backend.connect()

    def disconnect(self) -> None:
        self._backend.disconnect()

    def close(self) -> None:
        self.disconnect()

    @contextmanager
    def atomic(self) -> Iterator[None]:
        with self._backend.atomic():
            yield

    def exists(self, key: str) -> bool:
        return self._backend.exists(key)

    def get(self, key: str) -> Any:
        encrypted = self._backend.get(key)
        if not isinstance(encrypted, str) or not encrypted.startswith(self._FORMAT):
            raise ValueError(f"Storage value for {key!r} is not encrypted v1 data")
        try:
            token = encrypted[len(self._FORMAT) :].encode("ascii")
            return self._fernet.decrypt(token).decode("utf-8")
        except (InvalidToken, UnicodeError, ValueError) as exc:
            raise ValueError(
                f"Encrypted storage value for {key!r} failed authentication"
            ) from exc

    def set(self, key: str, value: Any) -> None:
        if not isinstance(value, str):
            raise TypeError("EncryptedStorageBackend accepts string values only")
        token = self._fernet.encrypt(value.encode("utf-8")).decode("ascii")
        self._backend.set(key, self._FORMAT + token)

    def delete(self, key: str) -> None:
        self._backend.delete(key)

    def clear(self) -> None:
        self._backend.clear()

    def keys(self) -> list[str]:
        return self._backend.keys()

    def rotate_key(self, new_key: bytes | str) -> None:
        replacement = Fernet(
            new_key.encode("ascii") if isinstance(new_key, str) else new_key
        )
        with self._backend.atomic():
            converted: dict[str, str] = {}
            for name in self._backend.keys():
                raw = self._backend.get(name)
                if not isinstance(raw, str) or not raw.startswith(self._FORMAT):
                    raise ValueError(f"Cannot rotate unencrypted value {name!r}")
                plain = self._fernet.decrypt(raw[len(self._FORMAT) :].encode("ascii"))
                converted[name] = self._FORMAT + replacement.encrypt(plain).decode(
                    "ascii"
                )
            for name, value in converted.items():
                self._backend.set(name, value)
        self._fernet = replacement
