"""
Authenticator implementation for the Sentinel Security subsystem.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from threading import RLock

from sentinel.security.credentials import SecurityCredentials
from sentinel.security.interfaces import Authenticator, Credentials

_PBKDF2_ITERATIONS = 600_000
_SALT_SIZE = 16
_DIGEST_SIZE = 32


@dataclass(frozen=True, slots=True)
class _CredentialRecord:
    """
    Internal stored credential verifier.

    The plaintext secret is never stored here.
    """

    salt: bytes
    digest: bytes


class SecurityAuthenticator(Authenticator):
    """
    Default authenticator implementation.

    Registered credentials are stored as salted PBKDF2 verifiers.
    Plaintext secrets are never retained by the authenticator.
    """

    def __init__(self) -> None:
        self._credentials: dict[str, _CredentialRecord] = {}
        self._lock = RLock()

    @staticmethod
    def _derive(
        secret: str,
        salt: bytes,
    ) -> bytes:
        """
        Derive a password verifier from a secret.
        """
        return hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode("utf-8"),
            salt,
            _PBKDF2_ITERATIONS,
            dklen=_DIGEST_SIZE,
        )

    @classmethod
    def _create_record(
        cls,
        secret: str,
    ) -> _CredentialRecord:
        """
        Create a salted credential verifier.
        """
        salt = os.urandom(_SALT_SIZE)

        return _CredentialRecord(
            salt=salt,
            digest=cls._derive(
                secret,
                salt,
            ),
        )

    def register(
        self,
        credentials: SecurityCredentials,
    ) -> None:
        """
        Register credentials.

        Existing usernames are replaced, preserving the previous
        registration semantics.
        """
        record = self._create_record(
            credentials.secret,
        )

        with self._lock:
            self._credentials[
                credentials.username
            ] = record

    def unregister(
        self,
        username: str,
    ) -> None:
        """
        Remove credentials.
        """
        with self._lock:
            self._credentials.pop(
                username,
                None,
            )

    def authenticate(
        self,
        credentials: Credentials,
    ) -> bool:
        """
        Authenticate supplied credentials.
        """
        with self._lock:
            stored = self._credentials.get(
                credentials.username
            )

        if stored is None:
            return False

        candidate = self._derive(
            credentials.secret,
            stored.salt,
        )

        return hmac.compare_digest(
            stored.digest,
            candidate,
        )

    def exists(
        self,
        username: str,
    ) -> bool:
        """
        Check whether credentials exist.
        """
        with self._lock:
            return username in self._credentials

    def clear(self) -> None:
        """
        Remove all registered credentials.
        """
        with self._lock:
            self._credentials.clear()

    def __contains__(
        self,
        username: str,
    ) -> bool:
        with self._lock:
            return username in self._credentials

    def __len__(self) -> int:
        with self._lock:
            return len(self._credentials)