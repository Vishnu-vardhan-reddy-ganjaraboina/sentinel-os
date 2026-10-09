"""
Manager for the Sentinel Brain subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.brain.constants import BrainState
from sentinel.brain.context import BrainContext
from sentinel.brain.engine import BrainEngine
from sentinel.brain.intent import Intent
from sentinel.brain.intent_resolver import (
    DefaultIntentResolver,
    IntentResolver,
)


class BrainManager:
    """
    Public manager for the Sentinel Brain subsystem.

    BrainManager owns the BrainEngine and the configured IntentResolver.
    It provides a stable interface for intent resolution, context creation,
    execution, and state inspection.
    """

    def __init__(
        self,
        intent_resolver: IntentResolver | None = None,
    ) -> None:
        self._engine = BrainEngine()

        if intent_resolver is None:
            self._intent_resolver = DefaultIntentResolver()
        else:
            if not isinstance(intent_resolver, IntentResolver):
                raise TypeError(
                    "intent_resolver must be an IntentResolver instance."
                )

            self._intent_resolver = intent_resolver

    @property
    def engine(self) -> BrainEngine:
        """
        Return the Brain engine.
        """
        return self._engine

    @property
    def intent_resolver(self) -> IntentResolver:
        """
        Return the configured intent resolver.
        """
        return self._intent_resolver

    def resolve_intent(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        """
        Resolve raw input into a structured Intent.

        Intent resolution only interprets the request. It does not execute
        capabilities or perform authorization.
        """
        return self._intent_resolver.resolve(
            input=input,
            context=context,
        )

    def execute(
        self,
        request: Any,
        context: BrainContext,
    ) -> dict[str, Any]:
        """
        Execute a Brain request through the BrainEngine.
        """
        return self._engine.execute(
            request,
            context,
        )

    def create_context(
        self,
        context_id: str,
        **kwargs: Any,
    ) -> BrainContext:
        """
        Create a Brain execution context.
        """
        return BrainContext(
            context_id=context_id,
            data=kwargs,
        )

    def state(self) -> BrainState:
        """
        Return the current Brain engine state.
        """
        return self._engine.state