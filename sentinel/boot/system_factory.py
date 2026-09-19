"""
Factory for composing the Sentinel OS system from boot configuration.
"""

from __future__ import annotations

from sentinel.application import Application
from sentinel.boot.configuration import BootConfiguration
from sentinel.control_plane.adapter import KernelAdapter
from sentinel.control_plane.authorizer import ControlAuthorizer
from sentinel.control_plane.context import ControlContext
from sentinel.control_plane.controller import KernelController
from sentinel.control_plane.permissions import ControlPermission
from sentinel.control_plane.service import ControlPlane
from sentinel.infrastructure.configuration import Configuration
from sentinel.kernel.bootstrap import Bootstrap
from sentinel.platform import Platform
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
    ) -> None:
        if configuration is not None and not isinstance(
            configuration,
            BootConfiguration,
        ):
            raise TypeError(
                "configuration must be a BootConfiguration instance."
            )

        self._configuration = configuration
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

        The system is not started by this method.
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

        application = Application(
            configuration=infrastructure_configuration,
        )

        bootstrap = application.bootstrap
        kernel = bootstrap.create_kernel()
        platform = application.platform

        adapter = KernelAdapter(kernel)

        authorizer = ControlAuthorizer(
            permissions={
                ControlPermission.READ,
                ControlPermission.CONTROL,
           }
        )

        controller = KernelController(
            target=adapter,
            authorizer=authorizer,
            context=ControlContext(
                caller_id="system",
                caller_type="system",
           ),
        )

        control_plane = ControlPlane(controller)

        system = System(
            kernel=kernel,
            platform=platform,
            control_plane=control_plane,
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
