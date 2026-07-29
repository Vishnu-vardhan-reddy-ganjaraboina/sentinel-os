"""
Base implementation of a Sentinel workflow.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from sentinel.automation.constants import WorkflowStatus
from sentinel.automation.exceptions import (
    WorkflowDisabledError,
)
from sentinel.automation.interfaces import Workflow


class BaseWorkflow(Workflow):
    """
    Base implementation for Sentinel workflows.

    Concrete workflows should inherit from this class and implement
    the `run()` method.
    """

    def __init__(
        self,
        workflow_id: str,
        name: str,
        enabled: bool = True,
    ) -> None:
        if not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty.")

        if not name.strip():
            raise ValueError("name cannot be empty.")

        self._id = workflow_id
        self._name = name
        self._enabled = enabled
        self._status = WorkflowStatus.IDLE

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def status(self) -> WorkflowStatus:
        """
        Current workflow status.
        """
        return self._status

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the workflow.
        """
        if not self.enabled:
            self._status = WorkflowStatus.DISABLED
            raise WorkflowDisabledError(
                f"Workflow '{self.id}' is disabled."
            )

        self._status = WorkflowStatus.RUNNING

        try:
            result = self.run(**kwargs)
            self._status = WorkflowStatus.COMPLETED
            return result

        except Exception:
            self._status = WorkflowStatus.FAILED
            raise

    @abstractmethod
    def run(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the concrete workflow.
        """