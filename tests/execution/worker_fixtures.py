"""Importable functions used by isolated-worker tests."""

from __future__ import annotations

import subprocess
import sys
import time

print("fixture-import-noise")


def add(a: int, b: int) -> int:
    return a + b


def emit_and_return(value: str) -> str:
    print("worker-output")
    print("worker-error", file=sys.stderr)
    return value


def sleep_for(seconds: float) -> str:
    time.sleep(seconds)
    return "finished"


def spawn_child_and_sleep(seconds: float) -> int:
    child = subprocess.Popen(
        [sys.executable, "-S", "-c", "import time; time.sleep(60)"]
    )
    time.sleep(seconds)
    return child.pid


def write_large_file(path: str, size: int) -> None:
    with open(path, "wb") as stream:
        stream.write(b"x" * size)



def plugin_hook(plugin_name: str) -> bool:
    return bool(plugin_name)



def spawn_child_and_record_pid(pid_file: str, seconds: float) -> None:
    child = subprocess.Popen(
        [sys.executable, "-S", "-c", "import time; time.sleep(60)"]
    )
    with open(pid_file, "w", encoding="ascii") as stream:
        stream.write(str(child.pid))
    time.sleep(seconds)


def large_result(size: int) -> str:
    return "x" * size



def current_resource_limits() -> dict[str, tuple[int, int]]:
    import resource

    return {
        "cpu": resource.getrlimit(resource.RLIMIT_CPU),
        "memory": resource.getrlimit(resource.RLIMIT_AS),
        "file_size": resource.getrlimit(resource.RLIMIT_FSIZE),
        "open_files": resource.getrlimit(resource.RLIMIT_NOFILE),
    }



def spawn_child_then_return(pid_file: str) -> str:
    child = subprocess.Popen(
        [sys.executable, "-S", "-c", "import time; time.sleep(60)"]
    )
    with open(pid_file, "w", encoding="ascii") as stream:
        stream.write(str(child.pid))
    return "parent-returned"
