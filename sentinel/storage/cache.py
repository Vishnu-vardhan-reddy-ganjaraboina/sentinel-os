"""
Thread-safe LRU cache for Sentinel OS.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from threading import RLock


class LRUCache[K, V]:
    """
    Thread-safe Least Recently Used (LRU) cache.

    Mutable values are defensively copied on insertion and retrieval
    so callers cannot mutate cache state accidentally.
    """

    def __init__(self, capacity: int = 1024) -> None:
        if not isinstance(capacity, int):
            raise TypeError(
                "Cache capacity must be an integer."
            )

        if capacity <= 0:
            raise ValueError(
                "Cache capacity must be positive."
            )

        self._capacity = capacity
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._lock = RLock()

    @property
    def capacity(self) -> int:
        """Return the configured cache capacity."""
        return self._capacity

    def get(
        self,
        key: K,
    ) -> V | None:
        """
        Retrieve a cached value and mark it as recently used.
        """
        with self._lock:
            if key not in self._cache:
                return None

            self._cache.move_to_end(key)

            return deepcopy(self._cache[key])

    def put(
        self,
        key: K,
        value: V,
    ) -> None:
        """
        Insert or update a cache entry.
        """
        copied_value = deepcopy(value)

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = copied_value

            if len(self._cache) > self._capacity:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """
        Remove all cache entries.
        """
        with self._lock:
            self._cache.clear()

    def __contains__(
        self,
        key: K,
    ) -> bool:
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)
