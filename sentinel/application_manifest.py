"""
Application metadata and dependency manifest for Sentinel OS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class ApplicationManifest:
    """
    Static metadata describing a Sentinel application.

    The manifest contains identity, version, dependencies, permissions,
    and arbitrary application metadata. It does not own application
    lifecycle.
    """

    name: str
    version: str = "0.1.0"
    dependencies: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")

        name = self.name.strip()

        if not name:
            raise ValueError("name must not be empty.")

        if not isinstance(self.version, str):
            raise TypeError("version must be a string.")

        version = self.version.strip()

        if not version:
            raise ValueError("version must not be empty.")

        if not isinstance(self.dependencies, tuple):
            raise TypeError("dependencies must be a tuple.")

        if not isinstance(self.permissions, tuple):
            raise TypeError("permissions must be a tuple.")

        normalized_dependencies: list[str] = []

        for dependency in self.dependencies:
            if not isinstance(dependency, str):
                raise TypeError(
                    "dependency names must be strings."
                )

            dependency = dependency.strip()

            if not dependency:
                raise ValueError(
                    "dependency names must not be empty."
                )

            if dependency == name:
                raise ValueError(
                    f"Application '{name}' cannot depend on itself."
                )

            if dependency not in normalized_dependencies:
                normalized_dependencies.append(dependency)

        normalized_permissions: list[str] = []

        for permission in self.permissions:
            if not isinstance(permission, str):
                raise TypeError(
                    "permission names must be strings."
                )

            permission = permission.strip()

            if not permission:
                raise ValueError(
                    "permission names must not be empty."
                )

            if permission not in normalized_permissions:
                normalized_permissions.append(permission)

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        normalized_metadata = dict(self.metadata)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "version", version)
        object.__setattr__(
            self,
            "dependencies",
            tuple(normalized_dependencies),
        )
        object.__setattr__(
            self,
            "permissions",
            tuple(normalized_permissions),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(normalized_metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return an isolated manifest representation."""
        return {
            "name": self.name,
            "version": self.version,
            "dependencies": tuple(self.dependencies),
            "permissions": tuple(self.permissions),
            "metadata": dict(self.metadata),
        }

    def __repr__(self) -> str:
        """Return a useful manifest representation."""
        return (
            "ApplicationManifest("
            f"name={self.name!r}, "
            f"version={self.version!r}, "
            f"dependencies={self.dependencies!r})"
        )