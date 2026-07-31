import pytest

from sentinel.kernel.dependency_resolver import DependencyResolver
from sentinel.kernel.exceptions import (
    CircularDependencyError,
    DependencyNotFoundError,
)
from sentinel.kernel.service import Service


class Dummy(Service):
    def __init__(self, name, deps=()):
        super().__init__(name, deps)

    def initialize(self):
        pass

    def shutdown(self):
        pass


def test_simple_dependency():
    logger = Dummy("logger")
    db = Dummy("db", ("logger",))
    app = Dummy("app", ("db",))

    order = DependencyResolver().resolve(
        [app, logger, db]
    )

    assert [s.name for s in order] == [
        "logger",
        "db",
        "app",
    ]


def test_missing_dependency():
    app = Dummy("app", ("database",))

    with pytest.raises(DependencyNotFoundError):
        DependencyResolver().resolve([app])


def test_cycle():
    a = Dummy("A", ("B",))
    b = Dummy("B", ("A",))

    with pytest.raises(CircularDependencyError):
        DependencyResolver().resolve([a, b])