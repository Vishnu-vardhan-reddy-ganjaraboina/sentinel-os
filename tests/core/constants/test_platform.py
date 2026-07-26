from sentinel.core.constants import (
    DEFAULT_ENCODING,
    DEVELOPMENT,
    PROJECT_DISPLAY_NAME,
    PROJECT_NAME,
    SUPPORTED_ENVIRONMENTS,
)


def test_project_name() -> None:
    assert PROJECT_NAME == "sentinel"


def test_display_name() -> None:
    assert PROJECT_DISPLAY_NAME == "Sentinel OS"


def test_encoding() -> None:
    assert DEFAULT_ENCODING == "utf-8"


def test_environment_exists() -> None:
    assert DEVELOPMENT in SUPPORTED_ENVIRONMENTS