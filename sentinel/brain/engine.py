"""
Engine implementation for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.brain.constants import BrainState
from sentinel.brain.interfaces import Context, Engine
from sentinel.brain.planner import BrainPlanner


class BrainEngine(Engine):
    """
    Default Brain engine implementation.
    """

    def __init__(self) -> None:
        self._planner = BrainPlanner()
        self._state = BrainState.IDLE

    @property
    def planner(self) -> BrainPlanner:
        return self._planner

    @property
    def state(self) -> BrainState:
        return self._state

    def execute(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any]:
        """
        Execute a request using the planner.
        """
        self._state = BrainState.THINKING

        plan = self._planner.create_plan(
            request=request,
            context=context,
        )

        self._state = BrainState.PLANNING

        self._planner.mark_ready(plan)

        self._state = BrainState.EXECUTING

        result = {
            "request": request,
            "plan": self._planner.mark_completed(plan),
            "context": context.to_dict(),
            "success": True,
        }

        self._state = BrainState.COMPLETED

        return result