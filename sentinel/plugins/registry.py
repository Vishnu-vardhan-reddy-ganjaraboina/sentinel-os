"""
Registry implementation for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from threading import RLock
from typing import Any

from sentinel.plugins.constants import PluginState
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

    The registry owns plugin registration metadata and synchronization.
    It does not execute plugin lifecycle operations.

    The lifecycle lock coordinates multi-step PluginManager operations
    with direct registry mutations. This prevents a direct registry
    mutation from racing a manager-owned lifecycle transition.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._lock = RLock()
        self._lifecycle_lock = RLock()

    def _lifecycle_context(self) -> AbstractContextManager[object]:
        """
        Return the registry lifecycle lock as a context manager.

        PluginManager uses this lock around multi-step lifecycle
        operations so direct registry mutations cannot interleave
        between plugin lookup and lifecycle execution.
        """
        return self._lifecycle_lock

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
            raise TypeError("plugin must implement Plugin")

        name = plugin.name

        if not isinstance(name, str):
            raise TypeError("plugin.name must be a string")

        if not name.strip():
            raise PluginRegistrationError(
                "Plugin name cannot be empty."
            )

        with self._lifecycle_context():
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
        Remove a safely removable plugin from the registry.

        Plugins that are still part of the active lifecycle cannot be
        removed directly. Lifecycle cleanup must be performed through
        the PluginManager.

        Raises:
            TypeError:
                If name is not a string.

            ValueError:
                If name is empty.

            PluginNotFoundError:
                If the plugin is not registered.

            PluginRegistrationError:
                If the plugin is still loaded, enabled, or disabled.
        """
        self._validate_name(name)

        with self._lifecycle_context():
            with self._lock:
                try:
                    plugin = self._plugins[name]
                except KeyError as exc:
                    raise PluginNotFoundError(
                        f"Plugin '{name}' not found."
                    ) from exc

                if plugin.state in {
                    PluginState.LOADED,
                    PluginState.ENABLED,
                    PluginState.DISABLED,
                }:
                    raise PluginRegistrationError(
                        f"Plugin '{name}' cannot be unregistered while "
                        f"in state '{plugin.state.value}'. "
                        "Use PluginManager lifecycle operations first."
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
        Remove plugins that are safe to unregister.

        Active lifecycle states are preserved. Lifecycle cleanup should
        be performed by PluginManager before registry removal.
        """
        with self._lifecycle_context():
            with self._lock:
                removable = [
                    name
                    for name, plugin in self._plugins.items()
                    if plugin.state
                    in {
                        PluginState.REGISTERED,
                        PluginState.UNLOADED,
                    }
                ]

                for name in removable:
                    del self._plugins[name]

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
            raise TypeError("plugin name must be a string")

        if not name.strip():
            raise ValueError("plugin name cannot be empty")
