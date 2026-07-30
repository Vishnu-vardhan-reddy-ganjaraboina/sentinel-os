"""
Authorizer implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

from sentinel.security.constants import Permission
from sentinel.security.identity import SecurityIdentity
from sentinel.security.interfaces import Authorizer
from sentinel.security.permissions import RolePermissionStore


class SecurityAuthorizer(Authorizer):
    """
    Default authorization implementation.
    """

    def __init__(
        self,
        permission_store: RolePermissionStore | None = None,
    ) -> None:
        self._permission_store = (
            permission_store
            if permission_store is not None
            else RolePermissionStore()
        )

    @property
    def permission_store(self) -> RolePermissionStore:
        """
        Return the underlying permission store.
        """
        return self._permission_store

    def authorize(
        self,
        identity: SecurityIdentity,
        permission: Permission,
    ) -> bool:
        """
        Determine whether an identity has the requested permission.
        """
        for role in identity.roles:
            if self._permission_store.has_permission(
                role,
                permission,
            ):
                return True

        return False

    def grant(
        self,
        role,
        permissions,
    ) -> None:
        """
        Grant permissions to a role.
        """
        self._permission_store.grant(
            role,
            permissions,
        )

    def revoke(
        self,
        role,
        permissions,
    ) -> None:
        """
        Revoke permissions from a role.
        """
        self._permission_store.revoke(
            role,
            permissions,
        )

    def clear(self) -> None:
        """
        Remove all permissions.
        """
        self._permission_store.clear()