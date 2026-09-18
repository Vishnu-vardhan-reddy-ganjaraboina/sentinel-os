from __future__ import annotations

from threading import Event, RLock, Thread
from typing import Callable

from sentinel.process import ProcessHost


class SupervisorMonitor:
    """
    Monitor a Sentinel ProcessHost in a background thread.

    The monitor observes process state only. Recovery decisions remain
    the responsibility of the Supervisor.
    """

    def __init__(
        self,
        process: ProcessHost,
        *,
        interval: float = 1.0,
        on_failure: Callable[[], None] | None = None,
    ) -> None:
        if not isinstance(process, ProcessHost):
            raise TypeError(
                "process must be a ProcessHost instance."
            )

        if not isinstance(interval, (int, float)):
            raise TypeError(
                "interval must be a number."
            )

        if interval <= 0:
            raise ValueError(
                "interval must be greater than zero."
            )

        if on_failure is not None and not callable(on_failure):
            raise TypeError(
                "on_failure must be callable or None."
            )

        self._process = process
        self._interval = float(interval)
        self._on_failure = on_failure

        self._stop_event = Event()
        self._thread: Thread | None = None
        self._failure_detected = False
        self._lock = RLock()

    @property
    def process(self) -> ProcessHost:
        """Return the monitored ProcessHost."""
        return self._process

    @property
    def interval(self) -> float:
        """Return the monitoring interval."""
        return self._interval

    @property
    def running(self) -> bool:
        """Return whether the monitor thread is running."""
        with self._lock:
            return (
                self._thread is not None
                and self._thread.is_alive()
            )

    @property
    def failure_detected(self) -> bool:
        """Return whether an unexpected process failure was detected."""
        with self._lock:
            return self._failure_detected

    def start(self) -> None:
        """Start monitoring the process."""
        with self._lock:
            if self.running:
                return

            self._stop_event.clear()
            self._failure_detected = False

            thread = Thread(
                target=self._run,
                name="sentinel-supervisor-monitor",
                daemon=True,
            )

            self._thread = thread
            thread.start()

    def stop(self, timeout: float | None = None) -> None:
        """Stop the monitoring thread."""
        if timeout is not None:
            if not isinstance(timeout, (int, float)):
                raise TypeError(
                    "timeout must be a number or None."
                )

            if timeout < 0:
                raise ValueError(
                    "timeout cannot be negative."
                )

        with self._lock:
            thread = self._thread
            self._stop_event.set()

        if thread is not None:
            thread.join(timeout)

        with self._lock:
            if thread is self._thread and (
                thread is None or not thread.is_alive()
            ):
                self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            if self._process.running:
                continue

            with self._lock:
                if self._stop_event.is_set():
                    return

                self._failure_detected = True

            if self._on_failure is not None:
                self._on_failure()

            return
