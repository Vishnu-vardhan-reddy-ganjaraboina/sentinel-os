"""
Persistent vector store for Sentinel Knowledge.

Provides a storage-backend-backed implementation of the VectorStore
interface while reusing Sentinel's existing storage abstraction.
"""

from __future__ import annotations

import json

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.similarity import (
    CosineSimilarity,
    SimilarityMetric,
)
from sentinel.knowledge.vector_store import VectorStore
from sentinel.storage.interfaces import StorageBackend


class PersistentVectorStore(VectorStore):
    """
    Persistent VectorStore implementation.

    Chunks and embeddings are serialized as JSON and persisted through
    the configured StorageBackend.

    The storage backend is injected so the vector store remains
    independent of the concrete persistence technology.
    """

    _KEY_PREFIX = "knowledge:chunk:"

    def __init__(
        self,
        backend: StorageBackend,
        similarity: SimilarityMetric | None = None,
    ) -> None:
        self._backend = backend
        self._similarity = similarity or CosineSimilarity()

    @property
    def backend(self) -> StorageBackend:
        """Return the underlying storage backend."""
        return self._backend

    def connect(self) -> None:
        """
        Connect the underlying storage backend.
        """
        self._backend.connect()

    def close(self) -> None:
        """
        Close the underlying storage backend.
        """
        self._backend.close()

    def add(
        self,
        chunk: Chunk,
        embedding: list[float],
    ) -> None:
        """
        Add or replace a chunk and its embedding.
        """
        payload = {
            "chunk": {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "index": chunk.index,
                "metadata": dict(chunk.metadata),
            },
            "embedding": [
                float(value)
                for value in embedding
            ],
        }

        self._backend.set(
            self._key(chunk.id),
            json.dumps(payload),
        )

    def delete(
        self,
        chunk_id: str,
    ) -> None:
        """
        Delete a chunk.

        Deleting a missing chunk is intentionally a no-op,
        matching InMemoryVectorStore behavior.
        """
        key = self._key(chunk_id)

        if self._backend.exists(key):
            self._backend.delete(key)

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """
        Delete all chunks belonging to a document.
        """
        for chunk in self.list_chunks():
            if chunk.document_id == document_id:
                self.delete(chunk.id)

    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Return chunks ranked by similarity.
        """
        if limit <= 0:
            return []

        ranked: list[tuple[float, Chunk]] = []

        for chunk_id in self._chunk_ids():
            stored = self._load(chunk_id)

            if stored is None:
                continue

            chunk, stored_embedding = stored

            score = self._similarity.similarity(
                embedding,
                stored_embedding,
            )

            ranked.append(
                (
                    score,
                    chunk,
                )
            )

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            chunk
            for _, chunk in ranked[:limit]
        ]

    def exists(
        self,
        chunk_id: str,
    ) -> bool:
        """Return whether a chunk exists."""
        return self._backend.exists(
            self._key(chunk_id),
        )

    def get(
        self,
        chunk_id: str,
    ) -> Chunk | None:
        """
        Retrieve a chunk by ID.

        Returns None when the chunk does not exist.
        """
        stored = self._load(chunk_id)

        if stored is None:
            return None

        chunk, _ = stored
        return chunk

    def list_chunks(self) -> list[Chunk]:
        """Return all persisted chunks."""
        chunks: list[Chunk] = []

        for chunk_id in self._chunk_ids():
            stored = self._load(chunk_id)

            if stored is None:
                continue

            chunk, _ = stored
            chunks.append(chunk)

        return chunks

    def clear(self) -> None:
        """Remove all persisted knowledge chunks."""
        for chunk_id in self._chunk_ids():
            self.delete(chunk_id)

    def __len__(self) -> int:
        """Return the number of persisted chunks."""
        return len(self._chunk_ids())

    def _key(
        self,
        chunk_id: str,
    ) -> str:
        """Build the storage key for a chunk."""
        return f"{self._KEY_PREFIX}{chunk_id}"

    def _chunk_ids(self) -> list[str]:
        """Return IDs of all persisted knowledge chunks."""
        return [
            key.removeprefix(self._KEY_PREFIX)
            for key in self._backend.keys()
            if key.startswith(self._KEY_PREFIX)
        ]

    def _load(
        self,
        chunk_id: str,
    ) -> tuple[Chunk, list[float]] | None:
        """
        Load and deserialize a persisted chunk.
        """
        key = self._key(chunk_id)

        if not self._backend.exists(key):
            return None

        raw = self._backend.get(key)

        if not isinstance(raw, str):
            raise TypeError(
                f"Stored knowledge value for '{chunk_id}' "
                "must be a string."
            )

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Stored knowledge value for '{chunk_id}' "
                "contains invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                f"Stored knowledge value for '{chunk_id}' "
                "must be a JSON object."
            )

        chunk_data = payload.get("chunk")
        embedding_data = payload.get("embedding")

        if not isinstance(chunk_data, dict):
            raise ValueError(
                f"Stored chunk '{chunk_id}' is invalid."
            )

        if not isinstance(embedding_data, list):
            raise ValueError(
                f"Stored embedding for '{chunk_id}' is invalid."
            )

        metadata = chunk_data.get("metadata", {})

        if not isinstance(metadata, dict):
            raise ValueError(
                f"Stored metadata for '{chunk_id}' is invalid."
            )

        chunk = Chunk(
            id=str(chunk_data["id"]),
            document_id=str(chunk_data["document_id"]),
            text=str(chunk_data["text"]),
            index=int(chunk_data["index"]),
            metadata={
                str(key): str(value)
                for key, value in metadata.items()
            },
        )

        embedding = [
            float(value)
            for value in embedding_data
        ]

        return chunk, embedding