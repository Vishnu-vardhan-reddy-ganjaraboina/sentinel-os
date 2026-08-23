from sentinel.security.authenticator import SecurityAuthenticator
from sentinel.security.credentials import SecurityCredentials


def test_register():
    authenticator = SecurityAuthenticator()

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    authenticator.register(credentials)

    assert authenticator.exists("admin")
    assert len(authenticator) == 1


def test_authenticate_success():
    authenticator = SecurityAuthenticator()

    credentials = SecurityCredentials(
        "admin",
        "password123",
    )

    authenticator.register(credentials)

    assert authenticator.authenticate(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )


def test_authenticate_wrong_password():
    authenticator = SecurityAuthenticator()

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    assert not authenticator.authenticate(
        SecurityCredentials(
            "admin",
            "wrong-password",
        )
    )


def test_authenticate_unknown_user():
    authenticator = SecurityAuthenticator()

    assert not authenticator.authenticate(
        SecurityCredentials(
            "unknown",
            "password",
        )
    )


def test_unregister():
    authenticator = SecurityAuthenticator()

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    authenticator.unregister("admin")

    assert not authenticator.exists("admin")


def test_clear():
    authenticator = SecurityAuthenticator()

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    authenticator.register(
        SecurityCredentials(
            "user",
            "password456",
        )
    )

    authenticator.clear()

    assert len(authenticator) == 0

def test_concurrent_registration_is_safe() -> None:
    from concurrent.futures import ThreadPoolExecutor

    authenticator = SecurityAuthenticator()

    def register(index: int) -> None:
        authenticator.register(
            SecurityCredentials(
                f"user-{index}",
                f"password-{index}",
            )
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                register,
                range(100),
            )
        )

    assert len(authenticator) == 100

def test_registered_credentials_do_not_store_plaintext_secret() -> None:
    authenticator = SecurityAuthenticator()

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    stored = authenticator._credentials["admin"]

    assert b"password123" not in stored.digest
    assert stored.salt != b"password123"

def test_registration_uses_unique_salts() -> None:
    authenticator = SecurityAuthenticator()

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    first = authenticator._credentials["admin"]

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    second = authenticator._credentials["admin"]

    assert first.salt != second.salt
    assert first.digest != second.digest

def test_hashed_credentials_still_authenticate() -> None:
    authenticator = SecurityAuthenticator()

    authenticator.register(
        SecurityCredentials(
            "admin",
            "password123",
        )
    )

    assert authenticator.authenticate(
        SecurityCredentials(
            "admin",
            "password123",
        )
    ) is True

    assert authenticator.authenticate(
        SecurityCredentials(
            "admin",
            "wrong-password",
        )
    ) is False