from __future__ import annotations
from pathlib import Path

import pytest

from sentinel.boot import BootConfiguration
from sentinel.boot.system_factory import SystemFactory
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.service import ControlPlane
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.kernel.kernel import Kernel
from sentinel.platform import Platform
from sentinel.system import System


def test_default_factory() -> None:
    factory = SystemFactory()

    assert factory.configuration is None

    with pytest.raises(
        RuntimeError,
        match="not been composed",
    ):
        _ = factory.system

    with pytest.raises(
        RuntimeError,
        match="not been composed",
    ):
        _ = factory.bootstrap


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
import ssl

from sentinel.infrastructure.configuration import Configuration
from sentinel.control_plane.commands import KernelCommand
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.request import ControlRequest
from sentinel.control_plane.transport_client import ControlPlaneTransportClient
from sentinel.control_plane.security_authorizer import SecurityControlAuthorizer
from sentinel.security.service import SecurityService
from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity


def test_factory_configures_tls_transport_from_configuration() -> None:
    cert_path = (
        Path(__file__).resolve().parent
        / "certs"
        / "transport-test-cert.pem"
    )
    key_path = (
        Path(__file__).resolve().parent
        / "certs"
        / "transport-test-key.pem"
    )

    configuration = BootConfiguration(
        Configuration.from_dict(
            {
                "control_plane": {
                    "tls": {
                        "enabled": True,
                        "certfile": str(cert_path),
                        "keyfile": str(key_path),
                    },
                },
            }
        )
    )

    system = SystemFactory(configuration).create()
    system.start()

    try:
        assert system.control_transport is not None

        client_context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH,
            cafile=str(cert_path),
        )

        client = ControlPlaneTransportClient(
            host=system.control_transport.host,
            port=system.control_transport.port,
            ssl_context=client_context,
        )

        result = client.execute(
            ControlRequest(
                command=KernelCommand.SYSTEM_HEALTH,
                context=ControlContext(
                    caller_id="system",
                    caller_type="system",
                ),
            )
        )

        assert result.success is True
    finally:
        system.shutdown()
def test_factory_uses_injected_security_service_with_tls() -> None:
    cert_dir = Path(__file__).resolve().parent / "certs"
    cert_path = cert_dir / "transport-test-cert.pem"
    key_path = cert_dir / "transport-test-key.pem"

    configuration = BootConfiguration(
        Configuration.from_dict(
            {
                "control_plane": {
                    "tls": {
                        "enabled": True,
                        "certfile": str(cert_path),
                        "keyfile": str(key_path),
                    },
                },
            }
        )
    )
    security = SecurityService()

    factory = SystemFactory(
        configuration,
        security_service=security,
    )
    system = factory.create()

    assert system.control_plane is not None
    authorizer = system.control_plane.controller.authorizer
    assert isinstance(authorizer, SecurityControlAuthorizer)
    assert authorizer.security is security


def test_factory_rejects_security_service_without_tls() -> None:
    factory = SystemFactory(
        security_service=SecurityService(),
    )

    with pytest.raises(ValueError, match="TLS"):
        factory.create()

def test_factory_security_authorizes_authenticated_identity_end_to_end() -> None:
    cert_dir = Path(__file__).resolve().parent / "certs"
    cert_path = cert_dir / "transport-test-cert.pem"
    key_path = cert_dir / "transport-test-key.pem"

    configuration = BootConfiguration(
        Configuration.from_dict(
            {
                "control_plane": {
                    "tls": {
                        "enabled": True,
                        "certfile": str(cert_path),
                        "keyfile": str(key_path),
                    },
                },
            }
        )
    )

    security = SecurityService()
    security.grant(Role.ADMIN, [Permission.READ, Permission.EXECUTE])
    security.grant(Role.USER, [Permission.READ])

    security.register_identity(
        SecurityIdentity("admin-client", "Admin Client", {Role.ADMIN}),
        SecurityCredentials("admin", "admin-secret"),
    )
    security.register_identity(
        SecurityIdentity("read-client", "Read Client", {Role.USER}),
        SecurityCredentials("read-client", "read-secret"),
    )

    system = SystemFactory(
        configuration,
        security_service=security,
    ).create()

    system.start()

    try:
        assert system.control_transport is not None

        client_context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH,
            cafile=str(cert_path),
        )

        read_client = ControlPlaneTransportClient(
            host=system.control_transport.host,
            port=system.control_transport.port,
            ssl_context=client_context,
            credentials=SecurityCredentials(
                "read-client",
                "read-secret",
            ),
        )

        health_result = read_client.execute(
            ControlRequest(
                command=KernelCommand.SYSTEM_HEALTH,
                context=ControlContext(
                    caller_id="read-client",
                    caller_type="api",
                ),
            )
        )

        assert health_result.success is True
        assert health_result.data["healthy"] is True

        spoofed_control_result = read_client.execute(
            ControlRequest(
                command=KernelCommand.SERVICE_START,
                context=ControlContext(
                    caller_id="admin-client",
                    caller_type="system",
                ),
                data={"service": "orchestration"},
            )
        )

        assert spoofed_control_result.success is False
        assert spoofed_control_result.error is not None

    finally:
        system.shutdown()
