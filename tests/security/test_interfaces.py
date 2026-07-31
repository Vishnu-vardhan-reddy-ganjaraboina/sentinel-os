import pytest

from sentinel.security.constants import Permission, Role
from sentinel.security.interfaces import (
    Authenticator,
    Authorizer,
    Credentials,
    Identity,
    PermissionStore,
)


class DummyIdentity(Identity):

    def __init__(self):
        self._roles = set()

    @property
    def id(self):
        return "user-1"

    @property
    def name(self):
        return "Sentinel"

    @property
    def roles(self):
        return self._roles

    def add_role(self, role):
        self._roles.add(role)

    def remove_role(self, role):
        self._roles.discard(role)


class DummyCredentials(Credentials):

    @property
    def username(self):
        return "admin"

    @property
    def secret(self):
        return "password"


class DummyAuthenticator(Authenticator):

    def authenticate(self, credentials):
        return credentials.username == "admin"


class DummyAuthorizer(Authorizer):

    def authorize(self, identity, permission):
        return permission == Permission.READ


class DummyPermissionStore(PermissionStore):

    def __init__(self):
        self._permissions = {}

    def grant(self, role, permissions):
        if role not in self._permissions:
            self._permissions[role] = set()

        self._permissions[role].update(permissions)

    def revoke(self, role, permissions):
        if role in self._permissions:
            self._permissions[role].difference_update(permissions)

    def permissions_for(self, role):
        return self._permissions.get(role, set())

    def has_permission(self, role, permission):
        return permission in self._permissions.get(role, set())


def test_identity():
    identity = DummyIdentity()

    identity.add_role(Role.ADMIN)

    assert Role.ADMIN in identity.roles

    identity.remove_role(Role.ADMIN)

    assert Role.ADMIN not in identity.roles


def test_credentials():
    credentials = DummyCredentials()

    assert credentials.username == "admin"
    assert credentials.secret == "password"


def test_authenticator():
    auth = DummyAuthenticator()

    assert auth.authenticate(DummyCredentials()) is True


def test_authorizer():
    authorizer = DummyAuthorizer()

    assert authorizer.authorize(
        DummyIdentity(),
        Permission.READ,
    )

    assert not authorizer.authorize(
        DummyIdentity(),
        Permission.DELETE,
    )


def test_permission_store():
    store = DummyPermissionStore()

    store.grant(
        Role.ADMIN,
        [Permission.READ, Permission.WRITE],
    )

    permissions = store.permissions_for(Role.ADMIN)

    assert Permission.READ in permissions
    assert Permission.WRITE in permissions

    assert store.has_permission(
        Role.ADMIN,
        Permission.READ,
    )

    store.revoke(
        Role.ADMIN,
        [Permission.WRITE],
    )

    assert not store.has_permission(
        Role.ADMIN,
        Permission.WRITE,
    )


def test_identity_is_abstract():
    with pytest.raises(TypeError):
        Identity()


def test_credentials_is_abstract():
    with pytest.raises(TypeError):
        Credentials()


def test_authenticator_is_abstract():
    with pytest.raises(TypeError):
        Authenticator()


def test_authorizer_is_abstract():
    with pytest.raises(TypeError):
        Authorizer()


def test_permission_store_is_abstract():
    with pytest.raises(TypeError):
        PermissionStore()