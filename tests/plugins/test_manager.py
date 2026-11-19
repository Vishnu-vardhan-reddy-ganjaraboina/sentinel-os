import threading

import pytest

from sentinel.plugins.constants import PluginState
from sentinel.plugins.exceptions import (
    PluginCleanupError,
    PluginDisableError,
    PluginLoadError,
    PluginRegistrationError,
    PluginUnloadError,
)
from sentinel.plugins.loader import SentinelPluginLoader
from sentinel.plugins.manager import PluginManager
from sentinel.plugins.plugin import SentinelPlugin


def test_registry_property():
    manager = PluginManager()

    assert manager.registry is not None


def test_loader_property():
    manager = PluginManager()

    assert manager.loader is not None


def test_register():
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    assert len(manager) == 1


def test_get():
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    assert manager.get("sample") is plugin


def test_lifecycle():
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    manager.load("sample")
    assert plugin.state == PluginState.LOADED

    manager.enable("sample")
    assert plugin.state == PluginState.ENABLED

    manager.disable("sample")
    assert plugin.state == PluginState.DISABLED

    manager.unload("sample")
    assert plugin.state == PluginState.UNLOADED


def test_plugins():
    manager = PluginManager()

    manager.register(
        SentinelPlugin("one")
    )

    manager.register(
        SentinelPlugin("two")
    )

    assert len(manager.plugins()) == 2


def test_unregister():
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    manager.unregister("sample")

    assert len(manager) == 0


def test_clear():
    manager = PluginManager()

    manager.register(
        SentinelPlugin("sample")
    )

    manager.clear()

    assert len(manager) == 0


def test_invalid_registry_rejected() -> None:
    with pytest.raises(TypeError):
        PluginManager(
            registry=object(),  # type: ignore[arg-type]
        )


def test_invalid_loader_rejected() -> None:
    with pytest.raises(TypeError):
        PluginManager(
            loader=object(),  # type: ignore[arg-type]
        )


def test_clear_unloads_loaded_plugin() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)
    manager.load("sample")

    manager.clear()

    assert plugin.state == PluginState.UNLOADED
    assert len(manager) == 0


def test_clear_disables_and_unloads_enabled_plugin() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)
    manager.load("sample")
    manager.enable("sample")

    manager.clear()

    assert plugin.state == PluginState.UNLOADED
    assert len(manager) == 0


class FailingDisablePlugin(SentinelPlugin):
    def disable(self) -> None:
        raise PluginDisableError("disable failure")


class FailingUnloadPlugin(SentinelPlugin):
    def unload(self) -> None:
        raise PluginUnloadError("unload failure")


def test_clear_continues_after_plugin_cleanup_failure() -> None:
    manager = PluginManager()

    failing = FailingDisablePlugin("failing")
    healthy = SentinelPlugin("healthy")

    manager.register(failing)
    manager.register(healthy)

    manager.load("failing")
    failing.enable()

    manager.load("healthy")

    with pytest.raises(PluginCleanupError):
        manager.clear()

    assert "failing" in manager.registry
    assert "healthy" not in manager.registry

    assert failing.state == PluginState.ENABLED


def test_clear_removes_successfully_cleaned_plugins() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)
    manager.load("sample")

    manager.clear()

    assert plugin.state == PluginState.UNLOADED
    assert len(manager) == 0


def test_clear_unloads_disabled_plugin() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)
    manager.load("sample")
    manager.enable("sample")
    manager.disable("sample")

    manager.clear()

    assert plugin.state == PluginState.UNLOADED
    assert len(manager) == 0


def test_clear_removes_registered_plugin_without_lifecycle_operation() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    manager.clear()

    assert plugin.state == PluginState.REGISTERED
    assert len(manager) == 0


def test_clear_removes_already_unloaded_plugin() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)
    manager.load("sample")
    manager.unload("sample")

    manager.clear()

    assert plugin.state == PluginState.UNLOADED
    assert len(manager) == 0


def test_multiple_managers_can_share_registry() -> None:
    from sentinel.plugins.registry import SentinelPluginRegistry

    registry = SentinelPluginRegistry()
    manager_one = PluginManager(registry=registry)
    manager_two = PluginManager(registry=registry)

    plugin = SentinelPlugin("shared")

    manager_one.register(plugin)

    assert manager_two.get("shared") is plugin
    assert manager_one.registry is manager_two.registry

    manager_two.load("shared")

    assert plugin.state == PluginState.LOADED
    assert manager_one.get("shared") is plugin

def test_concurrent_manager_lifecycle_operations_are_serialized() -> None:
    manager = PluginManager()
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    errors: list[Exception] = []
    lock = threading.Lock()

    def load() -> None:
        try:
            manager.load("sample")
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=load)
        for _ in range(20)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert plugin.state == PluginState.LOADED

    assert sum(
        isinstance(error, PluginLoadError)
        for error in errors
    ) == 19


class BlockingLoader(SentinelPluginLoader):
    def __init__(self) -> None:
        self.load_started = threading.Event()
        self.allow_load = threading.Event()

    def load(self, plugin: SentinelPlugin) -> None:
        self.load_started.set()

        if not self.allow_load.wait(timeout=5):
            raise TimeoutError("timed out waiting for test release")

        plugin.load()


def test_direct_registry_mutation_cannot_race_manager_load() -> None:
    loader = BlockingLoader()
    manager = PluginManager(loader=loader)
    plugin = SentinelPlugin("sample")

    manager.register(plugin)

    load_errors: list[Exception] = []

    def load_plugin() -> None:
        try:
            manager.load("sample")
        except Exception as exc:
            load_errors.append(exc)

    load_thread = threading.Thread(target=load_plugin)
    load_thread.start()

    assert loader.load_started.wait(timeout=5)

    unregister_done = threading.Event()
    unregister_errors: list[Exception] = []

    def unregister_plugin() -> None:
        try:
            manager.registry.unregister("sample")
        except Exception as exc:
            unregister_errors.append(exc)
        finally:
            unregister_done.set()

    unregister_thread = threading.Thread(target=unregister_plugin)
    unregister_thread.start()

    # Direct registry mutation must wait for the manager-owned lifecycle
    # operation to finish.
    assert not unregister_done.wait(timeout=0.2)

    loader.allow_load.set()

    load_thread.join(timeout=5)
    unregister_thread.join(timeout=5)

    assert not load_errors
    assert len(unregister_errors) == 1
    assert isinstance(unregister_errors[0], PluginRegistrationError)
    assert plugin.state == PluginState.LOADED
    assert manager.get("sample") is plugin
