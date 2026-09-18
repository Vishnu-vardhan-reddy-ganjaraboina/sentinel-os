"""
Public API for the Sentinel Kernel Control Plane.
"""

from sentinel.control_plane.adapter import KernelAdapter
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.result import ControlResult
from sentinel.control_plane.target import KernelControlTarget

__all__ = [
    "ControlResult",
    "KernelAdapter",
    "KernelCommand",
    "KernelControlTarget",
]