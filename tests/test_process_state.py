from sentinel.process import (
    ProcessControlError,
    ProcessError,
    ProcessShutdownError,
    ProcessStartupError,
    ProcessState,
    ProcessStateError,
)


def test_process_states() -> None:
    assert ProcessState.STOPPED.value == "stopped"
    assert ProcessState.STARTING.value == "starting"
    assert ProcessState.RUNNING.value == "running"
    assert ProcessState.STOPPING.value == "stopping"
    assert ProcessState.FAILED.value == "failed"


def test_process_states_are_strings() -> None:
    assert isinstance(ProcessState.STOPPED, str)
    assert ProcessState.RUNNING == "running"


def test_process_states_are_ordered_by_lifecycle_definition() -> None:
    assert list(ProcessState) == [
        ProcessState.STOPPED,
        ProcessState.STARTING,
        ProcessState.RUNNING,
        ProcessState.STOPPING,
        ProcessState.FAILED,
    ]


def test_process_error_hierarchy() -> None:
    assert issubclass(ProcessStateError, ProcessError)
    assert issubclass(ProcessStartupError, ProcessError)
    assert issubclass(ProcessShutdownError, ProcessError)
    assert issubclass(ProcessControlError, ProcessError)


def test_process_error_can_be_raised() -> None:
    try:
        raise ProcessStateError("invalid state")
    except ProcessError as exc:
        assert str(exc) == "invalid state"
