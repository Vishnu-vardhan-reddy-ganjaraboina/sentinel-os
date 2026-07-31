"""
Workflow manager for the Sentinel Automation subsystem.
"""

from __future__ import annotations

import builtins
from typing import Any

from sentinel.automation.exceptions import (
    WorkflowExecutionError,
)
from sentinel.automation.interfaces import Workflow
from sentinel.automation.registry import WorkflowRegistry


class WorkflowManager:
    """
    High-level manager for Sentinel workflows.
    """

    def __init__(self) -> None:
        self._registry = WorkflowRegistry()

    @property
    def registry(self) -> WorkflowRegistry:
        return self._registry

    def register(self, workflow: Workflow) -> None:
        self._registry.register(workflow)

    def unregister(self, workflow_id: str) -> None:
        self._registry.unregister(workflow_id)

    def get(self, workflow_id: str) -> Workflow:
        return self._registry.get(workflow_id)

    def exists(self, workflow_id: str) -> bool:
        return self._registry.exists(workflow_id)

    def list(self) -> builtins.list[Workflow]:
        return self._registry.list()

    def execute(self, workflow_id: str, **kwargs: Any) -> Any:
        """
        Execute a workflow by ID.
        """
        workflow = self._registry.get(workflow_id)

        try:
            return workflow.execute(**kwargs)
        except Exception as exc:
            if isinstance(exc, WorkflowExecutionError):
                raise

            raise WorkflowExecutionError(
                f"Workflow '{workflow_id}' execution failed."
            ) from exc

    def enable(self, workflow_id: str) -> None:
        self._registry.get(workflow_id).enable()

    def disable(self, workflow_id: str) -> None:
        self._registry.get(workflow_id).disable()

    def clear(self) -> None:
        self._registry.clear()