from __future__ import annotations

import json

import pytest

from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpoint,
    ControlPlaneEndpointRegistry,
)


def test_endpoint_validates_values() -> None:
    endpoint = ControlPlaneEndpoint(
        version=1,
        host="127.0.0.1",
        port=53142,
    )

    assert endpoint.version == 1
    assert endpoint.host == "127.0.0.1"
    assert endpoint.port == 53142


@pytest.mark.parametrize(
    "port",
    [0, -1, 65536],
)
def test_endpoint_rejects_invalid_port(port: int) -> None:
    with pytest.raises(ValueError):
        ControlPlaneEndpoint(
            version=1,
            host="127.0.0.1",
            port=port,
        )


def test_endpoint_rejects_empty_host() -> None:
    with pytest.raises(ValueError):
        ControlPlaneEndpoint(
            version=1,
            host="",
            port=53142,
        )


def test_registry_publishes_endpoint(tmp_path) -> None:
    path = tmp_path / "sentinel" / "kernel-control.json"
    registry = ControlPlaneEndpointRegistry(path)

    endpoint = ControlPlaneEndpoint(
        version=1,
        host="127.0.0.1",
        port=53142,
    )

    registry.publish(endpoint)

    assert registry.registered is True
    assert path.exists()

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    assert data == {
        "host": "127.0.0.1",
        "port": 53142,
        "version": 1,
    }


def test_registry_loads_endpoint(tmp_path) -> None:
    path = tmp_path / "kernel-control.json"
    registry = ControlPlaneEndpointRegistry(path)

    endpoint = ControlPlaneEndpoint(
        version=1,
        host="127.0.0.1",
        port=53142,
    )

    registry.publish(endpoint)

    loaded = registry.load()

    assert loaded == endpoint


def test_registry_clear_removes_endpoint(tmp_path) -> None:
    path = tmp_path / "kernel-control.json"
    registry = ControlPlaneEndpointRegistry(path)

    registry.publish(
        ControlPlaneEndpoint(
            version=1,
            host="127.0.0.1",
            port=53142,
        )
    )

    assert registry.registered is True

    registry.clear()

    assert registry.registered is False
    assert path.exists() is False


def test_registry_clear_is_idempotent(tmp_path) -> None:
    path = tmp_path / "kernel-control.json"
    registry = ControlPlaneEndpointRegistry(path)

    registry.clear()
    registry.clear()

    assert registry.registered is False


def test_registry_load_missing_endpoint_raises(tmp_path) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "missing.json"
    )

    with pytest.raises(FileNotFoundError):
        registry.load()


def test_endpoint_serialization_round_trip() -> None:
    endpoint = ControlPlaneEndpoint(
        version=1,
        host="127.0.0.1",
        port=53142,
    )

    restored = ControlPlaneEndpoint.from_mapping(
        endpoint.to_mapping()
    )

    assert restored == endpoint