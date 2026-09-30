"""
Security manager coordinating identity, authentication, and authorization.
"""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from .authenticator import SecurityAuthenticator
from .authorizer import SecurityAuthorizer
from .credentials import SecurityCredentials
from .identity import SecurityIdentity
from .permissions import Permission, Role


class SecurityManager:
    """Coordinate security identity, authentication, and authorization."""

    def __init__(self) -> None:
        self._authenticator = SecurityAuthenticator()
        self._authorizer = SecurityAuthorizer()
        self._identities: dict[str, SecurityIdentity] = {}
        self._lock = RLock()
        self._generation = 0

    def register_identity(
        self,
        identity: SecurityIdentity,
        credentials: SecurityCredentials,
    ) -> None:
        """
        Register an identity and its credentials atomically.
        """
        with self._lock:
            generation = self._generation
            previous_identity = self._identities.get(identity.id)

        record = self._authenticator._prepare(credentials)

        with self._lock:
            if generation != self._generation:
                raise RuntimeError(
                    "security state changed during identity registration."
                )

            self._identities[identity.id] = identity

            try:
                self._authenticator._commit(
                    credentials.username,
                    record,
                )
            except Exception:
                if previous_identity is None:
                    self._identities.pop(
                        identity.id,
                        None,
                    )
                else:
                    self._identities[identity.id] = previous_identity

                raise

    def unregister_identity(
        self,
        identity_id: str,
        username: str,
    ) -> None:
        """Remove an identity and its credentials."""
        with self._lock:
            self._identities.pop(
                identity_id,
                None,
            )
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
            self._authenticator.clear()
            self._authorizer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._identities)