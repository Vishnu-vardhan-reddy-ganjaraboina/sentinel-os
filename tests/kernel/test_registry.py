import pytest

from sentinel.kernel.exceptions import (
    DuplicateServiceError,
    ServiceNotFoundError,
)
from sentinel.kernel.registry import ServiceRegistry
from sentinel.kernel.service import Service


class DummyService(Service):
    def __init__(self, name: str):
        super().__init__(name)

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


def test_register_service():
    registry = ServiceRegistry()
    service = DummyService("logger")

    registry.register(service)

    assert registry.get("logger") is service


def test_duplicate_registration():
    registry = ServiceRegistry()

    registry.register(DummyService("logger"))

    with pytest.raises(DuplicateServiceError):
        registry.register(DummyService("logger"))


def test_unregister_service():
    registry = ServiceRegistry()

    service = DummyService("logger")
    registry.register(service)

    registry.unregister("logger")

    assert not registry.exists("logger")


def test_unregister_missing_service():
    registry = ServiceRegistry()

    with pytest.raises(ServiceNotFoundError):
        registry.unregister("missing")


def test_registry_length():
    registry = ServiceRegistry()

    registry.register(DummyService("logger"))
    registry.register(DummyService("brain"))

    assert len(registry) == 2