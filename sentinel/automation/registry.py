"""
Workflow registry for the Sentinel Automation subsystem.
"""

from __future__ import annotations

from threading import RLock
from typing import Dict, Iterator, List

from sentinel.automation.exceptions import (
    WorkflowAlreadyExistsError,
    WorkflowNotFoundError,
)
from sentinel.automation.interfaces import Workflow


class WorkflowRegistry:
    """
    Thread-safe registry for workflows.
    """

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}
        self._lock = RLock()

    def register(self, workflow: Workflow) -> None:
        with self._lock:
            if workflow.id in self._workflows:
                raise WorkflowAlreadyExistsError(
                    f"Workflow '{workflow.id}' already exists."
                )

            self._workflows[workflow.id] = workflow

    def unregister(self, workflow_id: str) -> None:
        with self._lock:
            if workflow_id not in self._workflows:
                raise WorkflowNotFoundError(
                    f"Workflow '{workflow_id}' not found."
                )

            del self._workflows[workflow_id]

    def get(self, workflow_id: str) -> Workflow:
        with self._lock:
            if workflow_id not in self._workflows:
                raise WorkflowNotFoundError(
                    f"Workflow '{workflow_id}' not found."
                )

            return self._workflows[workflow_id]

    def exists(self, workflow_id: str) -> bool:
        with self._lock:
            return workflow_id in self._workflows

    def list(self) -> List[Workflow]:
        with self._lock:
            return list(self._workflows.values())

    def list_enabled(self) -> List[Workflow]:
        with self._lock:
            return [
                workflow
                for workflow in self._workflows.values()
                if workflow.enabled
            ]

    def list_disabled(self) -> List[Workflow]:
        with self._lock:
            return [
                workflow
                for workflow in self._workflows.values()
                if not workflow.enabled
            ]

    def clear(self) -> None:
        with self._lock:
            self._workflows.clear()

    def __contains__(self, workflow_id: str) -> bool:
        return self.exists(workflow_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._workflows)

    def __iter__(self) -> Iterator[Workflow]:
        return iter(self.list())