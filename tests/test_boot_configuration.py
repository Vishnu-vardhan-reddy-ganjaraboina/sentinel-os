from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.boot import BootConfiguration, BootConfigurationError
from sentinel.infrastructure.configuration import Configuration


def test_default_configuration() -> None:
    boot = BootConfiguration()

    assert isinstance(boot.configuration, Configuration)
    assert boot.as_dict() == {}


def test_load_configuration() -> None:
    boot = BootConfiguration()

    boot.load("configs/development.yaml")

    assert boot.get("logging.level") == "INFO"
    assert boot.get("kernel.max_services") == 100


def test_exists() -> None:
    boot = BootConfiguration()

    boot.load("configs/development.yaml")

    assert boot.exists("logging.level") is True
    assert boot.exists("missing.value") is False


def test_default_value() -> None:
    boot = BootConfiguration()

    assert boot.get("missing.value", "fallback") == "fallback"


def test_get_returns_copy() -> None:
    boot = BootConfiguration(
        Configuration.from_dict(
            {
                "nested": {
                    "value": 10,
                }
            }
        )
    )

    value = boot.get("nested")
    value["value"] = 99

    assert boot.get("nested.value") == 10


def test_as_dict_returns_copy() -> None:
    boot = BootConfiguration(
        Configuration.from_dict(
            {
                "nested": {
                    "value": 10,
                }
            }
        )
    )

    exported = boot.as_dict()
    exported["nested"]["value"] = 99

    assert boot.get("nested.value") == 10


def test_missing_file_becomes_boot_configuration_error() -> None:
    boot = BootConfiguration()

    with pytest.raises(
        BootConfigurationError,
        match="Failed to load boot configuration",
    ):
        boot.load("missing-boot-config.yaml")


def test_invalid_configuration_becomes_boot_configuration_error(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(
        """
knowledge:
  backend: redis
""",
        encoding="utf-8",
    )

    boot = BootConfiguration()

    with pytest.raises(
        BootConfigurationError,
        match="Failed to load boot configuration",
    ):
        boot.load(config_file)


def test_invalid_constructor_configuration() -> None:
    with pytest.raises(TypeError):
        BootConfiguration(object())  # type: ignore[arg-type]


def test_repr() -> None:
    boot = BootConfiguration(
        Configuration.from_dict({"feature": {"enabled": True}})
    )

    representation = repr(boot)

    assert "BootConfiguration" in representation
    assert "feature" in representation
