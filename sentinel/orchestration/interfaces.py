"""
Interfaces for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OrchestrationRequest(ABC):
    """
    Abstract request submitted to the orchestration layer.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Return the unique request identifier."""

    @property
    @abstractmethod
    def input(self) -> Any:
        """Return the original request input."""

    @property
    @abstractmethod
    def context(self) -> dict[str, Any]:
        """Return request context."""


class OrchestrationResult(ABC):
    """
    Abstract result produced by orchestration.
    """

    @property
    @abstractmethod
    def request_id(self) -> str:
        """Return the originating request identifier."""

    @property
    @abstractmethod
    def success(self) -> bool:
        """Return whether orchestration succeeded."""

    @property
    @abstractmethod
    def data(self) -> Any:
        """Return the resulting data."""

    @property
    @abstractmethod
    def error(self) -> str | None:
        """Return the error message, if any."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the result."""


class Orchestrator(ABC):
    """
    Coordinates the Sentinel execution pipeline.
    """

    @abstractmethod
    def execute(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """
        Execute an orchestration request.
        """

    @abstractmethod
    def can_execute(
        self,
        request: OrchestrationRequest,
    ) -> bool:
        """
        Return whether the request can be executed.
        """