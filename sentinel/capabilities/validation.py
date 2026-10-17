"""Validation of arguments passed to Sentinel capabilities."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


class CapabilityArgumentValidationError(ValueError):
    """Raised when capability arguments or their schema are invalid."""


def validate_capability_arguments(
    input_schema: dict[str, Any],
    arguments: dict[str, Any],
) -> None:
    """Validate capability arguments without executing the capability.

    An empty schema is unconstrained for backward compatibility.
    Arguments must still be supplied as a dictionary.
    """
    if not isinstance(input_schema, dict):
        raise TypeError("input_schema must be a dictionary.")

    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a dictionary.")

    if not input_schema:
        return

    try:
        Draft202012Validator.check_schema(input_schema)
        validator = Draft202012Validator(input_schema)
        validator.validate(arguments)
    except SchemaError as exc:
        raise CapabilityArgumentValidationError(
            f"Capability input schema is invalid: {exc.message}"
        ) from exc
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        detail = f" at '{location}'" if location else ""
        raise CapabilityArgumentValidationError(
            f"Capability arguments are invalid{detail}: {exc.message}"
        ) from exc


def get_missing_required_arguments(
    input_schema: dict[str, Any],
    arguments: dict[str, Any],
) -> list[str]:
    """Return missing top-level required fields for a valid input schema."""
    if not isinstance(input_schema, dict):
        raise TypeError("input_schema must be a dictionary.")
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a dictionary.")
    if not input_schema:
        return []

    try:
        Draft202012Validator.check_schema(input_schema)
    except SchemaError as exc:
        raise CapabilityArgumentValidationError(
            f"Capability input schema is invalid: {exc.message}"
        ) from exc

    required = input_schema.get("required", [])
    if not isinstance(required, list):
        raise CapabilityArgumentValidationError(
            "Capability input schema has an invalid required list."
        )

    return [
        name for name in required
        if isinstance(name, str) and name not in arguments
    ]
