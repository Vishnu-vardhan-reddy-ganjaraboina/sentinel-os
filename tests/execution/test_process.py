import sys
import threading

import pytest

from sentinel.execution.exceptions import ProcessError
from sentinel.execution.process import ProcessManager


def test_start_process():
    manager = ProcessManager()

    try:
        pid = manager.start(
            [sys.executable, "-c", "print('hello')"]
        )

        assert isinstance(pid, int)
        assert manager.pid == pid
    finally:
        manager.terminate()


def test_wait():
    manager = ProcessManager()

    try:
        manager.start(
            [sys.executable, "-c", "print('hello')"]
        )

        exit_code = manager.wait()

        assert exit_code == 0
    finally:
        manager.read_output()


def test_read_output():
    manager = ProcessManager()

    try:
        manager.start(
            [sys.executable, "-c", "print('hello')"]
        )

        stdout, stderr = manager.read_output()

        assert "hello" in stdout
        assert stderr == ""
    finally:
        manager.terminate()


def test_double_start():
    manager = ProcessManager()

    try:
        manager.start(
            [sys.executable, "-c", "import time; time.sleep(1)"]
        )

        with pytest.raises(ProcessError):
            manager.start(
                [sys.executable, "--version"]
            )
    finally:
        manager.terminate()


def test_wait_without_process():
    manager = ProcessManager()

    with pytest.raises(ProcessError):
        manager.wait()

def test_concurrent_terminate_calls_are_safe():
    manager = ProcessManager()

    try:
        manager.start(
            [
                sys.executable,
                "-c",
                "import time; time.sleep(0.5)",
            ]
        )

        barrier = threading.Barrier(3)
        errors: list[BaseException] = []

        def terminate() -> None:
            try:
                barrier.wait(timeout=2)
                manager.terminate()
            except BaseException as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=terminate)
            for _ in range(2)
        ]

        for thread in threads:
            thread.start()

        barrier.wait(timeout=2)

        for thread in threads:
            thread.join(timeout=3)

        assert all(not thread.is_alive() for thread in threads)
        assert errors == []
        assert manager.process is None
        assert manager.pid is None
        assert manager.is_running is False

    finally:
        manager.terminate()