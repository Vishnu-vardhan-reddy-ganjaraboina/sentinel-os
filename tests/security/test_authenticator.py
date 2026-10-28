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

    assert (
        authenticator.authenticate(
            SecurityCredentials(
                "admin",
                "password123",
            )
        )
        is True
    )

    assert (
        authenticator.authenticate(
            SecurityCredentials(
                "admin",
                "wrong-password",
            )
        )
        is False
    )


def test_unknown_user_performs_dummy_password_derivation(monkeypatch):
    calls = []
    original_derive = SecurityAuthenticator._derive

    def tracking_derive(secret, salt):
        calls.append((secret, salt))
        return original_derive(secret, salt)

    monkeypatch.setattr(
        SecurityAuthenticator,
        "_derive",
        staticmethod(tracking_derive),
    )

    authenticator = SecurityAuthenticator()

    assert (
        authenticator.authenticate(SecurityCredentials("unknown", "some-password"))
        is False
    )

    assert len(calls) == 1


def test_unknown_user_dummy_derivation_does_not_register_user(monkeypatch):
    authenticator = SecurityAuthenticator()

    monkeypatch.setattr(
        authenticator,
        "_derive",
        lambda secret, salt: b"x" * 32,
    )

    assert (
        authenticator.authenticate(SecurityCredentials("unknown", "some-password"))
        is False
    )

    assert authenticator.exists("unknown") is False
    assert len(authenticator) == 0


def test_authentication_derivation_runs_outside_credential_lock(
    monkeypatch,
):
    from threading import Event, Thread

    authenticator = SecurityAuthenticator()
    authenticator.register(SecurityCredentials("admin", "password123"))

    derivation_started = Event()
    release_derivation = Event()
    original_derive = SecurityAuthenticator._derive

    def blocked_derive(secret, salt):
        derivation_started.set()
        assert release_derivation.wait(timeout=10)
        return original_derive(secret, salt)

    monkeypatch.setattr(
        SecurityAuthenticator,
        "_derive",
        staticmethod(blocked_derive),
    )

    result = []

    thread = Thread(
        target=lambda: result.append(
            authenticator.authenticate(SecurityCredentials("admin", "password123"))
        )
    )
    thread.start()

    try:
        assert derivation_started.wait(timeout=10)

        # This operation must not wait for the PBKDF2 derivation.
        assert authenticator.exists("admin") is True
    finally:
        release_derivation.set()
        thread.join(timeout=10)

    assert not thread.is_alive()
    assert result == [True]
