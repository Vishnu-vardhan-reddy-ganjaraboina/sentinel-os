from __future__ import annotations

from sentinel.control_plane.adapter import KernelAdapter
from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service
from sentinel.kernel.service_state import ServiceState


class StubService(Service):
    def __init__(
        self,
        name: str,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self._name = name
        self._dependencies = dependencies
        self.initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> tuple[str, ...]:
        return self._dependencies

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False

    def health(self) -> dict[str, bool]:
        return {"healthy": self.initialized}


def test_service_names_returns_registered_services() -> None:
    kernel = Kernel()
    kernel.register(StubService("memory"))
    kernel.register(StubService("execution"))

    adapter = KernelAdapter(kernel)

    assert adapter.service_names() == ("memory", "execution")


def test_service_state_returns_kernel_state() -> None:
    kernel = Kernel()
    service = StubService("memory")
    kernel.register(service)

    adapter = KernelAdapter(kernel)

    assert adapter.service_state("memory") == ServiceState.CREATED

    kernel.start("memory")

    assert adapter.service_state("memory") == ServiceState.RUNNING


def test_start_service_delegates_to_kernel() -> None:
    kernel = Kernel()
    service = StubService("memory")
    kernel.register(service)

    adapter = KernelAdapter(kernel)

    adapter.start_service("memory")

    assert service.initialized is True
    assert kernel.running("memory") is True


def test_stop_service_delegates_to_kernel() -> None:
    kernel = Kernel()
    service = StubService("memory")
    kernel.register(service)

    adapter = KernelAdapter(kernel)

    adapter.start_service("memory")
    adapter.stop_service("memory")

    assert service.initialized is False
    assert kernel.state("memory") == ServiceState.STOPPED


def test_restart_service_delegates_to_kernel() -> None:
    kernel = Kernel()
    service = StubService("memory")
    kernel.register(service)

    adapter = KernelAdapter(kernel)

    adapter.start_service("memory")
    adapter.restart_service("memory")

    assert service.initialized is True
    assert kernel.state("memory") == ServiceState.RUNNING


def test_health_delegates_to_kernel() -> None:
    kernel = Kernel()
    service = StubService("memory")
    kernel.register(service)

    adapter = KernelAdapter(kernel)

    kernel.start("memory")

    assert adapter.health() == {
        "healthy": True,
        "services": {
            "memory": {
                "healthy": True,
            },
        },
    }