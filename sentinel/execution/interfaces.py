"""
Interfaces for the Execution subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class Executor(ABC):
    """
    Abstract base class for task executors.

    An Executor is responsible for accepting work,
    executing it, and managing its lifecycle.
    """

    @abstractmethod
    def submit(
        self,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Submit a task for execution.

        Returns
        -------
        str
            Unique task identifier.
        """

    @abstractmethod
    def execute(
        self,
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a task immediately and return its result.
        """

    @abstractmethod
    def cancel(
        self,
        task_id: str,
    ) -> bool:
        """
        Cancel a submitted task.

        Returns
        -------
        bool
            True if the task was cancelled.
        """

    @abstractmethod
    def is_running(
        self,
        task_id: str,
    ) -> bool:
        """
        Return whether a task is currently running.
        """

    @abstractmethod
    def shutdown(self) -> None:
        """
        Shut down the executor and release resources.
        """