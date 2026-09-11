"""
Configuration management for Sentinel OS.

This module is responsible for loading, validating, and providing
read-only access to application configuration stored in YAML files.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

import yaml

from sentinel.core.exceptions import ConfigurationError


class Configuration:
    """
    Loads and provides access to Sentinel configuration.

    Configuration values can be accessed using dot notation.

    Example:
        >>> config = Configuration()
        >>> config.load("configs/sentinel.yaml")
        >>> config.get("logging.level")
        'INFO'
    """

    def __init__(self) -> None:
        """Initialize an empty configuration."""
        self._config: dict[str, Any] = {}
        self._lock = RLock()

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> Configuration:
        """
        Create configuration from a dictionary.

        The supplied data is deep-copied so callers cannot mutate
        configuration state after construction.

        Raises:
            TypeError:
                If data is not a dictionary.
        """
        if not isinstance(data, dict):
            raise TypeError("configuration data must be a dictionary")

        configuration = cls()

        with configuration._lock:
            configuration._config = deepcopy(data)

        return configuration

    def load(self, file_path: str | Path) -> None:
        """
        Load a YAML configuration file.

        Args:
            file_path:
                Path to the YAML configuration file.

        Raises:
            FileNotFoundError:
                If the configuration file does not exist.

            ConfigurationError:
                If the YAML file is invalid or its root element
                is not a mapping.
        """
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            raise FileNotFoundError(
                f"Configuration file not found: {path}"
            )

        try:
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"Invalid YAML configuration: {path}"
            ) from exc

        if data is None:
            new_config: dict[str, Any] = {}

        elif not isinstance(data, dict):
            raise ConfigurationError(
                "The root element of a configuration file "
                "must be a mapping (dictionary)."
            )

        else:
            new_config = deepcopy(data)

        with self._lock:
            self._config = new_config

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a configuration value using dot notation.

        Args:
            key:
                Dot-separated configuration key.

            default:
                Value returned if the key does not exist.

        Returns:
            The configuration value or the default value.

        Raises:
            TypeError:
                If key is not a string.

            ValueError:
                If key is empty or contains an empty component.
        """
        self._validate_key(key)

        with self._lock:
            value: Any = self._config

            for part in key.split("."):
                if not isinstance(value, dict):
                    return deepcopy(default)

                if part not in value:
                    return deepcopy(default)

                value = value[part]

            return deepcopy(value)

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Determine whether a configuration key exists.

        Unlike ``get()``, this correctly distinguishes an existing
        key whose value is ``None`` from a missing key.

        Args:
            key:
                Dot-separated configuration key.

        Returns:
            True if the key exists, otherwise False.
        """
        self._validate_key(key)

        with self._lock:
            value: Any = self._config

            for part in key.split("."):
                if not isinstance(value, dict):
                    return False

                if part not in value:
                    return False

                value = value[part]

            return True

    def as_dict(self) -> dict[str, Any]:
        """
        Return a deep copy of the configuration.

        Returns:
            A deep copy of the entire configuration dictionary.
        """
        with self._lock:
            return deepcopy(self._config)

    def validate(self) -> None:
        """
        Validate known Sentinel configuration values.

        Raises:
            ConfigurationError:
                If a configured value has an invalid type or value.
        """
        with self._lock:
            knowledge = deepcopy(
                self._config.get("knowledge", {})
            )

        if not isinstance(knowledge, dict):
            raise ConfigurationError(
                "The 'knowledge' configuration must be a mapping."
            )

        backend = knowledge.get(
            "backend",
            "memory",
        )

        if not isinstance(backend, str):
            raise ConfigurationError(
                "knowledge.backend must be a string."
            )

        backend = backend.strip().lower()

        if backend not in {"memory", "sqlite"}:
            raise ConfigurationError(
                f"Unsupported knowledge backend: '{backend}'."
            )

        if backend == "sqlite":
            database_path = knowledge.get(
                "database_path",
                "data/sentinel-knowledge.db",
            )

            if not isinstance(database_path, (str, Path)):
                raise ConfigurationError(
                    "knowledge.database_path must be a string or path."
                )

            if not str(database_path).strip():
                raise ConfigurationError(
                    "knowledge.database_path cannot be empty."
                )

    @staticmethod
    def _validate_key(key: str) -> None:
        """Validate a dotted configuration key."""
        if not isinstance(key, str):
            raise TypeError("configuration key must be a string")

        if not key.strip():
            raise ValueError("configuration key cannot be empty")

        if any(not part.strip() for part in key.split(".")):
            raise ValueError(
                "configuration key cannot contain empty components"
            )
