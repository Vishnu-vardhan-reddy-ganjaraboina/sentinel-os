import pytest

from sentinel.security.constants import Role
from sentinel.security.identity import SecurityIdentity


def test_create_identity():
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
    )

    assert identity.id == "user-1"
    assert identity.name == "Sentinel"
    assert identity.roles == set()


def test_add_role():
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
    )

    identity.add_role(Role.ADMIN)

    assert identity.has_role(Role.ADMIN)


def test_remove_role():
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
        {Role.ADMIN},
    )

    identity.remove_role(Role.ADMIN)

    assert not identity.has_role(Role.ADMIN)


def test_to_dict():
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
        {Role.USER},
    )

    data = identity.to_dict()

    assert data["id"] == "user-1"
    assert data["name"] == "Sentinel"
    assert data["roles"] == ["user"]


def test_equality():
    first = SecurityIdentity(
        "1",
        "Alice",
    )

    second = SecurityIdentity(
        "1",
        "Bob",
    )

    assert first == second


def test_hash():
    identity = SecurityIdentity(
        "1",
        "Alice",
    )

    assert hash(identity) == hash("1")


def test_invalid_identity_id():
    with pytest.raises(ValueError):
        SecurityIdentity(
            "",
            "Sentinel",
        )


def test_invalid_name():
    with pytest.raises(ValueError):
        SecurityIdentity(
            "user-1",
            "",
        )