import sys

import pytest

from sentinel.execution.exceptions import ProcessError
from sentinel.execution.process import ProcessManager


def test_start_process():
    manager = ProcessManager()

    try:
        pid = manager.start([sys.executable, "-c", "print('hello')"])

        assert isinstance(pid, int)
        assert manager.pid == pid
    finally:
        manager.terminate()


def test_wait():
    manager = ProcessManager()

    try:
        manager.start([sys.executable, "-c", "print('hello')"])

        exit_code = manager.wait()

        assert exit_code == 0
    finally:
        manager.terminate()


def test_read_output():
    manager = ProcessManager()

    manager.start([sys.executable, "-c", "print('hello')"])

    stdout, stderr = manager.read_output()

    assert "hello" in stdout
    assert stderr == ""


def test_double_start():
    manager = ProcessManager()

    manager.start([sys.executable, "-c", "import time; time.sleep(1)"])

    with pytest.raises(ProcessError):
        manager.start([sys.executable, "--version"])

    manager.terminate()


def test_wait_without_process():
    manager = ProcessManager()

    with pytest.raises(ProcessError):
        manager.wait()


def test_shell_execution_is_rejected():
    with pytest.raises(ValueError, match="shell=True is not supported"):
        ProcessManager(shell=True)


def test_shutdown_is_idempotent():
    manager = ProcessManager()
    manager.shutdown()
    manager.shutdown()


def test_start_after_shutdown_is_rejected():
    manager = ProcessManager()
    manager.shutdown()

    with pytest.raises(ProcessError, match="shut down"):
        manager.start([sys.executable, "--version"])


def test_concurrent_starts_allow_only_one_process():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    manager = ProcessManager()
    barrier = Barrier(2)

    def start_process():
        barrier.wait(timeout=2)
        try:
            return manager.start([sys.executable, "-c", "import time; time.sleep(1)"])
        except ProcessError:
            return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: start_process(), range(2)))

        successful = [pid for pid in results if pid is not None]
        assert len(successful) == 1
        assert manager.pid == successful[0]
    finally:
        manager.terminate()


def test_concurrent_wait_and_terminate():
    from threading import Event, Thread

    manager = ProcessManager()
    manager.start(
        [
            sys.executable,
            "-c",
            "import time; print('ready', flush=True); time.sleep(30)",
        ]
    )

    wait_started = Event()
    wait_errors = []

    def wait_for_process():
        wait_started.set()
        try:
            manager.wait()
        except Exception as exc:
            wait_errors.append(exc)

    waiter = Thread(target=wait_for_process)
    waiter.start()

    try:
        assert wait_started.wait(timeout=2)
        manager.terminate()
        waiter.join(timeout=5)

        assert not waiter.is_alive(), "wait() did not finish after termination"
        assert wait_errors == []
    finally:
        manager.terminate()
        waiter.join(timeout=2)
