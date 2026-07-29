"""
Service layer for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.brain.context import BrainContext
from sentinel.brain.manager import BrainManager


class BrainService:
    """
    Public service interface for the Brain subsystem.
    """

    def __init__(self) -> None:
        self._manager = BrainManager()

    @property
    def manager(self) -> BrainManager:
        """
        Return the underlying manager.
        """
        return self._manager

    def create_context(
        self,
        context_id: str,
        **kwargs: Any,
    ) -> BrainContext:
        """
        Create a new execution context.
        """
        return self._manager.create_context(
            context_id=context_id,
            **kwargs,
        )

    def execute(
        self,
        request: Any,
        context: BrainContext,
    ) -> dict[str, Any]:
        """
        Execute a request.
        """
        return self._manager.execute(
            request=request,
            context=context,
        )

    def state(self):
        """
        Return the current Brain state.
        """
        return self._manager.state()