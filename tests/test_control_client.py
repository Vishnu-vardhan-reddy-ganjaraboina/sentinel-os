from __future__ import annotations

import socket

import pytest

from sentinel.boot import BootManager
from sentinel.control import (
    ControlClient,
    ControlCommand,
    ControlConnectionError,
    ControlServer,
)
from sentinel.process import ProcessHost
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.system import System


class ControlTestService(Service):
    def __init__(self) -> None:
        super().__init__("control-test")

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


def make_host() -> ProcessHost:
    kernel = Kernel()
    kernel.register(ControlTestService())

    system = System(kernel)
    boot = BootManager(system)

    host = ProcessHost(boot)
    host.start()

    return host


def make_server(
    host: ProcessHost,
) -> ControlServer:
    server = ControlServer(
        host,
        port=0,
    )
    server.start()
    return server


def test_client_status() -> None:
    host = make_host()
    server = make_server(host)

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.status()

        assert success is True
        assert error is None
        assert data["state"] == "running"
        assert data["running"] is True

    finally:
        server.stop()
        host.stop()


def test_client_health() -> None:
    host = make_host()
    server = make_server(host)

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.health()

        assert success is True
        assert error is None
        assert data["state"] == "running"
        assert data["running"] is True
        assert data["healthy"] is True

    finally:
        server.stop()
        host.stop()


def test_client_stop_requests_shutdown() -> None:
    host = make_host()
    server = make_server(host)

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.stop()

        assert success is True
        assert error is None
        assert data["stop_requested"] is True
        assert data["state"] == "running"

        assert host.wait(0.5) is True

        host.stop()

        assert host.running is False

    finally:
        server.stop()


def test_client_generic_request() -> None:
    host = make_host()
    server = make_server(host)

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.request(
            ControlCommand.STATUS,
        )

        assert success is True
        assert data["running"] is True
        assert error is None

    finally:
        server.stop()
        host.stop()


def test_server_rejects_command_data() -> None:
    host = make_host()
    server = make_server(host)

    try:
        client = ControlClient(port=server.port)

        success, data, error = client.request(
            ControlCommand.STATUS,
            {"unexpected": True},
        )

        assert success is False
        assert data == {}
        assert error is not None
        assert "not supported" in error

    finally:
        server.stop()
        host.stop()


@pytest.mark.parametrize(
    "port",
    [1, 65535],
)
def test_client_accepts_valid_ports(port: int) -> None:
    client = ControlClient(port=port)

    assert client.port == port


@pytest.mark.parametrize(
    "port",
    [0, -1, 65536],
)
def test_client_rejects_invalid_ports(port: int) -> None:
    with pytest.raises(ValueError):
        ControlClient(port=port)


def test_client_rejects_non_loopback_host() -> None:
    with pytest.raises(
        ValueError,
        match="127.0.0.1",
    ):
        ControlClient(
            host="0.0.0.0",
            port=12345,
        )


def test_server_rejects_non_loopback_host() -> None:
    host = make_host()

    try:
        with pytest.raises(
            ValueError,
            match="127.0.0.1",
        ):
            ControlServer(
                host,
                host="0.0.0.0",
            )
    finally:
        host.stop()


def test_connection_failure() -> None:
    # Reserve a local port and then release it, leaving no server behind.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    client = ControlClient(
        port=port,
        timeout=0.2,
    )

    with pytest.raises(ControlConnectionError):
        client.status()


def test_server_context_manager() -> None:
    host = make_host()

    try:
        with ControlServer(host, port=0) as server:
            client = ControlClient(port=server.port)

            success, data, error = client.status()

            assert success is True
            assert data["running"] is True
            assert error is None

    finally:
        host.stop()


def test_server_port_zero_selects_ephemeral_port() -> None:
    host = make_host()
    server = ControlServer(host, port=0)

    try:
        assert server.port == 0

        server.start()

        assert server.port != 0
        assert server.address == (
            "127.0.0.1",
            server.port,
        )

    finally:
        server.stop()
        host.stop()


def test_server_start_twice_rejected() -> None:
    host = make_host()
    server = ControlServer(host, port=0)

    try:
        server.start()

        with pytest.raises(
            RuntimeError,
            match="already running",
        ):
            server.start()

    finally:
        server.stop()
        host.stop()


def test_server_stop_is_idempotent() -> None:
    host = make_host()
    server = ControlServer(host, port=0)

    server.stop()
    server.stop()

    host.stop()


def test_client_repr() -> None:
    client = ControlClient(
        port=12345,
        timeout=2.5,
    )

    representation = repr(client)

    assert "ControlClient" in representation
    assert "127.0.0.1" in representation
    assert "12345" in representation
