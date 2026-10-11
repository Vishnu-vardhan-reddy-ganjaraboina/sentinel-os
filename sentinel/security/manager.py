"""
Manager for the Sentinel Security subsystem.
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.security.authenticator import SecurityAuthenticator
from sentinel.security.authorizer import SecurityAuthorizer
from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity


class SecurityManager:
    """
    High-level manager for security operations.
    """

    def __init__(self) -> None:
        self._authenticator = SecurityAuthenticator()
        self._authorizer = SecurityAuthorizer()
        self._identities: dict[str, SecurityIdentity] = {}
        self._identity_ids_by_username: dict[str, str] = {}

    @property
    def authenticator(self) -> SecurityAuthenticator:
        return self._authenticator

    @property
    def authorizer(self) -> SecurityAuthorizer:
        return self._authorizer

    def register_identity(
        self,
        identity: SecurityIdentity,
        credentials: SecurityCredentials,
    ) -> None:
        """
        Register a new identity and its credentials.
        """
        previous_id = self._identity_ids_by_username.get(
            credentials.username,
        )
        if previous_id is not None and previous_id != identity.id:
            self._identities.pop(previous_id, None)

        previous_identity = self._identities.get(identity.id)
        if previous_identity is not None:
            for username, registered_id in list(
                self._identity_ids_by_username.items(),
            ):
                if registered_id == identity.id:
                    self._identity_ids_by_username.pop(username, None)
                    self._authenticator.unregister(username)

        self._identities[identity.id] = identity
        self._identity_ids_by_username[credentials.username] = identity.id
        self._authenticator.register(credentials)

    def unregister_identity(
        self,
        identity_id: str,
        username: str,
    ) -> None:
        """
        Remove an identity and its credentials.
        """
        registered_id = self._identity_ids_by_username.get(username)
        if registered_id == identity_id:
            self._identity_ids_by_username.pop(username, None)
            self._authenticator.unregister(username)

        self._identities.pop(identity_id, None)
        for registered_username, registered_id in list(
            self._identity_ids_by_username.items(),
        ):
            if registered_id == identity_id:
                self._identity_ids_by_username.pop(registered_username, None)
                self._authenticator.unregister(registered_username)

    def get_identity(
        self,
        identity_id: str,
    ) -> SecurityIdentity | None:
        """
        Retrieve an identity.
        """
        return self._identities.get(identity_id)

    def authenticate(
        self,
        credentials: SecurityCredentials,
    ) -> bool:
        """
        Authenticate credentials.
        """
        return self._authenticator.authenticate(credentials)

    def authenticate_identity(
        self,
        credentials: SecurityCredentials,
    ) -> SecurityIdentity | None:
        """
        Authenticate credentials and return their registered identity.
        """
        if not self._authenticator.authenticate(credentials):
            return None

        identity_id = self._identity_ids_by_username.get(
            credentials.username,
        )
        if identity_id is None:
            return None

        return self._identities.get(identity_id)

    def authorize(
        self,
        identity: SecurityIdentity,
        permission: Permission,
    ) -> bool:
        """
        Authorize an identity.
        """
        return self._authorizer.authorize(
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
        self._authorizer.grant(
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
        self._authorizer.revoke(
            role,
            permissions,
        )

    def clear(self) -> None:
        """
        Clear all registered identities and permissions.
        """
        self._identities.clear()
        self._identity_ids_by_username.clear()
        self._authenticator.clear()
        self._authorizer.clear()

    def __len__(self) -> int:
        return len(self._identities)