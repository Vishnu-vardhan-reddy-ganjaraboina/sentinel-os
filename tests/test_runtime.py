import pytest

from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.runtime import Runtime, RuntimeComposer


def test_runtime_composer_creates_core_runtime() -> None:
    runtime = RuntimeComposer().compose()

    assert isinstance(runtime, Runtime)
    assert len(runtime) == 4

    services = runtime.services

    assert isinstance(
        services[0],
        ExecutionRuntimeService,
    )
    assert isinstance(
        services[1],
        OrchestrationRuntimeService,
    )
    assert isinstance(
        services[2],
        MemoryRuntimeService,
    )
    assert isinstance(
        services[3],
        KnowledgeRuntimeService,
    )


def test_runtime_declares_orchestration_dependencies() -> None:
    runtime = RuntimeComposer().compose()

    orchestration = runtime.get("orchestration")

    assert orchestration.dependencies == (
        "memory",
        "knowledge",
    )


def test_runtime_shares_memory() -> None:
    runtime = RuntimeComposer().compose()

    orchestration = runtime.get("orchestration")
    memory = runtime.get("memory")

    assert orchestration.orchestration.memory is memory.memory


def test_runtime_shares_knowledge() -> None:
    runtime = RuntimeComposer().compose()

    orchestration = runtime.get("orchestration")
    knowledge = runtime.get("knowledge")

    assert orchestration.orchestration.knowledge is knowledge.knowledge


def test_runtime_get_returns_service() -> None:
    runtime = RuntimeComposer().compose()

    service = runtime.get("memory")

    assert isinstance(service, MemoryRuntimeService)


def test_runtime_get_typed_returns_expected_service() -> None:
    runtime = RuntimeComposer().compose()

    service = runtime.get_typed(
        "knowledge",
        KnowledgeRuntimeService,
    )

    assert isinstance(service, KnowledgeRuntimeService)


def test_runtime_get_missing_service_raises() -> None:
    runtime = RuntimeComposer().compose()

    with pytest.raises(
        KeyError,
        match="Service 'missing' is not registered",
    ):
        runtime.get("missing")


def test_runtime_get_empty_name_raises() -> None:
    runtime = RuntimeComposer().compose()

    with pytest.raises(
        ValueError,
        match="name must not be empty",
    ):
        runtime.get("   ")


def test_runtime_get_rejects_non_string_name() -> None:
    runtime = RuntimeComposer().compose()

    with pytest.raises(TypeError, match="name must be a string"):
        runtime.get(123)  # type: ignore[arg-type]


def test_runtime_get_typed_rejects_wrong_type() -> None:
    runtime = RuntimeComposer().compose()

    with pytest.raises(
        TypeError,
        match="not an instance of",
    ):
        runtime.get_typed(
            "memory",
            KnowledgeRuntimeService,
        )


def test_runtime_rejects_duplicate_service_names() -> None:
    execution = ExecutionRuntimeService()

    with pytest.raises(
        ValueError,
        match="service names must be unique",
    ):
        Runtime(
            (
                execution,
                execution,
            )
        )

def test_runtime_exposes_execution_accessor() -> None:
    runtime = RuntimeComposer().compose()

    assert runtime.execution is runtime.get("execution")


def test_runtime_exposes_orchestration_accessor() -> None:
    runtime = RuntimeComposer().compose()

    assert runtime.orchestration is runtime.get("orchestration")


def test_runtime_exposes_memory_accessor() -> None:
    runtime = RuntimeComposer().compose()

    assert runtime.memory is runtime.get("memory")


def test_runtime_exposes_knowledge_accessor() -> None:
    runtime = RuntimeComposer().compose()

    assert runtime.knowledge is runtime.get("knowledge")