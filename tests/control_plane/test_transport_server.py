from __future__ import annotations

import json
import select
import socket
import time

import pytest

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.service import ControlPlane
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


def create_server(
    read_timeout: float = 5.0,
) -> ControlPlaneTransportServer:
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
        read_timeout=read_timeout,
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


def test_server_stop_closes_idle_client_connection() -> None:
    server = create_server()
    server.start()

    connection = None
    server_thread = None

    try:
        wait_for_server(server)

        connection = socket.create_connection(
            (server.host, server.port),
            timeout=2.0,
        )

        # Allow the server to accept the connection and wait for its data.
        time.sleep(0.1)
        server_thread = server._thread

        assert server_thread is not None
        assert server_thread.is_alive()

        server.stop()

        assert not server_thread.is_alive(), (
            "Server thread remained alive after stopping with an idle client."
        )
    finally:
        if connection is not None:
            connection.close()
        server.stop()


def test_server_times_out_when_client_sends_incomplete_message() -> None:
    server = create_server(read_timeout=0.2)
    server.start()

    try:
        wait_for_server(server)

        with socket.create_connection(
            (server.host, server.port),
            timeout=2.0,
        ) as connection:
            connection.settimeout(3.0)
            connection.sendall(b'{"version":1,"type":"request"')

            data = b""
            while b"\n" not in data:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data += chunk

        result = ControlPlaneProtocol.decode_response(data)

        assert result.success is False
        assert result.command == "transport.error"
        assert result.error is not None
    finally:
        server.stop()


def test_server_enforces_total_message_deadline() -> None:
    base_server = create_server()
    server = ControlPlaneTransportServer(
        control_plane=base_server.control_plane,
        host="127.0.0.1",
        port=0,
        read_timeout=1.0,
        message_timeout=0.5,
    )
    server.start()

    try:
        wait_for_server(server)

        with socket.create_connection(
            (server.host, server.port),
            timeout=2.0,
        ) as connection:
            connection.settimeout(2.0)
            data = b""

            for _ in range(20):
                try:
                    connection.sendall(b"x")
                except OSError:
                    break

                readable, _, _ = select.select(
                    [connection], [], [], 0.1
                )
                if readable:
                    try:
                        chunk = connection.recv(4096)
                    except OSError:
                        break

                    if not chunk:
                        break

                    data += chunk
                    if b"\\n" in data:
                        break

        assert data, "Server closed the connection without a response."
        result = ControlPlaneProtocol.decode_response(data)

        assert result.success is False
        assert result.command == "transport.error"
        assert result.error is not None
        assert "timed out" in result.error.lower()
    finally:
        server.stop()


def test_server_can_restart_after_stop() -> None:
    server = create_server()
    server.start()

    try:
        wait_for_server(server)
    finally:
        server.stop()

    assert server.running is False

    server.start()

    try:
        wait_for_server(server)

        request = ControlRequest(
            command=KernelCommand.SYSTEM_STATUS,
            context=ControlContext(
                caller_id="restart-client",
                caller_type="cli",
            ),
        )

        result = send_request(server, request)

        assert result.success is True
        assert result.command == KernelCommand.SYSTEM_STATUS.value
    finally:
        server.stop()

    assert server.running is False


def test_server_stop_is_idempotent() -> None:
    server = create_server()

    server.stop()
    server.stop()

    assert server.running is False