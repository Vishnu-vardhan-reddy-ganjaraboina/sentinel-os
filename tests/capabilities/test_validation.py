from __future__ import annotations

import pytest

from sentinel.capabilities.validation import (
    CapabilityArgumentValidationError,
    get_missing_required_arguments,
    validate_capability_arguments,
)

MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"],
    "additionalProperties": False,
}



def test_get_missing_required_arguments_returns_missing_fields() -> None:
    assert get_missing_required_arguments(MESSAGE_SCHEMA, {}) == ["message"]


def test_get_missing_required_arguments_ignores_provided_fields() -> None:
    assert get_missing_required_arguments(
        MESSAGE_SCHEMA,
        {"message": "hello"},
    ) == []


def test_get_missing_required_arguments_accepts_empty_schema() -> None:
    assert get_missing_required_arguments({}, {}) == []

def test_accepts_valid_arguments() -> None:
    validate_capability_arguments(
        MESSAGE_SCHEMA,
        {"message": "hello"},
    )


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"message": 123},
        {"message": "hello", "unexpected": True},
    ],
)
def test_rejects_invalid_arguments(arguments: dict[str, object]) -> None:
    with pytest.raises(CapabilityArgumentValidationError):
        validate_capability_arguments(MESSAGE_SCHEMA, arguments)


def test_empty_schema_allows_arbitrary_dictionary() -> None:
    validate_capability_arguments({}, {"anything": 123})


def test_rejects_non_dictionary_arguments() -> None:
    with pytest.raises(TypeError, match="arguments must be a dictionary"):
        validate_capability_arguments(
            MESSAGE_SCHEMA,
            ["not", "a", "dictionary"],  # type: ignore[arg-type]
        )


def test_rejects_invalid_schema() -> None:
    with pytest.raises(
        CapabilityArgumentValidationError,
        match="input schema is invalid",
    ):
        validate_capability_arguments(
            {"type": "not-a-json-schema-type"},
            {},
        )
