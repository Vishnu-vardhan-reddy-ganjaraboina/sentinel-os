from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.cli import CLI


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


def test_status_without_process(capsys: pytest.CaptureFixture[str]) -> None:
    cli = CLI()

    result = cli.run(["status"])

    assert result == 0
    assert capsys.readouterr().out.strip() == (
        "Sentinel OS: stopped"
    )


def test_health_without_process(capsys: pytest.CaptureFixture[str]) -> None:
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
