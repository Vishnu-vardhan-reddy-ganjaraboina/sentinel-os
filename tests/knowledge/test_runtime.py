"""
Tests for the Sentinel Knowledge runtime service.
"""

from collections.abc import Iterable

from sentinel.kernel.service import Service
from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.document import Document
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.runtime import KnowledgeRuntimeService


def test_runtime_name() -> None:
    runtime = KnowledgeRuntimeService()

    assert runtime.name == "knowledge"


def test_runtime_default_service() -> None:
    runtime = KnowledgeRuntimeService()

    assert isinstance(runtime.knowledge, KnowledgeService)


def test_runtime_dependencies() -> None:
    runtime = KnowledgeRuntimeService()

    assert runtime.dependencies == ()


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


def test_runtime_is_service() -> None:
    runtime = KnowledgeRuntimeService()

    assert isinstance(runtime, Service)


def test_runtime_delegates_add_document() -> None:
    runtime = KnowledgeRuntimeService()

    document = Document(
        id="doc-1",
        text="Sentinel OS runtime test document.",
    )

    chunks = runtime.add_document(document)

    assert chunks
    assert all(isinstance(chunk, Chunk) for chunk in chunks)


def test_runtime_delegates_add_documents() -> None:
    runtime = KnowledgeRuntimeService()

    documents: Iterable[Document] = (
        Document(
            id="doc-1",
            text="First Sentinel OS document.",
        ),
        Document(
            id="doc-2",
            text="Second Sentinel OS document.",
        ),
    )

    chunks = runtime.add_documents(documents)

    assert chunks
    assert all(isinstance(chunk, Chunk) for chunk in chunks)


def test_runtime_delegates_search() -> None:
    runtime = KnowledgeRuntimeService()

    document = Document(
        id="doc-1",
        text="Sentinel OS runtime test document.",
    )

    runtime.add_document(document)

    results = runtime.search("Sentinel")

    assert results
    assert all(isinstance(chunk, Chunk) for chunk in results)


def test_runtime_delegates_remove_document() -> None:
    runtime = KnowledgeRuntimeService()

    document = Document(
        id="doc-1",
        text="Sentinel OS runtime test document.",
    )

    runtime.add_document(document)

    runtime.remove_document("doc-1")

    results = runtime.search("Sentinel")

    assert results == []


def test_runtime_delegates_reindex_document() -> None:
    runtime = KnowledgeRuntimeService()

    original = Document(
        id="doc-1",
        text="Original Sentinel document.",
    )

    updated = Document(
        id="doc-1",
        text="Updated Sentinel document.",
    )

    runtime.add_document(original)
    chunks = runtime.reindex_document(updated)

    assert chunks

    results = runtime.search("Updated")

    assert results