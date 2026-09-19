from __future__ import annotations

from enum import StrEnum


class ControlCallerType(StrEnum):
    """
    Identifies the type of component requesting Control Plane access.
    """

    SYSTEM = "system"
    CLI = "cli"
    API = "api"
    AUTOMATION = "automation"
    AI_AGENT = "ai_agent"