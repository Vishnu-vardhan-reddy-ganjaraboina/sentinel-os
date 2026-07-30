from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.service import SecurityService


def test_manager_property():
    service = SecurityService()

    assert service.manager is not None


def test_register_identity():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    assert len(service) == 1
    assert service.get_identity("1") == identity


def test_authenticate():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    assert service.authenticate(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )


def test_authorize():
    service = SecurityService()

    service.grant(
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

    assert service.authorize(
        identity,
        Permission.READ,
    )

    assert service.authorize(
        identity,
        Permission.WRITE,
    )


def test_unregister_identity():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    service.unregister_identity(
        "1",
        "admin",
    )

    assert service.get_identity("1") is None
    assert len(service) == 0


def test_clear():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    service.clear()

    assert len(service) == 0