from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.runtime import KnowledgeRuntimeService


def test_runtime_name() -> None:
    runtime = KnowledgeRuntimeService()

    assert runtime.name == "knowledge"


def test_runtime_default_service() -> None:
    runtime = KnowledgeRuntimeService()

    assert isinstance(runtime.knowledge, KnowledgeService)


def test_runtime_health_before_initialize() -> None:
    runtime = KnowledgeRuntimeService()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_initialize() -> None:
    runtime = KnowledgeRuntimeService()

    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_shutdown() -> None:
    runtime = KnowledgeRuntimeService()

    runtime.initialize()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_shutdown_is_idempotent() -> None:
    runtime = KnowledgeRuntimeService()

    runtime.initialize()
    runtime.shutdown()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }