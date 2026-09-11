"""
Tests for the Sentinel Application registry.
"""

from __future__ import annotations

import pytest

from sentinel.application import Application
from sentinel.application_registry import ApplicationRegistry


def test_empty_registry() -> None:
    registry = ApplicationRegistry()

    assert len(registry) == 0
    assert registry.all() == ()
    assert registry.names() == ()


def test_register_application() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register(
        "main",
        application,
    )

    assert len(registry) == 1
    assert registry.get("main") is application
    assert registry.contains("main") is True


def test_register_trims_name() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register(
        "  main  ",
        application,
    )

    assert registry.get("main") is application
    assert registry.contains("main") is True


def test_duplicate_name_is_rejected() -> None:
    registry = ApplicationRegistry()

    registry.register(
        "main",
        Application(),
    )

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(
            "main",
            Application(),
        )


def test_get_missing_application_raises() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        KeyError,
        match="Application 'missing' is not registered",
    ):
        registry.get("missing")


def test_unregister_application() -> None:
    registry = ApplicationRegistry()
    application = Application()

    registry.register(
        "main",
        application,
    )

    removed = registry.unregister("main")

    assert removed is application
    assert len(registry) == 0
    assert registry.contains("main") is False


def test_unregister_missing_application_raises() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        KeyError,
        match="Application 'missing' is not registered",
    ):
        registry.unregister("missing")


def test_all_returns_snapshot() -> None:
    registry = ApplicationRegistry()

    first = Application()
    second = Application()

    registry.register("first", first)
    registry.register("second", second)

    applications = registry.all()

    assert applications == (
        first,
        second,
    )

    registry.clear()

    assert applications == (
        first,
        second,
    )


def test_names_returns_snapshot() -> None:
    registry = ApplicationRegistry()

    registry.register("first", Application())
    registry.register("second", Application())

    assert registry.names() == (
        "first",
        "second",
    )


def test_contains_operator() -> None:
    registry = ApplicationRegistry()

    registry.register(
        "main",
        Application(),
    )

    assert "main" in registry
    assert "missing" not in registry
    assert 123 not in registry


def test_clear() -> None:
    registry = ApplicationRegistry()

    registry.register("first", Application())
    registry.register("second", Application())

    registry.clear()

    assert len(registry) == 0
    assert registry.all() == ()


def test_register_rejects_invalid_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.register(
            123,  # type: ignore[arg-type]
            Application(),
        )


def test_register_rejects_empty_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        ValueError,
        match="name must not be empty",
    ):
        registry.register(
            "   ",
            Application(),
        )


def test_register_rejects_invalid_application() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.register(
            "main",
            object(),  # type: ignore[arg-type]
        )


def test_get_rejects_invalid_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.get(123)  # type: ignore[arg-type]


def test_get_rejects_empty_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(
        ValueError,
        match="name must not be empty",
    ):
        registry.get("   ")


def test_unregister_rejects_invalid_name() -> None:
    registry = ApplicationRegistry()

    with pytest.raises(TypeError):
        registry.unregister(123)  # type: ignore[arg-type]


def test_registry_repr() -> None:
    registry = ApplicationRegistry()
    registry.register(
        "main",
        Application(),
    )

    assert repr(registry) == "ApplicationRegistry(applications=1)"