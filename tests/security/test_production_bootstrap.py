import pytest

from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.production_bootstrap import (
    create_production_security_service,
)


def test_production_bootstrap_registers_admin_with_limited_permissions():
    service = create_production_security_service(
        {
            "SENTINEL_ADMIN_USERNAME": "test-admin",
            "SENTINEL_ADMIN_SECRET": "test-secret-value",
        }
    )

    identity = service.authenticate_identity(
        SecurityCredentials("test-admin", "test-secret-value")
    )

    assert identity is not None
    assert identity.id == "sentinel-production-admin"
    assert identity.has_role(Role.ADMIN)
    assert service.authorize(identity, Permission.READ)
    assert service.authorize(identity, Permission.EXECUTE)
    assert not service.authorize(identity, Permission.WRITE)
    assert not service.authorize(identity, Permission.DELETE)
    assert not service.authorize(identity, Permission.CONFIGURE)


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {"SENTINEL_ADMIN_USERNAME": "test-admin"},
        {"SENTINEL_ADMIN_SECRET": "test-secret-value"},
        {
            "SENTINEL_ADMIN_USERNAME": "   ",
            "SENTINEL_ADMIN_SECRET": "test-secret-value",
        },
        {
            "SENTINEL_ADMIN_USERNAME": "test-admin",
            "SENTINEL_ADMIN_SECRET": "   ",
        },
    ],
)
def test_production_bootstrap_rejects_missing_or_blank_credentials(environment):
    with pytest.raises(RuntimeError):
        create_production_security_service(environment)
