"""
Configuration management for Sentinel OS.

Loads and provides access to YAML configuration files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class Configuration:
    """Loads and provides application configuration."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    def load(self, file_path: str | Path) -> None:
        """
        Load a YAML configuration file.

        Args:
            file_path: Path to the YAML configuration file.

        Raises:
            FileNotFoundError:
                If the configuration file does not exist.

            ValueError:
                If the YAML is invalid.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {path}"
            )

        try:
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            self._config = data or {}

        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid YAML configuration: {path}"
            ) from exc

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value using dot notation.

        Example:
            config.get("logging.level")
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
        Check whether a configuration key exists.
        """
        return self.get(key, None) is not None

    def as_dict(self) -> dict[str, Any]:
        """
        Return the entire configuration.
        """
        return self._config.copy()