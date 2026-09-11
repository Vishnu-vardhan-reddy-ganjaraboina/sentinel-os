import pytest

from sentinel.plugins.constants import PluginState
from sentinel.plugins.exceptions import (
    PluginDisableError,
    PluginEnableError,
    PluginLoadError,
    PluginUnloadError,
)
from sentinel.plugins.loader import SentinelPluginLoader
from sentinel.plugins.plugin import SentinelPlugin


def test_load():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)

    assert plugin.state == PluginState.LOADED


def test_enable():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)
    loader.enable(plugin)

    assert plugin.state == PluginState.ENABLED


def test_disable():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)
    loader.enable(plugin)
    loader.disable(plugin)

    assert plugin.state == PluginState.DISABLED


def test_unload():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)
    loader.unload(plugin)

    assert plugin.state == PluginState.UNLOADED


def test_unload_after_disable():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)
    loader.enable(plugin)
    loader.disable(plugin)
    loader.unload(plugin)

    assert plugin.state == PluginState.UNLOADED


def test_invalid_load():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)

    with pytest.raises(PluginLoadError):
        loader.load(plugin)


def test_invalid_enable():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    with pytest.raises(PluginEnableError):
        loader.enable(plugin)


def test_invalid_disable():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    loader.load(plugin)

    with pytest.raises(PluginDisableError):
        loader.disable(plugin)


def test_invalid_unload():

    loader = SentinelPluginLoader()
    plugin = SentinelPlugin("sample")

    with pytest.raises(PluginUnloadError):
        loader.unload(plugin)

class FailingLoadPlugin(SentinelPlugin):
    def load(self) -> None:
        raise RuntimeError("load failure")


class FailingEnablePlugin(SentinelPlugin):
    def enable(self) -> None:
        raise RuntimeError("enable failure")


class FailingDisablePlugin(SentinelPlugin):
    def disable(self) -> None:
        raise RuntimeError("disable failure")


class FailingUnloadPlugin(SentinelPlugin):
    def unload(self) -> None:
        raise RuntimeError("unload failure")


def test_load_failure_is_normalized() -> None:
    loader = SentinelPluginLoader()
    plugin = FailingLoadPlugin("sample")

    with pytest.raises(
        PluginLoadError,
        match="Failed to load",
    ):
        loader.load(plugin)


def test_enable_failure_is_normalized() -> None:
    loader = SentinelPluginLoader()
    plugin = FailingEnablePlugin("sample")

    loader.load(plugin)

    with pytest.raises(
        PluginEnableError,
        match="Failed to enable",
    ):
        loader.enable(plugin)


def test_disable_failure_is_normalized() -> None:
    loader = SentinelPluginLoader()
    plugin = FailingDisablePlugin("sample")

    loader.load(plugin)
    plugin.enable()

    with pytest.raises(
        PluginDisableError,
        match="Failed to disable",
    ):
        loader.disable(plugin)


def test_unload_failure_is_normalized() -> None:
    loader = SentinelPluginLoader()
    plugin = FailingUnloadPlugin("sample")

    loader.load(plugin)

    with pytest.raises(
        PluginUnloadError,
        match="Failed to unload",
    ):
        loader.unload(plugin)


def test_invalid_plugin_rejected() -> None:
    loader = SentinelPluginLoader()

    with pytest.raises(TypeError):
        loader.load(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        loader.enable(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        loader.disable(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        loader.unload(object())  # type: ignore[arg-type]