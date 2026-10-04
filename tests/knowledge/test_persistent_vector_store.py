"""
Tests for the persistent knowledge vector store.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.persistent_vector_store import (
    PersistentVectorStore,
)
from sentinel.knowledge.similarity import DotProductSimilarity
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


def test_concurrent_unique_adds(
    tmp_path: Path,
) -> None:
    store = create_store(
        tmp_path / "knowledge.db",
    )

    workers = 10
    per_worker = 20

    def add_worker(worker_id: int) -> None:
        for index in range(per_worker):
            chunk_id = f"{worker_id}:{index}"

            store.add(
                Chunk(
                    id=chunk_id,
                    document_id=f"doc:{worker_id}",
                    text=chunk_id,
                    index=index,
                ),
                [float(worker_id), float(index)],
            )

    with ThreadPoolExecutor(
        max_workers=workers,
    ) as executor:
        list(
            executor.map(
                add_worker,
                range(workers),
            )
        )

    assert len(store) == workers * per_worker

    for worker_id in range(workers):
        for index in range(per_worker):
            assert store.exists(
                f"{worker_id}:{index}",
            )


def test_concurrent_replacement_preserves_complete_records(
    tmp_path: Path,
) -> None:
    store = create_store(
        tmp_path / "knowledge.db",
    )

    store.add(
        Chunk(
            id="shared",
            document_id="initial",
            text="initial",
            index=0,
        ),
        [1.0, 0.0],
    )

    barrier = Barrier(10)

    def replace(worker_id: int) -> None:
        barrier.wait()

        store.add(
            Chunk(
                id="shared",
                document_id=f"doc:{worker_id}",
                text=f"text:{worker_id}",
                index=worker_id,
            ),
            [float(worker_id), 1.0],
        )

    with ThreadPoolExecutor(
        max_workers=10,
    ) as executor:
        list(
            executor.map(
                replace,
                range(10),
            )
        )

    stored = store.get("shared")

    assert stored is not None
    assert stored.id == "shared"

    results = store.search(
        [0.0, 1.0],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].id == "shared"


def test_concurrent_search_and_delete(
    tmp_path: Path,
) -> None:
    store = create_store(
        tmp_path / "knowledge.db",
    )

    for index in range(100):
        store.add(
            Chunk(
                id=str(index),
                document_id="doc",
                text=str(index),
                index=index,
            ),
            [1.0, 0.0],
        )

    def delete_worker() -> None:
        for index in range(100):
            store.delete(str(index))

    def search_worker() -> None:
        for _ in range(100):
            store.search(
                [1.0, 0.0],
                limit=10,
            )

    with ThreadPoolExecutor(
        max_workers=4,
    ) as executor:
        futures = [
            executor.submit(delete_worker),
            executor.submit(delete_worker),
            executor.submit(search_worker),
            executor.submit(search_worker),
        ]

        for future in futures:
            future.result()

    assert len(store) == 0


def test_concurrent_clear_and_reads(
    tmp_path: Path,
) -> None:
    store = create_store(
        tmp_path / "knowledge.db",
    )

    for index in range(50):
        store.add(
            Chunk(
                id=str(index),
                document_id="doc",
                text=str(index),
                index=index,
            ),
            [1.0, 0.0],
        )

    barrier = Barrier(4)

    def clear_worker() -> None:
        barrier.wait()

        for _ in range(20):
            store.clear()

    def read_worker() -> None:
        barrier.wait()

        for _ in range(20):
            store.list_chunks()
            len(store)
            store.exists("1")
            store.get("1")
            store.search(
                [1.0, 0.0],
            )

    with ThreadPoolExecutor(
        max_workers=4,
    ) as executor:
        futures = [
            executor.submit(clear_worker),
            executor.submit(clear_worker),
            executor.submit(read_worker),
            executor.submit(read_worker),
        ]

        for future in futures:
            future.result()

    assert len(store) == 0


def test_falsey_similarity_is_preserved(
    tmp_path: Path,
) -> None:
    class FalseySimilarity(DotProductSimilarity):
        def __bool__(self) -> bool:
            return False

    similarity = FalseySimilarity()

    backend = SQLiteBackend(
        tmp_path / "knowledge.db",
    )

    store = PersistentVectorStore(
        backend=backend,
        similarity=similarity,
    )

    assert store._similarity is similarity