from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.retriever import Retriever
from sentinel.knowledge.vector_store import InMemoryVectorStore


def test_retrieve():
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    chunk = Chunk(
        id="1",
        document_id="doc1",
        text="Sentinel OS",
        index=0,
    )

    store.add(chunk, provider.embed(chunk.text))

    retriever = Retriever(provider, store)

    results = retriever.retrieve("Sentinel")

    assert len(results) == 1
    assert results[0].id == "1"


def test_limit():
    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    for i in range(10):
        chunk = Chunk(
            id=str(i),
            document_id="doc",
            text=f"Chunk {i}",
            index=i,
        )

        store.add(chunk, provider.embed(chunk.text))

    retriever = Retriever(provider, store)

    results = retriever.retrieve(
        "anything",
        limit=3,
    )

    assert len(results) == 3