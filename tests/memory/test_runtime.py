from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService


def test_name() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.name == "memory"


def test_memory_property() -> None:
    memory = MemoryService()

    runtime = MemoryRuntimeService(memory)

    assert runtime.memory is memory


def test_default_memory_service() -> None:
    runtime = MemoryRuntimeService()

    assert isinstance(
        runtime.memory,
        MemoryService,
    )


def test_initialize() -> None:
    runtime = MemoryRuntimeService()

    runtime.initialize()


def test_shutdown() -> None:
    runtime = MemoryRuntimeService()

    runtime.shutdown()


def test_health() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.health() == {
        "healthy": True,
    }


def test_dependencies() -> None:
    runtime = MemoryRuntimeService()

    assert runtime.dependencies == ()
