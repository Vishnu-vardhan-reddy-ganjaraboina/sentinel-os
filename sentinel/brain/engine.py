"""
Engine implementation for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from threading import RLock
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
        self._state_lock = RLock()
        self._execution_lock = RLock()

    @property
    def planner(self) -> BrainPlanner:
        return self._planner

    @property
    def state(self) -> BrainState:
        with self._state_lock:
            return self._state

    @state.setter
    def state(self, value: BrainState) -> None:
        if not isinstance(value, BrainState):
            raise TypeError("state must be a BrainState.")
        with self._state_lock:
            self._state = value

    def execute(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any]:
        """
        Build and complete a Brain plan.

        Brain is responsible for planning, not capability execution.
        Concurrent executions are serialized to protect engine state.
        """
        if not isinstance(context, Context):
            raise TypeError("context must implement the Context interface.")

        with self._execution_lock:
            self.state = BrainState.THINKING

            try:
                plan = self._planner.create_plan(
                    request=request,
                    context=context,
                )

                self.state = BrainState.PLANNING

                plan = self._planner.mark_ready(plan)

                self.state = BrainState.EXECUTING

                completed_plan = self._planner.mark_completed(plan)

                result = {
                    "request": request,
                    "plan": completed_plan,
                    "context": context.to_dict(),
                    "success": True,
                }

                self.state = BrainState.COMPLETED

                return result

            except Exception:
                self.state = BrainState.FAILED
                raise
