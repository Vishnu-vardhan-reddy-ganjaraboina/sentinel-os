"""
Exceptions for the Sentinel Automation subsystem.
"""

from sentinel.core.exceptions import SentinelError


class AutomationError(SentinelError):
    """
    Base exception for all automation-related errors.
    """


class WorkflowNotFoundError(AutomationError):
    """
    Raised when a workflow cannot be found.
    """


class WorkflowAlreadyExistsError(AutomationError):
    """
    Raised when attempting to register an existing workflow.
    """


class TriggerError(AutomationError):
    """
    Raised when a trigger cannot be evaluated.
    """


class WorkflowExecutionError(AutomationError):
    """
    Raised when workflow execution fails.
    """


class InvalidWorkflowError(AutomationError):
    """
    Raised when a workflow is invalid.
    """


class WorkflowDisabledError(AutomationError):
    """
    Raised when attempting to execute a disabled workflow.
    """