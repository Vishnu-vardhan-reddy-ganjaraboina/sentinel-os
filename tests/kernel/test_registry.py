import pytest

import threading

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

def test_register_rejects_invalid_service() -> None:
    registry = ServiceRegistry()

    with pytest.raises(TypeError):
        registry.register(object())  # type: ignore[arg-type]


def test_invalid_name_operations_are_rejected() -> None:
    registry = ServiceRegistry()

    with pytest.raises(ValueError):
        registry.get("")

    with pytest.raises(ValueError):
        registry.unregister("")


def test_iter_returns_snapshot() -> None:
    registry = ServiceRegistry()

    first = DummyService("first")
    second = DummyService("second")

    registry.register(first)

    iterator = iter(registry)

    registry.register(second)

    services = tuple(iterator)

    assert services == (first,)


def test_concurrent_registration() -> None:
    registry = ServiceRegistry()

    def register(index: int) -> None:
        registry.register(
            DummyService(f"service-{index}")
        )

    threads = [
        threading.Thread(
            target=register,
            args=(index,),
        )
        for index in range(25)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(registry) == 25