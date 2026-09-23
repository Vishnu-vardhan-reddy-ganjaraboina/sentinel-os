from __future__ import annotations

import socket

import pytest

from sentinel.control import ControlConnectionError, ControlProtocolError
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.transport import ControlPlaneProtocol
from sentinel.control_plane.transport_client import ControlPlaneTransportClient


class FakeSocket:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.sent: bytes | None = None
        self.timeout: float | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def sendall(self, data: bytes) -> None:
        self.sent = data

    def recv(self, size: int) -> bytes:
        response = self.response
        self.response = b""
        return response


def make_request() -> ControlRequest:
    return ControlRequest(
        command=KernelCommand.SYSTEM_HEALTH,
        context=ControlContext(
            caller_id="test-client",
            caller_type="cli",
        ),
    )


def test_client_properties() -> None:
    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
        timeout=3,
    )

    assert client.host == "127.0.0.1"
    assert client.port == 12345
    assert client.timeout == 3.0


def test_client_rejects_invalid_host() -> None:
    with pytest.raises(ValueError):
        ControlPlaneTransportClient(host="", port=12345)


def test_client_rejects_invalid_port_type() -> None:
    with pytest.raises(TypeError):
        ControlPlaneTransportClient(
            host="127.0.0.1",
            port="12345",
        )


def test_client_rejects_invalid_port_value() -> None:
    with pytest.raises(ValueError):
        ControlPlaneTransportClient(
            host="127.0.0.1",
            port=0,
        )


def test_client_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError):
        ControlPlaneTransportClient(
            host="127.0.0.1",
            port=12345,
            timeout=0,
        )


def test_client_rejects_invalid_request() -> None:
    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
    )

    with pytest.raises(TypeError):
        client.execute("invalid")


def test_client_executes_request(monkeypatch) -> None:
    expected = ControlResult(
        success=True,
        command=KernelCommand.SYSTEM_HEALTH.value,
        data={"healthy": True},
    )

    fake_socket = FakeSocket(
        ControlPlaneProtocol.encode_response(expected)
    )

    def fake_create_connection(address, timeout):
        assert address == ("127.0.0.1", 12345)
        assert timeout == 5.0
        return fake_socket

    monkeypatch.setattr(
        socket,
        "create_connection",
        fake_create_connection,
    )

    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
    )

    result = client.execute(make_request())

    assert result == expected

    assert fake_socket.sent is not None

    decoded_request = ControlPlaneProtocol.decode_request(
        fake_socket.sent
    )

    assert decoded_request == make_request()


def test_client_converts_connection_errors(monkeypatch) -> None:
    def fail_connection(address, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr(
        socket,
        "create_connection",
        fail_connection,
    )

    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
    )

    with pytest.raises(ControlConnectionError):
        client.execute(make_request())


def test_client_propagates_protocol_errors(monkeypatch) -> None:
    fake_socket = FakeSocket(b"invalid-json\n")

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda address, timeout: fake_socket,
    )

    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
    )

    with pytest.raises(ControlProtocolError):
        client.execute(make_request())


def test_client_rejects_empty_response(monkeypatch) -> None:
    fake_socket = FakeSocket(b"")

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda address, timeout: fake_socket,
    )

    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
    )

    with pytest.raises(ControlProtocolError):
        client.execute(make_request())


def test_client_rejects_oversized_response(monkeypatch) -> None:
    oversized = b"x" * (
        ControlPlaneTransportClient.MAX_RESPONSE_SIZE + 1
    )

    fake_socket = FakeSocket(oversized)

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda address, timeout: fake_socket,
    )

    client = ControlPlaneTransportClient(
        host="127.0.0.1",
        port=12345,
    )

    with pytest.raises(ControlProtocolError):
        client.execute(make_request())