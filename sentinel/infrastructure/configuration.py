"""
Configuration management for Sentinel OS.

This module is responsible for loading, validating, and providing
read-only access to application configuration stored in YAML files.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
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
            self._config = {}

        elif not isinstance(data, dict):
            raise ConfigurationError(
                "The root element of a configuration file "
                "must be a mapping (dictionary)."
            )

        else:
            self._config = data

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value using dot notation.

        Args:
            key:
                Dot-separated configuration key.

            default:
                Value returned if the key does not exist.

        Returns:
            The configuration value or the default value.

        Example:
            >>> config.get("database.host")
            'localhost'
        """
        value: Any = self._config

        for part in key.split("."):
            if not isinstance(value, dict):
                return default

            if part not in value:
                return default

            value = value[part]

        return value

    def exists(self, key: str) -> bool:
        """
        Determine whether a configuration key exists.

        Args:
            key:
                Dot-separated configuration key.

        Returns:
            True if the key exists, otherwise False.
        """
        return self.get(key, None) is not None

    def as_dict(self) -> dict[str, Any]:
        """
        Return a deep copy of the configuration.

        Returns:
            A deep copy of the entire configuration dictionary.
        """
        return deepcopy(self._config)