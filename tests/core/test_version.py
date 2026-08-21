from sentinel.core.version import (
    VERSION,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
)


def test_version() -> None:
    assert VERSION == "0.1.0"


def test_version_components() -> None:
    assert VERSION_MAJOR == 0
    assert VERSION_MINOR == 1
    assert VERSION_PATCH == 0