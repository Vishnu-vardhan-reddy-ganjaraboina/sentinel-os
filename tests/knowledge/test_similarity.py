import math

import pytest

from sentinel.knowledge.similarity import (
    CosineSimilarity,
    DotProductSimilarity,
    EuclideanSimilarity,
)


@pytest.mark.parametrize(
    "metric",
    [
        CosineSimilarity(),
        DotProductSimilarity(),
        EuclideanSimilarity(),
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_similarity_rejects_non_finite_values(
    metric,
    invalid_value,
):
    with pytest.raises(
        ValueError,
        match="finite values",
    ):
        metric.similarity(
            [1.0, invalid_value],
            [1.0, 2.0],
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


def test_cosine_zero_vector():
    metric = CosineSimilarity()

    assert metric.similarity(
        [0, 0],
        [1, 2],
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


def test_euclidean_different_vectors():
    metric = EuclideanSimilarity()

    assert metric.similarity(
        [0, 0],
        [3, 4],
    ) == pytest.approx(1 / 6)


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


def test_empty_left_vector():
    metric = CosineSimilarity()

    with pytest.raises(ValueError):
        metric.similarity([], [1.0])


def test_empty_right_vector():
    metric = CosineSimilarity()

    with pytest.raises(ValueError):
        metric.similarity([1.0], [])


def test_valid_similarity_results_are_finite():
    metrics = (
        CosineSimilarity(),
        DotProductSimilarity(),
        EuclideanSimilarity(),
    )

    for metric in metrics:
        result = metric.similarity(
            [1.0, 2.0, 3.0],
            [3.0, 2.0, 1.0],
        )

        assert math.isfinite(result)