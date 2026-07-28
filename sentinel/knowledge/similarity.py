"""
Similarity metrics for Sentinel OS.

Similarity metrics compare two embedding vectors and return a similarity
score. Larger values indicate more similar vectors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt


class SimilarityMetric(ABC):
    """
    Base interface for similarity metrics.
    """

    @abstractmethod
    def similarity(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        """
        Compute the similarity between two vectors.
        """
        raise NotImplementedError

    @staticmethod
    def _validate_vectors(
        left: list[float],
        right: list[float],
    ) -> None:
        """
        Validate two vectors before comparison.
        """
        if not left:
            raise ValueError("Vectors cannot be empty.")

        if not right:
            raise ValueError("Vectors cannot be empty.")

        if len(left) != len(right):
            raise ValueError(
                "Vectors must have the same dimension."
            )


class CosineSimilarity(SimilarityMetric):
    """
    Cosine similarity.

    Returns values in the range [-1, 1].
    """

    def similarity(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        self._validate_vectors(left, right)

        dot = sum(a * b for a, b in zip(left, right))

        norm_left = sqrt(sum(a * a for a in left))
        norm_right = sqrt(sum(b * b for b in right))

        if norm_left == 0 or norm_right == 0:
            return 0.0

        return dot / (norm_left * norm_right)


class DotProductSimilarity(SimilarityMetric):
    """
    Dot product similarity.
    """

    def similarity(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        self._validate_vectors(left, right)

        return sum(a * b for a, b in zip(left, right))


class EuclideanSimilarity(SimilarityMetric):
    """
    Euclidean similarity.

    Converts Euclidean distance into a similarity score using:

        similarity = 1 / (1 + distance)

    Higher values indicate more similar vectors.
    """

    def similarity(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        self._validate_vectors(left, right)

        distance = sqrt(
            sum(
                (a - b) ** 2
                for a, b in zip(left, right)
            )
        )

        return 1.0 / (1.0 + distance)