from __future__ import annotations

from typing import Any, Mapping

from sentinel.control_plane.commands import KernelCommand


class ControlRequestValidator:
    """
    Validate command-specific Control Plane request data.
    """

    _COMMANDS_WITHOUT_DATA = {
        KernelCommand.SYSTEM_STATUS,
        KernelCommand.SYSTEM_HEALTH,
        KernelCommand.SERVICE_LIST,
    }

    _SERVICE_COMMANDS = {
        KernelCommand.SERVICE_STATUS,
        KernelCommand.SERVICE_START,
        KernelCommand.SERVICE_STOP,
        KernelCommand.SERVICE_RESTART,
    }

    @classmethod
    def validate(
        cls,
        command: KernelCommand,
        data: Mapping[str, Any],
    ) -> None:
        if command in cls._COMMANDS_WITHOUT_DATA:
            if data:
                raise ValueError(
                    f"Command '{command.value}' does not accept request data."
                )
            return

        if command in cls._SERVICE_COMMANDS:
            cls._validate_service_command(data)
            return

        raise ValueError(
            f"Unsupported control command: '{command.value}'."
        )

    @staticmethod
    def _validate_service_command(
        data: Mapping[str, Any],
    ) -> None:
        if "service" not in data:
            raise ValueError(
                "Command requires a non-empty 'service' value."
            )

        service = data["service"]

        if not isinstance(service, str):
            raise TypeError(
                "Service value must be a string."
            )

        if not service.strip():
            raise ValueError(
                "Command requires a non-empty 'service' value."
            )