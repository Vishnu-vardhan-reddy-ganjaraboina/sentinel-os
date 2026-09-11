
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

def test_from_dict_rejects_non_mapping() -> None:
    with pytest.raises(TypeError, match="dictionary"):
        Configuration.from_dict([])  # type: ignore[arg-type]


def test_get_returns_deep_copy() -> None:
    config = Configuration.from_dict(
        {
            "database": {
                "options": {
                    "timeout": 30,
                },
            },
        }
    )

    value = config.get("database.options")

    value["timeout"] = 999

    assert config.get("database.options")["timeout"] == 30


def test_exists_handles_none_value() -> None:
    config = Configuration.from_dict(
        {
            "feature": None,
        }
    )

    assert config.exists("feature") is True


def test_invalid_configuration_key() -> None:
    config = Configuration()

    with pytest.raises(ValueError):
        config.get("")

    with pytest.raises(ValueError):
        config.get("database..host")


def test_load_uses_copy() -> None:
    config = Configuration.from_dict(
        {
            "feature": {
                "enabled": True,
            },
        }
    )

    exported = config.as_dict()
    exported["feature"]["enabled"] = False

    assert config.get("feature.enabled") is True
