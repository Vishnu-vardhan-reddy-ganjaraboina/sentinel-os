import pytest

from sentinel.core.validators import (
    require_non_empty,
    require_non_negative,
    require_positive,
    require_type,
)


def test_require_non_empty() -> None:
    assert require_non_empty("sentinel") == "sentinel"


def test_require_non_empty_rejects_whitespace() -> None:
    with pytest.raises(ValueError):
        require_non_empty("   ", "name")


def test_require_non_empty_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        require_non_empty(123, "name")  # type: ignore[arg-type]


def test_require_positive() -> None:
    assert require_positive(10) == 10


def test_require_positive_rejects_zero() -> None:
    with pytest.raises(ValueError):
        require_positive(0)


def test_require_positive_rejects_negative() -> None:
    with pytest.raises(ValueError):
        require_positive(-1)


def test_require_non_negative() -> None:
    assert require_non_negative(0) == 0
    assert require_non_negative(10) == 10


def test_require_non_negative_rejects_negative() -> None:
    with pytest.raises(ValueError):
        require_non_negative(-1)


def test_require_type() -> None:
    assert require_type("sentinel", str) == "sentinel"


def test_require_type_rejects_wrong_type() -> None:
    with pytest.raises(TypeError):
        require_type(123, str, "name")