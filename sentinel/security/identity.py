
"""
Identity implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

from threading import RLock

from sentinel.security.constants import Role
from sentinel.security.interfaces import Identity


class SecurityIdentity(Identity):
    """Represents a security identity."""

    def __init__(
        self,
        identity_id: str,
        name: str,
        roles: set[Role] | None = None,
    ) -> None:
        if not identity_id.strip():
            raise ValueError("identity_id cannot be empty.")

        if not name.strip():
            raise ValueError("name cannot be empty.")

        self._id = identity_id
        self._name = name
        initial_roles = set(roles or [])
        if not all(isinstance(role, Role) for role in initial_roles):
            raise TypeError("All roles must be Role values.")

        self._roles: set[Role] = initial_roles
        self._lock = RLock()
        self._registration_token: object | None = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def roles(self) -> set[Role]:
        with self._lock:
            return set(self._roles)

    def _protect_registration(self, token: object) -> None:
        """Protect role mutations for the owning manager."""
        with self._lock:
            if (
                self._registration_token is not None
                and self._registration_token is not token
            ):
                raise RuntimeError(
                    "Identity is already registered elsewhere."
                )

            self._registration_token = token

    def _release_registration(self, token: object) -> None:
        """Release registration protection for the owning manager."""
        with self._lock:
            if self._registration_token is token:
                self._registration_token = None

    def _add_role(
        self,
        role: Role,
        token: object,
    ) -> None:
        """Add a role through the owning manager."""
        if not isinstance(role, Role):
            raise TypeError("role must be a Role value.")
        with self._lock:
            if self._registration_token is not token:
                raise PermissionError("Invalid identity registration token.")
            self._roles.add(role)

    def _remove_role(
        self,
        role: Role,
        token: object,
    ) -> None:
        """Remove a role through the owning manager."""
        if not isinstance(role, Role):
            raise TypeError("role must be a Role value.")
        with self._lock:
            if self._registration_token is not token:
                raise PermissionError("Invalid identity registration token.")
            self._roles.discard(role)

    def add_role(
        self,
        role: Role,
    ) -> None:
        if not isinstance(role, Role):
            raise TypeError("role must be a Role value.")
        with self._lock:
            if self._registration_token is not None:
                raise PermissionError(
                    "Roles of a registered identity must be changed "
                    "through its SecurityManager."
                )
            self._roles.add(role)

    def remove_role(
        self,
        role: Role,
    ) -> None:
        if not isinstance(role, Role):
            raise TypeError("role must be a Role value.")
        with self._lock:
            if self._registration_token is not None:
                raise PermissionError(
                    "Roles of a registered identity must be changed "
                    "through its SecurityManager."
                )
            self._roles.discard(role)

    def has_role(
        self,
        role: Role,
    ) -> bool:
        if not isinstance(role, Role):
            raise TypeError("role must be a Role value.")
        with self._lock:
            return role in self._roles

    def to_dict(self) -> dict[str, object]:
        with self._lock:
            roles = sorted(role.value for role in self._roles)

        return {
            "id": self.id,
            "name": self.name,
            "roles": roles,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecurityIdentity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        with self._lock:
            roles = [role.value for role in self._roles]

        return (
            f"SecurityIdentity("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"roles={roles!r})"
        )
