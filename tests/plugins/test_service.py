from sentinel.plugins.constants import PluginState
from sentinel.plugins.manager import PluginManager
from sentinel.plugins.plugin import SentinelPlugin
from sentinel.plugins.service import PluginService


def test_manager_property():

    manager = PluginManager()
    service = PluginService(manager)

    assert service.manager is manager


def test_register():

    service = PluginService()

    plugin = SentinelPlugin("sample")

    service.register(plugin)

    assert len(service) == 1


def test_get():

    service = PluginService()

    plugin = SentinelPlugin("sample")

    service.register(plugin)

    assert service.get("sample") is plugin


def test_lifecycle():

    service = PluginService()

    plugin = SentinelPlugin("sample")

    service.register(plugin)

    service.load("sample")
    assert plugin.state == PluginState.LOADED

    service.enable("sample")
    assert plugin.state == PluginState.ENABLED

    service.disable("sample")
    assert plugin.state == PluginState.DISABLED

    service.unload("sample")
    assert plugin.state == PluginState.UNLOADED


def test_plugins():

    service = PluginService()

    service.register(
        SentinelPlugin("one")
    )

    service.register(
        SentinelPlugin("two")
    )

    assert len(service.plugins()) == 2


def test_unregister():

    service = PluginService()

    plugin = SentinelPlugin("sample")

    service.register(plugin)

    service.unregister("sample")

    assert len(service) == 0


def test_clear():

    service = PluginService()

    service.register(
        SentinelPlugin("sample")
    )

    service.clear()

    assert len(service) == 0