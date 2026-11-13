import threading

from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.service import SecurityService


def test_service_does_not_expose_manager():
    service = SecurityService()

    assert not hasattr(service, "manager")

def test_register_identity():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    assert len(service) == 1
    assert service.get_identity("1") == identity


def test_authenticate():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    assert service.authenticate(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )


def test_authorize():
    service = SecurityService()

    service.grant(
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
    service.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    assert service.authorize(
        identity,
        Permission.READ,
    )

    assert service.authorize(
        identity,
        Permission.WRITE,
    )


def test_unregister_identity():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    service.unregister_identity(
        "1",
        "admin",
    )

    assert service.get_identity("1") is None
    assert len(service) == 0


def test_clear():
    service = SecurityService()

    identity = SecurityIdentity(
        "1",
        "Admin",
        {Role.ADMIN},
    )

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    service.register_identity(
        identity,
        credentials,
    )

    service.clear()

    assert len(service) == 0

def test_authenticate_identity_returns_registered_identity():
    service = SecurityService()
    identity = SecurityIdentity("admin-id", "Admin", {Role.ADMIN})
    service.register_identity(
        identity,
        SecurityCredentials("admin", "correct-secret"),
    )

    result = service.authenticate_identity(
        SecurityCredentials("admin", "correct-secret"),
    )

    assert result == identity


def test_authenticate_identity_rejects_invalid_secret():
    service = SecurityService()
    identity = SecurityIdentity("admin-id", "Admin", {Role.ADMIN})
    service.register_identity(
        identity,
        SecurityCredentials("admin", "correct-secret"),
    )

    result = service.authenticate_identity(
        SecurityCredentials("admin", "wrong-secret"),
    )

    assert result is None


def test_authenticate_identity_rejects_unknown_username():
    service = SecurityService()

    result = service.authenticate_identity(
        SecurityCredentials("unknown", "some-secret"),
    )

    assert result is None


def test_authenticate_identity_returns_none_after_unregister():
    service = SecurityService()
    identity = SecurityIdentity("admin-id", "Admin", {Role.ADMIN})
    service.register_identity(
        identity,
        SecurityCredentials("admin", "correct-secret"),
    )

    service.unregister_identity("admin-id", "admin")

    result = service.authenticate_identity(
        SecurityCredentials("admin", "correct-secret"),
    )

    assert result is None


def test_get_identity_returns_registered_identity():
    service = SecurityService()

    identity = SecurityIdentity(
        "user-1",
        "User",
        {Role.USER},
    )

    service.register_identity(
        identity,
        SecurityCredentials(
            "user",
            "password123",
        ),
    )

    assert service.get_identity("user-1") is identity

def test_authentication_failure_is_propagated():
    service = SecurityService()

    identity = SecurityIdentity(
        "user-1",
        "User",
        {Role.USER},
    )

    service.register_identity(
        identity,
        SecurityCredentials(
            "user",
            "password123",
        ),
    )

    assert not service.authenticate(
        SecurityCredentials(
            "user",
            "wrong-password",
        )
    )

def test_authorization_failure_is_propagated():
    service = SecurityService()

    identity = SecurityIdentity(
        "user-1",
        "User",
        {Role.USER},
    )

    service.register_identity(
        identity,
        SecurityCredentials(
            "user",
            "password123",
        ),
    )

    service.grant(
        Role.USER,
        [Permission.READ],
    )

    assert not service.authorize(
        identity,
        Permission.DELETE,
    )

def test_revoke_is_exposed_through_service():
    service = SecurityService()

    identity = SecurityIdentity(
        "admin-1",
        "Admin",
        {Role.ADMIN},
    )

    service.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    service.grant(
        Role.ADMIN,
        [Permission.WRITE],
    )

    assert service.authorize(
        identity,
        Permission.WRITE,
    )

    service.revoke(
        Role.ADMIN,
        [Permission.WRITE],
    )

    assert not service.authorize(
        identity,
        Permission.WRITE,
    )

def test_concurrent_identity_registration_is_safe():
    service = SecurityService()

    count = 10

    barrier = threading.Barrier(count)

    def register(index: int) -> None:
        barrier.wait()

        identity = SecurityIdentity(
            f"user-{index}",
            f"User {index}",
            {Role.USER},
        )

        credentials = SecurityCredentials(
            f"user-{index}",
            "password123",
        )

        service.register_identity(
            identity,
            credentials,
        )

    threads = [
        threading.Thread(
            target=register,
            args=(index,),
        )
        for index in range(count)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(service) == count

    for index in range(count):
        assert service.get_identity(
            f"user-{index}",
        ) is not None

def test_concurrent_authorization_is_safe():
    service = SecurityService()

    identity = SecurityIdentity(
        "admin-1",
        "Admin",
        {Role.ADMIN},
    )

    service.register_identity(
        identity,
        SecurityCredentials("admin", "password123"),
    )

    service.grant(
        Role.ADMIN,
        [
            Permission.READ,
            Permission.WRITE,
        ],
    )

    errors: list[Exception] = []

    def authorize() -> None:
        try:
            for _ in range(500):
                assert service.authorize(
                    identity,
                    Permission.READ,
                )

                assert service.authorize(
                    identity,
                    Permission.WRITE,
                )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(
            target=authorize,
        )
        for _ in range(10)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []

def test_concurrent_permission_updates_are_safe():
    service = SecurityService()

    identity = SecurityIdentity(
        "admin-1",
        "Admin",
        {Role.ADMIN},
    )

    errors: list[Exception] = []

    def update_permissions() -> None:
        try:
            for _ in range(100):
                service.grant(
                    Role.ADMIN,
                    [Permission.READ],
                )

                service.revoke(
                    Role.ADMIN,
                    [Permission.READ],
                )
        except Exception as exc:
            errors.append(exc)

    def authorize() -> None:
        try:
            for _ in range(500):
                service.authorize(
                    identity,
                    Permission.READ,
                )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(
            target=update_permissions,
        ),
        threading.Thread(
            target=authorize,
        ),
        threading.Thread(
            target=authorize,
        ),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []

def test_concurrent_clear_and_registration_are_safe():
    service = SecurityService()

    errors: list[Exception] = []

    def clear_service() -> None:
        try:
            for _ in range(50):
                service.clear()
        except Exception as exc:
            errors.append(exc)

    def register_identities() -> None:
        try:
            for index in range(100):
                identity = SecurityIdentity(
                    f"user-{index}",
                    f"User {index}",
                    {Role.USER},
                )

                service.register_identity(
                    identity,
                    SecurityCredentials(
                        f"user-{index}",
                        "password123",
                    ),
                )
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(
            target=clear_service,
        ),
        threading.Thread(
            target=register_identities,
        ),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert errors == []
