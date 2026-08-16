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

    The planner is deliberately deterministic. It does not execute
    capabilities or infer arbitrary actions from contextual data.

    Context supplied by Memory and Knowledge is preserved in the plan
    and summarized through the ``context_sources`` field so that the
    resulting plan is explicit and auditable.
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

        Memory and Knowledge context is preserved and explicitly
        identified in the generated plan.
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

        context_sources = self._get_context_sources(context)

        return {
            "request": request,
            "context_id": context.id,
            "context": context.data.copy(),
            "context_sources": context_sources,
            "status": PlanStatus.CREATED,
            "steps": [step],
        }

    def _get_context_sources(
        self,
        context: Context,
    ) -> dict[str, int]:
        """
        Identify available contextual information.

        The planner records the number of Memory and Knowledge
        entries supplied to it. It does not modify or interpret
        those entries.
        """
        memories = context.data.get("memories", [])
        knowledge = context.data.get("knowledge", [])

        return {
            "memories": (
                len(memories)
                if isinstance(memories, list)
                else 0
            ),
            "knowledge": (
                len(knowledge)
                if isinstance(knowledge, list)
                else 0
            ),
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