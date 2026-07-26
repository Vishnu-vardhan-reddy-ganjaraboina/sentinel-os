"""
sentinel.core.constants.platform
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Platform-wide immutable constants.

This module contains constants describing Sentinel OS itself.
It must remain independent of all other Sentinel packages.
"""

from __future__ import annotations

PROJECT_NAME: str = "sentinel"
PROJECT_DISPLAY_NAME: str = "Sentinel OS"

DEFAULT_ENCODING: str = "utf-8"

DEFAULT_TIMEZONE: str = "UTC"

DEFAULT_LANGUAGE: str = "en"

COPYRIGHT: str = "Copyright (c) Sentinel Project"