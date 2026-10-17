"""
Intent resolution for the Sentinel Brain subsystem.

Intent resolution converts an incoming user goal into a structured
Intent. Resolution does not execute capabilities, authorize actions,
or interact with the operating system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from sentinel.brain.intent import Intent
from sentinel.capabilities.discovery import (
    CapabilityDiscovery,
    DiscoveryStatus,
)
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.validation import (
    CapabilityArgumentValidationError,
    get_missing_required_arguments,
    validate_capability_arguments,
)


class IntentResolver(ABC):
    """
    Abstract interface for resolving user input into an Intent.
    """

    @abstractmethod
    def resolve(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        """
        Resolve input into a structured Intent.
        """


class DefaultIntentResolver(IntentResolver):
    """
    Deterministic default Intent resolver.

    The default resolver creates a structured Intent without executing
    any capability or performing authorization.
    """

    EXECUTION_SELECTION_THRESHOLD = 0.85

    def __init__(
        self,
        capabilities: CapabilityManager | None = None,
    ) -> None:
        if capabilities is not None and not isinstance(
            capabilities, CapabilityManager
        ):
            raise TypeError(
                "capabilities must be a CapabilityManager or None."
            )

        self._discovery = (
            CapabilityDiscovery(capabilities)
            if capabilities is not None
            else None
        )
        self._capabilities = capabilities

    def resolve(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        if not isinstance(input, str):
            raise TypeError("input must be a string.")

        if not input.strip():
            raise ValueError("input must not be empty.")

        if context is None:
            context = {}

        if not isinstance(context, dict):
            raise TypeError("context must be a dictionary.")

        resolved_context = deepcopy(context)
        capability_id: str | None = None
        arguments: dict[str, Any] = {}

        if self._discovery is not None and self._capabilities is not None:
            result = self._discovery.discover(input)
            discovery_info: dict[str, Any] = {
                "status": result.status.value,
                "selected": False,
                "candidates": [
                    {
                        "capability_id": item.capability_id,
                        "name": item.name,
                        "score": item.score,
                    }
                    for item in result.candidates
                ],
            }

            if (
                result.status == DiscoveryStatus.MATCHED
                and result.candidate is not None
                and result.candidate.score
                >= self.EXECUTION_SELECTION_THRESHOLD
            ):
                candidate = result.candidate
                capability = self._capabilities.registry.get(
                    candidate.capability_id
                )

                try:
                    missing = get_missing_required_arguments(
                        capability.metadata.input_schema,
                        arguments,
                    )
                    if missing:
                        capability_id = candidate.capability_id
                        discovery_info["capability_id"] = capability_id
                        discovery_info["missing_required_arguments"] = missing
                        discovery_info["selection_reason"] = (
                            "needs_clarification"
                        )
                    else:
                        validate_capability_arguments(
                            capability.metadata.input_schema,
                            arguments,
                        )
                        capability_id = candidate.capability_id
                        discovery_info["selected"] = True
                        discovery_info["selection_reason"] = "eligible"
                except (
                    CapabilityArgumentValidationError,
                    TypeError,
                ):
                    discovery_info["selection_reason"] = (
                        "arguments_required_or_schema_invalid"
                    )
            elif result.status == DiscoveryStatus.AMBIGUOUS:
                discovery_info["selection_reason"] = "ambiguous"
            elif (
                result.status == DiscoveryStatus.MATCHED
                and result.candidate is not None
            ):
                discovery_info["selection_reason"] = (
                    "below_confidence_threshold"
                )
            else:
                discovery_info["selection_reason"] = "unmatched"

            resolved_context["capability_discovery"] = discovery_info

        return Intent(
            name="user_request",
            input=input,
            capability_id=capability_id,
            arguments=arguments,
            context=resolved_context,
        )
