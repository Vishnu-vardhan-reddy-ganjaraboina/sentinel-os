from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.cli import CLI
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpointRegistry,
)
from sentinel.control_plane.result import ControlResult


def test_help_parser() -> None:
    parser = CLI._build_parser()

    args = parser.parse_args(
        [
            "start",
            "--config",
            "custom.yaml",
            "--profile",
            "development",
        ]
    )

    assert args.command == "start"
    assert args.config == Path("custom.yaml")
    assert args.profile == "development"


def test_system_status_parser() -> None:
    parser = CLI._build_parser()

    args = parser.parse_args(
        [
            "system",
            "status",
        ]
    )

    assert args.command == "system"
    assert args.system_command == "status"


def test_system_health_parser() -> None:
    parser = CLI._build_parser()

    args = parser.parse_args(
        [
            "system",
            "health",
        ]
    )

    assert args.command == "system"
    assert args.system_command == "health"


def test_service_list_parser() -> None:
    parser = CLI._build_parser()

    args = parser.parse_args(
        [
            "service",
            "list",
        ]
    )

    assert args.command == "service"
    assert args.service_command == "list"


@pytest.mark.parametrize(
    "command",
    [
        "status",
        "start",
        "stop",
        "restart",
    ],
)
def test_service_command_parser(command: str) -> None:
    parser = CLI._build_parser()

    args = parser.parse_args(
        [
            "service",
            command,
            "execution",
        ]
    )

    assert args.command == "service"
    assert args.service_command == command
    assert args.name == "execution"


def test_status_without_process(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = CLI()

    result = cli.run(["status"])

    assert result == 0

    assert capsys.readouterr().out.strip() == (
        "Sentinel OS: stopped"
    )


def test_health_without_process(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = CLI()

    result = cli.run(["health"])

    assert result == 1

    assert capsys.readouterr().out == (
        "Sentinel OS: stopped\n"
        "Healthy: false\n"
    )


def test_process_property_starts_empty() -> None:
    cli = CLI()

    assert cli.process is None
    assert cli.boot is None


def test_kernel_control_property_uses_registry(
    tmp_path,
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    assert cli.kernel_control.endpoint_registry is registry


def test_system_status_uses_kernel_control(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    captured = {}

    def fake_execute(command, data=None):
        captured["command"] = command
        captured["data"] = data

        return ControlResult(
            success=True,
            command=command.value,
            data={
                "running": True,
            },
        )

    monkeypatch.setattr(
        cli.kernel_control,
        "execute",
        fake_execute,
    )

    result = cli.run(
        [
            "system",
            "status",
        ]
    )

    assert result == 0
    assert captured["command"] is KernelCommand.SYSTEM_STATUS
    assert captured["data"] is None

    assert capsys.readouterr().out == (
        "running: True\n"
    )


def test_system_health_uses_kernel_control(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    captured = {}

    def fake_execute(command, data=None):
        captured["command"] = command
        captured["data"] = data

        return ControlResult(
            success=True,
            command=command.value,
            data={
                "healthy": True,
            },
        )

    monkeypatch.setattr(
        cli.kernel_control,
        "execute",
        fake_execute,
    )

    result = cli.run(
        [
            "system",
            "health",
        ]
    )

    assert result == 0
    assert captured["command"] is KernelCommand.SYSTEM_HEALTH
    assert captured["data"] is None

    assert capsys.readouterr().out == (
        "healthy: True\n"
    )


def test_service_list_uses_kernel_control(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    captured = {}

    def fake_execute(command, data=None):
        captured["command"] = command
        captured["data"] = data

        return ControlResult(
            success=True,
            command=command.value,
            data={
                "services": [
                    "execution",
                    "memory",
                ],
            },
        )

    monkeypatch.setattr(
        cli.kernel_control,
        "execute",
        fake_execute,
    )

    result = cli.run(
        [
            "service",
            "list",
        ]
    )

    assert result == 0
    assert captured["command"] is KernelCommand.SERVICE_LIST
    assert captured["data"] == {}

    assert capsys.readouterr().out == (
        "services: ['execution', 'memory']\n"
    )


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (
            "status",
            KernelCommand.SERVICE_STATUS,
        ),
        (
            "start",
            KernelCommand.SERVICE_START,
        ),
        (
            "stop",
            KernelCommand.SERVICE_STOP,
        ),
        (
            "restart",
            KernelCommand.SERVICE_RESTART,
        ),
    ],
)
def test_service_command_uses_kernel_control(
    command: str,
    expected: KernelCommand,
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    captured = {}

    def fake_execute(kernel_command, data=None):
        captured["command"] = kernel_command
        captured["data"] = data

        return ControlResult(
            success=True,
            command=kernel_command.value,
            data={
                "name": "execution",
            },
        )

    monkeypatch.setattr(
        cli.kernel_control,
        "execute",
        fake_execute,
    )

    result = cli.run(
        [
            "service",
            command,
            "execution",
        ]
    )

    assert result == 0
    assert captured["command"] is expected
    assert captured["data"] == {
        "name": "execution",
    }

    assert capsys.readouterr().out == (
        "name: execution\n"
    )


def test_kernel_control_failure_returns_one(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    monkeypatch.setattr(
        cli.kernel_control,
        "execute",
        lambda command, data=None: ControlResult(
            success=False,
            command=command.value,
            error="Permission denied.",
        ),
    )

    result = cli.run(
        [
            "system",
            "health",
        ]
    )

    assert result == 1

    assert capsys.readouterr().out == (
        "Permission denied.\n"
    )


def test_kernel_control_connection_failure_returns_one(
    tmp_path,
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = ControlPlaneEndpointRegistry(
        tmp_path / "kernel-control.json"
    )

    cli = CLI(
        kernel_endpoint_registry=registry,
    )

    def fail_execute(command, data=None):
        raise RuntimeError(
            "connection failed"
        )

    monkeypatch.setattr(
        cli.kernel_control,
        "execute",
        fail_execute,
    )

    result = cli.run(
        [
            "system",
            "status",
        ]
    )

    assert result == 1

    assert capsys.readouterr().out == (
        "Unable to contact Kernel Control Plane: "
        "connection failed\n"
    )