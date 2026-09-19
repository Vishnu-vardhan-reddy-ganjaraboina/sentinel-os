from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from sentinel.control_plane.callers import ControlCallerType


@dataclass(frozen=True, slots=True)
class ControlContext:
    caller_id: str
    caller_type: ControlCallerType | str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.caller_id.strip():
            raise ValueError("caller_id must not be empty.")

        if isinstance(self.caller_type, ControlCallerType):
            caller_type = self.caller_type
        elif isinstance(self.caller_type, str):
            if not self.caller_type.strip():
                raise ValueError("caller_type must not be empty.")

            try:
                caller_type = ControlCallerType(self.caller_type)
            except ValueError:
                caller_type = self.caller_type
        else:
            raise TypeError(
                "caller_type must be a ControlCallerType or string."
            )

        object.__setattr__(self, "caller_type", caller_type)
        object.__setattr__(self, "metadata", dict(self.metadata))