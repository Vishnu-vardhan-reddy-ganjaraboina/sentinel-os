"""
Concrete models for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.orchestration.interfaces import (
    OrchestrationRequest as OrchestrationRequestInterface,
)
from sentinel.orchestration.interfaces import (
    OrchestrationResult as OrchestrationResultInterface,
)


class OrchestrationRequest(OrchestrationRequestInterface):
    """Concrete orchestration request."""

    def __init__(
        self,
        request_id: str,
        input: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._request_id = request_id
        self._input = input
        self._context = (
            {} if context is None else dict(context)
        )

    @property
    def id(self) -> str:
        """Return the unique request identifier."""
        return self._request_id

    @property
    def input(self) -> Any:
        """Return the original request input."""
        return self._input

    @property
    def context(self) -> dict[str, Any]:
        """Return request context."""
        return self._context


class OrchestrationResult(OrchestrationResultInterface):
    """Concrete orchestration result."""

    def __init__(
        self,
        request_id: str,
        success: bool,
        data: Any = None,
        error: str | None = None,
    ) -> None:
        self._request_id = request_id
        self._success = success
        self._data = data
        self._error = error

    @property
    def request_id(self) -> str:
        """Return the originating request identifier."""
        return self._request_id

    @property
    def success(self) -> bool:
        """Return whether orchestration succeeded."""
        return self._success

    @property
    def data(self) -> Any:
        """Return the resulting data."""
        return self._data

    @property
    def error(self) -> str | None:
        """Return the error message, if any."""
        return self._error

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result."""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }