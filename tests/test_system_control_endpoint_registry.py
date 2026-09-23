from __future__ import annotations

import json

import pytest

from sentinel.boot.system_factory import SystemFactory
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpointRegistry,
)
from sentinel.control_plane.transport_server import (
    ControlPlaneTransportServer,
)
from sentinel.system import System


def test_factory_composes_endpoint_registry() -> None:
    factory = SystemFactory()
    system = factory.create()

    assert system.endpoint_registry is not None
    assert isinstance(
        system.endpoint_registry,
        ControlPlaneEndpointRegistry,
    )


def test_endpoint_is_not_registered_before_system_start() -> None:
    factory = SystemFactory()
    system = factory.create()

    registry = system.endpoint_registry
    assert registry is not None

    assert registry.registered is False


def test_system_start_publishes_endpoint() -> None:
    factory = SystemFactory()
    system = factory.create()

    registry = system.endpoint_registry
    transport = system.control_transport

    assert registry is not None
    assert transport is not None

    system.start()

    try:
        assert system.running is True
        assert registry.registered is True

        endpoint = registry.load()

        assert endpoint.version == 1
        assert endpoint.host == transport.host
        assert endpoint.port == transport.port
        assert endpoint.port > 0
    finally:
        system.shutdown()


def test_published_endpoint_contains_actual_transport_port() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    try:
        registry = system.endpoint_registry
        transport = system.control_transport

        assert registry is not None
        assert transport is not None

        endpoint = registry.load()

        assert endpoint.port == transport.port
    finally:
        system.shutdown()


def test_system_shutdown_removes_endpoint() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    registry = system.endpoint_registry
    assert registry is not None
    assert registry.registered is True

    system.shutdown()

    assert registry.registered is False


def test_endpoint_file_contains_expected_json() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    try:
        registry = system.endpoint_registry
        transport = system.control_transport

        assert registry is not None
        assert transport is not None

        with registry.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        assert data == {
            "host": transport.host,
            "port": transport.port,
            "version": 1,
        }
    finally:
        system.shutdown()


def test_endpoint_registry_requires_control_transport() -> None:
    factory = SystemFactory()
    system = factory.create()

    registry = ControlPlaneEndpointRegistry(
        path=system.endpoint_registry.path
        if system.endpoint_registry is not None
        else "kernel-control.json",
    )

    replacement = System(
        kernel=system.kernel,
        platform=system.platform,
        control_plane=system.control_plane,
        control_transport=None,
        endpoint_registry=registry,
    )

    with pytest.raises(
        RuntimeError,
        match="Endpoint registry requires",
    ):
        replacement.start()

    assert registry.registered is False


def test_system_health_reports_endpoint_registry() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    try:
        health = system.health()

        assert health["endpoint_registry"]["configured"] is True
        assert health["endpoint_registry"]["registered"] is True
        assert health["endpoint_registry"]["healthy"] is True
    finally:
        system.shutdown()


def test_system_health_before_start_reports_registry_as_not_registered() -> None:
    factory = SystemFactory()
    system = factory.create()

    health = system.health()

    assert health["running"] is False
    assert health["endpoint_registry"]["configured"] is True
    assert health["endpoint_registry"]["registered"] is False
    assert health["endpoint_registry"]["healthy"] is True