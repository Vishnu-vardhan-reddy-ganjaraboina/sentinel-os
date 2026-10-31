from concurrent.futures import ThreadPoolExecutor

import pytest

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

    assert store.has_permission(Role.ADMIN, Permission.READ)
    assert store.has_permission(Role.ADMIN, Permission.WRITE)


def test_revoke_permission():
    store = RolePermissionStore()

    store.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    store.revoke(Role.ADMIN, [Permission.WRITE])

    assert store.has_permission(Role.ADMIN, Permission.READ)
    assert not store.has_permission(Role.ADMIN, Permission.WRITE)


def test_permissions_for():
    store = RolePermissionStore()
    store.grant(Role.USER, [Permission.READ])

    permissions = store.permissions_for(Role.USER)

    assert Permission.READ in permissions
    assert len(permissions) == 1


def test_clear():
    store = RolePermissionStore()
    store.grant(Role.ADMIN, [Permission.READ])

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

    assert store.to_dict()["admin"] == ["read", "write"]


def test_contains():
    store = RolePermissionStore()
    store.grant(Role.USER, [Permission.READ])

    assert Role.USER in store


def test_permissions_for_returns_isolated_set() -> None:
    store = RolePermissionStore()
    store.grant(Role.ADMIN, [Permission.READ])

    permissions = store.permissions_for(Role.ADMIN)
    permissions.add(Permission.WRITE)

    assert Permission.WRITE not in store.permissions_for(Role.ADMIN)


def test_concurrent_grants_are_safe() -> None:
    store = RolePermissionStore()

    def grant(index: int) -> None:
        permission = (
            Permission.READ
            if index % 2 == 0
            else Permission.WRITE
        )
        store.grant(Role.ADMIN, [permission])

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(grant, range(100)))

    permissions = store.permissions_for(Role.ADMIN)

    assert Permission.READ in permissions
    assert Permission.WRITE in permissions


def test_concurrent_permission_operations_are_safe() -> None:
    store = RolePermissionStore()
    store.grant(Role.ADMIN, [Permission.READ, Permission.WRITE])

    def operate(index: int) -> None:
        if index % 4 == 0:
            store.grant(Role.ADMIN, [Permission.EXECUTE])
        elif index % 4 == 1:
            store.revoke(Role.ADMIN, [Permission.EXECUTE])
        elif index % 4 == 2:
            store.has_permission(Role.ADMIN, Permission.READ)
        else:
            store.to_dict()
            store.permissions_for(Role.ADMIN)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(operate, range(200)))

    assert store.has_permission(Role.ADMIN, Permission.READ)
    assert store.has_permission(Role.ADMIN, Permission.WRITE)


def test_grant_iterator_failure_does_not_partially_mutate_store() -> None:
    store = RolePermissionStore()
    store.grant(Role.USER, [Permission.READ])

    def failing_permissions():
        yield Permission.WRITE
        raise RuntimeError("iterator failed")

    with pytest.raises(RuntimeError, match="iterator failed"):
        store.grant(Role.USER, failing_permissions())

    assert store.permissions_for(Role.USER) == {Permission.READ}


def test_revoke_iterator_failure_does_not_partially_mutate_store() -> None:
    store = RolePermissionStore()
    store.grant(Role.USER, [Permission.READ, Permission.WRITE])

    def failing_permissions():
        yield Permission.READ
        raise RuntimeError("iterator failed")

    with pytest.raises(RuntimeError, match="iterator failed"):
        store.revoke(Role.USER, failing_permissions())

    assert store.permissions_for(Role.USER) == {
        Permission.READ,
        Permission.WRITE,
    }


@pytest.mark.parametrize("operation", ["grant", "revoke"])
def test_invalid_permission_value_does_not_mutate_store(
    operation: str,
) -> None:
    store = RolePermissionStore()
    store.grant(Role.USER, [Permission.READ])

    with pytest.raises(TypeError, match="Permission values"):
        getattr(store, operation)(Role.USER, [Permission.WRITE, "DELETE"])

    assert store.permissions_for(Role.USER) == {Permission.READ}
