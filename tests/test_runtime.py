from unittest.mock import patch

import pytest

from sentinel.execution.runtime import ExecutionRuntimeService
from sentinel.infrastructure.configuration import Configuration
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.runtime import KnowledgeRuntimeService
from sentinel.knowledge.vector_store import InMemoryVectorStore
from sentinel.memory.runtime import MemoryRuntimeService
from sentinel.memory.service import MemoryService
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


def test_runtime_preserves_injected_memory_service() -> None:
    memory = MemoryService()

    runtime = RuntimeComposer(memory=memory).compose()

    assert runtime.memory.memory is memory
    assert runtime.orchestration.orchestration.memory is memory


def test_runtime_preserves_injected_vector_store() -> None:
    vector_store = InMemoryVectorStore()

    runtime = RuntimeComposer(
        knowledge_vector_store=vector_store,
    ).compose()

    assert runtime.knowledge.knowledge.retriever.vector_store is vector_store


def test_runtime_get_typed_rejects_invalid_service_type() -> None:
    runtime = RuntimeComposer().compose()

    with pytest.raises(
        TypeError,
        match="service_type must be a type",
    ):
        runtime.get_typed(
            "memory",
            "not-a-type",  # type: ignore[arg-type]
        )


def test_runtime_services_are_tuple() -> None:
    runtime = RuntimeComposer().compose()

    assert isinstance(runtime.services, tuple)


def test_runtime_iteration_matches_services() -> None:
    runtime = RuntimeComposer().compose()

    assert tuple(runtime) == runtime.services


def test_runtime_length_matches_services() -> None:
    runtime = RuntimeComposer().compose()

    assert len(runtime) == len(runtime.services)


def test_runtime_rejects_non_tuple_services() -> None:
    with pytest.raises(
        TypeError,
        match="services must be a tuple",
    ):
        Runtime([])  # type: ignore[arg-type]


def test_runtime_rejects_non_service_entries() -> None:
    with pytest.raises(
        TypeError,
        match="only Service instances",
    ):
        Runtime((object(),))  # type: ignore[arg-type]


def test_runtime_uses_dummy_embedding_provider_by_default() -> None:
    runtime = RuntimeComposer().compose()

    indexer = runtime.knowledge.knowledge.indexer
    retriever = runtime.knowledge.knowledge.retriever

    assert isinstance(indexer.embedding_provider, DummyEmbeddingProvider)
    assert indexer.embedding_provider is retriever._embedding_provider


def test_runtime_selects_sentence_transformer_provider() -> None:
    configuration = Configuration.from_dict(
        {
            "knowledge": {
                "embedding": {
                    "provider": "sentence-transformers",
                    "model": "test-model",
                    "device": "cpu",
                    "batch_size": 16,
                },
            },
        }
    )

    with patch(
        "sentinel.runtime.SentenceTransformerEmbeddingProvider"
    ) as provider_factory:
        provider = provider_factory.return_value

        runtime = RuntimeComposer(configuration=configuration).compose()

    provider_factory.assert_called_once_with(
        model_name="test-model",
        device="cpu",
        batch_size=16,
    )
    indexer = runtime.knowledge.knowledge.indexer
    retriever = runtime.knowledge.knowledge.retriever

    assert indexer.embedding_provider is provider
    assert indexer.embedding_provider is retriever._embedding_provider


def test_runtime_preserves_injected_knowledge_without_loading_model() -> None:
    runtime_without_injection = RuntimeComposer().compose()
    knowledge = runtime_without_injection.knowledge.knowledge

    configuration = Configuration.from_dict(
        {
            "knowledge": {
                "embedding": {
                    "provider": "sentence-transformers",
                },
            },
        }
    )

    with patch(
        "sentinel.runtime.SentenceTransformerEmbeddingProvider"
    ) as provider_factory:
        runtime = RuntimeComposer(
            knowledge=knowledge,
            configuration=configuration,
        ).compose()

    provider_factory.assert_not_called()
    assert runtime.knowledge.knowledge is knowledge
