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
    """

    def load(self, plugin: Plugin) -> None:

        if plugin.state != PluginState.REGISTERED:
            raise PluginLoadError(
                f"Cannot load plugin in state '{plugin.state.value}'."
            )

        plugin.load()

    def enable(self, plugin: Plugin) -> None:

        if plugin.state != PluginState.LOADED:
            raise PluginEnableError(
                f"Cannot enable plugin in state '{plugin.state.value}'."
            )

        plugin.enable()

    def disable(self, plugin: Plugin) -> None:

        if plugin.state != PluginState.ENABLED:
            raise PluginDisableError(
                f"Cannot disable plugin in state '{plugin.state.value}'."
            )

        plugin.disable()

    def unload(self, plugin: Plugin) -> None:

        if plugin.state not in (
            PluginState.LOADED,
            PluginState.DISABLED,
        ):
            raise PluginUnloadError(
                f"Cannot unload plugin in state '{plugin.state.value}'."
            )

        plugin.unload()