"""
Factory for composing the Sentinel OS system from boot configuration.
"""

from __future__ import annotations

import ssl

from sentinel.application import Application
from sentinel.boot.configuration import BootConfiguration
from sentinel.control_plane.adapter import KernelAdapter
from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.endpoint_registry import (
    ControlPlaneEndpointRegistry,
)
from sentinel.control_plane.service import ControlPlane
from sentinel.control_plane.security_authorizer import SecurityControlAuthorizer
from sentinel.security.service import SecurityService
from sentinel.control_plane.transport_server import (
    ControlPlaneTransportServer,
)
from sentinel.infrastructure.configuration import Configuration
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.system import System


class SystemFactory:
    """
    Compose the top-level Sentinel System without starting it.

    Composition responsibilities belong here. Lifecycle remains owned by
    Bootstrap, System, and BootManager respectively.
    """

    def __init__(
        self,
        configuration: BootConfiguration | None = None,
        *,
        security_service: SecurityService | None = None,
    ) -> None:
        if configuration is not None and not isinstance(
            configuration,
            BootConfiguration,
        ):
            raise TypeError(
                "configuration must be a BootConfiguration instance."
            )

        if security_service is not None and not isinstance(
            security_service,
            SecurityService,
        ):
            raise TypeError(
                "security_service must be a SecurityService instance."
            )

        self._configuration = configuration
        self._security_service = security_service
        self._bootstrap: Bootstrap | None = None
        self._system: System | None = None

    @property
    def configuration(self) -> BootConfiguration | None:
        """Return the boot configuration."""
        return self._configuration

    @property
    def bootstrap(self) -> Bootstrap:
        """
        Return the composed Bootstrap.

        Raises:
            RuntimeError:
                If composition has not been performed yet.
        """
        if self._bootstrap is None:
            raise RuntimeError(
                "System has not been composed."
            )

        return self._bootstrap

    @property
    def system(self) -> System:
        """
        Return the composed System.

        Raises:
            RuntimeError:
                If composition has not been performed yet.
        """
        if self._system is None:
            raise RuntimeError(
                "System has not been composed."
            )

        return self._system

    def create(self) -> System:
        """
        Compose and return a new Sentinel System.

        The system and its Control Plane transport are not started
        by this method.
        """
        if self._system is not None:
            raise RuntimeError(
                "System has already been composed."
            )

        infrastructure_configuration: Configuration | None = None

        if self._configuration is not None:
            infrastructure_configuration = (
                self._configuration.configuration
            )
            infrastructure_configuration.validate()

        authentication_enabled = False
        if infrastructure_configuration is not None:
            authentication_enabled = infrastructure_configuration.get(
                "control_plane.authentication.enabled",
                False,
            )
            if not isinstance(authentication_enabled, bool):
                raise ValueError(
                    "control_plane.authentication.enabled must be a Boolean."
                )

            if authentication_enabled:
                tls_enabled = infrastructure_configuration.get(
                    "control_plane.tls.enabled",
                    False,
                )
                if not tls_enabled:
                    raise RuntimeError(
                        "Production authentication requires Control Plane TLS."
                    )
                if self._security_service is None:
                    raise RuntimeError(
                        "Control Plane authentication is enabled, but no "
                        "SecurityService was provided."
                    )

        ssl_context: ssl.SSLContext | None = None
        if infrastructure_configuration is not None:
            tls_enabled = infrastructure_configuration.get(
                "control_plane.tls.enabled",
                False,
            )
            if tls_enabled:
                certfile = infrastructure_configuration.get(
                    "control_plane.tls.certfile",
                )
                keyfile = infrastructure_configuration.get(
                    "control_plane.tls.keyfile",
                )
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(
                    certfile=certfile,
                    keyfile=keyfile,
                )

        application = Application(
            configuration=infrastructure_configuration,
        )

        bootstrap = application.bootstrap
        kernel = bootstrap.create_kernel()
        platform = application.platform

        adapter = KernelAdapter(kernel)

        context = ControlContext(
            caller_id="system",
            caller_type="system",
        )

        if self._security_service is not None:
            authorizer = SecurityControlAuthorizer(
                self._security_service,
            )
            use_caller_policy = False
        else:
            authorizer = ControlAuthorizer.from_context(
                context,
            )
            use_caller_policy = True

        controller = KernelController(
            target=adapter,
            authorizer=authorizer,
            context=context,
            use_caller_policy=use_caller_policy,
        )

        control_plane = ControlPlane(
            controller,
        )

        control_transport = ControlPlaneTransportServer(
            control_plane=control_plane,
            host="127.0.0.1",
            port=0,
            ssl_context=ssl_context,
        )

        endpoint_registry = ControlPlaneEndpointRegistry()

        system = System(
            kernel=kernel,
            platform=platform,
            control_plane=control_plane,
            control_transport=control_transport,
            endpoint_registry=endpoint_registry,
        )

        self._bootstrap = bootstrap
        self._system = system

        return system

    def __repr__(self) -> str:
        return (
            "SystemFactory("
            f"composed={self._system is not None}"
            ")"
        )