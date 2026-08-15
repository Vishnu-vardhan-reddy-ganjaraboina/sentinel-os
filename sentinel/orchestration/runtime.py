"""
Kernel runtime service for the Orchestration subsystem.
"""

from __future__ import annotations

from sentinel.kernel.service import Service
from sentinel.orchestration.service import OrchestrationService


class OrchestrationRuntimeService(Service):
    """
    Kernel-managed runtime wrapper for OrchestrationService.
    """

    def __init__(
        self,
        orchestration: OrchestrationService | None = None,
    ) -> None:
        super().__init__("orchestration")

        self._orchestration = (
            orchestration
            if orchestration is not None
            else OrchestrationService()
        )

    @property
    def orchestration(self) -> OrchestrationService:
        """Return the underlying orchestration service."""
        return self._orchestration

    def initialize(self) -> None:
        """
        Initialize orchestration resources.

        OrchestrationService creates its resources during
        construction, so no additional initialization is required.
        """

    def shutdown(self) -> None:
        """
        Shut down orchestration resources.

        OrchestrationService currently owns no external resources,
        so there is nothing to release at shutdown.
        """

    def health(self) -> dict[str, bool]:
        """Return orchestration service health information."""
        return {
            "healthy": True,
        }