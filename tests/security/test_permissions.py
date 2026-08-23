from sentinel.security.constants import Permission, Role
from sentinel.security.permissions import RolePermissionStore


def test_grant_permissions():
    store = RolePermissionStore()

    store.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    assert store.has_permission(
        Role.ADMIN,
        Permission.READ,
    )

    assert store.has_permission(
        Role.ADMIN,
        Permission.WRITE,
    )


def test_revoke_permission():
    store = RolePermissionStore()

    store.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    store.revoke(
        Role.ADMIN,
        [Permission.WRITE],
    )

    assert store.has_permission(
        Role.ADMIN,
        Permission.READ,
    )

    assert not store.has_permission(
        Role.ADMIN,
        Permission.WRITE,
    )


def test_permissions_for():
    store = RolePermissionStore()

    store.grant(
        Role.USER,
        [Permission.READ],
    )

    permissions = store.permissions_for(Role.USER)

    assert Permission.READ in permissions
    assert len(permissions) == 1


def test_clear():
    store = RolePermissionStore()

    store.grant(
        Role.ADMIN,
        [Permission.READ],
    )

    store.clear()

    assert len(store) == 0


def test_to_dict():
    store = RolePermissionStore()

    store.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    data = store.to_dict()

    assert data["admin"] == [
        "read",
        "write",
    ]


def test_contains():
    store = RolePermissionStore()

    store.grant(
        Role.USER,
        [Permission.READ],
    )

    assert Role.USER in store

def test_permissions_for_returns_isolated_set() -> None:
    store = RolePermissionStore()

    store.grant(
        Role.ADMIN,
        [Permission.READ],
    )

    permissions = store.permissions_for(Role.ADMIN)
    permissions.add(Permission.WRITE)

    assert Permission.WRITE not in store.permissions_for(
        Role.ADMIN
    )

def test_concurrent_grants_are_safe() -> None:
    from concurrent.futures import ThreadPoolExecutor

    store = RolePermissionStore()

    def grant(index: int) -> None:
        store.grant(
            Role.ADMIN,
            [
                Permission.READ
                if index % 2 == 0
                else Permission.WRITE
            ],
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                grant,
                range(100),
            )
        )

    permissions = store.permissions_for(Role.ADMIN)

    assert Permission.READ in permissions
    assert Permission.WRITE in permissions