from typing import Any

import pytest

from sentinel.capabilities.interfaces import Capability


class DummyCapability(Capability):

    def __init__(self):
        self._enabled = True

    @property
    def id(self) -> str:
        return "dummy"

    @property
    def name(self) -> str:
        return "Dummy"

    @property
    def description(self) -> str:
        return "Dummy capability"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        return kwargs


def test_capability():
    capability = DummyCapability()

    assert capability.id == "dummy"
    assert capability.name == "Dummy"
    assert capability.enabled is True


def test_enable_disable():
    capability = DummyCapability()

    capability.disable()
    assert capability.enabled is False

    capability.enable()
    assert capability.enabled is True


def test_execute():
    capability = DummyCapability()

    result = capability.execute(value=10)

    assert result["value"] == 10


def test_interface_is_abstract():
    with pytest.raises(TypeError):
        Capability()