"""
Kernel runtime service for the Orchestration subsystem.
"""

from __future__ import annotations

from sentinel.capabilities.manager import CapabilityManager
from sentinel.kernel.service import Service
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
)
from sentinel.orchestration.service import OrchestrationService
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class OrchestrationRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for OrchestrationService.

    The runtime service exposes the Orchestration subsystem API
    directly while retaining Kernel lifecycle management.
    """

    def __init__(
        self,
        orchestration: OrchestrationService | None = None,
        *,
        capabilities: CapabilityManager | None = None,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
        memory: MemoryService | None = None,
        knowledge: KnowledgeService | None = None,
    ) -> None:
        super().__init__(
            "orchestration",
            dependencies=("memory", "knowledge"),
        )

        self._orchestration = (
            orchestration
            if orchestration is not None
            else OrchestrationService(
                capabilities=capabilities,
                security=security,
                identity=identity,
                memory=memory,
                knowledge=knowledge,
            )
        )

        self._initialized = False
        self._shutdown = False

    @property
    def orchestration(self) -> OrchestrationService:
        """Return the underlying orchestration service."""
        return self._orchestration

    @property
    def capabilities(self) -> CapabilityManager:
        """Return the capability manager."""
        return self._orchestration.capabilities

    @property
    def security(self) -> SecurityManager:
        """Return the security manager."""
        return self._orchestration.security

    @property
    def identity(self) -> SecurityIdentity | None:
        """Return the identity used for authorization."""
        return self._orchestration.identity

    @property
    def memory(self) -> MemoryService:
        """Return the shared Memory service."""
        return self._orchestration.memory

    @property
    def knowledge(self) -> KnowledgeService | None:
        """Return the shared Knowledge service."""
        return self._orchestration.knowledge

    def execute(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """
        Execute an orchestration request.

        Delegates directly to the underlying OrchestrationService.
        """
        return self._orchestration.execute(request)

    def can_execute(
        self,
        request: OrchestrationRequest,
    ) -> bool:
        """
        Return whether an orchestration request can be executed.

        Delegates directly to the underlying OrchestrationService.
        """
        return self._orchestration.can_execute(request)

    def initialize(self) -> None:
        """
        Initialize orchestration resources.
        """
        if self._shutdown:
            raise RuntimeError(
                "Orchestration runtime has already been shut down."
            )

        if self._initialized:
            return

        self._initialized = True

    def shutdown(self) -> None:
        """
        Shut down orchestration resources.

        Shutdown is idempotent because the current service owns
        no external resources.
        """
        if self._shutdown:
            return

        self._initialized = False
        self._shutdown = True

    def health(self) -> dict[str, bool]:
        """Return orchestration service health information."""
        return {
            "healthy": (
                self._initialized
                and not self._shutdown
            ),
        }