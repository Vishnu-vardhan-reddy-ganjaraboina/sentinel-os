"""
Planner implementation for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.brain.constants import PlanStatus
from sentinel.brain.interfaces import Context, Planner


class BrainPlanner(Planner):
    """
    Default planner implementation.
    """

    def create_plan(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any]:
        """
        Create an execution plan.

        A capability can be supplied through the execution context
        using the ``capability_id`` key. Additional capability
        arguments can be supplied through ``capability_arguments``.
        """
        capability_id = context.data.get("capability_id")
        capability_arguments = context.data.get(
            "capability_arguments",
            {},
        )

        step: dict[str, Any] = {
            "step": 1,
            "action": "execute",
            "completed": False,
        }

        if capability_id is not None:
            step["capability_id"] = capability_id
            step["arguments"] = (
                capability_arguments.copy()
                if isinstance(capability_arguments, dict)
                else {}
            )

        return {
            "request": request,
            "context_id": context.id,
            "context": context.data.copy(),
            "status": PlanStatus.CREATED,
            "steps": [step],
        }

    def mark_ready(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Mark a plan as ready.
        """
        plan["status"] = PlanStatus.READY
        return plan

    def mark_completed(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Mark a plan as completed.
        """
        plan["status"] = PlanStatus.COMPLETED

        for step in plan["steps"]:
            step["completed"] = True

        return plan