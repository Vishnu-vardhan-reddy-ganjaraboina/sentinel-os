from concurrent.futures import ThreadPoolExecutor

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.knowledge_base import KnowledgeBase
from sentinel.knowledge.vector_store import (
    InMemoryVectorStore,
)


def test_add_document():
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    kb = KnowledgeBase(
        provider,
        store,
    )

    doc = Document(
        id="1",
        text="Sentinel OS",
    )

    kb.add_document(doc)

    results = kb.search("Sentinel")

    assert len(results) == 1
    assert results[0].document_id == "1"


def test_multiple_documents():
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    kb = KnowledgeBase(
        provider,
        store,
    )

    for i in range(5):
        kb.add_document(
            Document(
                id=str(i),
                text=f"Document {i}",
            )
        )

    results = kb.search(
        "Document",
        limit=3,
    )

    assert len(results) == 3

def test_concurrent_add_documents() -> None:
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    kb = KnowledgeBase(
        provider,
        store,
    )

    documents = [
        Document(
            id=str(index),
            text=f"Document {index}",
        )
        for index in range(20)
    ]

    def add_document(document: Document) -> None:
        kb.add_document(document)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(
                add_document,
                document,
            )
            for document in documents
        ]

        for future in futures:
            future.result()

    results = kb.search(
        "Document",
        limit=20,
    )

    assert len(results) == 20
    assert {
        chunk.document_id
        for chunk in results
    } == {
        document.id
        for document in documents
    }

def test_concurrent_search() -> None:
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    kb = KnowledgeBase(
        provider,
        store,
    )

    for index in range(10):
        kb.add_document(
            Document(
                id=str(index),
                text=f"Document {index}",
            )
        )

    def search() -> list[Chunk]:
        return kb.search(
            "Document",
            limit=5,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(search)
            for _ in range(8)
        ]

        results = [
            future.result()
            for future in futures
        ]

    assert len(results) == 8
    assert all(
        len(chunks) == 5
        for chunks in results
    )