from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.boot import BootManager
from sentinel.control import (
    ControlClient,
    ControlCommand,
    ControlConnectionError,
    ControlServer,
)
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.process import ProcessHost


class ControlTestService(Service):
    def __init__(self) -> None:
        super().__init__("control-test")

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


def make_process_host() -> ProcessHost:
    kernel = Kernel()
    kernel.register(ControlTestService())

    from sentinel.system import System

    system = System(kernel)
    manager = BootManager(system)
    return ProcessHost(manager)


def test_server_constructor() -> None:
    host = make_process_host()

    server = ControlServer(host)

    assert server.process_host is host
    assert server.host == "127.0.0.1"
    assert server.port == 0
    assert server.running is False


def test_server_rejects_invalid_process_host() -> None:
    with pytest.raises(TypeError):
        ControlServer(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "host",
    ["localhost", "0.0.0.0", "::1", "", None],
)
def test_server_rejects_non_loopback_host(host: object) -> None:
    process = make_process_host()

    with pytest.raises((TypeError, ValueError)):
        ControlServer(
            process,
            host=host,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "port",
    [-1, 65536, "9000", None],
)
def test_server_rejects_invalid_port(port: object) -> None:
    process = make_process_host()

    with pytest.raises((TypeError, ValueError)):
        ControlServer(
            process,
            port=port,  # type: ignore[arg-type]
        )


def test_server_start_and_stop() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.start()

    assert server.running is True
    assert server.port > 0
    assert server.address == ("127.0.0.1", server.port)

    server.stop()

    assert server.running is False


def test_server_start_twice_is_rejected() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.start()

    with pytest.raises(
        RuntimeError,
        match="already running",
    ):
        server.start()

    server.stop()


def test_server_stop_before_start_is_safe() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.stop()

    assert server.running is False


def test_client_status() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.start()

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.status()

        assert success is True
        assert error is None
        assert data["state"] == "stopped"
        assert data["running"] is False
    finally:
        server.stop()


def test_client_health() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.start()
    process.start()

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.health()

        assert success is True
        assert error is None
        assert data["state"] == "running"
        assert data["running"] is True
        assert data["healthy"] is True
    finally:
        process.stop()
        server.stop()


def test_client_stop_requests_shutdown() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.start()
    process.start()

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.stop()

        assert success is True
        assert error is None
        assert data["state"] == "running"
        assert data["stop_requested"] is True
        assert process.wait(0) is True
        assert process.running is True
    finally:
        process.stop()
        server.stop()


def test_client_request_supports_explicit_command() -> None:
    process = make_process_host()
    server = ControlServer(process)

    server.start()

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.request(
            ControlCommand.STATUS
        )

        assert success is True
        assert error is None
        assert data["state"] == "stopped"
    finally:
        server.stop()


def test_client_connection_failure() -> None:
    # Port 1 is normally unavailable for this local control protocol.
    client = ControlClient(
        port=1,
        timeout=0.1,
    )

    with pytest.raises(ControlConnectionError):
        client.status()


def test_server_context_manager() -> None:
    process = make_process_host()
    server = ControlServer(process)

    with server as active:
        assert active is server
        assert server.running is True

    assert server.running is False


def test_client_properties_and_repr() -> None:
    client = ControlClient(
        port=12345,
        timeout=2.5,
    )

    assert client.host == "127.0.0.1"
    assert client.port == 12345
    assert client.timeout == 2.5

    representation = repr(client)

    assert "ControlClient" in representation
    assert "127.0.0.1" in representation
    assert "12345" in representation


def test_server_repr() -> None:
    process = make_process_host()
    server = ControlServer(process)

    representation = repr(server)

    assert "ControlServer" in representation
    assert "127.0.0.1" in representation
    assert "running=False" in representation
