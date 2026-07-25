from typing import Dict

from sentinel.kernel.service import Service


class ServiceRegistry:
    """
    Stores every running service.
    """

    def __init__(self):
        self._services: Dict[str, Service] = {}

    def register(self, service: Service):
        self._services[service.name] = service

    def get(self, name: str):
        return self._services.get(name)

    def all(self):
        return self._services.values()