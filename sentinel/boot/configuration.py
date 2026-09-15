"""
Boot configuration adapter for Sentinel OS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sentinel.boot.exceptions import BootConfigurationError
from sentinel.infrastructure.configuration import Configuration


class BootConfiguration:
    """
    Load and validate the configuration required to boot Sentinel OS.

    This class intentionally delegates YAML parsing and general
    configuration handling to the existing Infrastructure Configuration
    subsystem.
    """

    def __init__(
        self,
        configuration: Configuration | None = None,
    ) -> None:
        if configuration is not None and not isinstance(
            configuration,
            Configuration,
        ):
            raise TypeError(
                "configuration must be a Configuration instance."
            )

        self._configuration = (
            configuration
            if configuration is not None
            else Configuration()
        )

    @property
    def configuration(self) -> Configuration:
        """Return the underlying configuration object."""
        return self._configuration

    def load(self, file_path: str | Path) -> None:
        """
        Load and validate a boot configuration file.
        """
        try:
            self._configuration.load(file_path)
            self._configuration.validate()
        except Exception as exc:
            if isinstance(exc, BootConfigurationError):
                raise

            raise BootConfigurationError(
                f"Failed to load boot configuration: {file_path}"
            ) from exc

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return a configuration value."""
        return self._configuration.get(key, default)

    def exists(self, key: str) -> bool:
        """Return whether a configuration key exists."""
        return self._configuration.exists(key)

    def as_dict(self) -> dict[str, Any]:
        """Return an isolated configuration snapshot."""
        return self._configuration.as_dict()

    def __repr__(self) -> str:
        return (
            "BootConfiguration("
            f"configuration={self._configuration.as_dict()!r}"
            ")"
        )
