
from sentinel.knowledge.chunker import FixedSizeChunker
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.vector_store import InMemoryVectorStore


def create_indexer() -> Indexer:
    return Indexer(
        chunker=FixedSizeChunker(chunk_size=100),
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
    )


def test_index_single_document():
    indexer = create_indexer()

    document = Document(
        id="doc1",
        text="Hello Sentinel"
    )

    chunks = indexer.index(document)

    assert len(chunks) == 1
    assert chunks[0].document_id == "doc1"


def test_index_multiple_documents():
    indexer = create_indexer()

    docs = [
        Document(id="1", text="One"),
        Document(id="2", text="Two"),
        Document(id="3", text="Three"),
    ]

    chunks = indexer.index_many(docs)

    assert len(chunks) == 3


def test_remove_document():
    indexer = create_indexer()

    document = Document(
        id="doc1",
        text="Hello"
    )

    indexer.index(document)

    indexer.remove("doc1")

    assert indexer.vector_store.search(
        [1.0] * indexer.embedding_provider.dimension(),
        limit=10,
    ) == []


def test_reindex_document():
    indexer = create_indexer()

    document = Document(
        id="doc1",
        text="Version 1"
    )

    indexer.index(document)

    document = Document(
        id="doc1",
        text="Version 2"
    )

    chunks = indexer.reindex(document)

    assert len(chunks) == 1
    assert chunks[0].text == "Version 2"

def test_reindex_replaces_old_chunks() -> None:
    indexer = create_indexer()

    indexer.index(
        Document(
            id="doc1",
            text="Old document",
        )
    )

    indexer.reindex(
        Document(
            id="doc1",
            text="New document",
        )
    )

    chunks = indexer.vector_store.list_chunks()

    assert len(chunks) == 1
    assert chunks[0].document_id == "doc1"
    assert chunks[0].text == "New document"