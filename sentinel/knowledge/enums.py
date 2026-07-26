"""
sentinel.knowledge.enums
~~~~~~~~~~~~~~~~~~~~~~~~

Canonical enumeration types for the Knowledge subsystem.

These enums define the shared vocabulary used throughout Sentinel OS.
They intentionally contain no business logic and provide stable,
human-readable values suitable for serialization.

RFC:
    RFC-0003 Knowledge Subsystem
"""

from __future__ import annotations

from enum import StrEnum, unique

__all__ = [
    "SentinelEnum",
    "KnowledgeType",
    "KnowledgeState",
    "KnowledgeScope",
    "KnowledgeImportance",
    "RelationshipType",
    "RelationshipDirection",
]


class SentinelEnum(StrEnum):
    """
    Base class for Sentinel string enumerations.

    Provides consistent string conversion across all Sentinel enums.
    """

    def __str__(self) -> str:
        return self.value


@unique
class KnowledgeType(SentinelEnum):
    """
    Represents the category of a knowledge entity.
    """

    USER = "user"
    DEVICE = "device"
    APPLICATION = "application"
    FILE = "file"
    DIRECTORY = "directory"
    PROJECT = "project"
    DOCUMENT = "document"

    PLUGIN = "plugin"
    SKILL = "skill"
    AUTOMATION = "automation"

    SERVICE = "service"
    PROCESS = "process"

    NETWORK = "network"

    CONTACT = "contact"
    EMAIL = "email"
    MESSAGE = "message"
    CALENDAR = "calendar"

    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

    MODEL = "model"

    CUSTOM = "custom"


@unique
class KnowledgeState(SentinelEnum):
    """
    Represents the lifecycle state of a knowledge entity.
    """

    CREATED = "created"
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


@unique
class KnowledgeScope(SentinelEnum):
    """
    Defines the persistence scope of a knowledge entity.
    """

    SESSION = "session"
    WORKING = "working"
    LONG_TERM = "long_term"


@unique
class KnowledgeImportance(SentinelEnum):
    """
    Indicates the relative importance of a knowledge entity.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@unique
class RelationshipType(SentinelEnum):
    """
    Defines the semantic relationship between two entities.
    """

    OWNS = "owns"
    USES = "uses"
    RUNS = "runs"

    CONTAINS = "contains"

    CREATED = "created"

    CONNECTED_TO = "connected_to"

    DEPENDS_ON = "depends_on"

    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"

    RELATED_TO = "related_to"


@unique
class RelationshipDirection(SentinelEnum):
    """
    Represents traversal direction for relationships.
    """

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BIDIRECTIONAL = "bidirectional"