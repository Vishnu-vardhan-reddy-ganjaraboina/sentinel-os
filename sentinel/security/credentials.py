"""
Credentials implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

from sentinel.security.interfaces import Credentials


class SecurityCredentials(Credentials):
    """
    Represents authentication credentials.
    """

    def __init__(
        self,
        username: str,
        secret: str,
    ) -> None:
        if not username.strip():
            raise ValueError("username cannot be empty.")

        if not secret.strip():
            raise ValueError("secret cannot be empty.")

        self._username = username
        self._secret = secret

    @property
    def username(self) -> str:
        return self._username

    @property
    def secret(self) -> str:
        return self._secret

    def verify(
        self,
        secret: str,
    ) -> bool:
        """
        Verify the supplied secret.
        """
        return self._secret == secret

    def to_dict(self) -> dict[str, str]:
        """
        Serialize credentials without exposing the secret.
        """
        return {
            "username": self.username,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecurityCredentials):
            return NotImplemented

        return (
            self.username == other.username
            and self.secret == other.secret
        )

    def __hash__(self) -> int:
        return hash((self.username, self.secret))

    def __repr__(self) -> str:
        return (
            f"SecurityCredentials("
            f"username={self.username!r})"
        )