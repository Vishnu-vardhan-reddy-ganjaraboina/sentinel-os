import pytest

from sentinel.plugins.exceptions import (
    PluginNotFoundError,
    PluginRegistrationError,
)
from sentinel.plugins.plugin import SentinelPlugin
from sentinel.plugins.registry import SentinelPluginRegistry


def test_register():

    registry = SentinelPluginRegistry()
    plugin = SentinelPlugin("sample")

    registry.register(plugin)

    assert len(registry) == 1


def test_duplicate_registration():

    registry = SentinelPluginRegistry()
    plugin = SentinelPlugin("sample")

    registry.register(plugin)

    with pytest.raises(PluginRegistrationError):
        registry.register(plugin)


def test_get():

    registry = SentinelPluginRegistry()
    plugin = SentinelPlugin("sample")

    registry.register(plugin)

    assert registry.get("sample") is plugin


def test_plugin_not_found():

    registry = SentinelPluginRegistry()

    with pytest.raises(PluginNotFoundError):
        registry.get("missing")


def test_unregister():

    registry = SentinelPluginRegistry()
    plugin = SentinelPlugin("sample")

    registry.register(plugin)
    registry.unregister("sample")

    assert len(registry) == 0


def test_all():

    registry = SentinelPluginRegistry()

    registry.register(SentinelPlugin("one"))
    registry.register(SentinelPlugin("two"))

    assert len(registry.all()) == 2


def test_contains():

    registry = SentinelPluginRegistry()

    registry.register(SentinelPlugin("sample"))

    assert "sample" in registry


def test_clear():

    registry = SentinelPluginRegistry()

    registry.register(SentinelPlugin("sample"))

    registry.clear()

    assert len(registry) == 0


def test_to_dict():

    registry = SentinelPluginRegistry()

    registry.register(SentinelPlugin("sample"))

    data = registry.to_dict()

    assert "sample" in data
    assert data["sample"]["name"] == "sample"