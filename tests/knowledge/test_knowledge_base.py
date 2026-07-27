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