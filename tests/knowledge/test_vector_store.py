from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.vector_store import (
    InMemoryVectorStore,
)


def test_add_chunk():
    store = InMemoryVectorStore()

    chunk = Chunk(
        id="1",
        document_id="doc",
        text="hello",
        index=0,
    )

    store.add(chunk, [1.0, 2.0])

    results = store.search([1.0, 2.0])

    assert len(results) == 1
    assert results[0].id == "1"


def test_delete_chunk():
    store = InMemoryVectorStore()

    chunk = Chunk(
        id="1",
        document_id="doc",
        text="hello",
        index=0,
    )

    store.add(chunk, [1.0])

    store.delete("1")

    assert store.search([1.0]) == []


def test_limit():
    store = InMemoryVectorStore()

    for i in range(10):
        store.add(
            Chunk(
                id=str(i),
                document_id="doc",
                text=f"text {i}",
                index=i,
            ),
            [float(i)],
        )

    results = store.search([0.0], limit=3)

    assert len(results) == 3