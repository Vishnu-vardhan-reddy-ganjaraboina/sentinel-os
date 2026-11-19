from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Thread

import pytest

from sentinel.security.authenticator import SecurityAuthenticator
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

    assert manager.authenticate(credentials) is True


def test_authorize():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    manager.grant(
        Role.ADMIN,
        {Permission.READ},
    )

    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is True
    )


def test_grant_single_permission():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    manager.grant(
        Role.ADMIN,
        Permission.READ,
    )

    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is True
    )

    assert (
        manager.authorize(
            identity,
            Permission.WRITE,
        )
        is False
    )


def test_grant_multiple_permissions():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    manager.grant(
        Role.ADMIN,
        {
            Permission.READ,
            Permission.WRITE,
        },
    )

    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is True
    )

    assert (
        manager.authorize(
            identity,
            Permission.WRITE,
        )
        is True
    )

    assert (
        manager.authorize(
            identity,
            Permission.DELETE,
        )
        is False
    )


def test_revoke_single_permission():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    manager.grant(
        Role.ADMIN,
        Permission.READ,
    )

    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is True
    )

    manager.revoke(
        Role.ADMIN,
        Permission.READ,
    )

    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is False
    )


def test_revoke_multiple_permissions():
    manager = SecurityManager()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    manager.grant(
        Role.ADMIN,
        {
            Permission.READ,
            Permission.WRITE,
        },
    )

    manager.revoke(
        Role.ADMIN,
        {
            Permission.READ,
            Permission.WRITE,
        },
    )

    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is False
    )

    assert (
        manager.authorize(
            identity,
            Permission.WRITE,
        )
        is False
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

    assert len(manager) == 0
    assert manager.get_identity("1") is None
    assert manager.authenticate(credentials) is False


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

    manager.grant(
        Role.ADMIN,
        {Permission.READ},
    )

    manager.clear()

    assert len(manager) == 0
    assert manager.get_identity("1") is None
    assert manager.authenticate(credentials) is False
    assert (
        manager.authorize(
            identity,
            Permission.READ,
        )
        is False
    )


def make_identity(index: int) -> SecurityIdentity:
    return SecurityIdentity(
        f"user-{index}",
        f"User {index}",
        {Role.USER},
    )


def make_credentials(index: int) -> SecurityCredentials:
    return SecurityCredentials(
        f"user-{index}",
        f"password-{index}",
    )


def test_concurrent_registration_is_safe():
    manager = SecurityManager()

    def register(index: int) -> None:
        manager.register_identity(
            make_identity(index),
            make_credentials(index),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                register,
                range(20),
            )
        )

    assert results == [None] * 20
    assert len(manager) == 20

    for index in range(20):
        assert (
            manager.get_identity(
                f"user-{index}",
            )
            is not None
        )


def test_concurrent_registration_preserves_authentication():
    manager = SecurityManager()

    for index in range(10):
        manager.register_identity(
            make_identity(index),
            make_credentials(index),
        )

    def authenticate(index: int) -> bool:
        return manager.authenticate(
            make_credentials(index),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                authenticate,
                range(10),
            )
        )

    assert all(results)


def test_concurrent_identity_lookup_is_safe():
    manager = SecurityManager()

    for index in range(10):
        manager.register_identity(
            make_identity(index),
            make_credentials(index),
        )

    def lookup(index: int) -> SecurityIdentity | None:
        return manager.get_identity(
            f"user-{index}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lookup,
                range(10),
            )
        )

    assert all(identity is not None for identity in results)


