"""
Service layer for the Sentinel Automation subsystem.
"""

from __future__ import annotations

import builtins
from typing import Any

from sentinel.automation.interfaces import Workflow
from sentinel.automation.manager import WorkflowManager
from sentinel.automation.registry import WorkflowRegistry


class AutomationService:
    """
    Public service interface for workflow management.
    """

    def __init__(self) -> None:
        self._manager = WorkflowManager()

    @property
    def manager(self) -> WorkflowManager:
        return self._manager

    @property
    def registry(self) -> WorkflowRegistry:
        return self._manager.registry

    def register(self, workflow: Workflow) -> None:
        self._manager.register(workflow)

    def unregister(self, workflow_id: str) -> None:
        self._manager.unregister(workflow_id)

    def get(self, workflow_id: str) -> Workflow:
        return self._manager.get(workflow_id)

    def execute(self, workflow_id: str, **kwargs: Any) -> Any:
        return self._manager.execute(workflow_id, **kwargs)

    def enable(self, workflow_id: str) -> None:
        self._manager.enable(workflow_id)

    def disable(self, workflow_id: str) -> None:
        self._manager.disable(workflow_id)

    def exists(self, workflow_id: str) -> bool:
        return self._manager.exists(workflow_id)

    def list(self) -> builtins.list[Workflow]:
        return self._manager.list()

    def clear(self) -> None:
        self._manager.clear()