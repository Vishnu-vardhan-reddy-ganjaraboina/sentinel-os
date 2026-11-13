import pytest

from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.validator import ControlRequestValidator


@pytest.mark.parametrize(
    "command",
    [
        KernelCommand.SYSTEM_STATUS,
        KernelCommand.SYSTEM_HEALTH,
        KernelCommand.SERVICE_LIST,
    ],
)
def test_commands_without_data_accept_empty_data(
    command: KernelCommand,
) -> None:
    ControlRequestValidator.validate(
        command,
        {},
    )


@pytest.mark.parametrize(
    "command",
    [
        KernelCommand.SYSTEM_STATUS,
        KernelCommand.SYSTEM_HEALTH,
        KernelCommand.SERVICE_LIST,
    ],
)
def test_commands_without_data_reject_data(
    command: KernelCommand,
) -> None:
    with pytest.raises(ValueError):
        ControlRequestValidator.validate(
            command,
            {"service": "memory"}
        )


@pytest.mark.parametrize(
    "command",
    [
        KernelCommand.SERVICE_STATUS,
        KernelCommand.SERVICE_START,
        KernelCommand.SERVICE_STOP,
        KernelCommand.SERVICE_RESTART,
    ],
)
def test_service_commands_require_name(
    command: KernelCommand,
) -> None:
    with pytest.raises(ValueError):
        ControlRequestValidator.validate(
            command,
            {},
        )


@pytest.mark.parametrize(
    "command",
    [
        KernelCommand.SERVICE_STATUS,
        KernelCommand.SERVICE_START,
        KernelCommand.SERVICE_STOP,
        KernelCommand.SERVICE_RESTART,
    ],
)
def test_service_commands_accept_valid_service(
    command: KernelCommand,
) -> None:
    ControlRequestValidator.validate(
        command,
        {"service": "memory"},
    )


def test_service_command_rejects_non_string_service() -> None:
    with pytest.raises(TypeError):
        ControlRequestValidator.validate(
            KernelCommand.SERVICE_START,
            {"service": 123},
        )


def test_service_command_rejects_empty_service() -> None:
    with pytest.raises(ValueError):
        ControlRequestValidator.validate(
            KernelCommand.SERVICE_START,
            {"service": "   "},
        )


def test_service_command_rejects_unexpected_fields() -> None:
    with pytest.raises(ValueError):
        ControlRequestValidator.validate(
            KernelCommand.SERVICE_START,
            {
                "service": "memory",
                "force": True,
            },
        )


def test_validator_rejects_invalid_command_type() -> None:
    with pytest.raises(TypeError, match="command must be a KernelCommand"):
        ControlRequestValidator.validate(
            "system.status",  # type: ignore[arg-type]
            {},
        )


def test_validator_rejects_non_mapping_data() -> None:
    with pytest.raises(TypeError, match="data must be a mapping"):
        ControlRequestValidator.validate(
            KernelCommand.SYSTEM_STATUS,
            None,  # type: ignore[arg-type]
        )
