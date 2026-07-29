"""
Interfaces for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Context(ABC):
    """
    Abstract interface representing the execution context.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique context identifier.
        """

    @property
    @abstractmethod
    def data(self) -> dict[str, Any]:
        """
        Context data.
        """

    @abstractmethod
    def update(self, **kwargs: Any) -> None:
        """
        Update context values.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the context.
        """


class Planner(ABC):
    """
    Abstract interface representing a planner.
    """

    @abstractmethod
    def create_plan(
        self,
        request: Any,
        context: Context,
    ) -> Any:
        """
        Produce an execution plan.
        """


class Engine(ABC):
    """
    Abstract interface representing the brain engine.
    """

    @abstractmethod
    def execute(
        self,
        request: Any,
        context: Context,
    ) -> Any:
        """
        Execute a request.
        """