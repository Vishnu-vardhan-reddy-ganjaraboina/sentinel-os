"""
Concrete implementation of the Sentinel Brain context.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from sentinel.brain.interfaces import Context


class BrainContext(Context):
    """
    Thread-safe execution context for the Brain subsystem.

    Context data is isolated from callers through defensive deep copies.
    """

    def __init__(
        self,
        context_id: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(context_id, str):
            raise TypeError("context_id must be a string.")

        if not context_id.strip():
            raise ValueError("context_id cannot be empty.")

        if data is not None and not isinstance(data, dict):
            raise TypeError("data must be a dictionary.")

        self._lock = RLock()
        self._id = context_id
        self._data: dict[str, Any] = (
            deepcopy(data) if data is not None else {}
        )

        self._created_at = datetime.now(UTC)
        self._updated_at = self._created_at

    @property
    def id(self) -> str:
        return self._id

    @property
    def data(self) -> dict[str, Any]:
        """
        Return a completely isolated snapshot of the context.
        """
        with self._lock:
            return deepcopy(self._data)

    @property
    def created_at(self) -> datetime:
        with self._lock:
            return self._created_at

    @property
    def updated_at(self) -> datetime:
        with self._lock:
            return self._updated_at

    def update(self, **kwargs: Any) -> None:
        """
        Atomically update context values.

        Values are deep-copied before entering the context so callers cannot
        mutate stored state through shared references.
        """
        copied_values = deepcopy(kwargs)

        with self._lock:
            self._data.update(copied_values)
            self._updated_at = datetime.now(UTC)

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve an isolated copy of a context value."""
        with self._lock:
            value = self._data.get(key, default)
            return deepcopy(value)

    def clear(self) -> None:
        """
        Atomically remove all context values.
        """
        with self._lock:
            self._data.clear()
            self._updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize an isolated context snapshot.
        """
        with self._lock:
            return {
                "id": self._id,
                "data": deepcopy(self._data),
                "created_at": self._created_at.isoformat(),
                "updated_at": self._updated_at.isoformat(),
            }
