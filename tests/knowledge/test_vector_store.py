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

def test_search_with_non_positive_limit_returns_empty() -> None:
    store = InMemoryVectorStore()

    store.add(
        Chunk(
            id="chunk.1",
            document_id="doc.1",
            text="Hello",
            index=0,
        ),
        [1.0, 0.0],
    )

    assert store.search([1.0, 0.0], limit=0) == []
    assert store.search([1.0, 0.0], limit=-1) == []


def test_replacing_chunk_replaces_embedding_and_chunk() -> None:
    store = InMemoryVectorStore()

    original = Chunk(
        id="chunk.1",
        document_id="doc.1",
        text="Original",
        index=0,
    )

    replacement = Chunk(
        id="chunk.1",
        document_id="doc.2",
        text="Replacement",
        index=1,
    )

    store.add(original, [1.0, 0.0])
    store.add(replacement, [0.0, 1.0])

    assert store.get("chunk.1") == replacement
    assert len(store) == 1

    result = store.search(
        [0.0, 1.0],
        limit=1,
    )

    assert result == [replacement]


def test_delete_document_only_removes_matching_document() -> None:
    store = InMemoryVectorStore()

    store.add(
        Chunk(
            id="chunk.1",
            document_id="doc.1",
            text="One",
            index=0,
        ),
        [1.0, 0.0],
    )

    store.add(
        Chunk(
            id="chunk.2",
            document_id="doc.2",
            text="Two",
            index=0,
        ),
        [0.0, 1.0],
    )

    store.delete_document("doc.1")

    assert store.exists("chunk.1") is False
    assert store.exists("chunk.2") is True


def test_missing_chunk_returns_none() -> None:
    store = InMemoryVectorStore()

    assert store.get("missing") is None


def test_clear_removes_chunks_and_embeddings() -> None:
    store = InMemoryVectorStore()

    store.add(
        Chunk(
            id="chunk.1",
            document_id="doc.1",
            text="One",
            index=0,
        ),
        [1.0, 0.0],
    )

    store.clear()

    assert len(store) == 0
    assert store.list_chunks() == []