"""Local multilingual sentence-transformer embedding provider."""

from __future__ import annotations

from typing import Any

from sentinel.knowledge.embeddings import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Generate normalized multilingual embeddings locally."""

    DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        *,
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string.")
        if not isinstance(device, str) or not device.strip():
            raise ValueError("device must be a non-empty string.")
        if (
            isinstance(batch_size, bool)
            or not isinstance(batch_size, int)
            or batch_size <= 0
        ):
            raise ValueError("batch_size must be a positive integer.")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "Local embeddings require the optional dependency. "
                'Install it with: python -m pip install "sentence-transformers>=5,<6"'
            ) from exc

        self._model: Any = SentenceTransformer(
            model_name.strip(),
            device=device.strip(),
            trust_remote_code=False,
        )
        self._batch_size = batch_size
        dimension = self._model.get_embedding_dimension()
        if (
            isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension <= 0
        ):
            raise RuntimeError("The embedding model returned an invalid dimension.")
        self._dimension = dimension

    def embed(self, text: str) -> list[float]:
        """Embed one text and return a normalized vector."""
        if not isinstance(text, str):
            raise TypeError("text must be a string.")
        vectors = self.embed_many([text])
        return vectors[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using the local model."""
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings.")
        if not all(isinstance(text, str) for text in texts):
            raise TypeError("every item in texts must be a string.")
        if not texts:
            return []

        encoded = self._model.encode(
            texts,
            batch_size=self._batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        encoded_vectors = encoded.tolist()
        if len(encoded_vectors) != len(texts):
            raise RuntimeError(
                "The embedding model returned an unexpected number of vectors."
            )

        vectors: list[list[float]] = []
        for vector in encoded_vectors:
            values = [float(value) for value in vector]
            if len(values) != self._dimension:
                raise RuntimeError(
                    "The embedding model returned an unexpected dimension."
                )
            vectors.append(values)
        return vectors

    def dimension(self) -> int:
        """Return the model's embedding dimension."""
        return self._dimension
