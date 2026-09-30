import threading

from sentinel.security.authorizer import SecurityAuthorizer
from sentinel.security.constants import Permission, Role
from sentinel.security.identity import SecurityIdentity
from sentinel.security.permissions import RolePermissionStore


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


def test_custom_permission_store_is_preserved():
    store = RolePermissionStore()
    authorizer = SecurityAuthorizer(store)

    assert authorizer.permission_store is store


def test_concurrent_authorization_is_safe():
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

    errors: list[Exception] = []

    def authorize_repeatedly() -> None:
        try:
            for _ in range(1000):
                assert authorizer.authorize(
                    identity,
                    Permission.READ,
                )
                assert authorizer.authorize(
                    identity,
                    Permission.WRITE,
                )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(
            target=authorize_repeatedly,
        )
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []


def test_concurrent_grants_are_safe():
    authorizer = SecurityAuthorizer()

    permissions = [
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
    ]

    barrier = threading.Barrier(len(permissions))

    def grant_permission(permission: Permission) -> None:
        barrier.wait()

        for _ in range(100):
            authorizer.grant(
                Role.ADMIN,
                [permission],
            )

    threads = [
        threading.Thread(
            target=grant_permission,
            args=(permission,),
        )
        for permission in permissions
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    for permission in permissions:
        assert authorizer.authorize(
            identity,
            permission,
        )


def test_concurrent_revokes_are_safe():
    authorizer = SecurityAuthorizer()

    permissions = [
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
    ]

    authorizer.grant(
        Role.ADMIN,
        permissions,
    )

    barrier = threading.Barrier(len(permissions))

    def revoke_permission(permission: Permission) -> None:
        barrier.wait()

        for _ in range(100):
            authorizer.revoke(
                Role.ADMIN,
                [permission],
            )

    threads = [
        threading.Thread(
            target=revoke_permission,
            args=(permission,),
        )
        for permission in permissions
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    for permission in permissions:
        assert not authorizer.authorize(
            identity,
            permission,
        )


def test_concurrent_grant_and_authorize_are_safe():
    authorizer = SecurityAuthorizer()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    errors: list[Exception] = []

    def grant_permissions() -> None:
        try:
            for _ in range(500):
                authorizer.grant(
                    Role.ADMIN,
                    [Permission.READ],
                )
        except Exception as exc:
            errors.append(exc)

    def authorize_permissions() -> None:
        try:
            for _ in range(500):
                authorizer.authorize(
                    identity,
                    Permission.READ,
                )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(
            target=grant_permissions,
        ),
        threading.Thread(
            target=authorize_permissions,
        ),
        threading.Thread(
            target=authorize_permissions,
        ),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []

    assert authorizer.authorize(
        identity,
        Permission.READ,
    )


def test_concurrent_clear_and_authorize_are_safe():
    authorizer = SecurityAuthorizer()

    authorizer.grant(
        Role.ADMIN,
        [Permission.READ],
    )

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    errors: list[Exception] = []

    def clear_permissions() -> None:
        try:
            for _ in range(100):
                authorizer.clear()
                authorizer.grant(
                    Role.ADMIN,
                    [Permission.READ],
                )
        except Exception as exc:
            errors.append(exc)

    def authorize_permissions() -> None:
        try:
            for _ in range(500):
                authorizer.authorize(
                    identity,
                    Permission.READ,
                )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(
            target=clear_permissions,
        ),
        threading.Thread(
            target=authorize_permissions,
        ),
        threading.Thread(
            target=authorize_permissions,
        ),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []