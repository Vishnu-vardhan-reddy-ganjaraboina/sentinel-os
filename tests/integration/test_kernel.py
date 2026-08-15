from sentinel.kernel.kernel import Kernel
from sentinel.kernel.service import Service


class Dummy(Service):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


def test_register() -> None:
    kernel = Kernel()

    service = Dummy("logger")

    kernel.register(service)

    assert kernel.get("logger") is service


def test_boot_shutdown() -> None:
    kernel = Kernel()

    service = Dummy("logger")

    kernel.register(service)

    kernel.boot()

    assert kernel.running("logger")

    kernel.shutdown()

    assert not kernel.running("logger")