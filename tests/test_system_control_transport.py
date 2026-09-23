from __future__ import annotations

import time

import pytest

from sentinel.boot.system_factory import SystemFactory
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.transport_client import (
    ControlPlaneTransportClient,
)


def wait_for_transport(system) -> None:
    transport = system.control_transport

    assert transport is not None

    deadline = time.monotonic() + 2.0

    while not transport.running:
        if time.monotonic() >= deadline:
            raise AssertionError(
                "Control Plane transport failed to start."
            )

        time.sleep(0.01)


def test_factory_composes_control_transport() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.control_transport is not None
    assert (
        system.control_transport.control_plane
        is system.control_plane
    )


def test_control_transport_is_not_started_during_composition() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.running is False
    assert system.control_transport is not None
    assert system.control_transport.running is False


def test_system_start_starts_control_transport() -> None:
    factory = SystemFactory()

    system = factory.create()

    system.start()

    try:
        assert system.running is True
        assert system.control_transport is not None
        assert system.control_transport.running is True
        assert system.control_transport.port > 0
    finally:
        system.shutdown()


def test_system_shutdown_stops_control_transport() -> None:
    factory = SystemFactory()

    system = factory.create()

    system.start()

    transport = system.control_transport

    assert transport is not None
    assert transport.running is True

    system.shutdown()

    assert system.running is False
    assert transport.running is False


def test_external_client_can_query_running_system() -> None:
    factory = SystemFactory()

    system = factory.create()
    system.start()

    try:
        wait_for_transport(system)

        transport = system.control_transport

        assert transport is not None

        client = ControlPlaneTransportClient(
            host=transport.host,
            port=transport.port,
        )

        request = ControlRequest(
            command=KernelCommand.SERVICE_LIST,
            context=ControlContext(
                caller_id="system",
                caller_type="system",
            ),
        )

        result = client.execute(request)

        assert result.success is True

        assert set(result.data["services"]) == {
            "execution",
            "memory",
            "knowledge",
            "orchestration",
        }

    finally:
        system.shutdown()


def test_system_health_reports_control_transport() -> None:
    factory = SystemFactory()

    system = factory.create()

    system.start()

    try:
        health = system.health()

        assert health["control_transport"]["configured"] is True
        assert health["control_transport"]["running"] is True
        assert health["control_transport"]["healthy"] is True
        assert health["control_transport"]["port"] > 0

    finally:
        system.shutdown()


def test_system_health_before_start_reports_transport_as_not_running() -> None:
    factory = SystemFactory()

    system = factory.create()

    health = system.health()

    assert health["running"] is False

    assert health["control_transport"]["configured"] is True
    assert health["control_transport"]["running"] is False
    assert health["control_transport"]["healthy"] is True


def test_system_rejects_transport_from_different_control_plane() -> None:
    factory_one = SystemFactory()
    system_one = factory_one.create()

    factory_two = SystemFactory()
    system_two = factory_two.create()

    assert system_one.control_plane is not system_two.control_plane

    with pytest.raises(
        ValueError,
        match="same ControlPlane",
    ):
        from sentinel.control_plane.transport_server import (
            ControlPlaneTransportServer,
        )

        transport = ControlPlaneTransportServer(
            control_plane=system_one.control_plane,
            host="127.0.0.1",
            port=0,
        )

        # Reuse Kernel/Platform from system_two but provide the
        # transport belonging to system_one.
        from sentinel.system import System

        System(
            kernel=system_two.kernel,
            platform=system_two.platform,
            control_plane=system_two.control_plane,
            control_transport=transport,
        )