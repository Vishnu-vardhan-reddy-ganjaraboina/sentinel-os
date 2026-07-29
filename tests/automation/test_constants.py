from sentinel.automation.constants import (
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_WORKFLOW_VERSION,
    TriggerType,
    WorkflowStatus,
)


def test_defaults():
    assert DEFAULT_WORKFLOW_VERSION == "1.0.0"
    assert DEFAULT_RETRY_COUNT == 3
    assert DEFAULT_RETRY_DELAY == 5


def test_workflow_status():
    assert WorkflowStatus.IDLE.value == "idle"
    assert WorkflowStatus.RUNNING.value == "running"
    assert WorkflowStatus.COMPLETED.value == "completed"
    assert WorkflowStatus.FAILED.value == "failed"
    assert WorkflowStatus.DISABLED.value == "disabled"


def test_trigger_types():
    assert TriggerType.MANUAL.value == "manual"
    assert TriggerType.EVENT.value == "event"
    assert TriggerType.SCHEDULE.value == "schedule"
    assert TriggerType.WEBHOOK.value == "webhook"
    assert TriggerType.CONDITION.value == "condition"