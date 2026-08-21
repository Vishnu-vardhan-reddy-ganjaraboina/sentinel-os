"""
Common validation helpers for Sentinel OS.
"""

from __future__ import annotations

from typing import Any


def require_non_empty(value: str, field_name: str = "value") -> str:
    """
    Validate that a string is not empty or whitespace-only.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")

    return value


def require_positive(
    value: int | float,
    field_name: str = "value",
) -> int | float:
    """
    Validate that a numeric value is greater than zero.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric.")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return value


def require_non_negative(
    value: int | float,
    field_name: str = "value",
) -> int | float:
    """
    Validate that a numeric value is zero or greater.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric.")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")

    return value


def require_type(
    value: Any,
    expected_type: type[Any],
    field_name: str = "value",
) -> Any:
    """
    Validate that a value has the expected type.
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{field_name} must be of type "
            f"{expected_type.__name__}."
        )

    return value