from __future__ import annotations

import json
import socket
import threading
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


class BlockingControlPlane(ControlPlane):
    def __init__(self, controller: KernelController) -> None:
        super().__init__(controller)
        self.started = threading.Event()
        self.release = threading.Event()

    def execute_request(
        self,
        request: ControlRequest,
    ) -> ControlResult:
        if request.context.caller_id == "slow-client":
            self.started.set()
            if not self.release.wait():
                raise RuntimeError("Blocking test was not released.")

        return super().execute_request(request)


def create_server(
    client_timeout: float | None = None,
    max_workers: int | None = None,
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

    server_kwargs: dict[str, object] = {
        "control_plane": plane,
        "host": "127.0.0.1",
        "port": 0,
    }

    if client_timeout is not None:
        server_kwargs["client_timeout"] = client_timeout

    if max_workers is not None:
        server_kwargs["max_workers"] = max_workers

    return ControlPlaneTransportServer(**server_kwargs)

def wait_for_server(server: ControlPlaneTransportServer) -> None:
    deadline = time.monotonic() + 2.0

    while not server.running:
        if time.monotonic() >= deadline:
            raise AssertionError("Server did not start.")
        time.sleep(0.01)


def send_request(
    server: ControlPlaneTransportServer,
    request: ControlRequest,
    timeout: float = 2.0,
) -> ControlResult:
    with socket.create_connection(
        (server.host, server.port),
        timeout=timeout,
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
def test_server_times_out_incomplete_client_message() -> None:
    server = create_server(client_timeout=0.1)
    server.start()

    try:
        wait_for_server(server)

        with socket.create_connection(
            (server.host, server.port),
            timeout=1.0,
        ) as connection:
            connection.sendall(b'{"version":1,"type":"request"')

            data = b""
            deadline = time.monotonic() + 1.0

            while b"\n" not in data:
                if time.monotonic() >= deadline:
                    raise AssertionError(
                        "Server did not respond to incomplete message."
                    )

                chunk = connection.recv(4096)

                if not chunk:
                    break

                data += chunk

        result = ControlPlaneProtocol.decode_response(data)

        assert result.success is False
        assert result.command == "transport.error"
        assert result.error
    finally:
        server.stop()
def test_server_rejects_non_positive_client_timeout() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        create_server(client_timeout=0)

    with pytest.raises(ValueError, match="greater than zero"):
        create_server(client_timeout=-1)


def test_server_rejects_invalid_client_timeout_type() -> None:
    with pytest.raises(TypeError, match="must be a number"):
        create_server(client_timeout="1")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must be a number"):
        create_server(client_timeout=True)  # type: ignore[arg-type]


def test_server_exposes_client_timeout() -> None:
    server = create_server(client_timeout=2.5)

    assert server.client_timeout == 2.5
def test_server_handles_connections_concurrently() -> None:
    controller = KernelController(
        target=FakeTarget(),
        authorizer=FakeAuthorizer(),
        context=ControlContext(
            caller_id="test",
            caller_type="test",
        ),
    )
    plane = BlockingControlPlane(controller)
    server = ControlPlaneTransportServer(
        control_plane=plane,
        host="127.0.0.1",
        port=0,
        client_timeout=1.0,
    )

    server.start()

    slow_connection: socket.socket | None = None

    try:
        wait_for_server(server)

        slow_request = ControlRequest(
            command=KernelCommand.SYSTEM_STATUS,
            context=ControlContext(
                caller_id="slow-client",
                caller_type="cli",
            ),
        )

        fast_request = ControlRequest(
            command=KernelCommand.SYSTEM_STATUS,
            context=ControlContext(
                caller_id="fast-client",
                caller_type="cli",
            ),
        )

        slow_connection = socket.create_connection(
            (server.host, server.port),
            timeout=1.0,
        )
        slow_connection.sendall(
            ControlPlaneProtocol.encode_request(slow_request)
        )

        assert plane.started.wait(timeout=1.0)

        fast_result = send_request(
            server,
            fast_request,
            timeout=0.5,
        )

        assert fast_result.success is True
        assert fast_result.command == KernelCommand.SYSTEM_STATUS.value
    finally:
        plane.release.set()

        if slow_connection is not None:
            try:
                slow_connection.close()
            except OSError:
                pass

        server.stop()
def test_server_respects_max_workers_limit() -> None:
    controller = KernelController(
        target=FakeTarget(),
        authorizer=FakeAuthorizer(),
        context=ControlContext(
            caller_id="test",
            caller_type="test",
        ),
    )
    plane = BlockingControlPlane(controller)
    server = ControlPlaneTransportServer(
        control_plane=plane,
        host="127.0.0.1",
        port=0,
        client_timeout=1.0,
        max_workers=1,
    )

    server.start()

    slow_connection: socket.socket | None = None
    fast_connection: socket.socket | None = None

    try:
        wait_for_server(server)

        slow_request = ControlRequest(
            command=KernelCommand.SYSTEM_STATUS,
            context=ControlContext(
                caller_id="slow-client",
                caller_type="cli",
            ),
        )

        fast_request = ControlRequest(
            command=KernelCommand.SYSTEM_STATUS,
            context=ControlContext(
                caller_id="fast-client",
                caller_type="cli",
            ),
        )

        slow_connection = socket.create_connection(
            (server.host, server.port),
            timeout=1.0,
        )
        slow_connection.sendall(
            ControlPlaneProtocol.encode_request(slow_request)
        )

        assert plane.started.wait(timeout=1.0)

        fast_connection = socket.create_connection(
            (server.host, server.port),
            timeout=1.0,
        )
        fast_connection.sendall(
            ControlPlaneProtocol.encode_request(fast_request)
        )
        fast_connection.settimeout(0.25)

        with pytest.raises(socket.timeout):
            fast_connection.recv(4096)

        plane.release.set()

        fast_connection.settimeout(1.0)
        response = fast_connection.recv(4096)

        fast_result = ControlPlaneProtocol.decode_response(response)

        assert fast_result.success is True
        assert fast_result.command == KernelCommand.SYSTEM_STATUS.value
    finally:
        plane.release.set()

        for connection in (slow_connection, fast_connection):
            if connection is not None:
                try:
                    connection.close()
                except OSError:
                    pass

        server.stop()


def test_server_rejects_invalid_max_workers() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        create_server(max_workers=0)

    with pytest.raises(ValueError, match="greater than zero"):
        create_server(max_workers=-1)

    with pytest.raises(TypeError, match="must be an integer"):
        create_server(max_workers="4")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must be an integer"):
        create_server(max_workers=True)  # type: ignore[arg-type]


def test_server_exposes_max_workers() -> None:
    server = create_server(max_workers=8)

    assert server.max_workers == 8
