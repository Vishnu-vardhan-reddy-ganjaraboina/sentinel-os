"""
Interfaces for the Sentinel Security subsystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from sentinel.security.constants import Permission, Role


class Identity(ABC):
    """
    Abstract identity.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique identity identifier.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Display name.
        """

    @property
    @abstractmethod
    def roles(self) -> set[Role]:
        """
        Assigned roles.
        """

    @abstractmethod
    def add_role(self, role: Role) -> None:
        """
        Add a role.
        """

    @abstractmethod
    def remove_role(self, role: Role) -> None:
        """
        Remove a role.
        """


class Credentials(ABC):
    """
    Abstract credentials.
    """

    @property
    @abstractmethod
    def username(self) -> str:
        """
        Username.
        """

    @property
    @abstractmethod
    def secret(self) -> str:
        """
        Password or secret.
        """


class Authenticator(ABC):
    """
    Abstract authenticator.
    """

    @abstractmethod
    def authenticate(
        self,
        credentials: Credentials,
    ) -> bool:
        """
        Authenticate credentials.
        """


class Authorizer(ABC):
    """
    Abstract authorizer.
    """

    @abstractmethod
    def authorize(
        self,
        identity: Identity,
        permission: Permission,
    ) -> bool:
        """
        Check permission.
        """


class PermissionStore(ABC):
    """
    Abstract permission store.
    """

    @abstractmethod
    def grant(
        self,
        role: Role,
        permissions: Iterable[Permission],
    ) -> None:
        """
        Grant permissions to a role.
        """

    @abstractmethod
    def permissions_for(
        self,
        role: Role,
    ) -> set[Permission]:
        """
        Return permissions for a role.
        """

    @abstractmethod
    def revoke(
        self,
        role: Role,
        permissions: Iterable[Permission],
) ->     None:
       """
       Revoke permissions from a role.
       """

    @abstractmethod
    def has_permission(
        self,
        role: Role,
        permission: Permission,
) ->    bool:
         """
         Check whether a role has a permission.
         """