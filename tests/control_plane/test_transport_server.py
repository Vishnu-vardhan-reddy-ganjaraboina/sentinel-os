from __future__ import annotations

import json
import socket
import time

import pytest

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.service import ControlPlane
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.transport import ControlPlaneProtocol
from sentinel.control_plane.transport_server import ControlPlaneTransportServer
from sentinel.kernel.lifecycle import ServiceState


class FakeTarget:
    def service_names(self) -> tuple[str, ...]:
        return ("alpha",)

    def service_state(self, name: str) -> ServiceState:
        return ServiceState.RUNNING

    def start_service(self, name: str) -> None:
        pass

    def stop_service(self, name: str) -> None:
        pass

    def restart_service(self, name: str) -> None:
        pass

    def health(self):
        return {"healthy": True}


class FakeAuthorizer:
    def is_allowed(self, context, permission) -> bool:
        return permission in {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }

    def require(self, context, permission) -> None:
        if not self.is_allowed(context, permission):
            raise PermissionError("denied")


def create_server() -> ControlPlaneTransportServer:
    controller = KernelController(
        target=FakeTarget(),
        authorizer=FakeAuthorizer(),
        context=ControlContext(
            caller_id="test",
            caller_type="test",
        ),
    )

    plane = ControlPlane(controller)

    return ControlPlaneTransportServer(
        control_plane=plane,
        host="127.0.0.1",
        port=0,
    )


def wait_for_server(server: ControlPlaneTransportServer) -> None:
    deadline = time.monotonic() + 2.0

    while not server.running:
        if time.monotonic() >= deadline:
            raise AssertionError("Server did not start.")
        time.sleep(0.01)


def send_request(
    server: ControlPlaneTransportServer,
    request: ControlRequest,
) -> ControlResult:
    with socket.create_connection(
        (server.host, server.port),
        timeout=2.0,
    ) as connection:
        connection.sendall(ControlPlaneProtocol.encode_request(request))

        data = b""

        while b"\n" not in data:
            chunk = connection.recv(4096)

            if not chunk:
                break

            data += chunk

    return ControlPlaneProtocol.decode_response(data)


def test_server_starts_and_stops() -> None:
    server = create_server()

    assert server.running is False

    server.start()

    try:
        wait_for_server(server)

        assert server.running is True
        assert server.port > 0
    finally:
        server.stop()

    assert server.running is False


def test_server_executes_control_plane_request() -> None:
    server = create_server()
    server.start()

    try:
        wait_for_server(server)

        request = ControlRequest(
            command=KernelCommand.SYSTEM_HEALTH,
            context=ControlContext(
                caller_id="test-client",
                caller_type="cli",
            ),
        )

        result = send_request(server, request)

        assert result.success is True
        assert result.command == KernelCommand.SYSTEM_HEALTH.value
        assert result.data["healthy"] is True
    finally:
        server.stop()


def test_server_returns_protocol_error_for_invalid_json() -> None:
    server = create_server()
    server.start()

    try:
        wait_for_server(server)

        with socket.create_connection(
            (server.host, server.port),
            timeout=2.0,
        ) as connection:
            connection.sendall(b"not-json\n")

            data = connection.recv(4096)

        result = ControlPlaneProtocol.decode_response(data)

        assert result.success is False
        assert result.command == "transport.error"
        assert result.error
    finally:
        server.stop()


def test_server_rejects_invalid_request() -> None:
    server = create_server()
    server.start()

    try:
        wait_for_server(server)

        payload = {
            "version": ControlPlaneProtocol.VERSION,
            "type": "request",
            "command": "invalid.command",
            "context": {
                "caller_id": "test",
                "caller_type": "cli",
                "metadata": {},
            },
            "data": {},
        }

        with socket.create_connection(
            (server.host, server.port),
            timeout=2.0,
        ) as connection:
            connection.sendall(
                (json.dumps(payload) + "\n").encode("utf-8")
            )

            data = connection.recv(4096)

        result = ControlPlaneProtocol.decode_response(data)

        assert result.success is False
        assert result.command == "transport.error"
        assert result.error
    finally:
        server.stop()


def test_server_can_handle_multiple_connections() -> None:
    server = create_server()
    server.start()

    try:
        wait_for_server(server)

        for caller_id in ("client-1", "client-2", "client-3"):
            request = ControlRequest(
                command=KernelCommand.SYSTEM_STATUS,
                context=ControlContext(
                    caller_id=caller_id,
                    caller_type="cli",
                ),
            )

            result = send_request(server, request)

            assert result.success is True
            assert result.command == KernelCommand.SYSTEM_STATUS.value
    finally:
        server.stop()


def test_server_rejects_second_start() -> None:
    server = create_server()

    server.start()

    try:
        wait_for_server(server)

        with pytest.raises(RuntimeError):
            server.start()
    finally:
        server.stop()


def test_server_stop_is_idempotent() -> None:
    server = create_server()

    server.stop()
    server.stop()

    assert server.running is False