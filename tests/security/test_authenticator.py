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