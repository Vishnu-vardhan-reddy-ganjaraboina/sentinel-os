"""
Loader implementation for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from sentinel.plugins.constants import PluginState
from sentinel.plugins.exceptions import (
    PluginDisableError,
    PluginEnableError,
    PluginLoadError,
    PluginUnloadError,
)
from sentinel.plugins.interfaces import (
    Plugin,
    PluginLoader,
)


class SentinelPluginLoader(PluginLoader):
    """
    Handles the lifecycle of Sentinel plugins.

    The loader validates lifecycle preconditions and normalizes unexpected
    plugin implementation failures into the corresponding lifecycle error.
    """

    @staticmethod
    def _validate_plugin(plugin: Plugin) -> None:
        """Validate a plugin object before lifecycle operations."""
        if not isinstance(plugin, Plugin):
            raise TypeError(
                "plugin must implement Plugin"
            )

    def load(self, plugin: Plugin) -> None:
        self._validate_plugin(plugin)

        if plugin.state != PluginState.REGISTERED:
            raise PluginLoadError(
                f"Cannot load plugin in state "
                f"'{plugin.state.value}'."
            )

        try:
            plugin.load()
        except PluginLoadError:
            raise
        except Exception as exc:
            raise PluginLoadError(
                f"Failed to load plugin '{plugin.name}'."
            ) from exc

    def enable(self, plugin: Plugin) -> None:
        self._validate_plugin(plugin)

        if plugin.state != PluginState.LOADED:
            raise PluginEnableError(
                f"Cannot enable plugin in state "
                f"'{plugin.state.value}'."
            )

        try:
            plugin.enable()
        except PluginEnableError:
            raise
        except Exception as exc:
            raise PluginEnableError(
                f"Failed to enable plugin '{plugin.name}'."
            ) from exc

    def disable(self, plugin: Plugin) -> None:
        self._validate_plugin(plugin)

        if plugin.state != PluginState.ENABLED:
            raise PluginDisableError(
                f"Cannot disable plugin in state "
                f"'{plugin.state.value}'."
            )

        try:
            plugin.disable()
        except PluginDisableError:
            raise
        except Exception as exc:
            raise PluginDisableError(
                f"Failed to disable plugin '{plugin.name}'."
            ) from exc

    def unload(self, plugin: Plugin) -> None:
        self._validate_plugin(plugin)

        if plugin.state not in (
            PluginState.LOADED,
            PluginState.DISABLED,
        ):
            raise PluginUnloadError(
                f"Cannot unload plugin in state "
                f"'{plugin.state.value}'."
            )

        try:
            plugin.unload()
        except PluginUnloadError:
            raise
        except Exception as exc:
            raise PluginUnloadError(
                f"Failed to unload plugin '{plugin.name}'."
            ) from exc
