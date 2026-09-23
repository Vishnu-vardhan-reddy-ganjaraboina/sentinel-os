from __future__ import annotations

import time

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.security_authorizer import SecurityControlAuthorizer
from sentinel.control_plane.service import ControlPlane
from sentinel.control_plane.transport_client import ControlPlaneTransportClient
from sentinel.control_plane.transport_server import ControlPlaneTransportServer
from sentinel.kernel.lifecycle import ServiceState
from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.service import SecurityService


class FakeTarget:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.stopped: list[str] = []
        self.restarted: list[str] = []

    def service_names(self) -> tuple[str, ...]:
        return ("alpha",)

    def service_state(self, name: str) -> ServiceState:
        return ServiceState.STOPPED

    def start_service(self, name: str) -> None:
        self.started.append(name)

    def stop_service(self, name: str) -> None:
        self.stopped.append(name)

    def restart_service(self, name: str) -> None:
        self.restarted.append(name)

    def health(self):
        return {"healthy": True}


def wait_for_server(server: ControlPlaneTransportServer) -> None:
    deadline = time.monotonic() + 2.0

    while not server.running:
        if time.monotonic() >= deadline:
            raise AssertionError("Server failed to start.")

        time.sleep(0.01)


def create_server() -> tuple[
    FakeTarget,
    ControlPlaneTransportServer,
    SecurityService,
]:
    security = SecurityService()

    security.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.EXECUTE,
        ],
    )

    security.grant(
        Role.USER,
        [
            Permission.READ,
        ],
    )

    admin_identity = SecurityIdentity(
        "admin-client",
        "Admin Client",
        {Role.ADMIN},
    )

    admin_credentials = SecurityCredentials(
        "admin",
        "admin-secret",
    )

    security.register_identity(
        admin_identity,
        admin_credentials,
    )

    read_identity = SecurityIdentity(
        "read-client",
        "Read Client",
        {Role.USER},
    )

    read_credentials = SecurityCredentials(
        "read-client",
        "read-secret",
    )

    security.register_identity(
        read_identity,
        read_credentials,
    )

    target = FakeTarget()

    authorizer = SecurityControlAuthorizer(security)

    controller = KernelController(
        target=target,
        authorizer=authorizer,
        context=ControlContext(
            caller_id="system",
            caller_type="system",
        ),
        use_caller_policy=False,
    )

    control_plane = ControlPlane(controller)

    server = ControlPlaneTransportServer(
        control_plane=control_plane,
        host="127.0.0.1",
        port=0,
    )

    return target, server, security


def test_authorized_remote_client_can_control_service() -> None:
    target, server, _security = create_server()

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
                caller_id="admin-client",
                caller_type="api",
            ),
            data={"service": "alpha"},
        )

        result = client.execute(request)

        assert result.success is True
        assert target.started == ["alpha"]

    finally:
        server.stop()


def test_unauthorized_remote_client_cannot_control_service() -> None:
    target, server, _security = create_server()

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
                caller_id="read-client",
                caller_type="api",
            ),
            data={"service": "alpha"},
        )

        result = client.execute(request)

        assert result.success is False
        assert result.command == KernelCommand.SERVICE_START.value
        assert result.error is not None

        assert target.started == []

    finally:
        server.stop()


def test_read_only_remote_client_can_read_health() -> None:
    _target, server, _security = create_server()

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
                caller_id="read-client",
                caller_type="api",
            ),
        )

        result = client.execute(request)

        assert result.success is True
        assert result.data["healthy"] is True

    finally:
        server.stop()