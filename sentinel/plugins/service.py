"""
Service layer for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from sentinel.plugins.interfaces import Plugin
from sentinel.plugins.manager import PluginManager


class PluginService:
    """
    Public service interface for the Plugin subsystem.
    """

    def __init__(
        self,
        manager: PluginManager | None = None,
    ) -> None:

        self._manager = (
            manager
            if manager is not None
            else PluginManager()
        )

    @property
    def manager(self) -> PluginManager:
        return self._manager

    def register(
        self,
        plugin: Plugin,
    ) -> None:
        self._manager.register(plugin)

    def unregister(
        self,
        name: str,
    ) -> None:
        self._manager.unregister(name)

    def get(
        self,
        name: str,
    ) -> Plugin:
        return self._manager.get(name)

    def load(
        self,
        name: str,
    ) -> None:
        self._manager.load(name)

    def enable(
        self,
        name: str,
    ) -> None:
        self._manager.enable(name)

    def disable(
        self,
        name: str,
    ) -> None:
        self._manager.disable(name)

    def unload(
        self,
        name: str,
    ) -> None:
        self._manager.unload(name)

    def plugins(self) -> list[Plugin]:
        return self._manager.plugins()

    def clear(self) -> None:
        self._manager.clear()

    def __len__(self) -> int:
        return len(self._manager)