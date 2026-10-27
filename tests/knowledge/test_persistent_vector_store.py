"""
Tests for the persistent knowledge vector store.
"""

import json
from collections.abc import Generator
from math import inf, nan
from pathlib import Path

import pytest

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.storage.backends.sqlite import SQLiteBackend

_CREATED_STORES: list[PersistentVectorStore] = []


def create_store(
    database: Path,
) -> PersistentVectorStore:
    """Create a persistent vector store for testing."""
    backend = SQLiteBackend(database)
    store = PersistentVectorStore(backend=backend)
    _CREATED_STORES.append(store)
    return store


@pytest.fixture(autouse=True)
def close_created_stores() -> Generator[None]:
    """Close all stores created during each test."""
    _CREATED_STORES.clear()
    try:
        yield
    finally:
        try:
            for store in reversed(_CREATED_STORES):
                store.close()
        finally:
            _CREATED_STORES.clear()


def test_add_and_get(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"

    store = create_store(database)

    chunk = Chunk(
        id="chunk.1",
        document_id="doc.1",
        text="Sentinel knowledge",
        index=0,
        metadata={
            "source": "test",
        },
    )

    store.add(
        chunk,
        [1.0, 0.0, 0.0],
    )

    assert store.exists("chunk.1") is True

    stored = store.get("chunk.1")

    assert stored == chunk


def test_persistence_survives_reopen(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"

    first = create_store(database)

    chunk = Chunk(
        id="chunk.1",
        document_id="doc.1",
        text="Persistent Sentinel knowledge",
        index=0,
    )

    first.add(
        chunk,
        [1.0, 0.0, 0.0],
    )

    first.backend.close()

    second = create_store(database)

    stored = second.get("chunk.1")

    assert stored is not None
    assert stored.id == "chunk.1"
    assert stored.document_id == "doc.1"
    assert stored.text == "Persistent Sentinel knowledge"

    second.backend.close()


def test_search(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"

    store = create_store(database)

    store.add(
        Chunk(
            id="chunk.1",
            document_id="doc.1",
            text="Python programming",
            index=0,
        ),
        [1.0, 0.0, 0.0],
    )

    store.add(
        Chunk(
            id="chunk.2",
            document_id="doc.2",
            text="Java programming",
            index=0,
        ),
        [0.0, 1.0, 0.0],
    )

    results = store.search(
        [1.0, 0.0, 0.0],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].id == "chunk.1"


def test_delete(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"

    store = create_store(database)

    store.add(
        Chunk(
            id="chunk.1",
            document_id="doc.1",
            text="Hello",
            index=0,
        ),
        [1.0, 0.0],
    )

    store.delete("chunk.1")

    assert store.exists("chunk.1") is False
    assert store.get("chunk.1") is None


def test_delete_document(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"

    store = create_store(database)

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
            document_id="doc.1",
            text="Two",
            index=1,
        ),
        [0.0, 1.0],
    )

    store.add(
        Chunk(
            id="chunk.3",
            document_id="doc.2",
            text="Three",
            index=0,
        ),
        [1.0, 1.0],
    )

    store.delete_document("doc.1")

    assert store.exists("chunk.1") is False
    assert store.exists("chunk.2") is False
    assert store.exists("chunk.3") is True


def test_clear(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"

    store = create_store(database)

    store.add(
        Chunk(
            id="chunk.1",
            document_id="doc.1",
            text="One",
            index=0,
        ),
        [1.0],
    )

    store.clear()

    assert len(store) == 0
    assert store.list_chunks() == []

def test_search_with_non_positive_limit_returns_empty(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path / "knowledge.db")

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


def test_missing_chunk_returns_none(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path / "knowledge.db")

    assert store.get("missing") is None


def test_corrupt_json_is_rejected(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"
    store = create_store(database)

    store.backend.set(
        "knowledge:chunk:broken",
        "{invalid-json",
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        store.get("broken")


def test_invalid_payload_is_rejected(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"
    store = create_store(database)

    store.backend.set(
        "knowledge:chunk:broken",
        json.dumps({"chunk": "invalid"}),
    )

    with pytest.raises(ValueError, match="Stored chunk"):
        store.get("broken")


def test_invalid_embedding_is_rejected(
    tmp_path: Path,
) -> None:
    database = tmp_path / "knowledge.db"
    store = create_store(database)

    store.backend.set(
        "knowledge:chunk:broken",
        json.dumps(
            {
                "chunk": {
                    "id": "broken",
                    "document_id": "doc.1",
                    "text": "Hello",
                    "index": 0,
                    "metadata": {},
                },
                "embedding": "invalid",
            }
        ),
    )

    with pytest.raises(ValueError, match="Stored embedding"):
        store.get("broken")

@pytest.mark.parametrize(
    "embedding",
    [
        [nan],
        [inf],
        [-inf],
    ],
)
def test_add_rejects_non_finite_embedding(
    tmp_path: Path,
    embedding: list[float],
) -> None:
    store = create_store(tmp_path / "knowledge.db")

    chunk = Chunk(
        id="chunk.nonfinite",
        document_id="doc.1",
        text="Test embedding",
        index=0,
    )

    with pytest.raises(ValueError, match="finite"):
        store.add(chunk, embedding)


@pytest.mark.parametrize(
    "embedding",
    [
        [nan],
        [inf],
        [-inf],
    ],
)
def test_search_rejects_non_finite_query_embedding(
    tmp_path: Path,
    embedding: list[float],
) -> None:
    store = create_store(tmp_path / "knowledge.db")

    with pytest.raises(ValueError, match="finite"):
        store.search(embedding)

def test_replace_document_rolls_back_when_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = create_store(tmp_path / "knowledge.db")
    old = Chunk(
        id="doc.1:0",
        document_id="doc.1",
        text="Old text",
        index=0,
    )
    store.add(old, [1.0, 0.0])

    original_set = store.backend.set
    calls = 0

    def failing_set(key: str, value: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated storage failure")
        original_set(key, value)

    monkeypatch.setattr(store.backend, "set", failing_set)

    replacements = [
        (
            Chunk(
                id="doc.1:0",
                document_id="doc.1",
                text="New first",
                index=0,
            ),
            [0.0, 1.0],
        ),
        (
            Chunk(
                id="doc.1:1",
                document_id="doc.1",
                text="New second",
                index=1,
            ),
            [0.5, 0.5],
        ),
    ]

    with pytest.raises(RuntimeError, match="simulated storage failure"):
        store.replace_document("doc.1", replacements)

    stored = store.get("doc.1:0")
    assert stored is not None
    assert stored.text == "Old text"
    assert store.get("doc.1:1") is None


def test_replace_document_collision_preserves_both_documents(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path / "knowledge.db")

    original_doc1 = Chunk(
        id="doc.1:0",
        document_id="doc.1",
        text="Original document one",
        index=0,
    )
    original_doc2 = Chunk(
        id="doc.2:0",
        document_id="doc.2",
        text="Original document two",
        index=0,
    )

    store.add(original_doc1, [1.0, 0.0])
    store.add(original_doc2, [0.0, 1.0])

    conflicting_replacement = Chunk(
        id="doc.2:0",
        document_id="doc.1",
        text="Must not overwrite document two",
        index=0,
    )

    with pytest.raises(ValueError):
        store.replace_document(
            "doc.1",
            [(conflicting_replacement, [0.5, 0.5])],
        )

    stored_doc1 = store.get("doc.1:0")
    stored_doc2 = store.get("doc.2:0")

    assert stored_doc1 == original_doc1
    assert stored_doc2 == original_doc2
    assert len(store) == 2


def test_replace_document_removes_stale_chunks_and_preserves_other_documents(
    tmp_path: Path,
) -> None:
    store = create_store(tmp_path / "knowledge.db")

    old_chunks = [
        Chunk(
            id=f"doc.1:{index}",
            document_id="doc.1",
            text=f"Old chunk {index}",
            index=index,
        )
        for index in range(3)
    ]
    other_document = Chunk(
        id="doc.2:0",
        document_id="doc.2",
        text="Keep this document",
        index=0,
    )

    for chunk in old_chunks:
        store.add(chunk, [1.0, 0.0])
    store.add(other_document, [0.0, 1.0])

    replacement = Chunk(
        id="doc.1:0",
        document_id="doc.1",
        text="Replacement chunk",
        index=0,
    )

    store.replace_document("doc.1", [(replacement, [0.5, 0.5])])

    assert store.get("doc.1:0") == replacement
    assert store.get("doc.1:1") is None
    assert store.get("doc.1:2") is None
    assert store.get("doc.2:0") == other_document
    assert len(store) == 2
