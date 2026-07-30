"""
Permission store implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.security.constants import Permission, Role
from sentinel.security.interfaces import PermissionStore


class RolePermissionStore(PermissionStore):
    """
    Stores permissions assigned to roles.
    """

    def __init__(self) -> None:
        self._permissions: dict[Role, set[Permission]] = {}

    def grant(
        self,
        role: Role,
        permissions: Iterable[Permission],
    ) -> None:
        """
        Grant permissions to a role.
        """
        if role not in self._permissions:
            self._permissions[role] = set()

        self._permissions[role].update(permissions)

    def revoke(
        self,
        role: Role,
        permissions: Iterable[Permission],
    ) -> None:
        """
        Revoke permissions from a role.
        """
        if role not in self._permissions:
            return

        self._permissions[role].difference_update(permissions)

    def permissions_for(
        self,
        role: Role,
    ) -> set[Permission]:
        """
        Return permissions assigned to a role.
        """
        return set(self._permissions.get(role, set()))

    def has_permission(
        self,
        role: Role,
        permission: Permission,
    ) -> bool:
        """
        Check whether a role has a permission.
        """
        return permission in self._permissions.get(role, set())

    def clear(self) -> None:
        """
        Remove all role-permission mappings.
        """
        self._permissions.clear()

    def to_dict(self) -> dict[str, list[str]]:
        """
        Serialize the permission store.
        """
        return {
            role.value: sorted(
                permission.value
                for permission in permissions
            )
            for role, permissions in self._permissions.items()
        }

    def __contains__(self, role: Role) -> bool:
        return role in self._permissions

    def __len__(self) -> int:
        return len(self._permissions)