from __future__ import annotations

import pytest

from sentinel.cli.kernel_control import CLIKernelControl
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpoint,
    ControlPlaneEndpointRegistry,
)
from sentinel.control_plane.result import ControlResult


def test_kernel_control_rejects_invalid_registry() -> None:
    with pytest.raises(TypeError):
        CLIKernelControl(
            endpoint_registry="invalid"  # type: ignore[arg-type]
        )


def test_kernel_control_rejects_invalid_command(tmp_path) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    adapter = CLIKernelControl(
        endpoint_registry=registry,
    )

    with pytest.raises(TypeError):
        adapter.execute(
            "service.list"  # type: ignore[arg-type]
        )


def test_kernel_control_discovers_endpoint_and_executes(
    tmp_path,
    monkeypatch,
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    registry.publish(
        ControlPlaneEndpoint(
            version=1,
            host="127.0.0.1",
            port=53142,
        )
    )

    captured = {}

    class FakeClient:
        def __init__(
            self,
            host: str,
            port: int,
        ) -> None:
            captured["host"] = host
            captured["port"] = port

        def execute(self, request):
            captured["request"] = request

            return ControlResult(
                success=True,
                command=request.command.value,
                data={
                    "services": [
                        "execution",
                    ],
                },
            )

    monkeypatch.setattr(
        "sentinel.cli.kernel_control.ControlPlaneTransportClient",
        FakeClient,
    )

    adapter = CLIKernelControl(
        endpoint_registry=registry,
    )

    result = adapter.execute(
        KernelCommand.SERVICE_LIST,
    )

    assert result.success is True
    assert result.data == {
        "services": [
            "execution",
        ],
    }

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 53142

    request = captured["request"]

    assert request.command is KernelCommand.SERVICE_LIST
    assert request.context.caller_id == "cli"
    assert request.context.caller_type.value == "cli"


def test_kernel_control_passes_command_data(
    tmp_path,
    monkeypatch,
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    registry.publish(
        ControlPlaneEndpoint(
            version=1,
            host="127.0.0.1",
            port=53142,
        )
    )

    captured = {}

    class FakeClient:
        def __init__(
            self,
            host: str,
            port: int,
        ) -> None:
            pass

        def execute(self, request):
            captured["request"] = request

            return ControlResult(
                success=True,
                command=request.command.value,
                data={
                    "name": "execution",
                },
            )

    monkeypatch.setattr(
        "sentinel.cli.kernel_control.ControlPlaneTransportClient",
        FakeClient,
    )

    adapter = CLIKernelControl(
        endpoint_registry=registry,
    )

    result = adapter.execute(
        KernelCommand.SERVICE_STATUS,
        {
            "name": "execution",
        },
    )

    assert result.success is True

    request = captured["request"]

    assert request.command is KernelCommand.SERVICE_STATUS
    assert request.data == {
        "name": "execution",
    }

def test_kernel_control_requires_complete_tls_credentials(tmp_path) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )
    registry.publish(
        ControlPlaneEndpoint(version=1, host="127.0.0.1", port=53142)
    )
    adapter = CLIKernelControl(
        endpoint_registry=registry,
        environ={"SENTINEL_ADMIN_USERNAME": "test-admin"},
    )

    with pytest.raises(RuntimeError, match="SENTINEL_TLS_CA_FILE"):
        adapter.execute(KernelCommand.SERVICE_LIST)


def test_kernel_control_passes_tls_and_credentials(
    tmp_path,
    monkeypatch,
) -> None:
    import ssl

    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )
    registry.publish(
        ControlPlaneEndpoint(version=1, host="127.0.0.1", port=53142)
    )

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    captured = {}

    class FakeClient:
        def __init__(self, host, port, **kwargs):
            captured["host"] = host
            captured["port"] = port
            captured.update(kwargs)

        def execute(self, request):
            return ControlResult(
                success=True,
                command=request.command.value,
                data={"services": []},
            )

    monkeypatch.setattr(
        "sentinel.cli.kernel_control.ssl.create_default_context",
        lambda purpose, cafile: context,
    )
    monkeypatch.setattr(
        "sentinel.cli.kernel_control.ControlPlaneTransportClient",
        FakeClient,
    )

    adapter = CLIKernelControl(
        endpoint_registry=registry,
        environ={
            "SENTINEL_ADMIN_USERNAME": "test-admin",
            "SENTINEL_ADMIN_SECRET": "test-secret-value",
            "SENTINEL_TLS_CA_FILE": "test-ca.pem",
        },
    )
    result = adapter.execute(KernelCommand.SERVICE_LIST)

    assert result.success is True
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 53142
    assert captured["ssl_context"] is context
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert captured["credentials"].username == "test-admin"
    assert captured["credentials"].secret == "test-secret-value"
