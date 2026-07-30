"""
Authenticator implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

from sentinel.security.credentials import SecurityCredentials
from sentinel.security.interfaces import Authenticator


class SecurityAuthenticator(Authenticator):
    """
    Default authenticator implementation.
    """

    def __init__(self) -> None:
        self._credentials: dict[str, SecurityCredentials] = {}

    def register(
        self,
        credentials: SecurityCredentials,
    ) -> None:
        """
        Register credentials.
        """
        self._credentials[credentials.username] = credentials

    def unregister(
        self,
        username: str,
    ) -> None:
        """
        Remove credentials.
        """
        self._credentials.pop(username, None)

    def authenticate(
        self,
        credentials: SecurityCredentials,
    ) -> bool:
        """
        Authenticate supplied credentials.
        """
        stored = self._credentials.get(credentials.username)

        if stored is None:
            return False

        return stored.verify(credentials.secret)

    def exists(
        self,
        username: str,
    ) -> bool:
        """
        Check whether credentials exist.
        """
        return username in self._credentials

    def clear(self) -> None:
        """
        Remove all registered credentials.
        """
        self._credentials.clear()

    def __contains__(
        self,
        username: str,
    ) -> bool:
        return username in self._credentials

    def __len__(self) -> int:
        return len(self._credentials)