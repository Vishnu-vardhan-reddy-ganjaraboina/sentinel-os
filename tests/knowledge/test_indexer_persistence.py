from threading import Barrier, Thread

import pytest

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.chunker import (
    DocumentChunker,
    FixedSizeChunker,
)
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.vector_store import InMemoryVectorStore


class FailingEmbeddingProvider:
    def __init__(
        self,
        fail_on: int,
    ) -> None:
        self._calls = 0
        self._fail_on = fail_on

    def embed(
        self,
        text: str,
    ) -> list[float]:
        self._calls += 1

        if self._calls == self._fail_on:
            raise RuntimeError(
                "embedding failure"
            )

        return [1.0, 2.0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def make_document(
    document_id: str,
    text: str,
) -> Document:
    return Document(
        id=document_id,
        text=text,
    )


def make_indexer(
    vector_store: InMemoryVectorStore,
    embedding_provider=None,
    chunk_size: int = 5,
) -> Indexer:
    return Indexer(
        chunker=FixedSizeChunker(
            chunk_size=chunk_size,
            overlap=0,
        ),
        embedding_provider=(
            embedding_provider
            if embedding_provider is not None
            else DummyEmbeddingProvider(
                dimension=2
            )
        ),
        vector_store=vector_store,
    )


def test_failed_embedding_preserves_previous_version() -> None:
    store = InMemoryVectorStore()

    initial_indexer = make_indexer(
        store,
    )

    initial_indexer.index(
        make_document(
            "doc-1",
            "abcdefghij",
        )
    )

    previous_chunks = store.list_chunks()

    failing_indexer = make_indexer(
        store,
        FailingEmbeddingProvider(
            fail_on=2,
        ),
    )

    replacement = make_document(
        "doc-1",
        "abcdefghijklmnopqrst",
    )

    with pytest.raises(
        RuntimeError,
        match="embedding failure",
    ):
        failing_indexer.reindex(
            replacement,
        )

    current_chunks = store.list_chunks()

    assert [
        chunk.id
        for chunk in current_chunks
    ] == [
        chunk.id
        for chunk in previous_chunks
    ]

    assert [
        chunk.text
        for chunk in current_chunks
    ] == [
        chunk.text
        for chunk in previous_chunks
    ]


def test_successful_replacement_removes_stale_chunks() -> None:
    store = InMemoryVectorStore()

    indexer = make_indexer(
        store,
        chunk_size=5,
    )

    indexer.index(
        make_document(
            "doc-1",
            "abcdefghijklmnopqrst",
        )
    )

    assert len(store) == 4

    indexer.reindex(
        make_document(
            "doc-1",
            "abcde",
        )
    )

    chunks = store.list_chunks()

    assert len(chunks) == 1
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].text == "abcde"


def test_empty_chunk_result_removes_old_chunks() -> None:
    store = InMemoryVectorStore()

    class EmptyChunker(DocumentChunker):
        def chunk(
            self,
            document: Document,
        ) -> list[Chunk]:
            return []

    initial_indexer = make_indexer(
        store,
        chunk_size=5,
    )

    initial_indexer.index(
        make_document(
            "doc-1",
            "abcdefghij",
        )
    )

    assert len(store) == 2

    replacement_indexer = Indexer(
        chunker=EmptyChunker(),
        embedding_provider=DummyEmbeddingProvider(
            dimension=2,
        ),
        vector_store=store,
    )

    replacement_indexer.reindex(
        make_document(
            "doc-1",
            "replacement",
        )
    )

    assert not any(
        chunk.document_id == "doc-1"
        for chunk in store.list_chunks()
    )


def test_document_lock_registry_is_cleaned() -> None:
    store = InMemoryVectorStore()

    indexer = make_indexer(
        store,
    )

    for number in range(100):
        indexer.index(
            make_document(
                f"doc-{number}",
                "hello",
            )
        )

    assert indexer._document_locks == {}


def test_same_document_operations_are_serialized() -> None:
    store = InMemoryVectorStore()

    indexer = make_indexer(
        store,
    )

    barrier = Barrier(4)
    errors: list[Exception] = []

    def worker(number: int) -> None:
        try:
            barrier.wait()

            indexer.index(
                make_document(
                    "same-document",
                    f"document-{number}",
                )
            )
        except Exception as exc:
            errors.append(exc)

    threads = [
        Thread(
            target=worker,
            args=(number,),
        )
        for number in range(4)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []

    chunks = store.list_chunks()

    assert chunks
    assert all(
        chunk.document_id == "same-document"
        for chunk in chunks
    )


def test_reindex_does_not_remove_previous_version_before_embedding() -> None:
    store = InMemoryVectorStore()

    initial_indexer = make_indexer(
        store,
        chunk_size=5,
    )

    initial_indexer.index(
        make_document(
            "doc-1",
            "abcdefghij",
        )
    )

    class AlwaysFailingEmbeddingProvider(
        DummyEmbeddingProvider,
    ):
        def embed(
            self,
            text: str,
        ) -> list[float]:
            raise RuntimeError(
                "embedding failed",
            )

    failing_indexer = Indexer(
        chunker=FixedSizeChunker(
            chunk_size=5,
            overlap=0,
        ),
        embedding_provider=AlwaysFailingEmbeddingProvider(
            dimension=2,
        ),
        vector_store=store,
    )

    with pytest.raises(
        RuntimeError,
        match="embedding failed",
    ):
        failing_indexer.reindex(
            make_document(
                "doc-1",
                "replacement",
            )
        )

    chunks = store.list_chunks()

    assert len(chunks) == 2
    assert {
        chunk.text
        for chunk in chunks
    } == {
        "abcde",
        "fghij",
    }
