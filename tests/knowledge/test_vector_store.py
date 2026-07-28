from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.similarity import DotProductSimilarity
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

    from sentinel.knowledge.similarity import DotProductSimilarity


def test_exists():
    store = InMemoryVectorStore()

    chunk = Chunk(
        id="1",
        document_id="doc",
        text="hello",
        index=0,
    )

    store.add(chunk, [1.0] * 8)

    assert store.exists("1")


def test_get():
    store = InMemoryVectorStore()

    chunk = Chunk(
        id="1",
        document_id="doc",
        text="hello",
        index=0,
    )

    store.add(chunk, [1.0] * 8)

    assert store.get("1") == chunk


def test_delete_document():
    store = InMemoryVectorStore()

    chunk1 = Chunk(
        id="1",
        document_id="doc",
        text="one",
        index=0,
    )

    chunk2 = Chunk(
        id="2",
        document_id="doc",
        text="two",
        index=1,
    )

    store.add(chunk1, [1.0] * 8)
    store.add(chunk2, [1.0] * 8)

    store.delete_document("doc")

    assert len(store) == 0


def test_clear():
    store = InMemoryVectorStore()

    chunk = Chunk(
        id="1",
        document_id="doc",
        text="hello",
        index=0,
    )

    store.add(chunk, [1.0] * 8)

    store.clear()

    assert len(store) == 0


def test_custom_similarity():
    store = InMemoryVectorStore(
        similarity=DotProductSimilarity()
    )

    chunk = Chunk(
        id="1",
        document_id="doc",
        text="hello",
        index=0,
    )

    store.add(chunk, [1.0] * 8)

    result = store.search(
        [1.0] * 8,
    )

    assert len(result) == 1