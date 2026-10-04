"""
Persistent vector store for Sentinel Knowledge.

Provides a storage-backend-backed implementation of the VectorStore
interface while reusing Sentinel's existing storage abstraction.
"""

from __future__ import annotations

import json
from math import isfinite
from threading import RLock

from sentinel.knowledge.chunk import Chunk
from sentinel.knowledge.similarity import (
    CosineSimilarity,
    SimilarityMetric,
)
from sentinel.knowledge.vector_store import VectorStore
from sentinel.storage.interfaces import StorageBackend


class PersistentVectorStore(VectorStore):
    """
    Thread-safe persistent VectorStore implementation.

    Each chunk is stored as one JSON record containing:

        {
            "chunk": {...},
            "embedding": [...]
        }

    Multi-chunk document replacement requires the storage backend to support
    atomic transactions. This prevents an indexing failure from leaving a
    partially replaced document.
    """

    _KEY_PREFIX = "knowledge:chunk:"

    def __init__(
        self,
        backend: StorageBackend,
        similarity: SimilarityMetric | None = None,
    ) -> None:
        self._lock = RLock()
        self._backend = backend

        self._similarity = (
            similarity
            if similarity is not None
            else CosineSimilarity()
        )

    @property
    def backend(self) -> StorageBackend:
        """Return the underlying storage backend."""
        return self._backend

    def connect(self) -> None:
        with self._lock:
            self._backend.connect()

    def close(self) -> None:
        with self._lock:
            self._backend.close()

    def add(
        self,
        chunk: Chunk,
        embedding: list[float],
    ) -> None:
        """
        Add or replace one chunk.

        Serialization happens before the storage mutation so invalid data
        cannot partially modify the store.
        """
        serialized = self._serialize(
            chunk,
            embedding,
        )

        with self._lock:
            self._backend.set(
                self._key(chunk.id),
                serialized,
            )

    def replace_document(
        self,
        document_id: str,
        chunks: list[tuple[Chunk, list[float]]],
    ) -> None:
        """
        Atomically replace every chunk belonging to a document.

        All chunks and embeddings are serialized before any mutation occurs.

        The storage backend must support atomic transactions. Otherwise,
        silently performing delete-then-insert would violate the production
        consistency guarantee.
        """
        prepared: list[tuple[str, str]] = []
        seen_ids: set[str] = set()

        for chunk, embedding in chunks:
            if chunk.document_id != document_id:
                raise ValueError(
                    "Chunk document ID does not match replacement "
                    f"document ID '{document_id}'."
                )

            if chunk.id in seen_ids:
                raise ValueError(
                    f"Duplicate chunk ID '{chunk.id}' in replacement."
                )

            seen_ids.add(chunk.id)

            prepared.append(
                (
                    self._key(chunk.id),
                    self._serialize(
                        chunk,
                        embedding,
                    ),
                )
            )

        with self._lock:
            try:
                transaction = self._backend.atomic()
            except AttributeError as exc:
                raise RuntimeError(
                    "Storage backend does not expose atomic transactions."
                ) from exc

            try:
                with transaction:
                    old_keys = self._document_keys_locked(
                        document_id,
                    )

                    for key in old_keys:
                        self._backend.delete(key)

                    for key, serialized in prepared:
                        self._backend.set(
                            key,
                            serialized,
                        )

            except NotImplementedError as exc:
                raise RuntimeError(
                    "Storage backend does not support atomic document "
                    "replacement."
                ) from exc

    def delete(
        self,
        chunk_id: str,
    ) -> None:
        """
        Delete a chunk if it exists.

        Missing chunks remain a no-op at the vector-store level.
        """
        key = self._key(chunk_id)

        with self._lock:
            if self._backend.exists(key):
                self._backend.delete(key)

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """
        Delete all chunks belonging to a document.

        This operation is serialized at the vector-store level.
        """
        with self._lock:
            keys = self._document_keys_locked(
                document_id,
            )

            for key in keys:
                if self._backend.exists(key):
                    self._backend.delete(key)

    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[Chunk]:
        """
        Return chunks ranked by similarity.

        Persistent records are loaded into a stable snapshot before
        similarity calculations.
        """
        if limit <= 0:
            return []

        with self._lock:
            snapshot = self._snapshot_locked()

        ranked: list[tuple[float, Chunk]] = []

        for chunk, stored_embedding in snapshot:
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
        with self._lock:
            return self._backend.exists(
                self._key(chunk_id)
            )

    def get(
        self,
        chunk_id: str,
    ) -> Chunk | None:
        with self._lock:
            stored = self._load_locked(
                chunk_id,
            )

        if stored is None:
            return None

        chunk, _ = stored
        return chunk

    def list_chunks(self) -> list[Chunk]:
        with self._lock:
            snapshot = self._snapshot_locked()

        return [
            chunk
            for chunk, _ in snapshot
        ]

    def clear(self) -> None:
        with self._lock:
            keys = self._chunk_keys_locked()

            for key in keys:
                if self._backend.exists(key):
                    self._backend.delete(key)

    def __len__(self) -> int:
        with self._lock:
            return len(
                self._chunk_keys_locked()
            )

    def _key(
        self,
        chunk_id: str,
    ) -> str:
        return f"{self._KEY_PREFIX}{chunk_id}"

    def _chunk_keys_locked(self) -> list[str]:
        """
        Return a stable list of persisted knowledge keys.

        Caller must hold ``self._lock``.
        """
        return [
            key
            for key in self._backend.keys()
            if key.startswith(
                self._KEY_PREFIX
            )
        ]

    def _document_keys_locked(
        self,
        document_id: str,
    ) -> list[str]:
        """
        Find all chunk keys belonging to a document.

        Caller must hold ``self._lock``.
        """
        keys: list[str] = []

        for key in self._chunk_keys_locked():
            chunk_id = key.removeprefix(
                self._KEY_PREFIX
            )

            stored = self._load_locked(
                chunk_id,
            )

            if stored is None:
                continue

            chunk, _ = stored

            if chunk.document_id == document_id:
                keys.append(key)

        return keys

    def _snapshot_locked(
        self,
    ) -> list[tuple[Chunk, list[float]]]:
        """
        Load all records into a stable snapshot.

        Caller must hold ``self._lock``.
        """
        snapshot: list[
            tuple[Chunk, list[float]]
        ] = []

        for key in self._chunk_keys_locked():
            chunk_id = key.removeprefix(
                self._KEY_PREFIX
            )

            stored = self._load_locked(
                chunk_id,
            )

            if stored is not None:
                chunk, embedding = stored

                snapshot.append(
                    (
                        chunk,
                        list(embedding),
                    )
                )

        return snapshot

    def _load_locked(
        self,
        chunk_id: str,
    ) -> tuple[Chunk, list[float]] | None:
        """
        Load and validate one persisted chunk.

        Caller must hold ``self._lock``.
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

        required_fields = (
            "id",
            "document_id",
            "text",
            "index",
        )

        for field_name in required_fields:
            if field_name not in chunk_data:
                raise ValueError(
                    f"Stored chunk '{chunk_id}' is missing "
                    f"'{field_name}'."
                )

        metadata = chunk_data.get(
            "metadata",
            {},
        )

        if not isinstance(metadata, dict):
            raise ValueError(
                f"Stored metadata for '{chunk_id}' is invalid."
            )

        try:
            chunk = Chunk(
                id=str(chunk_data["id"]),
                document_id=str(
                    chunk_data["document_id"]
                ),
                text=str(chunk_data["text"]),
                index=int(chunk_data["index"]),
                metadata={
                    str(key): str(value)
                    for key, value in metadata.items()
                },
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError(
                f"Stored chunk '{chunk_id}' is invalid."
            ) from exc

        embedding: list[float] = []

        for value in embedding_data:
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Stored embedding for '{chunk_id}' "
                    "contains a non-numeric value."
                ) from exc

            if not isfinite(numeric):
                raise ValueError(
                    f"Stored embedding for '{chunk_id}' "
                    "contains a non-finite value."
                )

            embedding.append(numeric)

        return (
            chunk,
            embedding,
        )

    @staticmethod
    def _serialize(
        chunk: Chunk,
        embedding: list[float],
    ) -> str:
        """
        Serialize one chunk/embedding pair.

        This intentionally serializes Chunk explicitly because Chunk does
        not own persistence concerns and does not expose to_dict().
        """
        serialized_embedding: list[float] = []

        for value in embedding:
            numeric = float(value)

            if not isfinite(numeric):
                raise ValueError(
                    "Embedding must contain only finite values."
                )

            serialized_embedding.append(
                numeric
            )

        payload = {
            "chunk": {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "index": chunk.index,
                "metadata": dict(chunk.metadata),
            },
            "embedding": serialized_embedding,
        }

        return json.dumps(
            payload,
            separators=(
                ",",
                ":",
            ),
        )