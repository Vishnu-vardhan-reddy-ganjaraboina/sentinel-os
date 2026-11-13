"""
Planner implementation for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sentinel.brain.constants import PlanStatus
from sentinel.brain.interfaces import Context, Planner


class BrainPlanner(Planner):
    """
    Default deterministic Brain planner.

    The planner produces plans and recommendations only. It never executes
    capabilities.
    """

    def create_plan(
        self,
        request: Any,
        context: Context,
    ) -> dict[str, Any]:
        """
        Create an execution plan.

        Explicit capability selection supplied through the context takes
        precedence over automatic recommendation.
        """
        if not isinstance(context, Context):
            raise TypeError("context must be a Context instance.")

        context_data = context.data

        capability_id = context_data.get("capability_id")

        capability_arguments = context_data.get(
            "capability_arguments",
            {},
        )

        step: dict[str, Any] = {
            "step": 1,
            "action": "execute",
            "completed": False,
        }

        if capability_id is not None:
            step["capability_id"] = deepcopy(capability_id)
            step["arguments"] = (
                deepcopy(capability_arguments)
                if isinstance(capability_arguments, dict)
                else {}
            )

        recommendation = self._recommend_capability(
            request=request,
            context_data=context_data,
        )

        return {
            "request": deepcopy(request),
            "context_id": context.id,
            "context": deepcopy(context_data),
            "context_sources": self._get_context_sources(
                context_data,
            ),
            "recommendation": deepcopy(recommendation),
            "status": PlanStatus.CREATED,
            "steps": [step],
        }

    def _recommend_capability(
        self,
        request: Any,
        context_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Recommend a capability using deterministic lexical matching.

        Recommendation is informational only.
        """
        if context_data.get("capability_id") is not None:
            return None

        capabilities = context_data.get(
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
        context_data: dict[str, Any],
    ) -> dict[str, int]:
        """
        Identify available contextual information.
        """
        memories = context_data.get("memories", [])
        knowledge = context_data.get("knowledge", [])
        capabilities = context_data.get("capabilities", [])

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
        """
        Mark a valid plan as ready.
        """
        self._validate_plan(plan)

        plan["status"] = PlanStatus.READY
        return plan

    def mark_completed(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Mark a valid plan as completed.
        """
        self._validate_plan(plan)

        plan["status"] = PlanStatus.COMPLETED

        for step in plan["steps"]:
            if not isinstance(step, dict):
                raise TypeError("plan steps must be dictionaries.")

            step["completed"] = True

        return plan

    @staticmethod
    def _validate_plan(
        plan: dict[str, Any],
    ) -> None:
        """
        Validate the minimum structure required by planner transitions.
        """
        if not isinstance(plan, dict):
            raise TypeError("plan must be a dictionary.")

        if "status" not in plan:
            raise ValueError("plan must contain status.")

        if "steps" not in plan:
            raise ValueError("plan must contain steps.")

        if not isinstance(plan["steps"], list):
            raise TypeError("plan steps must be a list.")
