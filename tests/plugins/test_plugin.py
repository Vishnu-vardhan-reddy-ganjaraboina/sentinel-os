import threading

import pytest

from sentinel.plugins.constants import (
    DEFAULT_PLUGIN_VERSION,
    PluginState,
    PluginType,
)
from sentinel.plugins.exceptions import (
    PluginDisableError,
    PluginEnableError,
    PluginLoadError,
    PluginUnloadError,
)
from sentinel.plugins.plugin import SentinelPlugin


def test_create_plugin():

    plugin = SentinelPlugin("sample")

    assert plugin.name == "sample"
    assert plugin.version == DEFAULT_PLUGIN_VERSION
    assert plugin.plugin_type == PluginType.USER
    assert plugin.state == PluginState.REGISTERED


def test_lifecycle():

    plugin = SentinelPlugin("sample")

    plugin.load()
    assert plugin.state == PluginState.LOADED

    plugin.enable()
    assert plugin.state == PluginState.ENABLED

    plugin.disable()
    assert plugin.state == PluginState.DISABLED

    plugin.unload()
    assert plugin.state == PluginState.UNLOADED


def test_to_dict():

    plugin = SentinelPlugin("sample")

    data = plugin.to_dict()

    assert data["name"] == "sample"
    assert data["version"] == DEFAULT_PLUGIN_VERSION
    assert data["plugin_type"] == PluginType.USER.value
    assert data["state"] == PluginState.REGISTERED.value


def test_repr():

    plugin = SentinelPlugin("sample")

    assert "SentinelPlugin" in repr(plugin)


def test_equality():

    a = SentinelPlugin("plugin")
    b = SentinelPlugin("plugin")

    assert a == b


def test_hash():

    plugin = SentinelPlugin("plugin")

    assert isinstance(hash(plugin), int)


def test_invalid_name():

    with pytest.raises(ValueError):
        SentinelPlugin("")


def test_invalid_type():

    with pytest.raises(TypeError):
        SentinelPlugin(
            "plugin",
            plugin_type="USER",
        )


def test_invalid_version():

    with pytest.raises(ValueError):
        SentinelPlugin(
            "plugin",
            version="",
        )

def test_invalid_lifecycle_transitions() -> None:
    plugin = SentinelPlugin("sample")

    with pytest.raises(PluginEnableError):
        plugin.enable()

    with pytest.raises(PluginDisableError):
        plugin.disable()

    with pytest.raises(PluginUnloadError):
        plugin.unload()


def test_cannot_load_twice() -> None:
    plugin = SentinelPlugin("sample")

    plugin.load()

    with pytest.raises(PluginLoadError):
        plugin.load()


def test_cannot_enable_twice() -> None:
    plugin = SentinelPlugin("sample")

    plugin.load()
    plugin.enable()

    with pytest.raises(PluginEnableError):
        plugin.enable()


def test_cannot_disable_twice() -> None:
    plugin = SentinelPlugin("sample")

    plugin.load()
    plugin.enable()
    plugin.disable()

    with pytest.raises(PluginDisableError):
        plugin.disable()


def test_cannot_unload_twice() -> None:
    plugin = SentinelPlugin("sample")

    plugin.load()
    plugin.unload()

    with pytest.raises(PluginUnloadError):
        plugin.unload()


def test_invalid_name_type() -> None:
    with pytest.raises(TypeError):
        SentinelPlugin(123)  # type: ignore[arg-type]


def test_invalid_version_type() -> None:
    with pytest.raises(TypeError):
        SentinelPlugin(
            "sample",
            version=123,  # type: ignore[arg-type]
        )


def test_concurrent_load_only_one_transition_succeeds() -> None:
    plugin = SentinelPlugin("sample")

    barrier = threading.Barrier(20)
    successes = 0
    failures = 0
    lock = threading.Lock()

    def load_plugin() -> None:
        nonlocal successes, failures

        barrier.wait()

        try:
            plugin.load()
        except PluginLoadError:
            with lock:
                failures += 1
        else:
            with lock:
                successes += 1

    threads = [
        threading.Thread(target=load_plugin)
        for _ in range(20)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert successes == 1
    assert failures == 19
    assert plugin.state == PluginState.LOADED

def test_concurrent_enable_only_one_transition_succeeds() -> None:
    plugin = SentinelPlugin("sample")
    plugin.load()

    barrier = threading.Barrier(20)
    successes = 0
    failures = 0
    lock = threading.Lock()

    def enable_plugin() -> None:
        nonlocal successes, failures

        barrier.wait()

        try:
            plugin.enable()
        except PluginEnableError:
            with lock:
                failures += 1
        else:
            with lock:
                successes += 1

    threads = [
        threading.Thread(target=enable_plugin)
        for _ in range(20)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert successes == 1
    assert failures == 19
    assert plugin.state == PluginState.ENABLED

def test_concurrent_disable_only_one_transition_succeeds() -> None:
    plugin = SentinelPlugin("sample")
    plugin.load()
    plugin.enable()

    barrier = threading.Barrier(20)
    successes = 0
    failures = 0
    lock = threading.Lock()

    def disable_plugin() -> None:
        nonlocal successes, failures

        barrier.wait()

        try:
            plugin.disable()
        except PluginDisableError:
            with lock:
                failures += 1
        else:
            with lock:
                successes += 1

    threads = [
        threading.Thread(target=disable_plugin)
        for _ in range(20)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert successes == 1
    assert failures == 19
    assert plugin.state == PluginState.DISABLED

def test_concurrent_unload_only_one_transition_succeeds() -> None:
    plugin = SentinelPlugin("sample")
    plugin.load()

    barrier = threading.Barrier(20)
    successes = 0
    failures = 0
    lock = threading.Lock()

    def unload_plugin() -> None:
        nonlocal successes, failures

        barrier.wait()

        try:
            plugin.unload()
        except PluginUnloadError:
            with lock:
                failures += 1
        else:
            with lock:
                successes += 1

    threads = [
        threading.Thread(target=unload_plugin)
        for _ in range(20)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert successes == 1
    assert failures == 19
    assert plugin.state == PluginState.UNLOADED
