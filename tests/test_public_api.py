"""
Public API tests for Sentinel OS.
"""

import sentinel

from sentinel import (
    Application,
    ApplicationRegistry,
    Runtime,
    RuntimeComposer,
)


def test_public_api_exports_expected_symbols() -> None:
    assert set(sentinel.__all__) == {
        "Application",
        "ApplicationRegistry",
        "Runtime",
        "RuntimeComposer",
    }


def test_public_api_application() -> None:
    assert sentinel.Application is Application


def test_public_api_application_registry() -> None:
    assert sentinel.ApplicationRegistry is ApplicationRegistry


def test_public_api_runtime() -> None:
    assert sentinel.Runtime is Runtime


def test_public_api_runtime_composer() -> None:
    assert sentinel.RuntimeComposer is RuntimeComposer