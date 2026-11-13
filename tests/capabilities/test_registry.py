import pytest

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.exceptions import (
    CapabilityAlreadyExistsError,
    CapabilityNotFoundError,
)
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.capabilities.registry import CapabilityRegistry


class DummyCapability(BaseCapability):

    def __init__(self, capability_id: str = "dummy.echo"):
        super().__init__(
            CapabilityMetadata(
                capability_id=capability_id,
                name="Dummy",
                description="Dummy capability",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_register():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    assert registry.exists(capability.id)


def test_duplicate_registration():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    with pytest.raises(CapabilityAlreadyExistsError):
        registry.register(capability)


def test_get():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    assert registry.get(capability.id) is capability


def test_unregister():
    registry = CapabilityRegistry()

    capability = DummyCapability()

    registry.register(capability)

    registry.unregister(capability.id)

    assert not registry.exists(capability.id)


def test_unregister_unknown():
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotFoundError):
        registry.unregister("missing")


def test_list():
    registry = CapabilityRegistry()

    registry.register(DummyCapability("a"))
    registry.register(DummyCapability("b"))

    assert len(registry.list()) == 2


def test_category_filter():
    registry = CapabilityRegistry()

    registry.register(DummyCapability())

    result = registry.list_by_category(
        CapabilityCategory.CUSTOM
    )

    assert len(result) == 1


def test_clear():
    registry = CapabilityRegistry()

    registry.register(DummyCapability())

    registry.clear()

    assert len(registry) == 0

def test_registry_concurrent_registration() -> None:
    from concurrent.futures import ThreadPoolExecutor

    registry = CapabilityRegistry()

    def register(index: int) -> None:
        registry.register(
            DummyCapability(f"capability.{index}")
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(register, range(100)))

    assert len(registry) == 100


def test_list_returns_snapshot() -> None:
    registry = CapabilityRegistry()

    first = DummyCapability("first")
    registry.register(first)

    snapshot = registry.list()

    registry.register(DummyCapability("second"))

    assert len(snapshot) == 1
    assert snapshot[0] is first


def test_list_by_category_returns_snapshot() -> None:
    registry = CapabilityRegistry()

    first = DummyCapability("first")
    registry.register(first)

    snapshot = registry.list_by_category(
        CapabilityCategory.CUSTOM
    )

    registry.register(DummyCapability("second"))

    assert len(snapshot) == 1
    assert snapshot[0] is first


def test_iteration_uses_snapshot() -> None:
    registry = CapabilityRegistry()

    first = DummyCapability("first")
    registry.register(first)

    iterator = iter(registry)

    registry.register(DummyCapability("second"))

    assert list(iterator) == [first]


def test_iteration_survives_clear() -> None:
    registry = CapabilityRegistry()

    first = DummyCapability("first")
    second = DummyCapability("second")

    registry.register(first)
    registry.register(second)

    iterator = iter(registry)

    registry.clear()

    assert list(iterator) == [first, second]


def test_contains() -> None:
    registry = CapabilityRegistry()

    capability = DummyCapability()
    registry.register(capability)

    assert capability.id in registry
    assert "missing" not in registry


def test_len() -> None:
    registry = CapabilityRegistry()

    assert len(registry) == 0

    registry.register(DummyCapability())

    assert len(registry) == 1


def test_get_rejects_invalid_id_type() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(TypeError):
        registry.get(123)  # type: ignore[arg-type]


def test_get_rejects_empty_id() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(ValueError):
        registry.get("")


def test_exists_rejects_invalid_id_type() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(TypeError):
        registry.exists(123)  # type: ignore[arg-type]


def test_unregister_rejects_empty_id() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(ValueError):
        registry.unregister("")


def test_category_rejects_invalid_category() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(TypeError):
        registry.list_by_category("custom")  # type: ignore[arg-type]

def test_concurrent_register_and_read() -> None:
    from concurrent.futures import ThreadPoolExecutor

    registry = CapabilityRegistry()

    def register(index: int) -> None:
        registry.register(
            DummyCapability(f"concurrent.{index}")
        )

    def read(index: int) -> None:
        registry.exists(f"concurrent.{index}")

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []

        for index in range(100):
            futures.append(
                executor.submit(register, index)
            )
            futures.append(
                executor.submit(read, index)
            )

        for future in futures:
            future.result()

    assert len(registry) == 100


def test_concurrent_register_and_iteration() -> None:
    from concurrent.futures import ThreadPoolExecutor

    registry = CapabilityRegistry()

    for index in range(50):
        registry.register(
            DummyCapability(f"initial.{index}")
        )

    def register(index: int) -> None:
        registry.register(
            DummyCapability(f"dynamic.{index}")
        )

    def iterate() -> int:
        return len(list(registry))

    with ThreadPoolExecutor(max_workers=16) as executor:
        register_futures = [
            executor.submit(register, index)
            for index in range(100)
        ]

        iteration_futures = [
            executor.submit(iterate)
            for _ in range(100)
        ]

        for future in register_futures:
            future.result()

        observed_sizes = [
            future.result()
            for future in iteration_futures
        ]

    assert all(size >= 50 for size in observed_sizes)
    assert len(registry) == 150


def test_concurrent_clear_and_read() -> None:
    from concurrent.futures import ThreadPoolExecutor

    registry = CapabilityRegistry()

    for index in range(100):
        registry.register(
            DummyCapability(f"clear.{index}")
        )

    def clear() -> None:
        registry.clear()

    def read() -> int:
        return len(registry.list())

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []

        for _ in range(20):
            futures.append(executor.submit(clear))

        for _ in range(100):
            futures.append(executor.submit(read))

        for future in futures:
            future.result()

    assert len(registry) == 0
