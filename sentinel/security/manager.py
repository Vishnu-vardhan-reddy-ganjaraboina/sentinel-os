"""
Security manager coordinating identity, authentication, and authorization.
"""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from .authenticator import SecurityAuthenticator
from .authorizer import SecurityAuthorizer
from .constants import Permission, Role
from .credentials import SecurityCredentials
from .identity import SecurityIdentity


class SecurityManager:
    """Coordinate security identity, authentication, and authorization."""

    def __init__(self) -> None:
        self._authenticator = SecurityAuthenticator()
        self._authorizer = SecurityAuthorizer()
        self._identities: dict[str, SecurityIdentity] = {}
        self._lock = RLock()
        self._generation = 0
        self._identity_ids_by_username: dict[str, str] = {}
        self._usernames_by_identity_id: dict[str, str] = {}


    def register_identity(
        self,
        identity: SecurityIdentity,
        credentials: SecurityCredentials,
    ) -> None:
        """Register an identity and its credentials atomically."""
        with self._lock:
            generation = self._generation

        record = self._authenticator._prepare(credentials)

        with self._lock:
            if generation != self._generation:
                raise RuntimeError(
                    "security state changed during identity registration."
                )

            username = credentials.username
            identity_id = identity.id

            username_owner = self._identity_ids_by_username.get(username)
            if username_owner is not None and username_owner != identity_id:
                raise ValueError(
                    f"username {username!r} is already registered."
                )

            previous_identity = self._identities.get(identity_id)
            previous_username = self._usernames_by_identity_id.get(identity_id)

            self._identities[identity_id] = identity
            self._identity_ids_by_username[username] = identity_id
            self._usernames_by_identity_id[identity_id] = username

            try:
                self._authenticator._commit(username, record)
            except Exception:
                if previous_identity is None:
                    self._identities.pop(identity_id, None)
                else:
                    self._identities[identity_id] = previous_identity

                self._identity_ids_by_username.pop(username, None)
                self._usernames_by_identity_id.pop(identity_id, None)

                if previous_username is not None:
                    self._identity_ids_by_username[
                        previous_username
                    ] = identity_id
                    self._usernames_by_identity_id[
                        identity_id
                    ] = previous_username

                raise

            if previous_username is not None and previous_username != username:
                self._identity_ids_by_username.pop(previous_username, None)
                self._authenticator.unregister(previous_username)

    def authenticate_identity(
        self,
        credentials: SecurityCredentials,
    ) -> SecurityIdentity | None:
        """Authenticate credentials and resolve their registered identity."""
        with self._lock:
            if not self._authenticator.authenticate(credentials):
                return None

            identity_id = self._identity_ids_by_username.get(
                credentials.username
            )

            if identity_id is None:
                return None

            return self._identities.get(identity_id)
    def unregister_identity(
        self,
        identity_id: str,
        username: str,
    ) -> None:
        """Remove an identity and its registered credentials."""
        with self._lock:
            self._identities.pop(identity_id, None)

            registered_username = self._usernames_by_identity_id.pop(
                identity_id,
                None,
            )

            if registered_username is not None:
                self._identity_ids_by_username.pop(
                    registered_username,
                    None,
                )
                self._authenticator.unregister(registered_username)
            elif self._identity_ids_by_username.get(username) == identity_id:
                self._identity_ids_by_username.pop(username, None)
                self._authenticator.unregister(username)

    def get_identity(
        self,
        identity_id: str,
    ) -> SecurityIdentity | None:
        """Return an identity by ID."""
        with self._lock:
            return self._identities.get(identity_id)

    def authenticate(
        self,
        credentials: SecurityCredentials,
    ) -> bool:
        """Authenticate credentials."""
        return self._authenticator.authenticate(credentials)

    def authorize(
        self,
        identity: SecurityIdentity,
        permission: Permission,
    ) -> bool:
        """Check whether an identity has a permission."""
        return self._authorizer.authorize(
            identity,
            permission,
        )

    def grant(
        self,
        role: Role,
        permission: Permission | Iterable[Permission],
    ) -> None:
        """Grant one or more permissions to a role."""
        permissions = (
            {permission}
            if isinstance(permission, Permission)
            else permission
        )

        self._authorizer.grant(
            role,
            permissions,
        )

    def revoke(
        self,
        role: Role,
        permission: Permission | Iterable[Permission],
    ) -> None:
        """Revoke one or more permissions from a role."""
        permissions = (
            {permission}
            if isinstance(permission, Permission)
            else permission
        )

        self._authorizer.revoke(
            role,
            permissions,
        )

    def clear(self) -> None:
        """Clear all security state."""
        with self._lock:
            self._generation += 1
            self._identities.clear()
            self._identity_ids_by_username.clear()
            self._usernames_by_identity_id.clear()
            self._authenticator.clear()
            self._authorizer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._identities)