import threading

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


def test_roles_returns_isolated_set() -> None:
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
        {Role.USER},
    )

    roles = identity.roles
    roles.add(Role.ADMIN)

    assert identity.has_role(Role.ADMIN) is False
    assert identity.has_role(Role.USER) is True


def test_concurrent_role_additions_are_safe() -> None:
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
    )

    roles = [
        Role.ADMIN,
        Role.USER,
    ]

    barrier = threading.Barrier(len(roles))

    def add_role(role: Role) -> None:
        barrier.wait()
        identity.add_role(role)

    threads = [
        threading.Thread(
            target=add_role,
            args=(role,),
        )
        for role in roles
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert identity.roles == set(roles)


def test_concurrent_role_removals_are_safe() -> None:
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
        {
            Role.ADMIN,
            Role.USER,
        },
    )

    roles = [
        Role.ADMIN,
        Role.USER,
    ]

    barrier = threading.Barrier(len(roles))

    def remove_role(role: Role) -> None:
        barrier.wait()
        identity.remove_role(role)

    threads = [
        threading.Thread(
            target=remove_role,
            args=(role,),
        )
        for role in roles
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert identity.roles == set()


def test_concurrent_add_and_remove_are_safe() -> None:
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
    )

    iterations = 100

    def add_roles() -> None:
        for _ in range(iterations):
            identity.add_role(Role.ADMIN)
            identity.add_role(Role.USER)

    def remove_roles() -> None:
        for _ in range(iterations):
            identity.remove_role(Role.ADMIN)
            identity.remove_role(Role.USER)

    threads = [
        threading.Thread(target=add_roles)
        for _ in range(4)
    ] + [
        threading.Thread(target=remove_roles)
        for _ in range(4)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # The final state is nondeterministic because add/remove operations
    # intentionally overlap. The important invariant is that the role
    # collection remains valid and internally consistent.
    assert identity.roles <= {
        Role.ADMIN,
        Role.USER,
    }


def test_concurrent_reads_are_safe() -> None:
    identity = SecurityIdentity(
        "user-1",
        "Sentinel",
        {
            Role.ADMIN,
            Role.USER,
        },
    )

    errors: list[Exception] = []

    def read_identity() -> None:
        try:
            for _ in range(1000):
                _roles = identity.roles
                identity.has_role(Role.ADMIN)
                identity.to_dict()
                repr(identity)
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=read_identity)
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []