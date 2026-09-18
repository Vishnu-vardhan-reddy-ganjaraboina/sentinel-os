from __future__ import annotations

import json
from pathlib import Path

import pytest

from sentinel.control import (
    ControlEndpoint,
    ControlEndpointRegistry,
)


def test_endpoint_defaults() -> None:
    endpoint = ControlEndpoint(port=12345)

    assert endpoint.host == "127.0.0.1"
    assert endpoint.port == 12345


def test_endpoint_to_dict() -> None:
    endpoint = ControlEndpoint(port=12345)

    assert endpoint.to_dict() == {
        "host": "127.0.0.1",
        "port": 12345,
    }


@pytest.mark.parametrize(
    "host",
    ["0.0.0.0", "localhost", "", "::1"],
)
def test_endpoint_rejects_non_loopback(host: str) -> None:
    with pytest.raises(ValueError):
        ControlEndpoint(host=host, port=12345)


@pytest.mark.parametrize(
    "port",
    [0, -1, 65536],
)
def test_endpoint_rejects_invalid_ports(port: int) -> None:
    with pytest.raises(ValueError):
        ControlEndpoint(port=port)


def test_endpoint_from_dict() -> None:
    endpoint = ControlEndpoint.from_dict(
        {
            "host": "127.0.0.1",
            "port": 12345,
        }
    )

    assert endpoint == ControlEndpoint(port=12345)


def test_registry_initially_missing(tmp_path: Path) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    assert registry.exists() is False

    with pytest.raises(FileNotFoundError):
        registry.load()


def test_registry_save_and_load(tmp_path: Path) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    endpoint = ControlEndpoint(port=12345)

    registry.save(endpoint)

    assert registry.exists() is True
    assert registry.load() == endpoint


def test_registry_file_format(tmp_path: Path) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    registry.save(
        ControlEndpoint(port=12345),
    )

    payload = json.loads(
        registry.path.read_text(encoding="utf-8"),
    )

    assert payload["version"] == 1
    assert payload["endpoint"] == {
        "host": "127.0.0.1",
        "port": 12345,
    }


def test_registry_remove_is_idempotent(tmp_path: Path) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    registry.remove()
    registry.remove()

    assert registry.exists() is False


def test_registry_rejects_invalid_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ControlEndpointRegistry(
            tmp_path / "endpoint.json",
        )


def test_registry_rejects_invalid_endpoint(tmp_path: Path) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    with pytest.raises(TypeError):
        registry.save(object())  # type: ignore[arg-type]


def test_registry_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "control.json"

    path.write_text(
        "not json",
        encoding="utf-8",
    )

    registry = ControlEndpointRegistry(path)

    with pytest.raises(ValueError):
        registry.load()


def test_registry_rejects_wrong_version(tmp_path: Path) -> None:
    path = tmp_path / "control.json"

    path.write_text(
        json.dumps(
            {
                "version": 999,
                "endpoint": {
                    "host": "127.0.0.1",
                    "port": 12345,
                },
            }
        ),
        encoding="utf-8",
    )

    registry = ControlEndpointRegistry(path)

    with pytest.raises(ValueError):
        registry.load()


def test_registry_rejects_invalid_endpoint_data(
    tmp_path: Path,
) -> None:
    path = tmp_path / "control.json"

    path.write_text(
        json.dumps(
            {
                "version": 1,
                "endpoint": {
                    "host": "0.0.0.0",
                    "port": 12345,
                },
            }
        ),
        encoding="utf-8",
    )

    registry = ControlEndpointRegistry(path)

    with pytest.raises(ValueError):
        registry.load()


def test_registry_creates_parent_directory(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "sentinel" / "control.json"

    registry = ControlEndpointRegistry(path)

    registry.save(
        ControlEndpoint(port=12345),
    )

    assert path.is_file()


def test_registry_repr(tmp_path: Path) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    assert "ControlEndpointRegistry" in repr(registry)

def test_clear_if_stale_removes_dead_endpoint(tmp_path: Path) -> None:
    import socket

    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    # Reserve a temporary local port and then release it.
    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.close()

    registry.save(
        ControlEndpoint(port=port),
    )

    assert registry.exists() is True

    removed = registry.clear_if_stale()

    assert removed is True
    assert registry.exists() is False


def test_clear_if_stale_keeps_active_endpoint(tmp_path: Path) -> None:
    import socket

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    server.bind(("127.0.0.1", 0))
    server.listen(1)

    try:
        port = server.getsockname()[1]

        registry = ControlEndpointRegistry(
            tmp_path / "control.json",
        )

        registry.save(
            ControlEndpoint(port=port),
        )

        removed = registry.clear_if_stale()

        assert removed is False
        assert registry.exists() is True

    finally:
        server.close()


def test_clear_if_stale_is_safe_when_registry_missing(
    tmp_path: Path,
) -> None:
    registry = ControlEndpointRegistry(
        tmp_path / "control.json",
    )

    assert registry.clear_if_stale() is False
    assert registry.exists() is False


def test_clear_if_stale_is_safe_for_invalid_registry(
    tmp_path: Path,
) -> None:
    path = tmp_path / "control.json"

    path.write_text(
        "invalid json",
        encoding="utf-8",
    )

    registry = ControlEndpointRegistry(path)

    assert registry.clear_if_stale() is False
    assert registry.exists() is True
