"""
sentinel.core.constants.exit_codes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard process exit codes used by Sentinel.
"""

from __future__ import annotations

SUCCESS: int = 0

GENERAL_ERROR: int = 1

CONFIGURATION_ERROR: int = 2

RUNTIME_ERROR: int = 3

INTERRUPTED: int = 130