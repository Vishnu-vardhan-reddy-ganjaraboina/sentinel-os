"""
Concrete implementation of the Sentinel Brain context.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sentinel.brain.interfaces import Context


class BrainContext(Context):
    """
    Represents the execution context for the Brain.

    Context data is protected from accidental external mutation.
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
        Return an isolated copy of the context data.
        """
        return deepcopy(self._data)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update(self, **kwargs: Any) -> None:
        """
        Update context values using isolated copies.
        """
        self._data.update(deepcopy(kwargs))
        self._updated_at = datetime.now(UTC)

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve an isolated copy of a context value.
        """
        return deepcopy(
            self._data.get(
                key,
                default,
            )
        )

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
            "data": deepcopy(self._data),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }