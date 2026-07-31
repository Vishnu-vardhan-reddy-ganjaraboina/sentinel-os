from sentinel.plugins.constants import (
    DEFAULT_PLUGIN_VERSION,
    PluginState,
    PluginType,
)


def test_version():
    assert DEFAULT_PLUGIN_VERSION == "1.0.0"


def test_plugin_state():
    assert PluginState.REGISTERED.value == "registered"
    assert PluginState.LOADED.value == "loaded"
    assert PluginState.ENABLED.value == "enabled"
    assert PluginState.DISABLED.value == "disabled"
    assert PluginState.UNLOADED.value == "unloaded"


def test_plugin_type():
    assert PluginType.CORE.value == "core"
    assert PluginType.SYSTEM.value == "system"
    assert PluginType.EXTENSION.value == "extension"
    assert PluginType.USER.value == "user"