from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock

import pytest

from sentinel.knowledge.chunker import FixedSizeChunker
from sentinel.knowledge.document import Document
from sentinel.knowledge.embeddings import DummyEmbeddingProvider
from sentinel.knowledge.indexer import Indexer
from sentinel.knowledge.vector_store import InMemoryVectorStore, VectorStore


class BlockingChunker:
    def __init__(self):
        self.delegate = FixedSizeChunker(chunk_size=100)
        self.first_entered = Event()
        self.second_started = Event()
        self.second_entered = Event()
        self.release_first = Event()
        self.guard = Lock()
        self.calls = 0
        self.active = 0
        self.max_active = 0

    def chunk(self, document):
        with self.guard:
            self.calls += 1
            call_number = self.calls
            self.active += 1
            self.max_active = max(self.max_active, self.active)

        try:
            if call_number == 1:
                self.first_entered.set()
                if not self.release_first.wait(timeout=5):
                    raise TimeoutError("First indexing operation was not released.")
            else:
                self.second_entered.set()

            return self.delegate.chunk(document)
        finally:
            with self.guard:
                self.active -= 1


class BarrierChunker:
    def __init__(self):
        self.delegate = FixedSizeChunker(chunk_size=100)
        self.barrier = Barrier(2)

    def chunk(self, document):
        self.barrier.wait(timeout=5)
        return self.delegate.chunk(document)


def make_indexer(chunker, store=None):
    return Indexer(
        chunker=chunker,
        embedding_provider=DummyEmbeddingProvider(),
        vector_store=store if store is not None else InMemoryVectorStore(),
    )


def test_same_document_indexing_is_serialized():
    chunker = BlockingChunker()
    indexer = make_indexer(chunker)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            indexer.index,
            Document(id="same-doc", text="First version"),
        )

        assert chunker.first_entered.wait(timeout=3)

        def second_operation():
            chunker.second_started.set()
            return indexer.index(
                Document(id="same-doc", text="Second version"),
            )

        second = executor.submit(second_operation)

        assert chunker.second_started.wait(timeout=3)
        assert not chunker.second_entered.wait(timeout=0.2)

        chunker.release_first.set()

        first.result(timeout=5)
        second.result(timeout=5)

    assert chunker.calls == 2
    assert chunker.max_active == 1
    assert indexer._document_locks == {}


def test_different_documents_can_be_indexed_concurrently():
    chunker = BarrierChunker()
    indexer = make_indexer(chunker)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            indexer.index,
            Document(id="doc-one", text="First document"),
        )
        second = executor.submit(
            indexer.index,
            Document(id="doc-two", text="Second document"),
        )

        first.result(timeout=7)
        second.result(timeout=7)

    assert len(indexer.vector_store.list_chunks()) == 2
    assert indexer._document_locks == {}


def test_indexer_rejects_store_without_document_replacement():
    class UnsupportedReplacementStore(InMemoryVectorStore):
        replace_document = VectorStore.replace_document

    with pytest.raises(
        TypeError,
        match="atomic document replacement",
    ):
        make_indexer(
            FixedSizeChunker(chunk_size=100),
            UnsupportedReplacementStore(),
        )

def test_remove_waits_for_concurrent_index_of_same_document():
    class TrackingStore(InMemoryVectorStore):
        def __init__(self):
            super().__init__()
            self.delete_called = Event()

        def delete_document(self, document_id):
            self.delete_called.set()
            super().delete_document(document_id)

    chunker = BlockingChunker()
    store = TrackingStore()
    indexer = make_indexer(chunker, store)

    remove_started = Event()

    def remove_document():
        remove_started.set()
        indexer.remove("shared-doc")

    with ThreadPoolExecutor(max_workers=2) as executor:
        indexing = executor.submit(
            indexer.index,
            Document(id="shared-doc", text="Document being indexed"),
        )

        assert chunker.first_entered.wait(timeout=3)

        removal = executor.submit(remove_document)

        assert remove_started.wait(timeout=3)

        try:
            assert not store.delete_called.wait(timeout=0.2)
        finally:
            chunker.release_first.set()

        indexing.result(timeout=5)
        removal.result(timeout=5)

    assert store.delete_called.is_set()
    assert store.list_chunks() == []
    assert indexer._document_locks == {}
