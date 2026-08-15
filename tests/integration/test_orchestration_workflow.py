from typing import Any, cast

import pytest

from sentinel.application import Application
from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.orchestration.models import OrchestrationRequest
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.security.constants import Permission, Role
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class EchoCapability(BaseCapability):
    """Safe capability used for integration testing."""

    def __init__(self) -> None:
        super().__init__(
            CapabilityMetadata(
                capability_id="system.echo",
                name="System Echo",
                description="Returns the supplied arguments.",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return dict(kwargs)


def create_authorized_security() -> tuple[
    SecurityManager,
    SecurityIdentity,
]:
    security = SecurityManager()

    security.grant(
        Role.USER,
        [Permission.EXECUTE],
    )

    identity = SecurityIdentity(
        "integration.user",
        "Integration User",
        {Role.USER},
    )

    return security, identity


def test_application_orchestration_capability_workflow() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    application = Application(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    try:
        kernel = application.start()

        orchestration_service = cast(
            OrchestrationRuntimeService,
            kernel.get("orchestration"),
        )

        orchestration = orchestration_service.orchestration

        request = OrchestrationRequest(
            request_id="integration.echo",
            input="hello",
            context={
                "capability_id": "system.echo",
                "capability_arguments": {
                    "message": "hello",
                },
            },
        )

        result = orchestration.execute(request)

        assert result.success is True
        assert result.request_id == "integration.echo"
        assert isinstance(result.data, dict)

        capability_results = result.data["capability_results"]

        assert len(capability_results) == 1
        assert capability_results[0]["capability_id"] == "system.echo"
        assert capability_results[0]["result"] == {
            "message": "hello",
        }

    finally:
        application.shutdown()


def test_application_orchestration_requires_permission() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security = SecurityManager()

    identity = SecurityIdentity(
        "integration.user",
        "Integration User",
        {Role.USER},
    )

    application = Application(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    try:
        kernel = application.start()

        orchestration_service = cast(
            OrchestrationRuntimeService,
            kernel.get("orchestration"),
        )

        orchestration = orchestration_service.orchestration

        request = OrchestrationRequest(
            request_id="integration.denied",
            input="hello",
            context={
                "capability_id": "system.echo",
                "capability_arguments": {
                    "message": "hello",
                },
            },
        )

        with pytest.raises(AuthorizationError):
            orchestration.execute(request)

    finally:
        application.shutdown()


def test_application_orchestration_uses_shared_memory() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    application = Application(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    try:
        kernel = application.start()

        orchestration_service = cast(
            OrchestrationRuntimeService,
            kernel.get("orchestration"),
        )

        memory_service = cast(
            MemoryRuntimeService,
            kernel.get("memory"),
        )

        orchestration = orchestration_service.orchestration
        memory = memory_service.memory

        assert orchestration.memory is memory

        request = OrchestrationRequest(
            request_id="integration.memory",
            input="hello",
            context={
                "capability_id": "system.echo",
                "capability_arguments": {
                    "message": "hello",
                },
            },
        )

        result = orchestration.execute(request)

        assert result.success is True
        assert isinstance(result.data, dict)

        capability_results = result.data["capability_results"]

        assert capability_results[0]["result"] == {
            "message": "hello",
        }

        memory_id = "orchestration:integration.memory"

        assert memory.exists(memory_id) is True

        stored = memory.get(memory_id)

        assert stored.id == memory_id
        assert stored.content == result.to_dict()

    finally:
        application.shutdown()