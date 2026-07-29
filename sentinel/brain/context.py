"""
Concrete implementation of the Sentinel Brain context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sentinel.brain.interfaces import Context


class BrainContext(Context):
    """
    Represents the execution context for the Brain.
    """

    def __init__(
        self,
        context_id: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        if not context_id.strip():
            raise ValueError("context_id cannot be empty.")

        self._id = context_id
        self._data: dict[str, Any] = data.copy() if data else {}

        self._created_at = datetime.now(UTC)
        self._updated_at = self._created_at

    @property
    def id(self) -> str:
        return self._id

    @property
    def data(self) -> dict[str, Any]:
        return self._data

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update(self, **kwargs: Any) -> None:
        """
        Update context values.
        """
        self._data.update(kwargs)
        self._updated_at = datetime.now(UTC)

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a context value.
        """
        return self._data.get(key, default)

    def clear(self) -> None:
        """
        Remove all context values.
        """
        self._data.clear()
        self._updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the context.
        """
        return {
            "id": self.id,
            "data": self.data.copy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }