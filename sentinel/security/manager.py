from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from sentinel.security.authenticator import (
    SecurityAuthenticator,
    _CredentialRecord,
)
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
        self._registration_token = object()

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

        record = self._authenticator._prepare(credentials)

        with self._lock:
            if generation != self._generation:
                raise RuntimeError(
                    "Security state changed during identity registration."
                )

            previous_identities = self._identities.copy()
            previous_username_map = self._identity_ids_by_username.copy()

            affected_usernames = {
                credentials.username,
                *(
                    username
                    for username, registered_id in (
                        self._identity_ids_by_username.items()
                    )
                    if registered_id == identity.id
                ),
            }

            previous_credentials: dict[str, _CredentialRecord | None] = {
                username: self._authenticator._snapshot(username)
                for username in affected_usernames
            }

            was_registered = self._identities.get(identity.id) is identity
            displaced_identities: set[SecurityIdentity] = set()

            previous_id = self._identity_ids_by_username.get(
                credentials.username
            )

            if previous_id is not None and previous_id != identity.id:
                previous_identity = self._identities.get(previous_id)
                if previous_identity is not None:
                    displaced_identities.add(previous_identity)

            previous_same_id = self._identities.get(identity.id)
            if previous_same_id is not None and previous_same_id is not identity:
                displaced_identities.add(previous_same_id)

            identity._protect_registration(self._registration_token)

            try:
                if previous_id is not None and previous_id != identity.id:
                    self._identities.pop(previous_id, None)

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

                for username, previous_record in previous_credentials.items():
                    self._authenticator._restore(username, previous_record)

                if not was_registered:
                    identity._release_registration(self._registration_token)

                raise

            for previous_identity in displaced_identities:
                previous_identity._release_registration(
                    self._registration_token
                )


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

            identity = self._identities.pop(identity_id, None)
            if identity is not None:
                identity._release_registration(self._registration_token)

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
        authenticated, verified_record = self._authenticator._authenticate_record(
            credentials
        )

        if not authenticated or verified_record is None:
            return None

        with self._lock:
            # Reject authentication if the credential record changed
            # while password verification was running.
            if (
                self._authenticator._snapshot(credentials.username)
                is not verified_record
            ):
                return None

            identity_id = self._identity_ids_by_username.get(credentials.username)
            if identity_id is None:
                return None

            return self._identities.get(identity_id)

    def authorize(
        self,
        identity: SecurityIdentity,
        permission: Permission,
    ) -> bool:
        """Authorize only a currently registered identity."""
        with self._lock:
            if self._identities.get(identity.id) is not identity:
                return False

            return self._authorizer.authorize(identity, permission)


    def add_role(
        self,
        identity: SecurityIdentity,
        role: Role,
    ) -> None:
        """Add a role to an identity registered with this manager."""
        with self._lock:
            if self._identities.get(identity.id) is not identity:
                raise PermissionError(
                    "Identity is not registered with this manager."
                )

            identity._add_role(role, self._registration_token)

    def remove_role(
        self,
        identity: SecurityIdentity,
        role: Role,
    ) -> None:
        """Remove a role from an identity registered with this manager."""
        with self._lock:
            if self._identities.get(identity.id) is not identity:
                raise PermissionError(
                    "Identity is not registered with this manager."
                )

            identity._remove_role(role, self._registration_token)

    def grant(
        self,
        role: Role,
        permissions: Permission | Iterable[Permission],
    ) -> None:
        """Grant one or more permissions to a role."""
        permission_set = (
            {permissions} if isinstance(permissions, Permission) else permissions
        )
        self._authorizer.grant(role, permission_set)

    def revoke(
        self,
        role: Role,
        permissions: Permission | Iterable[Permission],
    ) -> None:
        """Revoke one or more permissions from a role."""
        permission_set = (
            {permissions} if isinstance(permissions, Permission) else permissions
        )
        self._authorizer.revoke(role, permission_set)


    def clear(self) -> None:
        """Clear all registered identities and permissions."""
        with self._lock:
            self._generation += 1

            for identity in self._identities.values():
                identity._release_registration(self._registration_token)

            self._identities.clear()
            self._identity_ids_by_username.clear()
            self._authenticator.clear()
            self._authorizer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._identities)
