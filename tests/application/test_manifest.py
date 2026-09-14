"""
Tests for application manifests.
"""

import pytest

from sentinel.application_manifest import ApplicationManifest


def test_manifest_defaults() -> None:
    manifest = ApplicationManifest(name="test-app")

    assert manifest.name == "test-app"
    assert manifest.version == "0.1.0"
    assert manifest.dependencies == ()
    assert manifest.permissions == ()
    assert manifest.metadata == {}


def test_manifest_normalizes_name_and_version() -> None:
    manifest = ApplicationManifest(
        name="  test-app  ",
        version=" 1.2.3 ",
    )

    assert manifest.name == "test-app"
    assert manifest.version == "1.2.3"


def test_manifest_normalizes_dependencies() -> None:
    manifest = ApplicationManifest(
        name="app",
        dependencies=(" core ", "core", "database"),
    )

    assert manifest.dependencies == (
        "core",
        "database",
    )


def test_manifest_normalizes_permissions() -> None:
    manifest = ApplicationManifest(
        name="app",
        permissions=(" execute ", "execute", "memory"),
    )

    assert manifest.permissions == (
        "execute",
        "memory",
    )


def test_manifest_copies_metadata() -> None:
    metadata = {"owner": "sentinel"}

    manifest = ApplicationManifest(
        name="app",
        metadata=metadata,
    )

    metadata["owner"] = "changed"

    assert manifest.metadata["owner"] == "sentinel"


def test_manifest_metadata_is_read_only() -> None:
    manifest = ApplicationManifest(
        name="app",
        metadata={"owner": "sentinel"},
    )

    with pytest.raises(TypeError):
        manifest.metadata["owner"] = "changed"  # type: ignore[index]


def test_manifest_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        ApplicationManifest(name="   ")


def test_manifest_rejects_invalid_name() -> None:
    with pytest.raises(TypeError):
        ApplicationManifest(name=123)  # type: ignore[arg-type]


def test_manifest_rejects_empty_version() -> None:
    with pytest.raises(ValueError):
        ApplicationManifest(
            name="app",
            version="   ",
        )


def test_manifest_rejects_invalid_dependency() -> None:
    with pytest.raises(TypeError):
        ApplicationManifest(
            name="app",
            dependencies=(123,),  # type: ignore[arg-type]
        )


def test_manifest_rejects_empty_dependency() -> None:
    with pytest.raises(ValueError):
        ApplicationManifest(
            name="app",
            dependencies=(" ",),
        )


def test_manifest_rejects_self_dependency() -> None:
    with pytest.raises(ValueError):
        ApplicationManifest(
            name="app",
            dependencies=("app",),
        )


def test_manifest_rejects_invalid_permission() -> None:
    with pytest.raises(TypeError):
        ApplicationManifest(
            name="app",
            permissions=(123,),  # type: ignore[arg-type]
        )


def test_manifest_rejects_empty_permission() -> None:
    with pytest.raises(ValueError):
        ApplicationManifest(
            name="app",
            permissions=(" ",),
        )


def test_manifest_rejects_invalid_metadata() -> None:
    with pytest.raises(TypeError):
        ApplicationManifest(
            name="app",
            metadata="invalid",  # type: ignore[arg-type]
        )


def test_manifest_to_dict_isolated() -> None:
    manifest = ApplicationManifest(
        name="app",
        dependencies=("core",),
        permissions=("execute",),
        metadata={"owner": "sentinel"},
    )

    result = manifest.to_dict()
    result["metadata"]["owner"] = "changed"

    assert manifest.metadata["owner"] == "sentinel"


def test_manifest_repr() -> None:
    manifest = ApplicationManifest(
        name="app",
        version="1.2.3",
        dependencies=("core",),
    )

    assert repr(manifest) == (
        "ApplicationManifest("
        "name='app', "
        "version='1.2.3', "
        "dependencies=('core',))"
    )