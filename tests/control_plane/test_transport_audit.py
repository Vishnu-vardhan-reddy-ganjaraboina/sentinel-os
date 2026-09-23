from __future__ import annotations

import time

from sentinel.control_plane.audit import InMemoryControlAuditRecorder
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
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

    def service_names(self) -> tuple[str, ...]:
        return ("alpha",)

    def service_state(self, name: str) -> ServiceState:
        return ServiceState.STOPPED

    def start_service(self, name: str) -> None:
        self.started.append(name)

    def stop_service(self, name: str) -> None:
        pass

    def restart_service(self, name: str) -> None:
        pass

    def health(self):
        return {
            "healthy": True,
        }


def wait_for_server(
    server: ControlPlaneTransportServer,
) -> None:
    deadline = time.monotonic() + 2.0

    while not server.running:
        if time.monotonic() >= deadline:
            raise AssertionError(
                "Server failed to start."
            )

        time.sleep(0.01)


def create_server() -> tuple[
    FakeTarget,
    ControlPlaneTransportServer,
    InMemoryControlAuditRecorder,
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

    audit_recorder = InMemoryControlAuditRecorder()

    authorizer = SecurityControlAuthorizer(
        security
    )

    controller = KernelController(
        target=target,
        authorizer=authorizer,
        context=ControlContext(
            caller_id="system",
            caller_type="system",
        ),
        audit_recorder=audit_recorder,
        use_caller_policy=False,
    )

    control_plane = ControlPlane(
        controller
    )

    server = ControlPlaneTransportServer(
        control_plane=control_plane,
        host="127.0.0.1",
        port=0,
    )

    return (
        target,
        server,
        audit_recorder,
    )


def test_successful_remote_control_is_audited() -> None:
    target, server, audit_recorder = create_server()

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
            data={
                "service": "alpha",
            },
        )

        result = client.execute(request)

        assert result.success is True
        assert target.started == ["alpha"]

        events = audit_recorder.events

        assert len(events) == 1

        event = events[0]

        assert event.caller_id == "admin-client"
        assert event.command == KernelCommand.SERVICE_START.value
        assert event.success is True
        assert event.data == {
            "service": "alpha",
        }
        assert event.error is None

    finally:
        server.stop()


def test_denied_remote_control_is_audited() -> None:
    target, server, audit_recorder = create_server()

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
            data={
                "service": "alpha",
            },
        )

        result = client.execute(request)

        assert result.success is False
        assert result.error is not None

        # Authorization must prevent the Kernel operation.
        assert target.started == []

        events = audit_recorder.events

        assert len(events) == 1

        event = events[0]

        assert event.caller_id == "read-client"
        assert event.command == KernelCommand.SERVICE_START.value
        assert event.success is False
        assert event.data == {
            "service": "alpha",
        }
        assert event.error is not None

    finally:
        server.stop()