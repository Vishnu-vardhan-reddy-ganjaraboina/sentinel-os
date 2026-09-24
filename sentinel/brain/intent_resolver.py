"""
Intent resolution for the Sentinel Brain subsystem.

Intent resolution converts an incoming user goal into a structured
Intent. Resolution does not execute capabilities, authorize actions,
or interact with the operating system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sentinel.brain.intent import Intent


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

        return Intent(
            name="user_request",
            input=input,
            context=dict(context),
        )