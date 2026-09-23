from __future__ import annotations

import time

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.service import ControlPlane
from sentinel.control_plane.transport_client import ControlPlaneTransportClient
from sentinel.control_plane.transport_server import ControlPlaneTransportServer
from sentinel.kernel.lifecycle import ServiceState


class FakeTarget:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.stopped: list[str] = []
        self.restarted: list[str] = []

    def service_names(self) -> tuple[str, ...]:
        return ("alpha", "beta")

    def service_state(self, name: str) -> ServiceState:
        return ServiceState.RUNNING

    def start_service(self, name: str) -> None:
        self.started.append(name)

    def stop_service(self, name: str) -> None:
        self.stopped.append(name)

    def restart_service(self, name: str) -> None:
        self.restarted.append(name)

    def health(self):
        return {
            "healthy": True,
            "services": 2,
        }


class TestAuthorizer:
    def is_allowed(self, context, permission) -> bool:
        return permission in {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }

    def require(self, context, permission) -> None:
        if not self.is_allowed(context, permission):
            raise PermissionError("permission denied")


def create_system():
    target = FakeTarget()

    controller = KernelController(
        target=target,
        authorizer=TestAuthorizer(),
        context=ControlContext(
            caller_id="system",
            caller_type="system",
        ),
    )

    control_plane = ControlPlane(controller)

    server = ControlPlaneTransportServer(
        control_plane=control_plane,
        host="127.0.0.1",
        port=0,
    )

    return target, server


def wait_for_server(server: ControlPlaneTransportServer) -> None:
    deadline = time.monotonic() + 2.0

    while not server.running:
        if time.monotonic() >= deadline:
            raise AssertionError("Server failed to start.")

        time.sleep(0.01)


def test_client_to_server_control_plane_round_trip() -> None:
    target, server = create_system()

    server.start()

    try:
        wait_for_server(server)

        client = ControlPlaneTransportClient(
            host=server.host,
            port=server.port,
        )

        request = ControlRequest(
            command=KernelCommand.SYSTEM_HEALTH,
            context=ControlContext(
                caller_id="integration-client",
                caller_type="cli",
            ),
        )

        result = client.execute(request)

        assert result.success is True
        assert result.command == KernelCommand.SYSTEM_HEALTH.value
        assert result.data["healthy"] is True
        assert result.data["services"] == 2

        assert target.started == []
        assert target.stopped == []
        assert target.restarted == []

    finally:
        server.stop()


def test_client_can_control_service_through_control_plane() -> None:
    target, server = create_system()

    server.start()

    try:
        wait_for_server(server)

        client = ControlPlaneTransportClient(
            host=server.host,
            port=server.port,
        )

        request = ControlRequest(
            command=KernelCommand.SERVICE_START,
            context=ControlContext(
                caller_id="automation-client",
                caller_type="automation",
            ),
            data={
                "service": "alpha",
            },
        )

        result = client.execute(request)

        assert result.success is True
        assert result.command == KernelCommand.SERVICE_START.value
        assert target.started == ["alpha"]

    finally:
        server.stop()


def test_client_can_list_services_through_control_plane() -> None:
    _target, server = create_system()

    server.start()

    try:
        wait_for_server(server)

        client = ControlPlaneTransportClient(
            host=server.host,
            port=server.port,
        )

        request = ControlRequest(
            command=KernelCommand.SERVICE_LIST,
            context=ControlContext(
                caller_id="integration-client",
                caller_type="cli",
            ),
        )

        result = client.execute(request)

        assert result.success is True
        assert result.command == KernelCommand.SERVICE_LIST.value
        assert result.data["services"] == ["alpha", "beta"]

    finally:
        server.stop()