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