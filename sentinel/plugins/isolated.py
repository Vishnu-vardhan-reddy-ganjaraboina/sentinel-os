"""Plugin lifecycle proxy that dispatches hooks to isolated worker processes."""

from __future__ import annotations

from collections.abc import Mapping

from sentinel.execution.isolated_worker import IsolatedWorker
from sentinel.plugins.constants import PluginState, PluginType
from sentinel.plugins.plugin import SentinelPlugin


class IsolatedPlugin(SentinelPlugin):
    """A plugin proxy whose optional lifecycle hooks run in child processes.

    Hook references must be importable functions from modules explicitly
    allowlisted by the worker. Each hook receives ``plugin_name`` as a keyword.
    This is process isolation, not a filesystem/network sandbox.
    """

    _HOOKS = {"load", "enable", "disable", "unload"}

    def __init__(
        self,
        name: str,
        *,
        worker: IsolatedWorker,
        hooks: Mapping[str, str],
        plugin_type: PluginType = PluginType.USER,
        version: str = "1.0.0",
        timeout: float = 30.0,
    ) -> None:
        if not isinstance(worker, IsolatedWorker):
            raise TypeError("worker must be an IsolatedWorker.")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")
        if not set(hooks).issubset(self._HOOKS):
            raise ValueError("hooks may only define load/enable/disable/unload.")
        if any(
            not isinstance(value, str) or ":" not in value
            for value in hooks.values()
        ):
            raise ValueError("Each hook must use 'module:qualified_name'.")
        super().__init__(name, plugin_type=plugin_type, version=version)
        self._worker = worker
        self._hooks = dict(hooks)
        self._timeout = timeout

    def _dispatch(self, operation: str) -> None:
        reference = self._hooks.get(operation)
        if reference is not None:
            self._worker.execute(
                reference,
                plugin_name=self.name,
                timeout=self._timeout,
            )

    def load(self) -> None:
        if self.state is not PluginState.REGISTERED:
            super().load()  # Raise the canonical lifecycle error before dispatch.
        self._dispatch("load")
        super().load()

    def enable(self) -> None:
        if self.state is not PluginState.LOADED:
            super().enable()
        self._dispatch("enable")
        super().enable()

    def disable(self) -> None:
        if self.state is not PluginState.ENABLED:
            super().disable()
        self._dispatch("disable")
        super().disable()

    def unload(self) -> None:
        if self.state not in {PluginState.LOADED, PluginState.DISABLED}:
            super().unload()
        self._dispatch("unload")
        super().unload()
