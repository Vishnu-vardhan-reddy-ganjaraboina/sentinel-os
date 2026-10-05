from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from sentinel.control_plane.adapter import KernelAdapter
from sentinel.control_plane.audit import (
    ControlAuditEvent,
    InMemoryControlAuditRecorder,
)
from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.result import ControlResult
from sentinel.kernel.kernel import Kernel


def _event(index: int) -> ControlAuditEvent:
    return ControlAuditEvent(
        caller_id=f"caller-{index}",
        caller_type="test",
        command=KernelCommand.SYSTEM_STATUS.value,
        success=True,
        data={
            "index": index,
            "nested": {
                "value": index,
            },
        },
    )


def _create_controller(
    audit_recorder: InMemoryControlAuditRecorder | None = None,
) -> KernelController:
    kernel = Kernel()
    adapter = KernelAdapter(kernel)

    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )

    context = ControlContext(
        caller_id="test-caller",
        caller_type="test",
    )

    return KernelController(
        target=adapter,
        authorizer=authorizer,
        context=context,
        audit_recorder=audit_recorder,
    )


def test_in_memory_audit_recorder_supports_concurrent_recording() -> None:
    recorder = InMemoryControlAuditRecorder()

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(
            executor.map(
                recorder.record,
                (_event(index) for index in range(200)),
            )
        )

    events = recorder.events

    assert len(events) == 200
    assert {event.caller_id for event in events} == {
        f"caller-{index}" for index in range(200)
    }


def test_in_memory_audit_recorder_supports_concurrent_reading() -> None:
    recorder = InMemoryControlAuditRecorder()

    for index in range(100):
        recorder.record(_event(index))

    with ThreadPoolExecutor(max_workers=16) as executor:
        snapshots = list(
            executor.map(
                lambda _: recorder.events,
                range(100),
            )
        )

    assert all(len(snapshot) == 100 for snapshot in snapshots)


def test_in_memory_audit_recorder_supports_concurrent_record_and_clear() -> None:
    recorder = InMemoryControlAuditRecorder()

    def worker(index: int) -> None:
        recorder.record(_event(index))
        if index % 10 == 0:
            recorder.clear()

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(worker, range(200)))

    assert isinstance(recorder.events, tuple)


def test_control_audit_event_isolated_from_nested_input_mutation() -> None:
    data = {
        "nested": {
            "value": "original",
        }
    }

    event = ControlAuditEvent(
        caller_id="caller",
        caller_type="test",
        command=KernelCommand.SYSTEM_STATUS.value,
        success=True,
        data=data,
    )

    data["nested"]["value"] = "changed"

    assert event.data["nested"]["value"] == "original"


def test_control_request_isolated_from_nested_input_mutation() -> None:
    data = {
        "nested": {
            "value": "original",
        }
    }

    request = ControlRequest(
        command=KernelCommand.SYSTEM_STATUS,
        context=ControlContext(
            caller_id="caller",
            caller_type="test",
        ),
        data=data,
    )

    data["nested"]["value"] = "changed"

    assert request.data["nested"]["value"] == "original"


def test_control_result_isolated_from_nested_input_mutation() -> None:
    data = {
        "nested": {
            "value": "original",
        }
    }

    result = ControlResult(
        success=True,
        command=KernelCommand.SYSTEM_STATUS.value,
        data=data,
    )

    data["nested"]["value"] = "changed"

    assert result.data["nested"]["value"] == "original"


class FailingAuditRecorder(InMemoryControlAuditRecorder):
    def record(self, event: ControlAuditEvent) -> None:
        raise RuntimeError("audit backend unavailable")


def test_audit_failure_does_not_replace_successful_control_result() -> None:
    controller = _create_controller(FailingAuditRecorder())

    result = controller.execute(KernelCommand.SYSTEM_STATUS)

    assert result.success is True
    assert result.command == KernelCommand.SYSTEM_STATUS.value
class FailingKernelAdapter(KernelAdapter):
    def health(self) -> dict[str, object]:
        raise RuntimeError("kernel backend unavailable")


def test_audit_failure_does_not_replace_failed_control_result() -> None:
    kernel = Kernel()
    adapter = FailingKernelAdapter(kernel)

    authorizer = ControlAuthorizer(
        {
            ControlPermission.READ,
            ControlPermission.CONTROL,
        }
    )

    context = ControlContext(
        caller_id="test-caller",
        caller_type="test",
    )

    controller = KernelController(
        target=adapter,
        authorizer=authorizer,
        context=context,
        audit_recorder=FailingAuditRecorder(),
    )

    result = controller.execute(KernelCommand.SYSTEM_HEALTH)

    assert result.success is False
    assert result.command == KernelCommand.SYSTEM_HEALTH.value
    assert result.error is not None
    assert "kernel backend unavailable" in result.error
