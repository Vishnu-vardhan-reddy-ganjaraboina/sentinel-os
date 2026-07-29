import sys

import pytest

from sentinel.execution.exceptions import ProcessError
from sentinel.execution.process import ProcessManager


def test_start_process():
    manager = ProcessManager()

    pid = manager.start(
        [sys.executable, "-c", "print('hello')"]
    )

    assert isinstance(pid, int)
    assert manager.pid == pid


def test_wait():
    manager = ProcessManager()

    manager.start(
        [sys.executable, "-c", "print('hello')"]
    )

    exit_code = manager.wait()

    assert exit_code == 0


def test_read_output():
    manager = ProcessManager()

    manager.start(
        [sys.executable, "-c", "print('hello')"]
    )

    stdout, stderr = manager.read_output()

    assert "hello" in stdout
    assert stderr == ""


def test_double_start():
    manager = ProcessManager()

    manager.start(
        [sys.executable, "-c", "import time; time.sleep(1)"]
    )

    with pytest.raises(ProcessError):
        manager.start(
            [sys.executable, "--version"]
        )

    manager.terminate()


def test_wait_without_process():
    manager = ProcessManager()

    with pytest.raises(ProcessError):
        manager.wait()