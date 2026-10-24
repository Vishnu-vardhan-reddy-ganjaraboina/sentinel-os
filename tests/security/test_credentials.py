import hmac

import pytest

from sentinel.security.credentials import SecurityCredentials


def test_create_credentials():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert credentials.username == "admin"
    assert credentials.secret == "password123"


def test_verify_success():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert credentials.verify("password123") is True


def test_verify_failure():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert credentials.verify("wrong-password") is False


def test_verify_uses_constant_time_comparison(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[tuple[str, str]] = []

    def compare_digest(
        first: str,
        second: str,
    ) -> bool:
        calls.append((first, second))
        return first == second

    monkeypatch.setattr(
        hmac,
        "compare_digest",
        compare_digest,
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert credentials.verify("password123") is True

    assert calls == [
        (b"password123", b"password123"),
    ]


def test_to_dict():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    data = credentials.to_dict()

    assert data == {
        "username": "admin",
    }

    assert "secret" not in data
    assert "password123" not in str(data)


def test_equality():
    first = SecurityCredentials(
        "admin",
        "password123",
    )

    second = SecurityCredentials(
        "admin",
        "password123",
    )

    assert first == second


def test_inequality_for_different_secret():
    first = SecurityCredentials(
        "admin",
        "password123",
    )

    second = SecurityCredentials(
        "admin",
        "different-password",
    )

    assert first != second


def test_inequality_for_different_username():
    first = SecurityCredentials(
        "admin",
        "password123",
    )

    second = SecurityCredentials(
        "user",
        "password123",
    )

    assert first != second


def test_hash():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert hash(credentials) == hash(
        ("admin", "password123")
    )


def test_equal_credentials_have_equal_hash():
    first = SecurityCredentials(
        "admin",
        "password123",
    )

    second = SecurityCredentials(
        "admin",
        "password123",
    )

    assert first == second
    assert hash(first) == hash(second)


def test_invalid_username():
    with pytest.raises(ValueError):
        SecurityCredentials(
            "",
            "password123",
        )


def test_invalid_whitespace_username():
    with pytest.raises(ValueError):
        SecurityCredentials(
            "   ",
            "password123",
        )


def test_invalid_secret():
    with pytest.raises(ValueError):
        SecurityCredentials(
            "admin",
            "",
        )


def test_invalid_whitespace_secret():
    with pytest.raises(ValueError):
        SecurityCredentials(
            "admin",
            "   ",
        )


def test_repr_does_not_expose_secret():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    representation = repr(credentials)

    assert "password123" not in representation
    assert "admin" in representation


def test_string_representation_does_not_expose_secret():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    representation = str(credentials)

    assert "password123" not in representation


def test_to_dict_does_not_expose_secret():
    credentials = SecurityCredentials(
        "admin",
        "super-secret-value",
    )

    data = credentials.to_dict()

    assert data == {
        "username": "admin",
    }

    assert "super-secret-value" not in repr(data)