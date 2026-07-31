from sentinel.plugins.constants import PluginState
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