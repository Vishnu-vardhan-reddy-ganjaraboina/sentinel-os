"""
Plugin implementation for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from typing import Any

from sentinel.plugins.constants import (
    DEFAULT_PLUGIN_VERSION,
    PluginState,
    PluginType,
)
from sentinel.plugins.interfaces import Plugin


class SentinelPlugin(Plugin):
    """
    Default implementation of a Sentinel plugin.
    """

    def __init__(
        self,
        name: str,
        plugin_type: PluginType = PluginType.USER,
        version: str = DEFAULT_PLUGIN_VERSION,
    ) -> None:

        if not name:
            raise ValueError("name cannot be empty")

        if not isinstance(plugin_type, PluginType):
            raise TypeError("plugin_type must be a PluginType")

        if not version:
            raise ValueError("version cannot be empty")

        self._name = name
        self._plugin_type = plugin_type
        self._version = version
        self._state = PluginState.REGISTERED

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def plugin_type(self) -> PluginType:
        return self._plugin_type

    @property
    def state(self) -> PluginState:
        return self._state

    def load(self) -> None:
        self._state = PluginState.LOADED

    def enable(self) -> None:
        self._state = PluginState.ENABLED

    def disable(self) -> None:
        self._state = PluginState.DISABLED

    def unload(self) -> None:
        self._state = PluginState.UNLOADED

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "plugin_type": self.plugin_type.value,
            "state": self.state.value,
        }

    def __repr__(self) -> str:
        return (
            f"SentinelPlugin("
            f"name={self.name!r}, "
            f"version={self.version!r}, "
            f"state={self.state.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SentinelPlugin):
            return False

        return (
            self.name == other.name
            and self.version == other.version
            and self.plugin_type == other.plugin_type
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.name,
                self.version,
                self.plugin_type,
            )
        )