def test_concurrent_registration_and_lookup_is_safe():
    manager = SecurityManager()

    registration_count = 10
    operation_count = registration_count * 2
    barrier = Barrier(operation_count)

    def register(index: int) -> tuple[str, int]:
        barrier.wait()

        manager.register_identity(
            make_identity(index),
            make_credentials(index),
        )

        return ("register", index)

    def lookup(
        index: int,
    ) -> tuple[str, int, SecurityIdentity | None]:
        barrier.wait()

        identity = manager.get_identity(
            f"user-{index}",
        )

        return ("lookup", index, identity)

    tasks = []

    with ThreadPoolExecutor(
        max_workers=operation_count,
    ) as executor:
        for index in range(registration_count):
            tasks.append(
                executor.submit(
                    register,
                    index,
                )
            )

        for index in range(registration_count):
            tasks.append(
                executor.submit(
                    lookup,
                    index,
                )
            )

        results = [future.result() for future in tasks]

    registrations = [result for result in results if result[0] == "register"]

    lookups = [result for result in results if result[0] == "lookup"]

    assert len(registrations) == registration_count
    assert len(lookups) == registration_count
    assert len(manager) == registration_count

    for _, index, identity in lookups:
        assert identity is None or identity == make_identity(index)


def test_registration_rolls_back_identity_when_credentials_fail(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = SecurityManager()

    identity = SecurityIdentity(
        "user-1",
        "User One",
        {Role.USER},
    )

    credentials = SecurityCredentials(
        "user-1",
        "secret",
    )

    def fail_prepare(
        _credentials: SecurityCredentials,
    ):
        raise RuntimeError("credential registration failed")

    monkeypatch.setattr(
        manager._authenticator,
        "_prepare",
        fail_prepare,
    )

    with pytest.raises(
        RuntimeError,
        match="credential registration failed",
    ):
        manager.register_identity(
            identity,
            credentials,
        )

    assert manager.get_identity("user-1") is None
    assert len(manager) == 0


def test_registration_failure_restores_previous_identity(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = SecurityManager()

    original_identity = SecurityIdentity(
        "user-1",
        "Original User",
        {Role.USER},
    )

    original_credentials = SecurityCredentials(
        "user-1",
        "original-secret",
    )

    manager.register_identity(
        original_identity,
        original_credentials,
    )

    replacement_identity = SecurityIdentity(
        "user-1",
        "Replacement User",
        {Role.ADMIN},
    )

    replacement_credentials = SecurityCredentials(
        "replacement-user",
        "replacement-secret",
    )

    def fail_prepare(
        _credentials: SecurityCredentials,
    ):
        raise RuntimeError("credential registration failed")

    monkeypatch.setattr(
        manager._authenticator,
        "_prepare",
        fail_prepare,
    )

    with pytest.raises(
        RuntimeError,
        match="credential registration failed",
    ):
        manager.register_identity(
            replacement_identity,
            replacement_credentials,
        )

    assert manager.get_identity("user-1") == original_identity
    assert len(manager) == 1


def test_registration_rejected_after_clear(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = SecurityManager()

    prepared = Event()
    release = Event()

    original_prepare = manager._authenticator._prepare

    def blocked_prepare(
        credentials: SecurityCredentials,
    ):
        record = original_prepare(credentials)
        prepared.set()
        release.wait()
        return record

    monkeypatch.setattr(
        manager._authenticator,
        "_prepare",
        blocked_prepare,
    )

    identity = make_identity(1)
    credentials = make_credentials(1)

    error: list[Exception] = []

    def register() -> None:
        try:
            manager.register_identity(
                identity,
                credentials,
            )
        except Exception as exc:
            error.append(exc)

    thread = Thread(target=register)
    thread.start()

    assert prepared.wait(timeout=10)

    manager.clear()
    release.set()

    thread.join(timeout=10)

    assert not thread.is_alive()
    assert len(error) == 1
    assert isinstance(error[0], RuntimeError)

    assert manager.get_identity(identity.id) is None
    assert manager.authenticate(credentials) is False


def test_concurrent_registration_and_clear_do_not_leave_stale_identity():
    manager = SecurityManager()

    registration_started = Event()
    release_registration = Event()

    original_prepare = manager._authenticator._prepare

    def blocked_prepare(
        credentials: SecurityCredentials,
    ):
        record = original_prepare(credentials)
        registration_started.set()
        release_registration.wait()
        return record

    manager._authenticator._prepare = blocked_prepare

    identity = make_identity(100)
    credentials = make_credentials(100)

    errors: list[Exception] = []

    def register() -> None:
        try:
            manager.register_identity(
                identity,
                credentials,
            )
        except Exception as exc:
            errors.append(exc)

    thread = Thread(target=register)
    thread.start()

    assert registration_started.wait(timeout=10)

    manager.clear()
    release_registration.set()

    thread.join(timeout=10)

    assert not thread.is_alive()
    assert len(errors) == 1

    assert manager.get_identity(identity.id) is None
    assert manager.authenticate(credentials) is False


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
    assert (
        manager.authenticate_identity(SecurityCredentials("alice", "old-secret"))
        is None
    )
    assert (
        manager.authenticate_identity(SecurityCredentials("alice", "new-secret"))
        == new_identity
    )


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

    assert (
        manager.authenticate_identity(SecurityCredentials("alice", "alice-secret"))
        is None
    )
    assert (
        manager.authenticate_identity(SecurityCredentials("bob", "bob-secret"))
        == identity
    )


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
    assert (
        manager.authenticate_identity(SecurityCredentials("alice", "alice-secret"))
        == alice
    )
    assert (
        manager.authenticate_identity(SecurityCredentials("bob", "bob-secret")) == bob
    )


def test_registration_commit_failure_restores_credentials(monkeypatch):
    manager = SecurityManager()
    original_identity = SecurityIdentity(
        "user-1",
        "Original User",
        {Role.USER},
    )
    original_credentials = SecurityCredentials(
        "original-user",
        "original-secret",
    )
    replacement_credentials = SecurityCredentials(
        "replacement-user",
        "replacement-secret",
    )

    manager.register_identity(original_identity, original_credentials)

    original_commit = manager._authenticator._commit

    def commit_then_fail(username, record):
        original_commit(username, record)
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(
        manager._authenticator,
        "_commit",
        commit_then_fail,
    )

    with pytest.raises(RuntimeError, match="simulated commit failure"):
        manager.register_identity(original_identity, replacement_credentials)

    assert manager.get_identity("user-1") == original_identity
    assert manager.authenticate(original_credentials) is True
    assert manager.authenticate(replacement_credentials) is False


def test_authenticate_identity_does_not_hold_manager_lock_during_derivation(
    monkeypatch,
):
    from threading import Event, Thread

    manager = SecurityManager()
    identity = make_identity(1)
    credentials = make_credentials(1)
    manager.register_identity(identity, credentials)

    derivation_started = Event()
    release_derivation = Event()
    lookup_completed = Event()
    results = []

    original_derive = SecurityAuthenticator._derive

    def blocked_derive(secret, salt):
        derivation_started.set()
        if not release_derivation.wait(timeout=20):
            raise TimeoutError("Test did not release password derivation.")
        return original_derive(secret, salt)

    monkeypatch.setattr(
        SecurityAuthenticator,
        "_derive",
        staticmethod(blocked_derive),
    )

    authentication_thread = Thread(
        target=lambda: results.append(manager.authenticate_identity(credentials))
    )
    authentication_thread.start()

    try:
        assert derivation_started.wait(timeout=10)

        def lookup():
            manager.get_identity(identity.id)
            lookup_completed.set()

        lookup_thread = Thread(target=lookup)
        lookup_thread.start()

        try:
            assert lookup_completed.wait(timeout=2), (
                "Identity lookup was blocked during password derivation."
            )
        finally:
            lookup_thread.join(timeout=10)
    finally:
        release_derivation.set()
        authentication_thread.join(timeout=10)

    assert not authentication_thread.is_alive()
    assert results == [identity]


def test_authenticate_identity_rejects_credentials_replaced_during_derivation(
    monkeypatch,
):
    from threading import Event, Thread

    manager = SecurityManager()
    old_identity = SecurityIdentity("ID-OLD", "Old Admin", {Role.ADMIN})
    new_identity = SecurityIdentity("ID-NEW", "New Admin", {Role.ADMIN})
    old_credentials = SecurityCredentials("alice", "old-secret")
    new_credentials = SecurityCredentials("alice", "new-secret")

    manager.register_identity(old_identity, old_credentials)

    derivation_started = Event()
    release_derivation = Event()
    results = []

    original_derive = SecurityAuthenticator._derive

    def blocked_derive(secret, salt):
        if secret == old_credentials.secret:
            derivation_started.set()
            if not release_derivation.wait(timeout=20):
                raise TimeoutError("Test did not release password derivation.")
        return original_derive(secret, salt)

    monkeypatch.setattr(
        SecurityAuthenticator,
        "_derive",
        staticmethod(blocked_derive),
    )

    thread = Thread(
        target=lambda: results.append(manager.authenticate_identity(old_credentials))
    )
    thread.start()

    try:
        assert derivation_started.wait(timeout=10)

        # Reassign the username while the old password is being verified.
        manager.register_identity(new_identity, new_credentials)
    finally:
        release_derivation.set()
        thread.join(timeout=10)

    assert not thread.is_alive()
    assert results == [None]
    assert manager.authenticate_identity(new_credentials) == new_identity


def test_authorize_rejects_unregistered_identity():
    manager = SecurityManager()
    identity = SecurityIdentity("stale-1", "Admin", {Role.ADMIN})
    manager.grant(Role.ADMIN, Permission.EXECUTE)

    assert manager.authorize(identity, Permission.EXECUTE) is False


def test_authorize_rejects_identity_after_unregister():
    manager = SecurityManager()
    identity = SecurityIdentity("stale-2", "Admin", {Role.ADMIN})
    credentials = SecurityCredentials("stale-admin", "password123")

    manager.register_identity(identity, credentials)
    manager.grant(Role.ADMIN, Permission.EXECUTE)

    assert manager.authorize(identity, Permission.EXECUTE) is True

    manager.unregister_identity(identity.id, credentials.username)

    assert manager.get_identity(identity.id) is None
    assert manager.authorize(identity, Permission.EXECUTE) is False


def test_authorize_rejects_replaced_identity_object():
    manager = SecurityManager()
    old_identity = SecurityIdentity("stale-3", "Old Admin", {Role.ADMIN})
    new_identity = SecurityIdentity("stale-3", "New Admin", {Role.ADMIN})

    manager.register_identity(
        old_identity,
        SecurityCredentials("old-admin", "password123"),
    )
    manager.grant(Role.ADMIN, Permission.EXECUTE)

    manager.register_identity(
        new_identity,
        SecurityCredentials("new-admin", "password456"),
    )

    assert manager.authorize(old_identity, Permission.EXECUTE) is False
    assert manager.authorize(new_identity, Permission.EXECUTE) is True

def test_registered_identity_rejects_direct_role_escalation():
    manager = SecurityManager()
    identity = SecurityIdentity(
        "role-protection-1",
        "Normal User",
        {Role.USER},
    )

    manager.grant(Role.ADMIN, Permission.DELETE)

    manager.register_identity(
        identity,
        SecurityCredentials("normal-user", "password123"),
    )

    assert manager.authorize(identity, Permission.DELETE) is False

    with pytest.raises(PermissionError):
        identity.add_role(Role.ADMIN)

    assert identity.roles == {Role.USER}
    assert manager.authorize(identity, Permission.DELETE) is False


def test_registered_identity_rejects_direct_role_removal():
    manager = SecurityManager()
    identity = SecurityIdentity(
        "role-protection-2",
        "Admin",
        {Role.ADMIN},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("protected-admin", "password123"),
    )

    with pytest.raises(PermissionError):
        identity.remove_role(Role.ADMIN)

    assert identity.roles == {Role.ADMIN}


def test_unregistered_identity_can_still_mutate_roles():
    identity = SecurityIdentity(
        "role-protection-3",
        "Standalone User",
        {Role.USER},
    )

    identity.add_role(Role.ADMIN)
    assert identity.has_role(Role.ADMIN)

    identity.remove_role(Role.ADMIN)
    assert identity.has_role(Role.ADMIN) is False

def test_manager_controls_registered_identity_role_changes():
    manager = SecurityManager()
    identity = SecurityIdentity(
        "role-manager-1",
        "Normal User",
        {Role.USER},
    )

    manager.grant(Role.ADMIN, Permission.DELETE)
    manager.register_identity(
        identity,
        SecurityCredentials("role-manager-user", "password123"),
    )

    manager.add_role(identity, Role.ADMIN)
    assert manager.authorize(identity, Permission.DELETE) is True

    manager.remove_role(identity, Role.ADMIN)
    assert manager.authorize(identity, Permission.DELETE) is False


def test_identity_cannot_be_registered_with_two_managers():
    first_manager = SecurityManager()
    second_manager = SecurityManager()

    identity = SecurityIdentity(
        "cross-manager-1",
        "Shared Identity",
        {Role.USER},
    )

    first_manager.register_identity(
        identity,
        SecurityCredentials("first-manager-user", "password123"),
    )

    with pytest.raises(RuntimeError, match="already registered elsewhere"):
        second_manager.register_identity(
            identity,
            SecurityCredentials("second-manager-user", "password123"),
        )

    assert first_manager.get_identity(identity.id) is identity
    assert second_manager.get_identity(identity.id) is None

    with pytest.raises(PermissionError):
        identity.add_role(Role.ADMIN)


def test_unregister_releases_identity_role_protection():
    manager = SecurityManager()
    identity = SecurityIdentity(
        "role-unregister-1",
        "Unregistered User",
        {Role.USER},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("unregister-user", "password123"),
    )

    manager.unregister_identity(identity.id, "unregister-user")

    identity.add_role(Role.ADMIN)
    assert identity.has_role(Role.ADMIN)


def test_clear_releases_all_identity_role_protection():
    manager = SecurityManager()
    identity = SecurityIdentity(
        "role-clear-1",
        "Cleared User",
        {Role.USER},
    )

    manager.register_identity(
        identity,
        SecurityCredentials("clear-user", "password123"),
    )

    manager.clear()

    identity.add_role(Role.ADMIN)
    assert identity.has_role(Role.ADMIN)


def test_replacing_identity_releases_previous_identity_protection():
    manager = SecurityManager()

    old_identity = SecurityIdentity(
        "replacement-user",
        "Old User",
        {Role.USER},
    )
    new_identity = SecurityIdentity(
        "replacement-user",
        "New User",
        {Role.USER},
    )

    manager.register_identity(
        old_identity,
        SecurityCredentials("replacement-account", "old-password"),
    )

    manager.register_identity(
        new_identity,
        SecurityCredentials("replacement-account", "new-password"),
    )

    old_identity.add_role(Role.ADMIN)
    assert old_identity.has_role(Role.ADMIN)

    with pytest.raises(PermissionError):
        new_identity.add_role(Role.ADMIN)

    assert manager.get_identity("replacement-user") is new_identity


def test_failed_registration_releases_new_identity_protection():
    manager = SecurityManager()

    original_identity = SecurityIdentity(
        "rollback-original",
        "Original User",
        {Role.USER},
    )
    new_identity = SecurityIdentity(
        "rollback-new",
        "New User",
        {Role.USER},
    )

    manager.register_identity(
        original_identity,
        SecurityCredentials("rollback-original-user", "password123"),
    )

    original_commit = manager._authenticator._commit

    def commit_then_fail(username, record):
        original_commit(username, record)
        raise RuntimeError("simulated registration failure")

    manager._authenticator._commit = commit_then_fail

    try:
        with pytest.raises(
            RuntimeError,
            match="simulated registration failure",
        ):
            manager.register_identity(
                new_identity,
                SecurityCredentials("rollback-new-user", "password123"),
            )
    finally:
        manager._authenticator._commit = original_commit

    assert manager.get_identity(original_identity.id) is original_identity
    assert manager.get_identity(new_identity.id) is None

    with pytest.raises(PermissionError):
        original_identity.add_role(Role.ADMIN)

    new_identity.add_role(Role.ADMIN)
    assert new_identity.has_role(Role.ADMIN)


def test_manager_does_not_expose_mutable_security_components():
    manager = SecurityManager()

    assert not hasattr(manager, "authenticator")
    assert not hasattr(manager, "authorizer")
