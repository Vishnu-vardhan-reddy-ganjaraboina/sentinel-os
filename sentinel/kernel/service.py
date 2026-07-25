from abc import ABC, abstractmethod


class Service(ABC):
    """
    Base class for every Sentinel service.
    """

    def __init__(self, name: str):
        self.name = name
        self.running = False

    @abstractmethod
    def start(self):
        """Start the service."""

    @abstractmethod
    def stop(self):
        """Stop the service."""

    def status(self):
        return "Running" if self.running else "Stopped"