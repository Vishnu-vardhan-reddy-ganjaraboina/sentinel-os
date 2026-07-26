"""
Infrastructure constants for Sentinel OS.

This module defines immutable configuration values shared across
the infrastructure layer.
"""

from __future__ import annotations

# ============================================================================
# Logging
# ============================================================================

DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_LOG_DIRECTORY = "logs"

DEFAULT_LOG_FILE = "sentinel.log"

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_LOG_ENCODING = "utf-8"

DEFAULT_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB

DEFAULT_LOG_BACKUP_COUNT = 5


# ============================================================================
# Scheduler
# ============================================================================

DEFAULT_SCHEDULER_POLL_INTERVAL = 0.5


# ============================================================================
# Monitor
# ============================================================================

DEFAULT_MONITOR_HEALTHY = True