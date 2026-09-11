"""
Registry implementation for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from threading import RLock
from typing import Any

from sentinel.plugins.exceptions import (
    PluginNotFoundError,
    PluginRegistrationError,
)
from sentinel.plugins.interfaces import (
    Plugin,
    PluginRegistry,
)


class SentinelPluginRegistry(PluginRegistry):
    """
    Thread-safe registry for Sentinel plugins.

    The registry owns plugin registration metadata but does not execute
    plugin lifecycle operations.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._lock = RLock()

    def register(
        self,
        plugin: Plugin,
    ) -> None:
        """
        Register a plugin.

        Raises:
            TypeError:
                If the supplied object is not a Plugin.

            PluginRegistrationError:
                If the plugin name is invalid or already registered.
        """
        if not isinstance(plugin, Plugin):
            raise TypeError(
                "plugin must implement Plugin"
            )

        name = plugin.name

        if not isinstance(name, str):
            raise TypeError(
                "plugin.name must be a string"
            )

        if not name.strip():
            raise PluginRegistrationError(
                "Plugin name cannot be empty."
            )

        with self._lock:
            if name in self._plugins:
                raise PluginRegistrationError(
                    f"Plugin '{name}' is already registered."
                )

            self._plugins[name] = plugin

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        Remove a registered plugin.

        Raises:
            TypeError:
                If name is not a string.

            ValueError:
                If name is empty.

            PluginNotFoundError:
                If the plugin is not registered.
        """
        self._validate_name(name)

        with self._lock:
            if name not in self._plugins:
                raise PluginNotFoundError(
                    f"Plugin '{name}' not found."
                )

            del self._plugins[name]

    def get(
        self,
        name: str,
    ) -> Plugin:
        """
        Return a registered plugin instance.
        """
        self._validate_name(name)

        with self._lock:
            try:
                return self._plugins[name]
            except KeyError as exc:
                raise PluginNotFoundError(
                    f"Plugin '{name}' not found."
                ) from exc

    def all(self) -> list[Plugin]:
        """
        Return a snapshot of registered plugin references.
        """
        with self._lock:
            return list(self._plugins.values())

    def clear(self) -> None:
        """
        Remove all registered plugins.
        """
        with self._lock:
            self._plugins.clear()

    def to_dict(self) -> dict[str, Any]:
        """
        Return a snapshot of plugin metadata.
        """
        with self._lock:
            plugins = list(self._plugins.items())

        return {
            name: plugin.to_dict()
            for name, plugin in plugins
        }

    def __contains__(
        self,
        name: str,
    ) -> bool:
        if not isinstance(name, str):
            return False

        with self._lock:
            return name in self._plugins

    def __len__(self) -> int:
        with self._lock:
            return len(self._plugins)

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate a plugin name."""
        if not isinstance(name, str):
            raise TypeError(
                "plugin name must be a string"
            )

        if not name.strip():
            raise ValueError(
                "plugin name cannot be empty"
            )
