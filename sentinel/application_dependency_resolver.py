"""
Application dependency resolution for Sentinel OS.
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.application_manifest import ApplicationManifest


class ApplicationDependencyError(RuntimeError):
    """Base error for application dependency resolution."""


class ApplicationDependencyMissingError(
    ApplicationDependencyError,
):
    """Raised when an application dependency is not registered."""


class ApplicationDependencyCycleError(
    ApplicationDependencyError,
):
    """Raised when application dependencies contain a cycle."""


class ApplicationDependencyResolver:
    """
    Resolve application startup order from application manifests.

    Dependencies are resolved so that every dependency appears before
    the application that requires it.
    """

    def resolve(
        self,
        manifests: Iterable[ApplicationManifest],
    ) -> tuple[str, ...]:
        """Return application names in dependency-safe startup order."""
        manifest_map: dict[str, ApplicationManifest] = {}

        for manifest in manifests:
            if not isinstance(manifest, ApplicationManifest):
                raise TypeError(
                    "manifests must contain ApplicationManifest instances."
                )

            if manifest.name in manifest_map:
                raise ValueError(
                    f"Application '{manifest.name}' is duplicated."
                )

            manifest_map[manifest.name] = manifest

        resolved: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return

            if name in visiting:
                raise ApplicationDependencyCycleError(
                    f"Application dependency cycle detected at '{name}'."
                )

            manifest = manifest_map.get(name)

            if manifest is None:
                raise ApplicationDependencyMissingError(
                    f"Application '{name}' is not registered."
                )

            visiting.add(name)

            for dependency in manifest.dependencies:
                if dependency not in manifest_map:
                    raise ApplicationDependencyMissingError(
                        f"Application '{name}' depends on "
                        f"missing application '{dependency}'."
                    )

                visit(dependency)

            visiting.remove(name)
            visited.add(name)
            resolved.append(name)

        for name in manifest_map:
            visit(name)

        return tuple(resolved)