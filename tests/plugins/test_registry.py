import pytest

import threading

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

def test_register_rejects_invalid_plugin() -> None:
    registry = SentinelPluginRegistry()

    with pytest.raises(TypeError):
        registry.register(object())  # type: ignore[arg-type]


def test_register_rejects_empty_plugin_name() -> None:
    registry = SentinelPluginRegistry()

    class InvalidPlugin(SentinelPlugin):
        @property
        def name(self) -> str:
            return "   "

    with pytest.raises(PluginRegistrationError):
        registry.register(InvalidPlugin("sample"))


def test_invalid_name_operations() -> None:
    registry = SentinelPluginRegistry()

    with pytest.raises(ValueError):
        registry.get("")

    with pytest.raises(TypeError):
        registry.get(123)  # type: ignore[arg-type]


def test_registry_concurrent_registration() -> None:
    registry = SentinelPluginRegistry()

    def register_plugin(index: int) -> None:
        registry.register(
            SentinelPlugin(f"plugin-{index}")
        )

    threads = [
        threading.Thread(
            target=register_plugin,
            args=(index,),
        )
        for index in range(50)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(registry) == 50
    assert len(registry.all()) == 50