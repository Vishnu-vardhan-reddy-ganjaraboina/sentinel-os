import pytest

from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.security_authorizer import (
    SecurityControlAuthorizer,
)
from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.service import SecurityService


def create_security_service() -> SecurityService:
    return SecurityService()


def create_identity(
    identity_id: str = "user-1",
    name: str = "Test User",
    roles: set[Role] | None = None,
) -> SecurityIdentity:
    return SecurityIdentity(
        identity_id=identity_id,
        name=name,
        roles=roles or {Role.USER},
    )


def create_credentials(
    username: str = "test-user",
    secret: str = "test-secret",
) -> SecurityCredentials:
    return SecurityCredentials(
        username=username,
        secret=secret,
    )


def create_context(
    caller_id: str = "user-1",
) -> ControlContext:
    return ControlContext(
        caller_id=caller_id,
        caller_type="api",
    )


def test_read_maps_to_security_read_permission() -> None:
    assert (
        SecurityControlAuthorizer.map_permission(
            ControlPermission.READ
        )
        == Permission.READ
    )


def test_control_maps_to_security_execute_permission() -> None:
    assert (
        SecurityControlAuthorizer.map_permission(
            ControlPermission.CONTROL
        )
        == Permission.EXECUTE
    )


def test_unknown_control_permission_is_rejected() -> None:
    with pytest.raises(ValueError):
        SecurityControlAuthorizer.map_permission(
            "invalid"  # type: ignore[arg-type]
        )


def test_identity_with_read_permission_is_allowed() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    security.grant(
        Role.USER,
        {Permission.READ},
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    assert authorizer.is_allowed(
        context,
        ControlPermission.READ,
    ) is True


def test_identity_without_read_permission_is_denied() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    assert authorizer.is_allowed(
        context,
        ControlPermission.READ,
    ) is False


def test_control_permission_uses_execute_permission() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    security.grant(
        Role.USER,
        {Permission.EXECUTE},
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    assert authorizer.is_allowed(
        context,
        ControlPermission.CONTROL,
    ) is True


def test_control_permission_is_denied_without_execute_permission() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    security.grant(
        Role.USER,
        {Permission.READ},
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    assert authorizer.is_allowed(
        context,
        ControlPermission.CONTROL,
    ) is False


def test_unknown_identity_is_denied() -> None:
    security = create_security_service()

    authorizer = SecurityControlAuthorizer(security)

    context = create_context(
        caller_id="does-not-exist",
    )

    assert authorizer.is_allowed(
        context,
        ControlPermission.READ,
    ) is False


def test_caller_id_resolves_security_identity() -> None:
    security = create_security_service()

    identity = create_identity(
        identity_id="caller-123",
    )

    security.register_identity(
        identity,
        create_credentials(),
    )

    security.grant(
        Role.USER,
        {Permission.READ},
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context(
        caller_id="caller-123",
    )

    assert authorizer.is_allowed(
        context,
        ControlPermission.READ,
    ) is True


def test_require_succeeds_for_authorized_identity() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    security.grant(
        Role.USER,
        {Permission.READ},
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    authorizer.require(
        context,
        ControlPermission.READ,
    )


def test_require_raises_for_unauthorized_identity() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    with pytest.raises(
        PermissionError,
        match="Permission denied",
    ):
        authorizer.require(
            context,
            ControlPermission.READ,
        )


def test_security_service_is_the_authorization_source() -> None:
    security = create_security_service()

    identity = create_identity()

    security.register_identity(
        identity,
        create_credentials(),
    )

    authorizer = SecurityControlAuthorizer(security)

    context = create_context()

    assert authorizer.security is security

    security.grant(
        Role.USER,
        {Permission.READ},
    )

    assert authorizer.is_allowed(
        context,
        ControlPermission.READ,
    ) is True

    security.revoke(
        Role.USER,
        {Permission.READ},
    )

    assert authorizer.is_allowed(
        context,
        ControlPermission.READ,
    ) is False