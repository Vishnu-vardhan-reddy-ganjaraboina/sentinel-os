"""
SQLite-compatible persistent memory store.

The store uses Sentinel's StorageBackend abstraction and JSON-compatible
records. It deliberately does not use pickle or deserialize executable data.
"""

from __future__ import annotations

import builtins
import json
from collections.abc import Iterator
from threading import RLock
from typing import Any

from sentinel.memory.entry import BaseMemoryEntry
from sentinel.memory.exceptions import (
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from sentinel.memory.interfaces import Memory, MemoryEntry
from sentinel.storage.exceptions import StorageKeyNotFoundError
from sentinel.storage.interfaces import StorageBackend


class PersistentMemoryStore(Memory):
    """Persist memory entries through an injected StorageBackend."""

    _KEY_PREFIX = "sentinel:memory:entry:"

    def __init__(self, backend: StorageBackend) -> None:
        self._backend = backend
        self._lock = RLock()

    def connect(self) -> None:
        """Reconnect the backing storage backend after a runtime restart."""
        self._backend.connect()

    def close(self) -> None:
        """Close the backing storage backend."""
        self._backend.close()

    @property
    def backend(self) -> StorageBackend:
        """Return the injected backend without taking ownership of its lifecycle."""
        return self._backend

    def add(self, entry: MemoryEntry) -> None:
        """Persist a new entry, rejecting duplicate IDs atomically."""
        key = self._key(entry.id)
        payload = self._serialize(entry)
        with self._lock, self._backend.atomic():
            if self._backend.exists(key):
                raise MemoryAlreadyExistsError(
                    f"Memory '{entry.id}' already exists."
                )
            self._backend.set(key, payload)

    def upsert(self, entry: MemoryEntry) -> None:
        """Insert or replace an entry atomically."""
        key = self._key(entry.id)
        payload = self._serialize(entry)
        with self._lock, self._backend.atomic():
            self._backend.set(key, payload)

    def get(self, memory_id: str) -> MemoryEntry:
        """Load an entry, preserving its original timestamps and expiry."""
        key = self._key(memory_id)
        with self._lock, self._backend.atomic():
            try:
                payload = self._backend.get(key)
            except StorageKeyNotFoundError as exc:
                raise MemoryNotFoundError(
                    f"Memory '{memory_id}' was not found."
                ) from exc
            entry = self._deserialize(memory_id, payload)
            if not entry.expired:
                entry.touch()
                self._backend.set(key, self._serialize(entry))
            return entry

    def remove(self, memory_id: str) -> None:
        """Permanently remove an entry."""
        key = self._key(memory_id)
        with self._lock, self._backend.atomic():
            try:
                self._backend.delete(key)
            except StorageKeyNotFoundError as exc:
                raise MemoryNotFoundError(
                    f"Memory '{memory_id}' was not found."
                ) from exc

    def exists(self, memory_id: str) -> bool:
        """Return whether an entry exists."""
        with self._lock:
            return self._backend.exists(self._key(memory_id))

    def search(self, keyword: str) -> builtins.list[MemoryEntry]:
        """Search persisted entries by case-insensitive content text."""
        normalized = keyword.strip().lower()
        if not normalized:
            return []
        matches: builtins.list[MemoryEntry] = []
        for entry in self.list():
            if normalized in str(entry.content).lower():
                matches.append(entry)
                # Reading content updates last_accessed; persist that timestamp.
                self.upsert(entry)
        return matches

    def clear(self) -> None:
        """Remove only memory records owned by this store."""
        with self._lock, self._backend.atomic():
            for key in self._keys():
                self._backend.delete(key)

    def list(self) -> builtins.list[MemoryEntry]:
        """Load all entries in deterministic key order."""
        with self._lock:
            return [
                self._load_key(key)
                for key in self._keys()
            ]

    def __iter__(self) -> Iterator[MemoryEntry]:
        """Iterate over a stable snapshot."""
        return iter(self.list())

    def __contains__(self, memory_id: object) -> bool:
        return isinstance(memory_id, str) and self.exists(memory_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._keys())

    def _key(self, memory_id: str) -> str:
        if not isinstance(memory_id, str) or not memory_id.strip():
            raise ValueError("memory_id must be a non-empty string.")
        return f"{self._KEY_PREFIX}{memory_id}"

    def _keys(self) -> builtins.list[str]:
        return sorted(
            key for key in self._backend.keys()
            if key.startswith(self._KEY_PREFIX)
        )

    def _load_key(self, key: str) -> MemoryEntry:
        memory_id = key.removeprefix(self._KEY_PREFIX)
        try:
            payload = self._backend.get(key)
        except StorageKeyNotFoundError as exc:
            raise MemoryNotFoundError(
                f"Memory '{memory_id}' was not found."
            ) from exc
        return self._deserialize(memory_id, payload)

    @staticmethod
    def _serialize(entry: MemoryEntry) -> str:
        if not isinstance(entry, MemoryEntry):
            raise TypeError("entry must implement MemoryEntry.")
        payload: Any = entry.to_dict()
        try:
            return json.dumps(payload, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "Persistent memory content must be JSON-serializable."
            ) from exc

    @staticmethod
    def _deserialize(memory_id: str, payload: Any) -> BaseMemoryEntry:
        if not isinstance(payload, str):
            raise ValueError(f"Stored memory '{memory_id}' is not text.")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Stored memory '{memory_id}' contains invalid JSON."
            ) from exc
        if not isinstance(data, dict) or data.get("id") != memory_id:
            raise ValueError(f"Stored memory '{memory_id}' has an invalid record.")
        return BaseMemoryEntry.from_dict(data)
