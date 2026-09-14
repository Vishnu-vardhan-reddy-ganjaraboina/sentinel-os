"""
Tests for the Sentinel application registry.
"""

import pytest

from sentinel.application import Application
from sentinel.application_manifest import ApplicationManifest
from sentinel.application_registry import ApplicationRegistry


def test_empty_registry() -> None:
    registry = ApplicationRegistry()

    assert len(registry) == 0
    assert registry.names() == ()
    assert registry.all() == ()


def test_register_application() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register("test-app", application)

    assert len(registry) == 1
    assert registry.get("test-app") is application
    assert "test-app" in registry


def test_register_trims_name() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register("  test-app  ", application)

    assert registry.get("test-app") is application
    assert registry.contains("test-app")


def test_duplicate_name_is_rejected() -> None:
    registry = ApplicationRegistry()

    registry.register("test-app", Application())

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register("test-app", Application())


def test_get_missing_application_raises() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        KeyError,
        match="is not registered",
    ):
        registry.get("missing")


def test_unregister_application() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register("test-app", application)

    result = registry.unregister("test-app")

    assert result is application
    assert len(registry) == 0


def test_unregister_missing_application_raises() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        KeyError,
        match="is not registered",
    ):
        registry.unregister("missing")


def test_all_returns_snapshot() -> None:
    registry = ApplicationRegistry()

    first = Application()
    second = Application()

    registry.register("first", first)
    registry.register("second", second)

    applications = registry.all()

    assert applications == (first, second)


def test_names_returns_snapshot() -> None:
    registry = ApplicationRegistry()

    registry.register("first", Application())
    registry.register("second", Application())

    names = registry.names()

    assert names == ("first", "second")


def test_contains_operator() -> None:
    registry = ApplicationRegistry()

    registry.register("test-app", Application())

    assert "test-app" in registry
    assert "missing" not in registry
    assert "" not in registry
    assert 123 not in registry


def test_clear() -> None:
    registry = ApplicationRegistry()

    registry.register("first", Application())
    registry.register("second", Application())

    registry.clear()

    assert len(registry) == 0
    assert registry.names() == ()
    assert registry.all() == ()
    assert registry.manifests() == ()


def test_register_rejects_invalid_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.register(123, Application())  # type: ignore[arg-type]


def test_register_rejects_empty_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(ValueError):
        registry.register("   ", Application())


def test_register_rejects_invalid_application() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.register(
            "test-app",
            object(),  # type: ignore[arg-type]
        )


def test_get_rejects_invalid_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.get(123)  # type: ignore[arg-type]


def test_get_rejects_empty_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(ValueError):
        registry.get("   ")


def test_unregister_rejects_invalid_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.unregister(123)  # type: ignore[arg-type]


def test_registry_repr() -> None:
    registry = ApplicationRegistry()
    registry.register("one", Application())
    registry.register("two", Application())

    assert repr(registry) == (
        "ApplicationRegistry(applications=2)"
    )


def test_register_without_manifest_creates_default_manifest() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register("test-app", application)

    manifest = registry.manifest("test-app")

    assert isinstance(manifest, ApplicationManifest)
    assert manifest.name == "test-app"


def test_register_with_manifest() -> None:
    registry = ApplicationRegistry()
    application = Application()

    manifest = ApplicationManifest(
        name="test-app",
        version="1.2.3",
        dependencies=("database",),
        permissions=("execute",),
    )

    registry.register(
        "test-app",
        application,
        manifest,
    )

    assert registry.manifest("test-app") is manifest


def test_manifest_name_must_match_registration_name() -> None:
    registry = ApplicationRegistry()
    application = Application()

    manifest = ApplicationManifest(
        name="different-app",
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        registry.register(
            "test-app",
            application,
            manifest,
        )


def test_manifest_rejects_invalid_type() -> None:
    registry = ApplicationRegistry()
    application = Application()

    with pytest.raises(TypeError):
        registry.register(
            "test-app",
            application,
            "invalid",  # type: ignore[arg-type]
        )


def test_manifest_lookup_missing_application_is_rejected() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        KeyError,
        match="is not registered",
    ):
        registry.manifest("missing")


def test_manifests_returns_snapshot() -> None:
    registry = ApplicationRegistry()

    first = ApplicationManifest(name="first")
    second = ApplicationManifest(name="second")

    registry.register(
        "first",
        Application(),
        first,
    )
    registry.register(
        "second",
        Application(),
        second,
    )

    manifests = registry.manifests()

    assert manifests == (
        ("first", first),
        ("second", second),
    )


def test_application_info() -> None:
    registry = ApplicationRegistry()

    application = Application()
    manifest = ApplicationManifest(
        name="test-app",
        version="2.0.0",
        dependencies=("core",),
        permissions=("execute",),
    )

    registry.register(
        "test-app",
        application,
        manifest,
    )

    info = registry.application_info("test-app")

    assert info["name"] == "test-app"
    assert info["application"] is application
    assert info["manifest"] is manifest