"""
Registry implementation for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

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
    Stores and manages registered plugins.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(
        self,
        plugin: Plugin,
    ) -> None:

        if plugin.name in self._plugins:
            raise PluginRegistrationError(
                f"Plugin '{plugin.name}' is already registered."
            )

        self._plugins[plugin.name] = plugin

    def unregister(
        self,
        name: str,
    ) -> None:

        if name not in self._plugins:
            raise PluginNotFoundError(
                f"Plugin '{name}' not found."
            )

        del self._plugins[name]

    def get(
        self,
        name: str,
    ) -> Plugin:

        if name not in self._plugins:
            raise PluginNotFoundError(
                f"Plugin '{name}' not found."
            )

        return self._plugins[name]

    def all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def clear(self) -> None:
        self._plugins.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            name: plugin.to_dict()
            for name, plugin in self._plugins.items()
        }

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __len__(self) -> int:
        return len(self._plugins)