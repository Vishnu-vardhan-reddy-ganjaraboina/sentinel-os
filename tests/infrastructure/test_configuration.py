
import pytest

from sentinel.core.exceptions import ConfigurationError
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

def test_validate_default_configuration() -> None:
    config = Configuration()

    config.validate()


def test_validate_memory_backend() -> None:
    config = Configuration.from_dict(
        {
            "knowledge": {
                "backend": "memory",
            },
        }
    )

    config.validate()


def test_validate_sqlite_backend() -> None:
    config = Configuration.from_dict(
        {
            "knowledge": {
                "backend": "sqlite",
                "database_path": "data/knowledge.db",
            },
        }
    )

    config.validate()


def test_validate_rejects_unknown_backend() -> None:
    config = Configuration.from_dict(
        {
            "knowledge": {
                "backend": "redis",
            },
        }
    )

    with pytest.raises(
        ConfigurationError,
        match="Unsupported knowledge backend",
    ):
        config.validate()


def test_validate_rejects_invalid_backend_type() -> None:
    config = Configuration.from_dict(
        {
            "knowledge": {
                "backend": 123,
            },
        }
    )

    with pytest.raises(
        ConfigurationError,
        match="knowledge.backend must be a string",
    ):
        config.validate()


def test_validate_rejects_invalid_database_path() -> None:
    config = Configuration.from_dict(
        {
            "knowledge": {
                "backend": "sqlite",
                "database_path": 123,
            },
        }
    )

    with pytest.raises(
        ConfigurationError,
        match="knowledge.database_path",
    ):
        config.validate()


def test_validate_rejects_empty_database_path() -> None:
    config = Configuration.from_dict(
        {
            "knowledge": {
                "backend": "sqlite",
                "database_path": "   ",
            },
        }
    )

    with pytest.raises(
        ConfigurationError,
        match="database_path cannot be empty",
    ):
        config.validate()
