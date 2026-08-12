"""
Tests for logging enumerations.
"""

from __future__ import annotations

from sentinel.logging.enums import LogLevel


def test_log_level_values() -> None:
    assert LogLevel.DEBUG.value == 10
    assert LogLevel.INFO.value == 20
    assert LogLevel.WARNING.value == 30
    assert LogLevel.ERROR.value == 40
    assert LogLevel.CRITICAL.value == 50


def test_log_level_order() -> None:
    assert LogLevel.DEBUG < LogLevel.INFO
    assert LogLevel.INFO < LogLevel.WARNING
    assert LogLevel.WARNING < LogLevel.ERROR
    assert LogLevel.ERROR < LogLevel.CRITICAL


def test_log_level_names() -> None:
    assert LogLevel.DEBUG.name == "DEBUG"
    assert LogLevel.INFO.name == "INFO"
    assert LogLevel.WARNING.name == "WARNING"
    assert LogLevel.ERROR.name == "ERROR"
    assert LogLevel.CRITICAL.name == "CRITICAL"