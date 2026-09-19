from sentinel.control_plane.callers import ControlCallerType


def test_control_caller_types() -> None:
    assert ControlCallerType.SYSTEM.value == "system"
    assert ControlCallerType.CLI.value == "cli"
    assert ControlCallerType.API.value == "api"
    assert ControlCallerType.AUTOMATION.value == "automation"
    assert ControlCallerType.AI_AGENT.value == "ai_agent"


def test_control_caller_type_is_string_compatible() -> None:
    assert ControlCallerType.SYSTEM == "system"
    assert ControlCallerType.AI_AGENT == "ai_agent"