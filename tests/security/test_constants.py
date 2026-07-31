from sentinel.security.constants import (
    DEFAULT_SECURITY_VERSION,
    AuthenticationStatus,
    AuthorizationStatus,
    Permission,
    Role,
)


def test_version():
    assert DEFAULT_SECURITY_VERSION == "1.0.0"


def test_roles():
    assert Role.ADMIN.value == "admin"
    assert Role.SYSTEM.value == "system"
    assert Role.USER.value == "user"
    assert Role.GUEST.value == "guest"


def test_permissions():
    assert Permission.READ.value == "read"
    assert Permission.WRITE.value == "write"
    assert Permission.EXECUTE.value == "execute"
    assert Permission.DELETE.value == "delete"
    assert Permission.CONFIGURE.value == "configure"


def test_authentication_status():
    assert AuthenticationStatus.AUTHENTICATED.value == "authenticated"
    assert AuthenticationStatus.UNAUTHENTICATED.value == "unauthenticated"
    assert AuthenticationStatus.FAILED.value == "failed"


def test_authorization_status():
    assert AuthorizationStatus.ALLOWED.value == "allowed"
    assert AuthorizationStatus.DENIED.value == "denied"