from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from sentinel.execution.exceptions import ExecutionTimeoutError, ProcessError
from sentinel.execution.isolated_worker import IsolatedWorker, WorkerLimits


def make_worker(**kwargs):
    return IsolatedWorker(
        allowed_modules={"tests.execution.worker_fixtures"},
        **kwargs,
    )


def test_worker_executes_allowlisted_json_callable():
    worker = make_worker()
    assert worker.execute(
        "tests.execution.worker_fixtures:add",
        19,
        23,
    ) == 42


def test_worker_rejects_module_outside_allowlist():
    worker = make_worker()
    with pytest.raises(PermissionError, match="allowlist"):
        worker.execute("os:getcwd")


def test_worker_rejects_non_json_arguments():
    worker = make_worker()
    with pytest.raises(ProcessError, match="JSON-serializable"):
        worker.execute("tests.execution.worker_fixtures:add", object(), 1)


def test_worker_rejects_local_function_reference():
    worker = make_worker()
    with pytest.raises(ValueError, match="module-level"):
        worker.execute("tests.execution.worker_fixtures:outer.<locals>.inner")


def test_worker_enforces_wall_clock_timeout():
    worker = make_worker()
    started = time.monotonic()
    with pytest.raises(ExecutionTimeoutError):
        worker.execute(
            "tests.execution.worker_fixtures:sleep_for",
            10,
            timeout=0.2,
        )
    assert time.monotonic() - started < 5


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group assertion")
def test_worker_timeout_terminates_descendant_processes():
    worker = make_worker()
    with pytest.raises(ExecutionTimeoutError):
        pid_file = Path(__file__).with_name("worker-child.pid")
        pid_file.unlink(missing_ok=True)
        try:
            worker.execute(
                "tests.execution.worker_fixtures:spawn_child_and_record_pid",
                str(pid_file),
                10,
                timeout=0.8,
            )
        finally:
            child_pid = int(pid_file.read_text()) if pid_file.exists() else None
            pid_file.unlink(missing_ok=True)
        if child_pid is not None:
            # A terminated orphan may briefly remain as a zombie; it must not
            # remain running after the worker's process group is killed.
            status = Path(f"/proc/{child_pid}/status")
            if status.exists():
                state = next(
                    (
                        line
                        for line in status.read_text().splitlines()
                        if line.startswith("State:")
                    ),
                    "",
                )
                assert "Z" in state


def test_worker_limits_validate_positive_integers():
    with pytest.raises(ValueError, match="greater than zero"):
        WorkerLimits(memory_bytes=0)
    with pytest.raises(TypeError, match="must be an integer"):
        WorkerLimits(cpu_seconds=True)



def test_worker_rejects_oversized_results():
    worker = make_worker(limits=WorkerLimits(max_result_bytes=128))
    with pytest.raises(ProcessError, match="ResultLimitError"):
        worker.execute(
            "tests.execution.worker_fixtures:large_result",
            10000,
        )



@pytest.mark.skipif(os.name != "posix", reason="POSIX rlimit assertion")
def test_worker_applies_os_resource_limits_before_callable():
    limits = WorkerLimits(
        cpu_seconds=7,
        memory_bytes=256 * 1024 * 1024,
        file_size_bytes=2 * 1024 * 1024,
        open_files=48,
    )
    values = make_worker(limits=limits).execute(
        "tests.execution.worker_fixtures:current_resource_limits"
    )
    assert values["cpu"][0] == 7
    assert values["memory"][0] == limits.memory_bytes
    assert values["file_size"][0] == limits.file_size_bytes
    assert values["open_files"][0] == limits.open_files
