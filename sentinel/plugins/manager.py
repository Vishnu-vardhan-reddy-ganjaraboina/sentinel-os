"""
Manager for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from sentinel.plugins.constants import PluginState
from sentinel.plugins.interfaces import Plugin
from sentinel.plugins.loader import SentinelPluginLoader
from sentinel.plugins.registry import SentinelPluginRegistry


class PluginManager:
    """
    Coordinates plugin registration and lifecycle management.

    The manager owns orchestration only. Registry synchronization and
    lifecycle validation remain delegated to their respective components.
    """

    def __init__(
        self,
        registry: SentinelPluginRegistry | None = None,
        loader: SentinelPluginLoader | None = None,
    ) -> None:
        if registry is not None and not isinstance(
            registry,
            SentinelPluginRegistry,
        ):
            raise TypeError(
                "registry must be a SentinelPluginRegistry"
            )

        if loader is not None and not isinstance(
            loader,
            SentinelPluginLoader,
        ):
            raise TypeError(
                "loader must be a SentinelPluginLoader"
            )

        self._registry = (
            registry
            if registry is not None
            else SentinelPluginRegistry()
        )

        self._loader = (
            loader
            if loader is not None
            else SentinelPluginLoader()
        )

    @property
    def registry(self) -> SentinelPluginRegistry:
        return self._registry

    @property
    def loader(self) -> SentinelPluginLoader:
        return self._loader

    def register(self, plugin: Plugin) -> None:
        self._registry.register(plugin)

    def unregister(self, name: str) -> None:
        self._registry.unregister(name)

    def get(self, name: str) -> Plugin:
        return self._registry.get(name)

    def load(self, name: str) -> None:
        self._loader.load(
            self._registry.get(name)
        )

    def enable(self, name: str) -> None:
        self._loader.enable(
            self._registry.get(name)
        )

    def disable(self, name: str) -> None:
        self._loader.disable(
            self._registry.get(name)
        )

    def unload(self, name: str) -> None:
        self._loader.unload(
            self._registry.get(name)
        )

    def plugins(self) -> list[Plugin]:
        return self._registry.all()

    def clear(self) -> None:
        """
        Safely remove all plugins.

        Loaded or disabled plugins are unloaded before registry removal.
        Enabled plugins are disabled first, then unloaded.

        Plugins already in REGISTERED or UNLOADED states are simply removed.
        """
        plugins = self._registry.all()

        for plugin in plugins:
            if plugin.state == PluginState.ENABLED:
                self.disable(plugin.name)

            if plugin.state in {
                PluginState.LOADED,
                PluginState.DISABLED,
           }:
                self.unload(plugin.name)

        self._registry.clear()

    def __len__(self) -> int:
        return len(self._registry)
