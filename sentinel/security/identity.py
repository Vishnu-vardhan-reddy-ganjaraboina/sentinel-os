"""
Identity implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

from sentinel.security.constants import Role
from sentinel.security.interfaces import Identity


class SecurityIdentity(Identity):
    """
    Represents a security identity.
    """

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
        self._roles: set[Role] = set(roles or [])

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def roles(self) -> set[Role]:
        return set(self._roles)

    def add_role(
        self,
        role: Role,
    ) -> None:
        self._roles.add(role)

    def remove_role(
        self,
        role: Role,
    ) -> None:
        self._roles.discard(role)

    def has_role(
        self,
        role: Role,
    ) -> bool:
        return role in self._roles

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "roles": sorted(role.value for role in self._roles),
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecurityIdentity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"SecurityIdentity("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"roles={[r.value for r in self._roles]!r})"
        )