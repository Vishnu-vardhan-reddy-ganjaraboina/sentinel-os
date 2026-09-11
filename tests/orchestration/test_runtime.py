"""
Tests for the Sentinel Orchestration runtime service.
"""

from __future__ import annotations

import pytest

from sentinel.capabilities.manager import CapabilityManager
from sentinel.kernel.service import Service
from sentinel.knowledge.chunker import FixedSizeChunker
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.vector_store import InMemoryVectorStore
from sentinel.memory.service import MemoryService
from sentinel.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
)
from sentinel.orchestration.runtime import OrchestrationRuntimeService
from sentinel.orchestration.service import OrchestrationService
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


def test_runtime_name() -> None:
    runtime = OrchestrationRuntimeService()

    assert runtime.name == "orchestration"


def test_runtime_dependencies() -> None:
    runtime = OrchestrationRuntimeService()

    assert runtime.dependencies == (
        "memory",
        "knowledge",
    )


def test_runtime_default_service() -> None:
    runtime = OrchestrationRuntimeService()

    assert isinstance(
        runtime.orchestration,
        OrchestrationService,
    )


def test_runtime_is_service() -> None:
    runtime = OrchestrationRuntimeService()

    assert isinstance(runtime, Service)


def test_runtime_exposes_capabilities() -> None:
    runtime = OrchestrationRuntimeService()

    assert isinstance(
        runtime.capabilities,
        CapabilityManager,
    )


def test_runtime_exposes_security() -> None:
    runtime = OrchestrationRuntimeService()

    assert isinstance(
        runtime.security,
        SecurityManager,
    )


def test_runtime_exposes_identity() -> None:
    identity = SecurityIdentity(
        "test-user",
        "Test User",
    )

    runtime = OrchestrationRuntimeService(
        identity=identity,
    )

    assert runtime.identity is identity


def test_runtime_exposes_memory() -> None:
    memory = MemoryService()

    runtime = OrchestrationRuntimeService(
        memory=memory,
    )

    assert runtime.memory is memory


def test_runtime_exposes_knowledge() -> None:
    vector_store = InMemoryVectorStore()
    embedding_provider = DummyEmbeddingProvider()

    knowledge = KnowledgeService(
        indexer=Indexer(
            chunker=FixedSizeChunker(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        ),
        retriever=Retriever(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        ),
    )

    runtime = OrchestrationRuntimeService(
        knowledge=knowledge,
    )

    assert runtime.knowledge is knowledge


def test_runtime_health_before_initialize() -> None:
    runtime = OrchestrationRuntimeService()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_initialize() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_initialize_is_idempotent() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()
    runtime.initialize()

    assert runtime.health() == {
        "healthy": True,
    }


def test_runtime_shutdown() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_shutdown_is_idempotent() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()
    runtime.shutdown()
    runtime.shutdown()

    assert runtime.health() == {
        "healthy": False,
    }


def test_runtime_initialize_after_shutdown_raises() -> None:
    runtime = OrchestrationRuntimeService()

    runtime.initialize()
    runtime.shutdown()

    with pytest.raises(
        RuntimeError,
        match="already been shut down",
    ):
        runtime.initialize()


def test_runtime_can_execute_delegates() -> None:
    service = OrchestrationService()

    runtime = OrchestrationRuntimeService(
        orchestration=service,
    )

    request = OrchestrationRequest(
        "request-1",
        "hello",
    )

    assert runtime.can_execute(request) is True


def test_runtime_execute_delegates() -> None:
    def handler(
        request: OrchestrationRequest,
    ) -> str:
        return f"processed:{request.input}"

    service = OrchestrationService(
        handler=handler,
    )

    runtime = OrchestrationRuntimeService(
        orchestration=service,
    )

    request = OrchestrationRequest(
        "request-1",
        "hello",
    )

    result = runtime.execute(request)

    assert isinstance(result, OrchestrationResult)
    assert result.request_id == "request-1"
    assert result.success is True
    assert result.data == "processed:hello"