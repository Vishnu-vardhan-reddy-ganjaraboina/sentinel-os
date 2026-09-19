from __future__ import annotations

import pytest

from sentinel.boot import BootConfiguration
from sentinel.boot.system_factory import SystemFactory
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel
from sentinel.platform import Platform
from sentinel.system import System
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.service import ControlPlane


def test_default_factory() -> None:
    factory = SystemFactory()

    assert factory.configuration is None

    with pytest.raises(
        RuntimeError,
        match="not been composed",
    ):
        factory.system

    with pytest.raises(
        RuntimeError,
        match="not been composed",
    ):
        factory.bootstrap


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(TypeError):
        SystemFactory(object())  # type: ignore[arg-type]


def test_create_returns_stopped_system() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert isinstance(system, System)
    assert isinstance(system.kernel, Kernel)
    assert isinstance(system.platform, Platform)
    assert isinstance(factory.bootstrap, Bootstrap)

    assert system.running is False


def test_create_does_not_start_kernel() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.kernel.health()["healthy"] is False
    assert system.running is False


def test_create_preserves_configuration() -> None:
    configuration = BootConfiguration()

    factory = SystemFactory(configuration)

    assert factory.configuration is configuration


def test_create_from_yaml_configuration() -> None:
    configuration = BootConfiguration()
    configuration.load("configs/development.yaml")

    factory = SystemFactory(configuration)
    system = factory.create()

    assert isinstance(system, System)
    assert system.running is False
    assert factory.bootstrap is not None


def test_create_cannot_be_called_twice() -> None:
    factory = SystemFactory()

    first = factory.create()

    assert isinstance(first, System)

    with pytest.raises(
        RuntimeError,
        match="already been composed",
    ):
        factory.create()


def test_composed_properties_return_same_instances() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert factory.system is system
    assert factory.bootstrap is not None


def test_created_system_can_be_started_and_shutdown() -> None:
    factory = SystemFactory()

    system = factory.create()

    system.start()

    assert system.running is True

    system.shutdown()

    assert system.running is False


def test_repr_before_composition() -> None:
    factory = SystemFactory()

    assert repr(factory) == "SystemFactory(composed=False)"


def test_repr_after_composition() -> None:
    factory = SystemFactory()

    factory.create()

    assert repr(factory) == "SystemFactory(composed=True)"

def test_create_registers_runtime_services_in_kernel() -> None:
    factory = SystemFactory()

    system = factory.create()

    services = system.kernel.services()

    assert {service.name for service in services} == {
        "execution",
        "memory",
        "knowledge",
        "orchestration",
    }

def test_created_system_can_control_individual_kernel_services() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    assert system.kernel.running("memory")
    assert system.kernel.running("knowledge")
    assert system.kernel.running("execution")
    assert system.kernel.running("orchestration")

    system.kernel.stop("orchestration")

    assert not system.kernel.running("orchestration")
    assert system.kernel.running("memory")
    assert system.kernel.running("knowledge")
    assert system.kernel.running("execution")

    system.kernel.start("orchestration")

    assert system.kernel.running("orchestration")

    system.shutdown()

def test_created_system_preserves_orchestration_dependencies() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    system.kernel.stop("orchestration")

    system.kernel.stop("memory")

    assert not system.kernel.running("memory")
    assert not system.kernel.running("orchestration")
    assert system.kernel.running("knowledge")

    system.kernel.start("orchestration")

    assert system.kernel.running("memory")
    assert system.kernel.running("knowledge")
    assert system.kernel.running("orchestration")

    system.shutdown()

def test_created_system_restart_orchestration_preserves_dependencies() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    memory = system.kernel.get("memory")
    knowledge = system.kernel.get("knowledge")

    system.kernel.restart("orchestration")

    assert system.kernel.get("memory") is memory
    assert system.kernel.get("knowledge") is knowledge
    assert system.kernel.running("memory")
    assert system.kernel.running("knowledge")
    assert system.kernel.running("orchestration")

    system.shutdown()

def test_system_shutdown_after_individual_kernel_service_stop() -> None:
    factory = SystemFactory()
    system = factory.create()

    system.start()

    system.kernel.stop("orchestration")

    system.shutdown()

    assert system.running is False

def test_create_composes_control_plane() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert isinstance(system.control_plane, ControlPlane)

def test_control_plane_targets_system_kernel() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.control_plane is not None
    assert system.control_plane.controller.target.kernel is system.kernel

def test_control_plane_uses_system_context() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.control_plane is not None
    assert system.control_plane.context.caller_id == "system"
    assert system.control_plane.context.caller_type == "system"

def test_control_plane_can_query_kernel() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.control_plane is not None

    result = system.control_plane.execute(
        KernelCommand.SERVICE_LIST,
    )

    assert result.success is True
    assert set(result.data["services"]) == {
        "execution",
        "memory",
        "knowledge",
        "orchestration",
    }
def test_control_plane_composition_does_not_start_kernel() -> None:
    factory = SystemFactory()

    system = factory.create()

    assert system.running is False
    assert system.kernel.health()["healthy"] is False