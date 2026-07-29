"""
Interfaces for the Sentinel Automation subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Trigger(ABC):
    """
    Abstract interface for workflow triggers.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique trigger identifier.
        """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        Whether the trigger is enabled.
        """

    @abstractmethod
    def enable(self) -> None:
        """
        Enable the trigger.
        """

    @abstractmethod
    def disable(self) -> None:
        """
        Disable the trigger.
        """

    @abstractmethod
    def evaluate(self, **kwargs: Any) -> bool:
        """
        Evaluate whether the trigger should fire.
        """


class Workflow(ABC):
    """
    Abstract interface for Sentinel workflows.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique workflow identifier.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Workflow name.
        """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        Whether the workflow is enabled.
        """

    @abstractmethod
    def enable(self) -> None:
        """
        Enable the workflow.
        """

    @abstractmethod
    def disable(self) -> None:
        """
        Disable the workflow.
        """

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the workflow.
        """