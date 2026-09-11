"""
Application registry for Sentinel OS.
"""

from __future__ import annotations

from threading import RLock

from sentinel.application import Application


class ApplicationRegistry:
    """
    Thread-safe registry for Sentinel applications.

    The registry manages application identity and lookup only.
    Application lifecycle remains owned by Application itself.
    """

    def __init__(self) -> None:
        self._applications: dict[str, Application] = {}
        self._lock = RLock()

    def register(
        self,
        name: str,
        application: Application,
    ) -> None:
        """
        Register an application.

        Raises:
            TypeError:
                If name or application has an invalid type.
            ValueError:
                If name is empty or already registered.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")

        name = name.strip()

        if not name:
            raise ValueError("name must not be empty.")

        if not isinstance(application, Application):
            raise TypeError(
                "application must be an Application instance."
            )

        with self._lock:
            if name in self._applications:
                raise ValueError(
                    f"Application '{name}' is already registered."
                )

            self._applications[name] = application

    def unregister(
        self,
        name: str,
    ) -> Application:
        """
        Remove and return a registered application.

        Raises:
            TypeError:
                If name is not a string.
            ValueError:
                If name is empty.
            KeyError:
                If the application does not exist.
        """
        self._validate_name(name)

        with self._lock:
            try:
                return self._applications.pop(name)
            except KeyError:
                raise KeyError(
                    f"Application '{name}' is not registered."
                ) from None

    def get(
        self,
        name: str,
    ) -> Application:
        """
        Return a registered application.

        Raises:
            TypeError:
                If name is not a string.
            ValueError:
                If name is empty.
            KeyError:
                If the application does not exist.
        """
        self._validate_name(name)

        with self._lock:
            try:
                return self._applications[name]
            except KeyError:
                raise KeyError(
                    f"Application '{name}' is not registered."
                ) from None

    def all(self) -> tuple[Application, ...]:
        """Return a snapshot of all registered applications."""
        with self._lock:
            return tuple(self._applications.values())

    def names(self) -> tuple[str, ...]:
        """Return a snapshot of all registered application names."""
        with self._lock:
            return tuple(self._applications.keys())

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether an application is registered."""
        self._validate_name(name)

        with self._lock:
            return name in self._applications

    def clear(self) -> None:
        """Remove all registered applications."""
        with self._lock:
            self._applications.clear()

    def __len__(self) -> int:
        """Return the number of registered applications."""
        with self._lock:
            return len(self._applications)

    def __contains__(
        self,
        name: object,
    ) -> bool:
        """Return whether a valid string name is registered."""
        if not isinstance(name, str):
            return False

        name = name.strip()

        if not name:
            return False

        with self._lock:
            return name in self._applications

    def __repr__(self) -> str:
        """Return a useful registry representation."""
        with self._lock:
            return (
                f"ApplicationRegistry("
                f"applications={len(self._applications)})"
            )

    @staticmethod
    def _validate_name(name: str) -> str:
        """Validate and normalize an application name."""
        if not isinstance(name, str):
            raise TypeError("name must be a string.")

        name = name.strip()

        if not name:
            raise ValueError("name must not be empty.")

        return name