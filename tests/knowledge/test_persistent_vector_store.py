"""
Tests for the persistent knowledge vector store.
"""

import json
from pathlib import Path

import pytest

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.storage.backends.sqlite import SQLiteBackend


def create_store(
    database: Path,
) -> PersistentVectorStore:
    """Create a persistent vector store for testing."""
    backend = SQLiteBackend(database)

    return PersistentVectorStore(
        backend=backend,
    )


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