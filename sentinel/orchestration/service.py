"""
Public service interface for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sentinel.capabilities.manager import CapabilityManager
from sentinel.memory.service import MemoryService
from sentinel.orchestration.manager import OrchestrationManager
from sentinel.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
)
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class OrchestrationService:
    """
    Public service interface for Sentinel orchestration.
    """

    def __init__(
        self,
        manager: OrchestrationManager | None = None,
        handler: Callable[[OrchestrationRequest], Any] | None = None,
        capabilities: CapabilityManager | None = None,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
        memory: MemoryService | None = None,
    ) -> None:
        self._manager = (
            manager
            if manager is not None
            else OrchestrationManager(
                handler=handler,
                capabilities=capabilities,
                security=security,
                identity=identity,
                memory=memory,
            )
        )

    @property
    def manager(self) -> OrchestrationManager:
        """Return the underlying orchestration manager."""
        return self._manager

    @property
    def capabilities(self) -> CapabilityManager:
        """Return the capability manager."""
        return self._manager.capabilities

    @property
    def security(self) -> SecurityManager:
        """Return the Security manager."""
        return self._manager.security

    @property
    def identity(self) -> SecurityIdentity | None:
        """Return the identity used for authorization."""
        return self._manager.identity

    @property
    def memory(self) -> MemoryService:
        """Return the Memory service."""
        return self._manager.memory

    def execute(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """Execute an orchestration request."""
        return self._manager.execute(request)

    def can_execute(
        self,
        request: OrchestrationRequest,
    ) -> bool:
        """Return whether a request can be executed."""
        return self._manager.can_execute(request)