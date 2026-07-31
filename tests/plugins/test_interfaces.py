import pytest

from sentinel.plugins.constants import PluginState, PluginType
from sentinel.plugins.interfaces import (
    Plugin,
    PluginLoader,
    PluginRegistry,
)


class DummyPlugin(Plugin):

    def __init__(self):
        self._state = PluginState.REGISTERED

    @property
    def name(self):
        return "dummy"

    @property
    def version(self):
        return "1.0.0"

    @property
    def plugin_type(self):
        return PluginType.USER

    @property
    def state(self):
        return self._state

    def load(self):
        self._state = PluginState.LOADED

    def enable(self):
        self._state = PluginState.ENABLED

    def disable(self):
        self._state = PluginState.DISABLED

    def unload(self):
        self._state = PluginState.UNLOADED

    def to_dict(self):
        return {
            "name": self.name,
            "version": self.version,
            "plugin_type": self.plugin_type.value,
            "state": self.state.value,
        }


class DummyRegistry(PluginRegistry):

    def __init__(self):
        self.plugins = {}

    def register(self, plugin):
        self.plugins[plugin.name] = plugin

    def unregister(self, name):
        self.plugins.pop(name)

    def get(self, name):
        return self.plugins[name]

    def all(self):
        return list(self.plugins.values())


class DummyLoader(PluginLoader):

    def load(self, plugin):
        plugin.load()

    def enable(self, plugin):
        plugin.enable()

    def disable(self, plugin):
        plugin.disable()

    def unload(self, plugin):
        plugin.unload()


def test_plugin():

    plugin = DummyPlugin()

    assert plugin.name == "dummy"
    assert plugin.version == "1.0.0"

    plugin.load()
    assert plugin.state == PluginState.LOADED

    plugin.enable()
    assert plugin.state == PluginState.ENABLED

    plugin.disable()
    assert plugin.state == PluginState.DISABLED

    plugin.unload()
    assert plugin.state == PluginState.UNLOADED

    assert plugin.to_dict()["name"] == "dummy"


def test_registry():

    registry = DummyRegistry()
    plugin = DummyPlugin()

    registry.register(plugin)

    assert registry.get("dummy") is plugin
    assert len(registry.all()) == 1

    registry.unregister("dummy")

    assert registry.all() == []


def test_loader():

    loader = DummyLoader()
    plugin = DummyPlugin()

    loader.load(plugin)
    assert plugin.state == PluginState.LOADED

    loader.enable(plugin)
    assert plugin.state == PluginState.ENABLED

    loader.disable(plugin)
    assert plugin.state == PluginState.DISABLED

    loader.unload(plugin)
    assert plugin.state == PluginState.UNLOADED


def test_plugin_is_abstract():
    with pytest.raises(TypeError):
        Plugin()


def test_registry_is_abstract():
    with pytest.raises(TypeError):
        PluginRegistry()


def test_loader_is_abstract():
    with pytest.raises(TypeError):
        PluginLoader()