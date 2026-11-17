"""Environment-based bootstrap for production authentication."""

from __future__ import annotations

import os
from collections.abc import Mapping

from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.service import SecurityService


def create_production_security_service(
    environ: Mapping[str, str] | None = None,
) -> SecurityService:
    """Create a fail-closed SecurityService using environment credentials."""
    source = os.environ if environ is None else environ

    username = source.get("SENTINEL_ADMIN_USERNAME", "")
    secret = source.get("SENTINEL_ADMIN_SECRET", "")

    if not isinstance(username, str) or not username.strip():
        raise RuntimeError(
            "Production authentication requires SENTINEL_ADMIN_USERNAME."
        )

    if not isinstance(secret, str) or not secret.strip():
        raise RuntimeError(
            "Production authentication requires SENTINEL_ADMIN_SECRET."
        )

    service = SecurityService()
    service.grant(Role.ADMIN, {Permission.READ, Permission.EXECUTE})
    service.register_identity(
        SecurityIdentity(
            identity_id="sentinel-production-admin",
            name=username,
            roles={Role.ADMIN},
        ),
        SecurityCredentials(username=username, secret=secret),
    )
    return service
