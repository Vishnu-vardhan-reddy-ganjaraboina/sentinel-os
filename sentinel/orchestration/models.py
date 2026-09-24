"""
Concrete models for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sentinel.brain.intent import Intent
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
        intent: Intent | None = None,
    ) -> None:
        if not isinstance(request_id, str):
            raise TypeError("request_id must be a string.")

        if intent is not None and not isinstance(intent, Intent):
            raise TypeError(
                "intent must be an Intent instance or None."
            )

        self._request_id = request_id
        self._input = deepcopy(input)
        self._context = (
            {}
            if context is None
            else deepcopy(context)
        )
        self._intent = deepcopy(intent)

    @property
    def id(self) -> str:
        """Return the unique request identifier."""
        return self._request_id

    @property
    def input(self) -> Any:
        """Return an isolated copy of the original input."""
        return deepcopy(self._input)

    @property
    def context(self) -> dict[str, Any]:
        """Return an isolated copy of the request context."""
        return deepcopy(self._context)

    @property
    def intent(self) -> Intent | None:
        """Return an isolated copy of the structured intent."""
        return deepcopy(self._intent)


class OrchestrationResult(OrchestrationResultInterface):
    """Concrete orchestration result."""

    def __init__(
        self,
        request_id: str,
        success: bool,
        data: Any = None,
        error: str | None = None,
    ) -> None:
        if not isinstance(request_id, str):
            raise TypeError("request_id must be a string.")

        if not isinstance(success, bool):
            raise TypeError("success must be a boolean.")

        if error is not None and not isinstance(error, str):
            raise TypeError("error must be a string or None.")

        self._request_id = request_id
        self._success = success
        self._data = deepcopy(data)
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
        """Return an isolated copy of the resulting data."""
        return deepcopy(self._data)

    @property
    def error(self) -> str | None:
        """Return the error message, if any."""
        return self._error

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result without exposing mutable internals."""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "data": deepcopy(self._data),
            "error": self.error,
        }