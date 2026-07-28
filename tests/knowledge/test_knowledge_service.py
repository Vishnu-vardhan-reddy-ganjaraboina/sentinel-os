from sentinel.knowledge.chunker import FixedSizeChunker
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.knowledge_service import KnowledgeService
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.vector_store import InMemoryVectorStore


def create_service() -> KnowledgeService:
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    indexer = Indexer(
        chunker=FixedSizeChunker(),
        embedding_provider=provider,
        vector_store=store,
    )

    retriever = Retriever(
        embedding_provider=provider,
        vector_store=store,
    )

    return KnowledgeService(
        indexer=indexer,
        retriever=retriever,
    )


def test_add_document():
    service = create_service()

    chunks = service.add_document(
        Document(
            id="1",
            text="Sentinel AI"
        )
    )

    assert len(chunks) == 1


def test_search():
    service = create_service()

    service.add_document(
        Document(
            id="1",
            text="Knowledge Service"
        )
    )

    results = service.search("Knowledge")

    assert len(results) == 1


def test_remove_document():
    service = create_service()

    service.add_document(
        Document(
            id="1",
            text="Hello"
        )
    )

    service.remove_document("1")

    assert service.search("Hello") == []


def test_reindex_document():
    service = create_service()

    service.add_document(
        Document(
            id="1",
            text="Old"
        )
    )

    service.reindex_document(
        Document(
            id="1",
            text="New"
        )
    )

    results = service.search("New")

    assert len(results) == 1