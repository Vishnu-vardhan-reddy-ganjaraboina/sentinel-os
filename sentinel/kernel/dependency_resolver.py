"""
Dependency resolution for Sentinel OS.

Responsibilities:
    - Validate dependencies
    - Detect circular dependencies
    - Produce startup order
"""

from __future__ import annotations

from collections.abc import Iterable

from sentinel.kernel.exceptions import (
    CircularDependencyError,
    DependencyNotFoundError,
)
from sentinel.kernel.service import Service


class DependencyResolver:
    """Resolves service startup order."""

    def resolve(
        self,
        services: Iterable[Service],
    ) -> tuple[Service, ...]:

        service_map = {
            service.name: service
            for service in services
        }

        visited: set[str] = set()
        visiting: set[str] = set()

        result: list[Service] = []

        def visit(name: str) -> None:

            if name in visited:
                return

            if name in visiting:
                raise CircularDependencyError(
                    f"Circular dependency detected involving '{name}'."
                )

            try:
                service = service_map[name]
            except KeyError as exc:
                raise DependencyNotFoundError(
                    f"Dependency '{name}' is not registered."
                ) from exc

            visiting.add(name)

            for dependency in service.dependencies:
                visit(dependency)

            visiting.remove(name)
            visited.add(name)

            result.append(service)

        for service in service_map.values():
            visit(service.name)

        return tuple(result)