from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from sentinel.security.authenticator import SecurityAuthenticator
from sentinel.security.authorizer import SecurityAuthorizer
from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity


class SecurityManager:
    """High-level manager for security operations."""

    def __init__(self) -> None:
        self._authenticator = SecurityAuthenticator()
        self._authorizer = SecurityAuthorizer()
        self._identities: dict[str, SecurityIdentity] = {}
        self._identity_ids_by_username: dict[str, str] = {}
        self._lock = RLock()
        self._generation = 0

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
        """Register an identity and its credentials atomically."""
        with self._lock:
            generation = self._generation

        # Password hashing is expensive, so don't hold the manager lock.
        record = self._authenticator._prepare(credentials)

        with self._lock:
            if generation != self._generation:
                raise RuntimeError(
                    "Security state changed during identity registration."
                )

            # Snapshot identity mappings and only the credential records
            # that this registration may modify.
            previous_identities = self._identities.copy()
            previous_username_map = self._identity_ids_by_username.copy()
            affected_usernames = {
                credentials.username,
                *(
                    username
                    for username, registered_id
                    in self._identity_ids_by_username.items()
                    if registered_id == identity.id
                ),
            }
            previous_credentials = {
                username: self._authenticator._snapshot(username)
                for username in affected_usernames
            }

            try:
                previous_id = self._identity_ids_by_username.get(
                    credentials.username
                )

                if previous_id is not None and previous_id != identity.id:
                    self._identities.pop(previous_id, None)

                # Re-registering an identity with a new username invalidates
                # the old username and its credentials.
                for username, registered_id in list(
                    self._identity_ids_by_username.items()
                ):
                    if registered_id == identity.id:
                        self._identity_ids_by_username.pop(username, None)
                        self._authenticator.unregister(username)

                self._identities[identity.id] = identity
                self._identity_ids_by_username[credentials.username] = identity.id

                self._authenticator._commit(
                    credentials.username,
                    record,
                )
            except Exception:
                self._identities = previous_identities
                self._identity_ids_by_username = previous_username_map
                for username, record in previous_credentials.items():
                    self._authenticator._restore(username, record)
                raise

    def unregister_identity(
        self,
        identity_id: str,
        username: str,
    ) -> None:
        """Remove an identity only when the username belongs to it."""
        with self._lock:
            registered_id = self._identity_ids_by_username.get(username)
            if registered_id != identity_id:
                return

            self._identity_ids_by_username.pop(username, None)
            self._authenticator.unregister(username)
            self._identities.pop(identity_id, None)

    def get_identity(
        self,
        identity_id: str,
    ) -> SecurityIdentity | None:
        """Retrieve an identity."""
        with self._lock:
            return self._identities.get(identity_id)

    def authenticate(
        self,
        credentials: SecurityCredentials,
    ) -> bool:
        """Authenticate credentials."""
        return self._authenticator.authenticate(credentials)

    def authenticate_identity(
        self,
        credentials: SecurityCredentials,
    ) -> SecurityIdentity | None:
        """Authenticate credentials and return their registered identity."""
        with self._lock:
            if not self._authenticator.authenticate(credentials):
                return None

            identity_id = self._identity_ids_by_username.get(
                credentials.username
            )
            if identity_id is None:
                return None

            return self._identities.get(identity_id)

    def authorize(
        self,
        identity: SecurityIdentity,
        permission: Permission,
    ) -> bool:
        """Authorize an identity."""
        return self._authorizer.authorize(identity, permission)

    def grant(
        self,
        role: Role,
        permissions: Permission | Iterable[Permission],
    ) -> None:
        """Grant one or more permissions to a role."""
        permission_set = (
            {permissions}
            if isinstance(permissions, Permission)
            else permissions
        )
        self._authorizer.grant(role, permission_set)

    def revoke(
        self,
        role: Role,
        permissions: Permission | Iterable[Permission],
    ) -> None:
        """Revoke one or more permissions from a role."""
        permission_set = (
            {permissions}
            if isinstance(permissions, Permission)
            else permissions
        )
        self._authorizer.revoke(role, permission_set)

    def clear(self) -> None:
        """Clear all registered identities and permissions."""
        with self._lock:
            self._generation += 1
            self._identities.clear()
            self._identity_ids_by_username.clear()
            self._authenticator.clear()
            self._authorizer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._identities)
