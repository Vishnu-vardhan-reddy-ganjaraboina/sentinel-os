"""
Tests for application dependency resolution.
"""

import pytest

from sentinel.application_dependency_resolver import (
    ApplicationDependencyCycleError,
    ApplicationDependencyMissingError,
    ApplicationDependencyResolver,
)
from sentinel.application_manifest import ApplicationManifest


def test_empty_manifests() -> None:
    resolver = ApplicationDependencyResolver()

    assert resolver.resolve(()) == ()


def test_single_application() -> None:
    resolver = ApplicationDependencyResolver()

    result = resolver.resolve(
        (
            ApplicationManifest(name="app"),
        )
    )

    assert result == ("app",)


def test_dependency_is_started_before_application() -> None:
    resolver = ApplicationDependencyResolver()

    result = resolver.resolve(
        (
            ApplicationManifest(
                name="frontend",
                dependencies=("backend",),
            ),
            ApplicationManifest(name="backend"),
        )
    )

    assert result == (
        "backend",
        "frontend",
    )


def test_multi_level_dependencies() -> None:
    resolver = ApplicationDependencyResolver()

    result = resolver.resolve(
        (
            ApplicationManifest(
                name="frontend",
                dependencies=("backend",),
            ),
            ApplicationManifest(
                name="backend",
                dependencies=("database",),
            ),
            ApplicationManifest(name="database"),
        )
    )

    assert result == (
        "database",
        "backend",
        "frontend",
    )


def test_multiple_dependencies() -> None:
    resolver = ApplicationDependencyResolver()

    result = resolver.resolve(
        (
            ApplicationManifest(
                name="app",
                dependencies=("database", "cache"),
            ),
            ApplicationManifest(name="database"),
            ApplicationManifest(name="cache"),
        )
    )

    assert result.index("database") < result.index("app")
    assert result.index("cache") < result.index("app")


def test_missing_dependency_is_rejected() -> None:
    resolver = ApplicationDependencyResolver()

    with pytest.raises(
        ApplicationDependencyMissingError,
        match="missing application 'database'",
    ):
        resolver.resolve(
            (
                ApplicationManifest(
                    name="app",
                    dependencies=("database",),
                ),
            )
        )


def test_dependency_cycle_is_rejected() -> None:
    resolver = ApplicationDependencyResolver()

    with pytest.raises(
        ApplicationDependencyCycleError,
        match="dependency cycle",
    ):
        resolver.resolve(
            (
                ApplicationManifest(
                    name="one",
                    dependencies=("two",),
                ),
                ApplicationManifest(
                    name="two",
                    dependencies=("one",),
                ),
            )
        )


def test_duplicate_manifest_name_is_rejected() -> None:
    resolver = ApplicationDependencyResolver()

    with pytest.raises(
        ValueError,
        match="is duplicated",
    ):
        resolver.resolve(
            (
                ApplicationManifest(name="app"),
                ApplicationManifest(name="app"),
            )
        )


def test_invalid_manifest_type_is_rejected() -> None:
    resolver = ApplicationDependencyResolver()

    with pytest.raises(TypeError):
        resolver.resolve(("invalid",))  # type: ignore[arg-type]


def test_resolution_is_deterministic() -> None:
    resolver = ApplicationDependencyResolver()

    manifests = (
        ApplicationManifest(name="one"),
        ApplicationManifest(
            name="two",
            dependencies=("one",),
        ),
        ApplicationManifest(
            name="three",
            dependencies=("one",),
        ),
    )

    assert resolver.resolve(manifests) == resolver.resolve(manifests)