from sentinel.capabilities.constants import (
    DEFAULT_CAPABILITY_VERSION,
    CapabilityCategory,
    CapabilityStatus,
)


def test_default_version():
    assert DEFAULT_CAPABILITY_VERSION == "1.0.0"


def test_categories():
    assert CapabilityCategory.FILESYSTEM.value == "filesystem"
    assert CapabilityCategory.AI.value == "ai"
    assert CapabilityCategory.CUSTOM.value == "custom"


def test_status():
    assert CapabilityStatus.ENABLED.value == "enabled"
    assert CapabilityStatus.DISABLED.value == "disabled"