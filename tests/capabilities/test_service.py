from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.capabilities.service import CapabilityService
from sentinel.security.constants import Permission, Role
from sentinel.security.credentials import SecurityCredentials
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


def authorized_service():
    security = SecurityManager()
    identity = SecurityIdentity("service-test", "Service Test", {Role.ADMIN})
    security.register_identity(
        identity,
        SecurityCredentials("service-test", "test-password"),
    )
    security.grant(Role.ADMIN, Permission.EXECUTE)
    return CapabilityService(security=security, identity=identity)


class EchoCapability(BaseCapability):

    def __init__(self):
        super().__init__(
            CapabilityMetadata(
                capability_id="echo",
                name="Echo",
                description="Echo capability",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(self, **kwargs):
        return kwargs


def test_register():
    service = CapabilityService()

    service.register(EchoCapability())

    assert service.exists("echo")


def test_execute():
    service = authorized_service()

    service.register(EchoCapability())

    result = service.execute(
        "echo",
        message="hello",
    )

    assert result["message"] == "hello"


def test_unregister():
    service = CapabilityService()

    service.register(EchoCapability())

    service.unregister("echo")

    assert service.exists("echo") is False


def test_list():
    service = CapabilityService()

    service.register(EchoCapability())

    assert len(service.list()) == 1


def test_clear():
    service = CapabilityService()

    service.register(EchoCapability())

    service.clear()

    assert len(service.list()) == 0

def test_service_does_not_expose_internal_manager_or_registry() -> None:
    service = CapabilityService()

    assert not hasattr(service, "manager")
    assert not hasattr(service, "registry")



def test_execute_requires_identity() -> None:
    service = CapabilityService()
    service.register(EchoCapability())

    import pytest

    with pytest.raises(PermissionError, match="authenticated identity"):
        service.execute("echo", message="blocked")


def test_execute_rejects_unregistered_identity() -> None:
    security = SecurityManager()
    identity = SecurityIdentity("unregistered", "Unregistered", {Role.ADMIN})
    security.grant(Role.ADMIN, Permission.EXECUTE)
    service = CapabilityService(security=security, identity=identity)
    service.register(EchoCapability())

    import pytest

    with pytest.raises(PermissionError, match="not authorized"):
        service.execute("echo", message="blocked")


def test_execute_rejects_identity_without_execute_permission() -> None:
    security = SecurityManager()
    identity = SecurityIdentity("read-only", "Read Only", {Role.USER})
    security.register_identity(
        identity,
        SecurityCredentials("read-only", "test-password"),
    )
    service = CapabilityService(security=security, identity=identity)
    service.register(EchoCapability())

    import pytest

    with pytest.raises(PermissionError, match="not authorized"):
        service.execute("echo", message="blocked")


def _assert_execution_rejected_after_security_change(change_security) -> None:
    from threading import Event, Thread

    security = SecurityManager()
    identity = SecurityIdentity("race-test", "Race Test", {Role.ADMIN})
    credentials = SecurityCredentials("race-test", "test-password")

    security.register_identity(identity, credentials)
    security.grant(Role.ADMIN, Permission.EXECUTE)

    service = CapabilityService(security=security, identity=identity)
    service.register(EchoCapability())

    admission_checkpoint = Event()
    continue_admission = Event()
    results = []
    errors = []

    original_authorize_and_admit = security.authorize_and_admit

    def pause_before_admission(identity_arg, permission, admission):
        admission_checkpoint.set()
        if not continue_admission.wait(timeout=10):
            raise TimeoutError("Test did not release authorization admission.")
        return original_authorize_and_admit(identity_arg, permission, admission)

    security.authorize_and_admit = pause_before_admission

    def execute():
        try:
            results.append(service.execute("echo", message="must be blocked"))
        except Exception as exc:
            errors.append(exc)

    thread = Thread(target=execute)
    thread.start()

    try:
        assert admission_checkpoint.wait(timeout=10), (
            "Execution did not reach the atomic admission checkpoint."
        )
        change_security(security, identity, credentials)
    finally:
        continue_admission.set()
        thread.join(timeout=10)

    assert not thread.is_alive(), "Execution thread did not finish."
    assert results == [], f"Capability unexpectedly executed: {results!r}"
    assert len(errors) == 1
    assert isinstance(errors[0], PermissionError), repr(errors[0])


def test_execute_rejects_permission_revoked_before_admission() -> None:
    def revoke(security, _identity, _credentials):
        security.revoke(Role.ADMIN, Permission.EXECUTE)

    _assert_execution_rejected_after_security_change(revoke)


def test_execute_rejects_identity_unregistered_before_admission() -> None:
    def unregister(security, identity, credentials):
        security.unregister_identity(identity.id, credentials.username)

    _assert_execution_rejected_after_security_change(unregister)


def _assert_admitted_execution_finishes_after_security_change(change_security) -> None:
    from threading import Event, Thread

    import pytest

    security = SecurityManager()
    identity = SecurityIdentity("admitted-test", "Admitted Test", {Role.ADMIN})
    credentials = SecurityCredentials("admitted-test", "test-password")

    security.register_identity(identity, credentials)
    security.grant(Role.ADMIN, Permission.EXECUTE)

    execution_started = Event()
    release_execution = Event()

    class BlockingCapability(EchoCapability):
        def run(self, **kwargs):
            execution_started.set()
            if not release_execution.wait(timeout=10):
                raise TimeoutError("Test did not release admitted execution.")
            return kwargs

    service = CapabilityService(security=security, identity=identity)
    service.register(BlockingCapability())

    results = []
    errors = []

    def execute():
        try:
            results.append(service.execute("echo", message="admitted"))
        except Exception as exc:
            errors.append(exc)

    thread = Thread(target=execute)
    thread.start()

    try:
        assert execution_started.wait(timeout=10), (
            "Capability execution did not start after admission."
        )

        change_security(security, identity, credentials)

        with pytest.raises(PermissionError, match="not authorized"):
            service.execute("echo", message="new attempt")

    finally:
        release_execution.set()
        thread.join(timeout=10)

    assert not thread.is_alive(), "Admitted execution thread did not finish."
    assert errors == [], f"Admitted execution unexpectedly failed: {errors!r}"
    assert results == [{"message": "admitted"}]


def test_admitted_execution_finishes_after_permission_revocation() -> None:
    def revoke(security, _identity, _credentials):
        security.revoke(Role.ADMIN, Permission.EXECUTE)

    _assert_admitted_execution_finishes_after_security_change(revoke)


def test_admitted_execution_finishes_after_identity_unregistration() -> None:
    def unregister(security, identity, credentials):
        security.unregister_identity(identity.id, credentials.username)

    _assert_admitted_execution_finishes_after_security_change(unregister)
