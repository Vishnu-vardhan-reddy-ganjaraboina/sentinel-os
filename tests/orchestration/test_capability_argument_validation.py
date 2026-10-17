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
from sentinel.orchestration.exceptions import OrchestrationExecutionError
from sentinel.orchestration.manager import OrchestrationManager
from sentinel.security.constants import Permission, Role
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class ValidationTestCapability(BaseCapability):
    """Capability that records whether execution was reached."""

    def __init__(self, input_schema: dict[str, Any]) -> None:
        super().__init__(
            CapabilityMetadata(
                capability_id="test.validation",
                name="Validation Test",
                description="Tests orchestration argument validation.",
                category=CapabilityCategory.CUSTOM,
                input_schema=input_schema,
            )
        )
        self.run_called = False

    def run(self, **kwargs: Any) -> dict[str, Any]:
        self.run_called = True
        return dict(kwargs)


class FixedIntentResolver(IntentResolver):
    """Resolver returning a predetermined capability and arguments."""

    def __init__(self, arguments: dict[str, Any]) -> None:
        self.arguments = arguments

    def resolve(
        self,
        input: str,
        context: dict[str, Any] | None = None,
    ) -> Intent:
        return Intent(
            name="test_request",
            input=input,
            capability_id="test.validation",
            arguments=self.arguments,
            context=context or {},
        )


def make_security(
    authorized: bool,
) -> tuple[SecurityManager, SecurityIdentity]:
    security = SecurityManager()
    if authorized:
        security.grant(Role.USER, [Permission.EXECUTE])

    identity = SecurityIdentity(
        "test.user",
        "Test User",
        {Role.USER},
    )
    return security, identity


def make_manager(
    capability: ValidationTestCapability,
    arguments: dict[str, Any],
    authorized: bool,
) -> OrchestrationManager:
    capabilities = CapabilityManager()
    capabilities.register(capability)
    security, identity = make_security(authorized)
    brain = BrainManager(
        intent_resolver=FixedIntentResolver(arguments),
    )
    return OrchestrationManager(
        brain=brain,
        capabilities=capabilities,
        security=security,
        identity=identity,
    )


def test_invalid_arguments_never_execute_capability() -> None:
    capability = ValidationTestCapability(
        {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
            "additionalProperties": False,
        }
    )
    manager = make_manager(
        capability,
        {"message": 123},
        authorized=True,
    )

    with pytest.raises(
        OrchestrationExecutionError,
        match="Invalid arguments for capability",
    ):
        manager.execute_goal(
            request_id="req.invalid.arguments",
            input="test invalid arguments",
        )

    assert capability.run_called is False


def test_authorization_precedes_schema_validation() -> None:
    capability = ValidationTestCapability(
        {"type": "not-a-valid-json-schema-type"}
    )
    manager = make_manager(
        capability,
        {},
        authorized=False,
    )

    with pytest.raises(AuthorizationError):
        manager.execute_goal(
            request_id="req.unauthorized.invalid.schema",
            input="test authorization order",
        )

    assert capability.run_called is False
