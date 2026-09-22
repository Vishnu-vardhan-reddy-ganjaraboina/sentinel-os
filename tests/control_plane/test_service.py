from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.service import ControlPlane
from sentinel.control_plane.request import ControlRequest


class FakeTarget:
    def __init__(self) -> None:
        self.started: list[str] = []

    def service_names(self) -> tuple[str, ...]:
        return ("memory", "execution")

    def service_state(self, name: str):
        raise NotImplementedError

    def start_service(self, name: str) -> None:
        self.started.append(name)

    def stop_service(self, name: str) -> None:
        raise NotImplementedError

    def restart_service(self, name: str) -> None:
        raise NotImplementedError

    def health(self):
        return {
            "healthy": True,
            "services": {},
        }


def create_control_plane() -> ControlPlane:
    target = FakeTarget()

    context = ControlContext(
        caller_id="test-user",
        caller_type="user",
    )

    authorizer = ControlAuthorizer(
        permissions={
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )

    controller = KernelController(
        target=target,
        authorizer=authorizer,
        context=context,
    )

    return ControlPlane(controller)


def test_control_plane_exposes_controller() -> None:
    control_plane = create_control_plane()

    assert control_plane.controller is not None


def test_control_plane_exposes_context() -> None:
    control_plane = create_control_plane()

    assert control_plane.context.caller_id == "test-user"
    assert control_plane.context.caller_type == "user"


def test_control_plane_executes_command() -> None:
    control_plane = create_control_plane()

    result = control_plane.execute(
        KernelCommand.SERVICE_LIST
    )

    assert result.success is True
    assert result.command == KernelCommand.SERVICE_LIST.value
    assert result.data["services"] == (
        "memory",
        "execution",
    )


def test_control_plane_preserves_authorization() -> None:
    target = FakeTarget()

    context = ControlContext(
        caller_id="readonly-user",
        caller_type="user",
    )

    authorizer = ControlAuthorizer(
        permissions={
            ControlPermission.READ,
        }
    )

    controller = KernelController(
        target=target,
        authorizer=authorizer,
        context=context,
    )

    control_plane = ControlPlane(controller)

    result = control_plane.execute(
        KernelCommand.SERVICE_START,
        {"service": "memory"},
    )

    assert result.success is False
    assert "permission" in result.error.lower()


def test_control_plane_preserves_controller_context() -> None:
    control_plane = create_control_plane()

    assert control_plane.context is control_plane.controller.context

def test_control_plane_executes_structured_request() -> None:
    control_plane = create_control_plane()

    request = ControlRequest(
        command=KernelCommand.SERVICE_LIST,
        context=control_plane.context,
    )

    result = control_plane.execute_request(request)

    assert result.success is True
    assert result.command == KernelCommand.SERVICE_LIST.value
    assert result.data["services"] == (
        "memory",
        "execution",
    )

def test_control_plane_preserves_request_context() -> None:
    control_plane = create_control_plane()

    request_context = ControlContext(
        caller_id="request-user",
        caller_type="automation",
    )

    request = ControlRequest(
        command=KernelCommand.SERVICE_LIST,
        context=request_context,
    )

    result = control_plane.execute_request(request)

    assert result.success is True
    assert control_plane.context.caller_id == "test-user"

def test_control_plane_request_context_controls_authorization() -> None:
    control_plane = create_control_plane()

    request_context = ControlContext(
        caller_id="ai-agent",
        caller_type="ai_agent",
    )

    request = ControlRequest(
        command=KernelCommand.SERVICE_START,
        context=request_context,
        data={"service": "memory"},
    )

    result = control_plane.execute_request(request)

    assert result.success is False
    assert "permission" in result.error.lower()

def test_control_plane_executes_system_status() -> None:
    control_plane = create_control_plane()

    result = control_plane.execute(
        KernelCommand.SYSTEM_STATUS,
    )

    assert result.success is True
    assert result.command == KernelCommand.SYSTEM_STATUS.value
    assert result.data == {
        "services": (
            "memory",
            "execution",
        ),
        "service_count": 2,
    }


def test_control_plane_executes_system_health() -> None:
    control_plane = create_control_plane()

    result = control_plane.execute(
        KernelCommand.SYSTEM_HEALTH,
    )

    assert result.success is True
    assert result.command == KernelCommand.SYSTEM_HEALTH.value
    assert result.data == {
        "healthy": True,
        "services": {},
    }