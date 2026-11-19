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
            control_plane = deepcopy(
                self._config.get("control_plane", {})
            )

        if not isinstance(control_plane, dict):
            raise ConfigurationError(
                "The control_plane configuration must be a mapping."
            )

        tls = control_plane.get("tls", {})
        if not isinstance(tls, dict):
            raise ConfigurationError(
                "control_plane.tls must be a mapping."
            )

        tls_enabled = tls.get("enabled", False)
        if not isinstance(tls_enabled, bool):
            raise ConfigurationError(
                "control_plane.tls.enabled must be a Boolean."
            )

        for path_key in ("certfile", "keyfile"):
            if path_key in tls:
                path_value = tls[path_key]
                if not isinstance(path_value, str) or not path_value.strip():
                    raise ConfigurationError(
                        f"control_plane.tls.{path_key} must be a non-empty string."
                    )

        if tls_enabled:
            for path_key in ("certfile", "keyfile"):
                path_value = tls.get(path_key)
                if not isinstance(path_value, str) or not path_value.strip():
                    raise ConfigurationError(
                        f"control_plane.tls.{path_key} is required when TLS is enabled."
                    )


        authentication = control_plane.get("authentication", {})
        if not isinstance(authentication, dict):
            raise ConfigurationError(
                "control_plane.authentication must be a mapping."
            )

        authentication_enabled = authentication.get("enabled", False)
        if not isinstance(authentication_enabled, bool):
            raise ConfigurationError(
                "control_plane.authentication.enabled must be a Boolean."
            )

        if authentication_enabled and not tls_enabled:
            raise ConfigurationError(
                "control_plane.authentication.enabled requires TLS."
            )


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

        embedding = knowledge.get("embedding", {})
        if not isinstance(embedding, dict):
            raise ConfigurationError(
                "knowledge.embedding must be a mapping."
            )

        provider = embedding.get("provider", "dummy")
        if not isinstance(provider, str):
            raise ConfigurationError(
                "knowledge.embedding.provider must be a string."
            )

        provider = provider.strip().lower()
        if provider not in {"dummy", "sentence-transformers"}:
            raise ConfigurationError(
                f"Unsupported knowledge embedding provider: '{provider}'."
            )

        for key in ("model", "device"):
            if key in embedding:
                value = embedding[key]
                if not isinstance(value, str) or not value.strip():
                    raise ConfigurationError(
                        f"knowledge.embedding.{key} must be a non-empty string."
                    )

        if "batch_size" in embedding:
            batch_size = embedding["batch_size"]
            if (
                isinstance(batch_size, bool)
                or not isinstance(batch_size, int)
                or batch_size <= 0
            ):
                raise ConfigurationError(
                    "knowledge.embedding.batch_size must be a positive integer."
                )
        with self._lock:
            storage = deepcopy(self._config.get("storage", {}))

        if not isinstance(storage, dict):
            raise ConfigurationError(
                "The 'storage' configuration must be a mapping."
            )

        storage_backend = storage.get("backend", "memory")
        if not isinstance(storage_backend, str):
            raise ConfigurationError(
                "storage.backend must be a string."
            )

        storage_backend = storage_backend.strip().lower()
        if storage_backend not in {"memory", "filesystem", "sqlite"}:
            raise ConfigurationError(
                f"Unsupported storage backend: '{storage_backend}'."
            )

        if storage_backend == "sqlite":
            storage_database = storage.get("database", "data/sentinel.db")
            if not isinstance(storage_database, (str, Path)):
                raise ConfigurationError(
                    "storage.database must be a string or path."
                )
            if not str(storage_database).strip():
                raise ConfigurationError(
                    "storage.database cannot be empty."
                )

        if storage_backend == "filesystem":
            storage_directory = storage.get("directory", "data/storage")
            if not isinstance(storage_directory, (str, Path)):
                raise ConfigurationError(
                    "storage.directory must be a string or path."
                )
            if not str(storage_directory).strip():
                raise ConfigurationError(
                    "storage.directory cannot be empty."
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
