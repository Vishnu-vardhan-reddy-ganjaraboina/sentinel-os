import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.orchestration.models import OrchestrationRequest
from sentinel.orchestration.service import OrchestrationService
from sentinel.security.constants import Permission, Role
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class EchoCapability(BaseCapability):
    """Safe test capability for service integration."""

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


def test_execute() -> None:
    service = OrchestrationService()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    result = service.execute(request)

    assert result.success is True


def test_can_execute() -> None:
    service = OrchestrationService()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    assert service.can_execute(request) is True


def test_can_execute_without_handler() -> None:
    service = OrchestrationService()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    assert service.can_execute(request) is True


def test_execute_without_handler() -> None:
    service = OrchestrationService()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    result = service.execute(request)

    assert result.success is True


def test_execute_capability() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

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

    service = OrchestrationService(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    result = service.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    assert result.data["capability_results"][0]["result"] == {
        "message": "hello",
    }


def test_execute_capability_without_permission() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security = SecurityManager()

    identity = SecurityIdentity(
        "user.1",
        "Test User",
        {Role.USER},
    )

    service = OrchestrationService(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.denied",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    with pytest.raises(AuthorizationError):
        service.execute(request)


def test_execute_capability_without_identity() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    service = OrchestrationService(
        capabilities=capabilities,
    )

    request = OrchestrationRequest(
        request_id="req.no-identity",
        input="hello",
        context={
            "capability_id": "system.echo",
        },
    )

    with pytest.raises(AuthorizationError):
        service.execute(request)