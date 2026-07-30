from sentinel.security.authorizer import SecurityAuthorizer
from sentinel.security.constants import Permission, Role
from sentinel.security.identity import SecurityIdentity


def test_authorize_success():
    authorizer = SecurityAuthorizer()

    authorizer.grant(
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

    assert authorizer.authorize(
        identity,
        Permission.READ,
    )

    assert authorizer.authorize(
        identity,
        Permission.WRITE,
    )


def test_authorize_failure():
    authorizer = SecurityAuthorizer()

    authorizer.grant(
        Role.USER,
        [
            Permission.READ,
        ],
    )

    identity = SecurityIdentity(
        "1",
        "User",
        {Role.USER},
    )

    assert not authorizer.authorize(
        identity,
        Permission.DELETE,
    )


def test_multiple_roles():
    authorizer = SecurityAuthorizer()

    authorizer.grant(
        Role.USER,
        [
            Permission.READ,
        ],
    )

    authorizer.grant(
        Role.ADMIN,
        [
            Permission.WRITE,
        ],
    )

    identity = SecurityIdentity(
        "1",
        "Alice",
        {
            Role.USER,
            Role.ADMIN,
        },
    )

    assert authorizer.authorize(
        identity,
        Permission.READ,
    )

    assert authorizer.authorize(
        identity,
        Permission.WRITE,
    )


def test_revoke():
    authorizer = SecurityAuthorizer()

    authorizer.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    authorizer.revoke(
        Role.ADMIN,
        [
            Permission.WRITE,
        ],
    )

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    assert authorizer.authorize(
        identity,
        Permission.READ,
    )

    assert not authorizer.authorize(
        identity,
        Permission.WRITE,
    )


def test_clear():
    authorizer = SecurityAuthorizer()

    authorizer.grant(
        Role.ADMIN,
        [
            Permission.READ,
        ],
    )

    authorizer.clear()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    assert not authorizer.authorize(
        identity,
        Permission.READ,
    )


def test_permission_store_property():
    authorizer = SecurityAuthorizer()

    assert authorizer.permission_store is not None