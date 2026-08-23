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

    assert credentials.verify("password123")


def test_verify_failure():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert not credentials.verify("wrong-password")


def test_to_dict():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    data = credentials.to_dict()

    assert data == {
        "username": "admin",
    }


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


def test_hash():
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert hash(credentials) == hash(
        ("admin", "password123")
    )


def test_invalid_username():
    with pytest.raises(ValueError):
        SecurityCredentials(
            "",
            "password123",
        )


def test_invalid_secret():
    with pytest.raises(ValueError):
        SecurityCredentials(
            "admin",
            "",
        )

def test_verify_accepts_correct_secret() -> None:
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert credentials.verify("password123") is True


def test_verify_rejects_wrong_secret() -> None:
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    assert credentials.verify("wrong-password") is False


def test_repr_does_not_expose_secret() -> None:
    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    representation = repr(credentials)

    assert "password123" not in representation
    assert "admin" in representation