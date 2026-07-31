import pytest

from sentinel.plugins.exceptions import (
    PluginDisableError,
    PluginEnableError,
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    PluginRegistrationError,
    PluginUnloadError,
)


def test_plugin_error():
    with pytest.raises(PluginError):
        raise PluginError("plugin")


def test_registration_error():
    with pytest.raises(PluginRegistrationError):
        raise PluginRegistrationError("register")


def test_load_error():
    with pytest.raises(PluginLoadError):
        raise PluginLoadError("load")


def test_unload_error():
    with pytest.raises(PluginUnloadError):
        raise PluginUnloadError("unload")


def test_enable_error():
    with pytest.raises(PluginEnableError):
        raise PluginEnableError("enable")


def test_disable_error():
    with pytest.raises(PluginDisableError):
        raise PluginDisableError("disable")


def test_not_found_error():
    with pytest.raises(PluginNotFoundError):
        raise PluginNotFoundError("missing")


def test_inheritance():
    assert issubclass(PluginRegistrationError, PluginError)
    assert issubclass(PluginLoadError, PluginError)
    assert issubclass(PluginUnloadError, PluginError)
    assert issubclass(PluginEnableError, PluginError)
    assert issubclass(PluginDisableError, PluginError)
    assert issubclass(PluginNotFoundError, PluginError)