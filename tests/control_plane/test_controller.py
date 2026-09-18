from __future__ import annotations

from sentinel.control_plane.adapter import KernelAdapter
from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest


class StubService(Service):
    def __init__(
        self,
        name: str,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self._name = name
        self._dependencies = dependencies
        self.initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> tuple[str, ...]:
        return self._dependencies

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False

    def health(self) -> dict[str, bool]:
        return {"healthy": self.initialized}


def create_controller(
    permissions: set[ControlPermission] | None = None,
) -> tuple[Kernel, KernelController]:
    kernel = Kernel()
    kernel.register(StubService("memory"))
    kernel.register(StubService("execution"))

    adapter = KernelAdapter(kernel)

    authorizer = ControlAuthorizer(
        permissions
        if permissions is not None
        else {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )

    context = ControlContext(
        caller_id="test-caller",
        caller_type="test",
    )

    return kernel, KernelController(
        adapter,
        authorizer,
        context,
    )

def test_system_status_requires_read_permission() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(KernelCommand.SYSTEM_STATUS)

    assert result.success is True
    assert result.data == {
        "services": ("memory", "execution"),
        "service_count": 2,
    }


def test_system_health_requires_read_permission() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(KernelCommand.SYSTEM_HEALTH)

    assert result.success is True


def test_service_list_requires_read_permission() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(KernelCommand.SERVICE_LIST)

    assert result.success is True
    assert result.data == {
        "services": ("memory", "execution"),
    }


def test_service_status_requires_read_permission() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(
        KernelCommand.SERVICE_STATUS,
        {"service": "memory"},
    )

    assert result.success is True
    assert result.data["service"] == "memory"


def test_service_control_is_denied_without_control_permission() -> None:
    kernel, controller = create_controller({ControlPermission.READ})

    result = controller.execute(
        KernelCommand.SERVICE_START,
        {"service": "memory"},
    )

    assert result.success is False
    assert result.error == (
        "Permission denied: 'control' permission required."
    )
    assert kernel.running("memory") is False


def test_service_start_requires_control_permission() -> None:
    _, controller = create_controller({ControlPermission.CONTROL})

    result = controller.execute(
        KernelCommand.SERVICE_START,
        {"service": "memory"},
    )

    assert result.success is True
    assert result.data == {
        "service": "memory",
        "state": "running",
    }


def test_service_stop_requires_control_permission() -> None:
    kernel, controller = create_controller({ControlPermission.CONTROL})

    kernel.start("memory")

    result = controller.execute(
        KernelCommand.SERVICE_STOP,
        {"service": "memory"},
    )

    assert result.success is True
    assert result.data == {
        "service": "memory",
        "state": "stopped",
    }


def test_service_restart_requires_control_permission() -> None:
    kernel, controller = create_controller({ControlPermission.CONTROL})

    kernel.start("memory")

    result = controller.execute(
        KernelCommand.SERVICE_RESTART,
        {"service": "memory"},
    )

    assert result.success is True
    assert result.data == {
        "service": "memory",
        "state": "running",
    }


def test_missing_service_name_still_returns_failure() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(KernelCommand.SERVICE_STATUS)

    assert result.success is False
    assert result.error == (
        "Command requires a non-empty 'service' value."
    )


def test_unknown_service_still_returns_failure() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(
        KernelCommand.SERVICE_STATUS,
        {"service": "does-not-exist"},
    )

    assert result.success is False
    assert result.error is not None
    assert "does-not-exist" in result.error

def test_execute_builds_request_from_controller_context() -> None:
    _, controller = create_controller({ControlPermission.READ})

    result = controller.execute(
        KernelCommand.SYSTEM_STATUS,
    )

    assert result.success is True
    assert controller.context.caller_id == "test-caller"
    assert controller.context.caller_type == "test"


def test_execute_request_uses_request_context() -> None:
    _, controller = create_controller({ControlPermission.READ})

    request = ControlRequest(
        command=KernelCommand.SYSTEM_HEALTH,
        context=ControlContext(
            caller_id="explicit-caller",
            caller_type="test",
        ),
    )

    result = controller.execute_request(request)

    assert result.success is True


def test_execute_request_enforces_request_context_permission() -> None:
    _, controller = create_controller({ControlPermission.READ})

    request = ControlRequest(
        command=KernelCommand.SERVICE_START,
        context=ControlContext(
            caller_id="unprivileged-caller",
            caller_type="test",
        ),
        data={"service": "memory"},
    )

    result = controller.execute_request(request)

    assert result.success is False
    assert result.error == (
        "Permission denied: 'control' permission required."
    )