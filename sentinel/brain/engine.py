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

    Brain performs planning only. Capability execution belongs to downstream
    execution/capability subsystems.

    The public API exposes one engine-wide BrainState, so executions are
    serialized to keep that state internally consistent.
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

    def _set_state(self, state: BrainState) -> None:
        with self._state_lock:
            self._state = state

    def execute(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any]:
        """
        Build and complete a Brain plan.

        Brain does not execute capabilities.
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance.")

        with self._execution_lock:
            self._set_state(BrainState.THINKING)

            try:
                plan = self._planner.create_plan(
                    request=request,
                    context=context,
                )

                self._set_state(BrainState.PLANNING)

                plan = self._planner.mark_ready(plan)

                self._set_state(BrainState.EXECUTING)

                completed_plan = self._planner.mark_completed(plan)

                result = {
                    "request": request,
                    "plan": completed_plan,
                    "context": context.to_dict(),
                    "success": True,
                }

                self._set_state(BrainState.COMPLETED)
                return result

            except Exception:
                self._set_state(BrainState.FAILED)
                raise
