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