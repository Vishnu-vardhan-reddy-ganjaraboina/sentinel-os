import pytest

from sentinel.brain.constants import PlanStatus
from sentinel.brain.manager import BrainManager
from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.orchestration.exceptions import (
    OrchestrationExecutionError,
    OrchestrationValidationError,
)
from sentinel.orchestration.manager import OrchestrationManager
from sentinel.orchestration.models import OrchestrationRequest
from sentinel.security.constants import Permission, Role
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class EchoCapability(BaseCapability):
    """Safe test capability for orchestration integration."""

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


def test_handler_property() -> None:
    def handler(request: OrchestrationRequest) -> str:
        return str(request.input)

    manager = OrchestrationManager(handler)

    assert manager.handler is handler


def test_brain_property() -> None:
    brain = BrainManager()

    manager = OrchestrationManager(brain=brain)

    assert manager.brain is brain


def test_execute_with_handler() -> None:
    def handler(request: OrchestrationRequest) -> dict[str, object]:
        return {
            "input": request.input,
            "context": request.context,
        }

    manager = OrchestrationManager(handler)

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={"user": "Sentinel"},
    )

    result = manager.execute(request)

    assert result.request_id == "req.1"
    assert result.success is True
    assert result.data == {
        "input": "hello",
        "context": {"user": "Sentinel"},
    }
    assert result.error is None


def test_execute_with_brain() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={"user": "Sentinel"},
    )

    result = manager.execute(request)

    assert result.request_id == "req.1"
    assert result.success is True

    assert isinstance(result.data, dict)
    assert result.data["request"] == "hello"
    assert result.data["success"] is True

    plan = result.data["plan"]

    assert plan["context_id"] == "req.1"
    assert plan["status"] == PlanStatus.COMPLETED


def test_brain_receives_request_context() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={
            "user": "Sentinel",
            "source": "integration",
        },
    )

    result = manager.execute(request)

    assert isinstance(result.data, dict)

    context = result.data["context"]

    assert context["id"] == "req.1"
    assert context["data"]["user"] == "Sentinel"
    assert context["data"]["source"] == "integration"


def test_execute_invalid_request_raises() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="   ",
        input="hello",
    )

    with pytest.raises(OrchestrationValidationError):
        manager.execute(request)


def test_can_execute() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    assert manager.can_execute(request) is True


def test_can_execute_invalid_request() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="",
        input="hello",
    )

    assert manager.can_execute(request) is False


def test_execute_handler_failure() -> None:
    def handler(request: OrchestrationRequest) -> str:
        raise RuntimeError("boom")

    manager = OrchestrationManager(handler)

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)


def test_execute_capability_plan() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.echo",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    capability_results = result.data["capability_results"]

    assert len(capability_results) == 1

    execution = capability_results[0]

    assert execution["capability_id"] == "system.echo"
    assert execution["result"] == {
        "message": "hello",
    }


def test_execute_unknown_capability_fails() -> None:
    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.unknown",
        input="hello",
        context={
            "capability_id": "does.not.exist",
        },
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)


def test_execute_capability_with_permission() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.authorized",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    result = manager.execute(request)

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

    manager = OrchestrationManager(
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
        manager.execute(request)


def test_execute_capability_without_identity() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    manager = OrchestrationManager(
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
        manager.execute(request)