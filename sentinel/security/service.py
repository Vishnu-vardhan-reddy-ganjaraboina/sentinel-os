"""
Service layer for the Sentinel Security subsystem.
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class SecurityService:
    """
    Public service interface for the Security subsystem.
    """

    def __init__(self) -> None:
        self._manager = SecurityManager()

    @property
    def manager(self) -> SecurityManager:
        """
        Return the underlying manager.
        """
        return self._manager

    def register_identity(
        self,
        identity: SecurityIdentity,
        credentials: SecurityCredentials,
    ) -> None:
        """
        Register an identity.
        """
        self._manager.register_identity(
            identity,
            credentials,
        )

    def unregister_identity(
        self,
        identity_id: str,
        username: str,
    ) -> None:
        """
        Remove an identity.
        """
        self._manager.unregister_identity(
            identity_id,
            username,
        )

    def get_identity(
        self,
        identity_id: str,
    ) -> SecurityIdentity | None:
        """
        Retrieve an identity.
        """
        return self._manager.get_identity(identity_id)

    def authenticate(
        self,
        credentials: SecurityCredentials,
    ) -> bool:
        """
        Authenticate credentials.
        """
        return self._manager.authenticate(credentials)

    def authorize(
        self,
        identity: SecurityIdentity,
        permission: Permission,
    ) -> bool:
        """
        Check whether an identity has a permission.
        """
        return self._manager.authorize(
            identity,
            permission,
        )

    def grant(
        self,
        role: Role,
        permissions: Iterable[Permission],
    ) -> None:
        """
        Grant permissions to a role.
        """
        self._manager.grant(
            role,
            permissions,
        )

    def revoke(
        self,
        role: Role,
        permissions: Iterable[Permission],
    ) -> None:
        """
        Revoke permissions from a role.
        """
        self._manager.revoke(
            role,
            permissions,
        )

    def clear(self) -> None:
        """
        Remove all identities and permissions.
        """
        self._manager.clear()

    def __len__(self) -> int:
        return len(self._manager)