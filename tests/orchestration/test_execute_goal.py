from __future__ import annotations

from typing import Any

import pytest

from sentinel.brain.intent import Intent
from sentinel.brain.intent_resolver import IntentResolver
from sentinel.brain.manager import BrainManager
from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.orchestration.manager import OrchestrationManager
from sentinel.security.constants import Permission, Role
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class EchoCapability(BaseCapability):
    """Safe capability used to test execute_goal()."""

    def __init__(self) -> None:
        super().__init__(
            CapabilityMetadata(
                capability_id="system.echo",
                name="System Echo",
                description="Returns the supplied message.",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(
        self,
        **kwargs: object,
    ) -> dict[str, object]:
        return dict(kwargs)


def create_authorized_security() -> tuple[
    SecurityManager,
    SecurityIdentity,
]:
    """Create security configuration allowing capability execution."""
    security = SecurityManager()

    security.grant(
        Role.USER,
        [Permission.EXECUTE],
    )

    identity = SecurityIdentity(
        "user.1",
        "Test User",
        {Role.USER},
    )

    return security, identity


class CapabilityIntentResolver(IntentResolver):
    """Resolver that produces an executable capability Intent."""

    def resolve(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        return Intent(
            name="echo",
            input=input,
            capability_id="system.echo",
            arguments={
                "message": "hello from goal",
            },
            context=context or {},
        )


class ContextCaptureIntentResolver(IntentResolver):
    """Resolver used to verify context propagation."""

    def __init__(self) -> None:
        self.received_input: str | None = None
        self.received_context: dict[str, Any] | None = None

    def resolve(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        self.received_input = input
        self.received_context = context

        return Intent(
            name="user_request",
            input=input,
            context=context or {},
        )


def test_execute_goal_resolves_intent() -> None:
    resolver = ContextCaptureIntentResolver()

    brain = BrainManager(
        intent_resolver=resolver,
    )

    manager = OrchestrationManager(
        brain=brain,
    )

    result = manager.execute_goal(
        request_id="req.goal",
        input="open calculator",
    )

    assert result.success is True
    assert resolver.received_input == "open calculator"
    assert resolver.received_context is None

    assert isinstance(result.data, dict)
    assert result.data["request"] == "open calculator"


def test_execute_goal_passes_context_to_intent_resolver() -> None:
    resolver = ContextCaptureIntentResolver()

    brain = BrainManager(
        intent_resolver=resolver,
    )

    manager = OrchestrationManager(
        brain=brain,
    )

    context = {
        "source": "test",
        "user": "Sentinel",
    }

    result = manager.execute_goal(
        request_id="req.goal.context",
        input="open calculator",
        context=context,
    )

    assert result.success is True

    assert resolver.received_input == "open calculator"
    assert resolver.received_context == context

    assert isinstance(result.data, dict)

    brain_context = result.data["context"]

    assert brain_context["data"]["source"] == "test"
    assert brain_context["data"]["user"] == "Sentinel"


def test_execute_goal_executes_resolved_capability() -> None:
    capabilities = CapabilityManager()

    capabilities.register(
        EchoCapability()
    )

    security, identity = create_authorized_security()

    brain = BrainManager(
        intent_resolver=CapabilityIntentResolver(),
    )

    manager = OrchestrationManager(
        brain=brain,
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    result = manager.execute_goal(
        request_id="req.goal.echo",
        input="echo hello",
    )

    assert result.success is True
    assert isinstance(result.data, dict)

    capability_results = result.data["capability_results"]

    assert len(capability_results) == 1

    execution = capability_results[0]

    assert execution["capability_id"] == "system.echo"
    assert execution["result"] == {
        "message": "hello from goal",
    }


def test_execute_goal_requires_capability_authorization() -> None:
    capabilities = CapabilityManager()

    capabilities.register(
        EchoCapability()
    )

    security = SecurityManager()

    identity = SecurityIdentity(
        "user.1",
        "Test User",
        {Role.USER},
    )

    brain = BrainManager(
        intent_resolver=CapabilityIntentResolver(),
    )

    manager = OrchestrationManager(
        brain=brain,
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    with pytest.raises(AuthorizationError):
        manager.execute_goal(
            request_id="req.goal.denied",
            input="echo hello",
        )


def test_execute_goal_rejects_invalid_request_id() -> None:
    manager = OrchestrationManager()

    with pytest.raises((TypeError, ValueError)):
        manager.execute_goal(
            request_id="",
            input="hello",
        )


def test_execute_goal_rejects_invalid_input() -> None:
    manager = OrchestrationManager()

    with pytest.raises((TypeError, ValueError)):
        manager.execute_goal(
            request_id="req.goal",
            input="",
        )


def test_execute_goal_rejects_invalid_context() -> None:
    manager = OrchestrationManager()

    with pytest.raises(TypeError):
        manager.execute_goal(
            request_id="req.goal",
            input="hello",
            context=[],  # type: ignore[arg-type]
        )