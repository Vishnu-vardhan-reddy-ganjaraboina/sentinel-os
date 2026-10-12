from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


def test_register_identity():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    assert len(manager) == 1
    assert manager.get_identity("1") == identity


def test_authenticate():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    assert manager.authenticate(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )


def test_authorize():
    manager = SecurityManager()

    manager.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    assert manager.authorize(
        identity,
        Permission.READ,
    )

    assert manager.authorize(
        identity,
        Permission.WRITE,
    )


def test_unregister_identity():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    manager.unregister_identity(
        "1",
        "admin",
    )

    assert manager.get_identity("1") is None
    assert len(manager) == 0


def test_clear():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    manager.register_identity(
        identity,
        credentials,
    )

    manager.clear()

    assert len(manager) == 0
def test_reassign_username_removes_previous_identity_and_credentials():
    manager = SecurityManager()

    old_identity = SecurityIdentity("ID-1", "Old Admin", {Role.ADMIN})
    new_identity = SecurityIdentity("ID-2", "New Admin", {Role.ADMIN})

    manager.register_identity(
        old_identity,
        SecurityCredentials("alice", "old-secret"),
    )
    manager.register_identity(
        new_identity,
        SecurityCredentials("alice", "new-secret"),
    )

    assert manager.get_identity("ID-1") is None
    assert manager.get_identity("ID-2") == new_identity
    assert manager.authenticate_identity(
        SecurityCredentials("alice", "old-secret")
    ) is None
    assert manager.authenticate_identity(
        SecurityCredentials("alice", "new-secret")
    ) == new_identity


def test_reregister_identity_with_new_username_invalidates_old_credentials():
    manager = SecurityManager()

    identity = SecurityIdentity("ID-1", "Admin", {Role.ADMIN})

    manager.register_identity(
        identity,
        SecurityCredentials("alice", "alice-secret"),
    )
    manager.register_identity(
        identity,
        SecurityCredentials("bob", "bob-secret"),
    )

    assert manager.authenticate_identity(
        SecurityCredentials("alice", "alice-secret")
    ) is None
    assert manager.authenticate_identity(
        SecurityCredentials("bob", "bob-secret")
    ) == identity


def test_unregister_identity_rejects_mismatched_username():
    manager = SecurityManager()

    alice = SecurityIdentity("ID-1", "Alice", {Role.ADMIN})
    bob = SecurityIdentity("ID-2", "Bob", {Role.USER})

    manager.register_identity(
        alice,
        SecurityCredentials("alice", "alice-secret"),
    )
    manager.register_identity(
        bob,
        SecurityCredentials("bob", "bob-secret"),
    )

    manager.unregister_identity("ID-1", "bob")

    assert manager.get_identity("ID-1") == alice
    assert manager.get_identity("ID-2") == bob
    assert manager.authenticate_identity(
        SecurityCredentials("alice", "alice-secret")
    ) == alice
    assert manager.authenticate_identity(
        SecurityCredentials("bob", "bob-secret")
    ) == bob
