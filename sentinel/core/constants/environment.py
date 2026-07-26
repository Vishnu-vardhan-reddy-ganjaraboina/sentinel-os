"""
sentinel.core.constants.environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Runtime environment constants.
"""

from __future__ import annotations

DEVELOPMENT: str = "development"
TESTING: str = "testing"
PRODUCTION: str = "production"

SUPPORTED_ENVIRONMENTS: tuple[str, ...] = (
    DEVELOPMENT,
    TESTING,
    PRODUCTION,
)