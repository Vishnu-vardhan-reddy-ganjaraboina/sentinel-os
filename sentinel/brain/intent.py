"""
Intent model for Sentinel Brain.

An Intent represents the structured meaning of a requested action.

Intent is a data model only. It does not execute capabilities,
perform authorization, or interact with the operating system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Intent:
    """
    Structured representation of an intended action.

    Attributes:
        name:
            Stable identifier for the intent.

        input:
            Original user/request input associated with the intent.

        capability_id:
            Optional capability selected for the intent.

        arguments:
            Arguments that may be supplied to the selected capability.

        context:
            Additional contextual information associated with the intent.
    """

    name: str
    input: str
    capability_id: str | None = None
    arguments: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")

        if not self.name.strip():
            raise ValueError("name must not be empty.")

        if not isinstance(self.input, str):
            raise TypeError("input must be a string.")

        if not isinstance(self.arguments, Mapping):
            raise TypeError("arguments must be a mapping.")

        if not isinstance(self.context, Mapping):
            raise TypeError("context must be a mapping.")

        if self.capability_id is not None:
            if not isinstance(self.capability_id, str):
                raise TypeError(
                    "capability_id must be a string or None."
                )

            if not self.capability_id.strip():
                raise ValueError(
                    "capability_id must not be empty."
                )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the intent into a serializable mapping.
        """
        return {
            "name": self.name,
            "input": self.input,
            "capability_id": self.capability_id,
            "arguments": dict(self.arguments),
            "context": dict(self.context),
        }