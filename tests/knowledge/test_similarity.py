from math import inf, nan

import pytest

from sentinel.knowledge.similarity import (
    CosineSimilarity,
    DotProductSimilarity,
    EuclideanSimilarity,
)


def test_cosine_identical():
    metric = CosineSimilarity()

    assert metric.similarity(
        [1, 2, 3],
        [1, 2, 3],
    ) == pytest.approx(1.0)


def test_cosine_orthogonal():
    metric = CosineSimilarity()

    assert metric.similarity(
        [1, 0],
        [0, 1],
    ) == pytest.approx(0.0)


def test_dot_product():
    metric = DotProductSimilarity()

    assert metric.similarity(
        [1, 2],
        [3, 4],
    ) == 11


def test_euclidean_identical():
    metric = EuclideanSimilarity()

    assert metric.similarity(
        [5, 5],
        [5, 5],
    ) == pytest.approx(1.0)


def test_dimension_mismatch():
    metric = CosineSimilarity()

    with pytest.raises(ValueError):
        metric.similarity(
            [1, 2],
            [1],
        )


def test_empty_vector():
    metric = CosineSimilarity()

    with pytest.raises(ValueError):
        metric.similarity([], [])

@pytest.mark.parametrize(
    "vector",
    [
        [nan],
        [inf],
        [-inf],
    ],
)
def test_cosine_rejects_non_finite_values(
    vector: list[float],
) -> None:
    with pytest.raises(ValueError, match="finite"):
        CosineSimilarity().similarity(vector, [1.0])


@pytest.mark.parametrize(
    "metric",
    [
        CosineSimilarity(),
        DotProductSimilarity(),
        EuclideanSimilarity(),
    ],
)
def test_similarity_metrics_reject_non_finite_values(
    metric,
) -> None:
    with pytest.raises(ValueError, match="finite"):
        metric.similarity([nan], [1.0])