from threading import Event, Thread

import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityDisabledError,
    CapabilityExecutionError,
    CapabilityNotFoundError,
)
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata


class EchoCapability(BaseCapability):

    def __init__(self):
        super().__init__(
            CapabilityMetadata(
                capability_id="echo",
                name="Echo",
                description="Echo capability",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


class FailingCapability(BaseCapability):

    def __init__(self):
        super().__init__(
            CapabilityMetadata(
                capability_id="fail",
                name="Fail",
                description="Always fails",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        raise RuntimeError("boom")


def test_register():
    manager = CapabilityManager()

    capability = EchoCapability()

    manager.register(capability)

    assert manager.exists("echo")


def test_execute():
    manager = CapabilityManager()

    manager.register(EchoCapability())

    result = manager.execute(
        "echo",
        value=100,
    )

    assert result["value"] == 100


def test_execute_failure():
    manager = CapabilityManager()

    manager.register(FailingCapability())

    with pytest.raises(CapabilityExecutionError):
        manager.execute("fail")


def test_unregister():
    manager = CapabilityManager()

    manager.register(EchoCapability())

    manager.unregister("echo")

    assert not manager.exists("echo")


def test_clear():
    manager = CapabilityManager()

    manager.register(EchoCapability())

    manager.clear()

    assert len(manager.list()) == 0


def test_execute_admitted_run_finishes_after_unregister(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = CapabilityManager()
    capability = EchoCapability()
    manager.register(capability)

    admitted = Event()
    release = Event()
    result_holder = {}
    error_holder = {}
    original_execute_admitted = capability._execute_admitted

    def pause_after_admission(**kwargs):
        admitted.set()
        if not release.wait(timeout=5):
            raise TimeoutError("Test did not release admitted execution.")
        return original_execute_admitted(**kwargs)

    monkeypatch.setattr(
        capability,
        "_execute_admitted",
        pause_after_admission,
    )

    def execute() -> None:
        try:
            result_holder["result"] = manager.execute_instance(
                capability,
                value=42,
            )
        except Exception as exc:
            error_holder["error"] = exc

    worker = Thread(target=execute)
    worker.start()

    try:
        assert admitted.wait(timeout=5), "Execution was not admitted."
        manager.unregister("echo")
        release.set()
        worker.join(timeout=5)

        assert not worker.is_alive(), "Worker thread did not finish."
        assert "error" not in error_holder
        assert result_holder["result"] == {"value": 42}
    finally:
        release.set()
        worker.join(timeout=5)


def test_execute_instance_rejects_unregistered_reference() -> None:
    manager = CapabilityManager()
    capability = EchoCapability()
    manager.register(capability)

    stale_reference = manager.get("echo")
    manager.unregister("echo")

    with pytest.raises(CapabilityNotFoundError):
        manager.execute_instance(stale_reference)


def test_execute_instance_rejects_replaced_reference() -> None:
    manager = CapabilityManager()
    original = EchoCapability()
    replacement = EchoCapability()
    manager.register(original)

    manager.unregister("echo")
    manager.register(replacement)

    with pytest.raises(CapabilityNotFoundError):
        manager.execute_instance(original)

def test_disabled_capability_preserves_disabled_error() -> None:
    manager = CapabilityManager()

    capability = EchoCapability()
    capability.disable()

    manager.register(capability)

    with pytest.raises(CapabilityDisabledError):
        manager.execute("echo")

def test_get_returns_registered_capability() -> None:
    manager = CapabilityManager()
    capability = EchoCapability()

    manager.register(capability)

    assert manager.get("echo") is capability


def test_constructor_preserves_supplied_empty_registry() -> None:
    from sentinel.capabilities.registry import CapabilityRegistry

    registry = CapabilityRegistry()
    manager = CapabilityManager(registry=registry)

    manager.register(EchoCapability())

    assert len(registry) == 1
