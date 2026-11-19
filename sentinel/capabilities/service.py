"""
Authorized public service for the Sentinel Capabilities subsystem.

CapabilityManager remains a trusted composition primitive. Callers that
cross the public service boundary must provide a registered identity with
Permission.EXECUTE before any capability is invoked.
"""

from __future__ import annotations

from typing import Any

from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.exceptions import (
    CapabilityExecutionError,
    CapabilityNotFoundError,
)
from sentinel.capabilities.manager import CapabilityManager
from sentinel.security.constants import Permission
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class CapabilityService:
    """Public capability API with identity-aware execution authorization."""

    def __init__(
        self,
        manager: CapabilityManager | None = None,
        *,
        security: SecurityManager | None = None,
        identity: SecurityIdentity | None = None,
    ) -> None:
        self._manager = manager if manager is not None else CapabilityManager()
        self._security = security
        self._identity = identity

    def register(self, capability: BaseCapability) -> None:
        """Register a capability."""
        self._manager.register(capability)

    def unregister(self, capability_id: str) -> None:
        """Unregister a capability."""
        self._manager.unregister(capability_id)

    def execute(self, capability_id: str, **kwargs: Any) -> Any:
        """Authorize and admit a capability before executing it."""
        if self._security is None or self._identity is None:
            raise PermissionError(
                "Capability execution requires an authenticated identity."
            )

        try:
            admitted = self._security.authorize_and_admit(
                self._identity,
                Permission.EXECUTE,
                lambda: self._manager._admit_instance(
                    self._manager.get(capability_id)
                ),
            )
        except CapabilityNotFoundError as exc:
            raise CapabilityExecutionError(
                f"Capability '{capability_id}' is not registered."
            ) from exc

        return self._manager._execute_admitted_instance(admitted, **kwargs)

    def exists(self, capability_id: str) -> bool:
        """Return whether a capability is registered."""
        return self._manager.exists(capability_id)

    def list(self) -> list[BaseCapability]:
        """Return registered capabilities."""
        return self._manager.list()

    def clear(self) -> None:
        """Remove all registered capabilities."""
        self._manager.clear()
