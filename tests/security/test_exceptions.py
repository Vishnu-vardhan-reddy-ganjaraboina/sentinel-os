import pytest

from sentinel.security.exceptions import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    IdentityError,
    CredentialError,
    PermissionError,
)


def test_security_error():
    with pytest.raises(SecurityError):
        raise SecurityError("security")


def test_authentication_error():
    with pytest.raises(AuthenticationError):
        raise AuthenticationError("authentication")


def test_authorization_error():
    with pytest.raises(AuthorizationError):
        raise AuthorizationError("authorization")


def test_identity_error():
    with pytest.raises(IdentityError):
        raise IdentityError("identity")


def test_credential_error():
    with pytest.raises(CredentialError):
        raise CredentialError("credential")


def test_permission_error():
    with pytest.raises(PermissionError):
        raise PermissionError("permission")


def test_inheritance():
    assert issubclass(AuthenticationError, SecurityError)
    assert issubclass(AuthorizationError, SecurityError)
    assert issubclass(IdentityError, SecurityError)
    assert issubclass(CredentialError, SecurityError)
    assert issubclass(PermissionError, SecurityError)