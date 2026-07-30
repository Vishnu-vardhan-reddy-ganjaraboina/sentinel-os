from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


def test_register_identity():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    assert len(manager) == 1
    assert manager.get_identity("1") == identity


def test_authenticate():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    assert manager.authenticate(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )


def test_authorize():
    manager = SecurityManager()

    manager.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    assert manager.authorize(
        identity,
        Permission.READ,
    )

    assert manager.authorize(
        identity,
        Permission.WRITE,
    )


def test_unregister_identity():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    manager.unregister_identity(
        "1",
        "admin",
    )

    assert manager.get_identity("1") is None
    assert len(manager) == 0


def test_clear():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    manager.clear()

    assert len(manager) == 0