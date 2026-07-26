from sentinel.kernel.service_state import ServiceState


def test_service_state_values() -> None:
    assert ServiceState.CREATED.value == "created"
    assert ServiceState.RUNNING.value == "running"
    assert ServiceState.FAILED.value == "failed"


def test_service_state_is_enum() -> None:
    assert ServiceState.STOPPED.name == "STOPPED"