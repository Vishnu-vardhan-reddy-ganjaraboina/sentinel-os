from pathlib import Path

import pytest

from sentinel.infrastructure.configuration import Configuration


def test_load_configuration() -> None:
    config = Configuration()
    config.load("configs/development.yaml")

    assert config.get("logging.level") == "INFO"


def test_missing_file() -> None:
    config = Configuration()

    with pytest.raises(FileNotFoundError):
        config.load("missing.yaml")


def test_default_value() -> None:
    config = Configuration()

    assert config.get("unknown.key", "default") == "default"


def test_exists() -> None:
    config = Configuration()
    config.load("configs/development.yaml")

    assert config.exists("logging.level")