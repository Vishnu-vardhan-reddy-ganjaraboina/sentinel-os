"""
Kernel runtime service for the Orchestration subsystem.
"""

from __future__ import annotations

from sentinel.capabilities.manager import CapabilityManager
from sentinel.kernel.service import Service
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.memory.service import MemoryService
from sentinel.orchestration.service import OrchestrationService
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class OrchestrationRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for OrchestrationService.
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
        super().__init__("orchestration")

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