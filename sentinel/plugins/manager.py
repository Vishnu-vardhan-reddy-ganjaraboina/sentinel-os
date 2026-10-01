"""
Manager for the Sentinel Plugin subsystem.
"""

from __future__ import annotations

from threading import RLock

from sentinel.plugins.constants import PluginState
from sentinel.plugins.exceptions import PluginCleanupError
from sentinel.plugins.interfaces import Plugin
from sentinel.plugins.loader import SentinelPluginLoader
from sentinel.plugins.registry import SentinelPluginRegistry


class PluginManager:
    """
    Coordinates plugin registration and lifecycle management.

    Responsibilities are deliberately separated:

    - PluginRegistry owns registry storage synchronization.
    - PluginLoader owns lifecycle validation and error normalization.
    - Plugin owns its lifecycle state machine.
    - PluginManager owns multi-step orchestration.

    The manager lock prevents concurrent orchestration operations from
    interleaving in unsafe ways.
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

        self._lock = RLock()

    @property
    def registry(self) -> SentinelPluginRegistry:
        return self._registry

    @property
    def loader(self) -> SentinelPluginLoader:
        return self._loader

    def register(self, plugin: Plugin) -> None:
        with self._lock:
            self._registry.register(plugin)

    def unregister(self, name: str) -> None:
        with self._lock:
            self._registry.unregister(name)

    def get(self, name: str) -> Plugin:
        with self._lock:
            return self._registry.get(name)

    def load(self, name: str) -> None:
        with self._lock:
            plugin = self._registry.get(name)
            self._loader.load(plugin)

    def enable(self, name: str) -> None:
        with self._lock:
            plugin = self._registry.get(name)
            self._loader.enable(plugin)

    def disable(self, name: str) -> None:
        with self._lock:
            plugin = self._registry.get(name)
            self._loader.disable(plugin)

    def unload(self, name: str) -> None:
        with self._lock:
            plugin = self._registry.get(name)
            self._loader.unload(plugin)

    def plugins(self) -> list[Plugin]:
        with self._lock:
            return self._registry.all()

    def clear(self) -> None:
        """
        Clean up every registered plugin.

        Cleanup is best-effort:

        - One plugin failure does not prevent other plugins from being
          cleaned up.
        - A plugin that cannot be safely unloaded remains registered.
        - Successfully cleaned plugins are removed from the registry.
        - Multiple failures are reported together.
        """
        with self._lock:
            plugins = self._registry.all()
            failures: list[Exception] = []
            cleaned: list[str] = []

            for plugin in plugins:
                try:
                    self._cleanup_plugin(plugin)
                except Exception as exc:
                    failures.append(exc)
                    continue

                cleaned.append(plugin.name)

            for name in cleaned:
                try:
                    self._registry.unregister(name)
                except Exception as exc:
                    failures.append(exc)

            if failures:
                if len(failures) == 1:
                    raise PluginCleanupError(
                        "One or more plugins could not be cleaned up."
                    ) from failures[0]

                group = ExceptionGroup(
                    "Multiple plugin cleanup failures.",
                    failures,
                )

                raise PluginCleanupError(
                    "One or more plugins could not be cleaned up."
                ) from group

    def _cleanup_plugin(self, plugin: Plugin) -> None:
        """
        Clean up one plugin according to its current lifecycle state.
        """
        state = plugin.state

        if state == PluginState.ENABLED:
            self._loader.disable(plugin)
            state = plugin.state

        if state in {
            PluginState.LOADED,
            PluginState.DISABLED,
        }:
            self._loader.unload(plugin)

        elif state in {
            PluginState.REGISTERED,
            PluginState.UNLOADED,
        }:
            return

        else:
            raise PluginCleanupError(
                f"Plugin '{plugin.name}' has unsupported state "
                f"'{state.value}'."
            )

    def __len__(self) -> int:
        with self._lock:
            return len(self._registry)