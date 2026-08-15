"""
Exceptions for the Sentinel Orchestration subsystem.
"""

from __future__ import annotations


class OrchestrationError(Exception):
    """Base exception for orchestration failures."""


class OrchestrationValidationError(OrchestrationError):
    """Raised when an orchestration request is invalid."""


class OrchestrationAuthorizationError(OrchestrationError):
    """Raised when a request is not authorized."""


class OrchestrationExecutionError(OrchestrationError):
    """Raised when request execution fails."""