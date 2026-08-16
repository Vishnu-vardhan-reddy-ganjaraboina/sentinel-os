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

    The planner is deterministic and does not execute capabilities.

    Explicit capability selections supplied through the context take
    precedence. Available capability metadata may also be inspected
    to produce a safe recommendation for the current request.
    """

    def create_plan(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any]:
        """
        Create an execution plan.

        An explicit ``capability_id`` supplied through the context
        takes precedence over automatic recommendation.

        Automatic recommendation is informational only and does not
        cause capability execution.
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

        recommendation = self._recommend_capability(
            request=request,
            context=context,
        )

        return {
            "request": request,
            "context_id": context.id,
            "context": context.data.copy(),
            "context_sources": self._get_context_sources(context),
            "recommendation": recommendation,
            "status": PlanStatus.CREATED,
            "steps": [step],
        }

    def _recommend_capability(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any] | None:
        """
        Recommend a capability using simple deterministic matching.

        Explicit capability selection is never overridden.

        The recommendation is informational and is not executed
        automatically.
        """
        if context.data.get("capability_id") is not None:
            return None

        capabilities = context.data.get(
            "capabilities",
            [],
        )

        if not isinstance(capabilities, list):
            return None

        request_text = str(request).strip().lower()

        if not request_text:
            return None

        best_match: dict[str, Any] | None = None
        best_score = 0

        for capability in capabilities:
            if not isinstance(capability, dict):
                continue

            if capability.get("enabled") is not True:
                continue

            capability_id = capability.get("capability_id")

            if not isinstance(capability_id, str):
                continue

            searchable_text = " ".join(
                str(capability.get(field, ""))
                for field in (
                    "name",
                    "description",
                )
            ).lower()

            metadata = capability.get("metadata")

            if isinstance(metadata, dict):
                tags = metadata.get("tags", [])

                if isinstance(tags, list):
                    searchable_text += " " + " ".join(
                        str(tag)
                        for tag in tags
                    ).lower()

            score = self._calculate_match_score(
                request_text,
                searchable_text,
            )

            if score > best_score:
                best_score = score
                best_match = {
                    "capability_id": capability_id,
                    "score": score,
                }

        return best_match

    def _calculate_match_score(
        self,
        request: str,
        capability_text: str,
    ) -> int:
        """
        Calculate a deterministic lexical match score.
        """
        words = {
            word
            for word in request.split()
            if len(word) > 2
        }

        if not words:
            return 0

        return sum(
            1
            for word in words
            if word in capability_text
        )

    def _get_context_sources(
        self,
        context: Context,
    ) -> dict[str, int]:
        """
        Identify available contextual information.
        """
        memories = context.data.get("memories", [])
        knowledge = context.data.get("knowledge", [])
        capabilities = context.data.get("capabilities", [])

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
            "capabilities": (
                len(capabilities)
                if isinstance(capabilities, list)
                else 0
            ),
        }

    def mark_ready(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """Mark a plan as ready."""
        plan["status"] = PlanStatus.READY
        return plan

    def mark_completed(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """Mark a plan as completed."""
        plan["status"] = PlanStatus.COMPLETED

        for step in plan["steps"]:
            step["completed"] = True

        return plan