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
    DuplicateServiceError,
)
from sentinel.kernel.service import Service


class DependencyResolver:
    """Resolves service startup order."""

    def resolve(
        self,
        services: Iterable[Service],
    ) -> tuple[Service, ...]:

        service_map: dict[str, Service] = {}

        for service in services:
            if service.name in service_map:
                raise DuplicateServiceError(
                    f"Service '{service.name}' is already registered."
                )

            service_map[service.name] = service

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