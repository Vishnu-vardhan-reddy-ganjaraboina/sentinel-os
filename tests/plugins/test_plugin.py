import pytest

from sentinel.plugins.constants import (
    DEFAULT_PLUGIN_VERSION,
    PluginState,
    PluginType,
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