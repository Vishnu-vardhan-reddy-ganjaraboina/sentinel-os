"""
Manager for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.brain.constants import BrainState
from sentinel.brain.context import BrainContext
from sentinel.brain.engine import BrainEngine


class BrainManager:
    """
    High-level manager for Brain operations.
    """

    def __init__(self) -> None:
        self._engine = BrainEngine()

    @property
    def engine(self) -> BrainEngine:
        return self._engine

    def execute(
        self,
        request: Any,
        context: BrainContext,
    ) -> dict[str, Any]:
        """
        Execute a request using the Brain engine.
        """
        return self._engine.execute(request, context)

    def create_context(
        self,
        context_id: str,
        **kwargs: Any,
    ) -> BrainContext:
        """
        Create a new Brain context.
        """
        return BrainContext(
            context_id=context_id,
            data=kwargs,
        )

    def state(self) -> BrainState:
        """
        Return the current engine state.
        """
        return self._engine.state