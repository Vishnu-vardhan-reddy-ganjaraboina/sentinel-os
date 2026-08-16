import pytest

from sentinel.brain.constants import PlanStatus
from sentinel.brain.manager import BrainManager
from sentinel.capabilities.capability import BaseCapability
from sentinel.capabilities.constants import CapabilityCategory
from sentinel.capabilities.manager import CapabilityManager
from sentinel.capabilities.metadata import CapabilityMetadata
from sentinel.orchestration.exceptions import (
    OrchestrationExecutionError,
    OrchestrationValidationError,
)
from sentinel.orchestration.manager import OrchestrationManager
from sentinel.orchestration.models import OrchestrationRequest
from sentinel.security.constants import Permission, Role
from sentinel.security.exceptions import AuthorizationError
from sentinel.security.identity import SecurityIdentity
from sentinel.security.manager import SecurityManager


class EchoCapability(BaseCapability):
    """Safe test capability for orchestration integration."""

    def __init__(self) -> None:
        super().__init__(
            CapabilityMetadata(
                capability_id="system.echo",
                name="System Echo",
                description="Returns the supplied message.",
                category=CapabilityCategory.CUSTOM,
            )
        )

    def run(
        self,
        **kwargs: object,
    ) -> dict[str, object]:
        return dict(kwargs)


def create_authorized_security() -> tuple[
    SecurityManager,
    SecurityIdentity,
]:
    """Create security configuration allowing capability execution."""
    security = SecurityManager()

    security.grant(
        Role.USER,
        [Permission.EXECUTE],
    )

    identity = SecurityIdentity(
        "user.1",
        "Test User",
        {Role.USER},
    )

    return security, identity


def test_handler_property() -> None:
    def handler(request: OrchestrationRequest) -> str:
        return str(request.input)

    manager = OrchestrationManager(handler)

    assert manager.handler is handler


def test_brain_property() -> None:
    brain = BrainManager()

    manager = OrchestrationManager(brain=brain)

    assert manager.brain is brain


def test_execute_with_handler() -> None:
    def handler(request: OrchestrationRequest) -> dict[str, object]:
        return {
            "input": request.input,
            "context": request.context,
        }

    manager = OrchestrationManager(handler)

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={"user": "Sentinel"},
    )

    result = manager.execute(request)

    assert result.request_id == "req.1"
    assert result.success is True
    assert result.data == {
        "input": "hello",
        "context": {"user": "Sentinel"},
    }
    assert result.error is None


def test_execute_with_brain() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={"user": "Sentinel"},
    )

    result = manager.execute(request)

    assert result.request_id == "req.1"
    assert result.success is True

    assert isinstance(result.data, dict)
    assert result.data["request"] == "hello"
    assert result.data["success"] is True

    plan = result.data["plan"]

    assert plan["context_id"] == "req.1"
    assert plan["status"] == PlanStatus.COMPLETED


def test_brain_receives_request_context() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
        context={
            "user": "Sentinel",
            "source": "integration",
        },
    )

    result = manager.execute(request)

    assert isinstance(result.data, dict)

    context = result.data["context"]

    assert context["id"] == "req.1"
    assert context["data"]["user"] == "Sentinel"
    assert context["data"]["source"] == "integration"


def test_execute_invalid_request_raises() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="   ",
        input="hello",
    )

    with pytest.raises(OrchestrationValidationError):
        manager.execute(request)


def test_can_execute() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    assert manager.can_execute(request) is True


def test_can_execute_invalid_request() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="",
        input="hello",
    )

    assert manager.can_execute(request) is False


def test_execute_handler_failure() -> None:
    def handler(request: OrchestrationRequest) -> str:
        raise RuntimeError("boom")

    manager = OrchestrationManager(handler)

    request = OrchestrationRequest(
        request_id="req.1",
        input="hello",
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)


def test_execute_capability_plan() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.echo",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    capability_results = result.data["capability_results"]

    assert len(capability_results) == 1

    execution = capability_results[0]

    assert execution["capability_id"] == "system.echo"
    assert execution["result"] == {
        "message": "hello",
    }


def test_execute_unknown_capability_fails() -> None:
    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.unknown",
        input="hello",
        context={
            "capability_id": "does.not.exist",
        },
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)


def test_execute_capability_with_permission() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.authorized",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    assert result.data["capability_results"][0]["result"] == {
        "message": "hello",
    }


def test_execute_capability_without_permission() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security = SecurityManager()

    identity = SecurityIdentity(
        "user.1",
        "Test User",
        {Role.USER},
    )

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.denied",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    with pytest.raises(AuthorizationError):
        manager.execute(request)


def test_execute_capability_without_identity() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    manager = OrchestrationManager(
        capabilities=capabilities,
    )

    request = OrchestrationRequest(
        request_id="req.no-identity",
        input="hello",
        context={
            "capability_id": "system.echo",
        },
    )

    with pytest.raises(AuthorizationError):
        manager.execute(request)

def test_successful_execution_is_stored_in_memory() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.memory",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    result = manager.execute(request)

    memory_id = "orchestration:req.memory"

    assert manager.memory.exists(memory_id) is True

    memory = manager.memory.get(memory_id)

    assert memory.content == result.to_dict()

def test_failed_execution_is_not_stored_in_memory() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security = SecurityManager()

    identity = SecurityIdentity(
        "user.1",
        "Test User",
        {Role.USER},
    )

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.memory.denied",
        input="hello",
        context={
            "capability_id": "system.echo",
            "capability_arguments": {
                "message": "hello",
            },
        },
    )

    with pytest.raises(AuthorizationError):
        manager.execute(request)

    memory_id = "orchestration:req.memory.denied"

    assert manager.memory.exists(memory_id) is False

def test_memory_is_available_to_brain_context() -> None:
    capabilities = CapabilityManager()
    capabilities.register(EchoCapability())

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    manager.memory.create(
        memory_id="memory.python",
        content="User prefers Python development.",
    )

    request = OrchestrationRequest(
        request_id="req.memory.context",
        input="Python",
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    context = result.data["context"]

    memories = context["memories"]

    assert len(memories) == 1
    assert memories[0]["id"] == "memory.python"
    assert memories[0]["content"] == (
        "User prefers Python development."
    )


def test_brain_context_contains_empty_memories_when_no_match() -> None:
    manager = OrchestrationManager()

    request = OrchestrationRequest(
        request_id="req.no.memory",
        input="something-that-does-not-exist",
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    context = result.data["context"]

    assert context["memories"] == []

def test_knowledge_is_available_to_brain_context() -> None:
    from sentinel.knowledge.chunker import FixedSizeChunker
    from sentinel.knowledge.document import Document
    from sentinel.knowledge.embeddings import DummyEmbeddingProvider
    from sentinel.knowledge.indexer import Indexer
    from sentinel.knowledge.knowledge_service import KnowledgeService
    from sentinel.knowledge.retriever import Retriever
    from sentinel.knowledge.vector_store import InMemoryVectorStore

    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    knowledge = KnowledgeService(
        indexer=Indexer(
            chunker=FixedSizeChunker(),
            embedding_provider=provider,
            vector_store=store,
        ),
        retriever=Retriever(
            embedding_provider=provider,
            vector_store=store,
        ),
    )

    knowledge.add_document(
        Document(
            id="knowledge.python",
            text="Python is used for Sentinel development.",
        )
    )

    manager = OrchestrationManager(
        knowledge=knowledge,
    )

    request = OrchestrationRequest(
        request_id="req.knowledge.context",
        input="Python",
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    context = result.data["context"]

    knowledge_context = context["knowledge"]

    assert len(knowledge_context) == 1
    assert knowledge_context[0]["id"] == "knowledge.python:0"
    assert knowledge_context[0]["document_id"] == "knowledge.python"
    assert knowledge_context[0]["text"] == (
        "Python is used for Sentinel development."
    )

    from sentinel.knowledge.chunker import FixedSizeChunker
    from sentinel.knowledge.document import Document
    from sentinel.knowledge.embeddings import DummyEmbeddingProvider
    from sentinel.knowledge.indexer import Indexer
    from sentinel.knowledge.knowledge_service import KnowledgeService
    from sentinel.knowledge.retriever import Retriever
    from sentinel.knowledge.vector_store import InMemoryVectorStore

    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    indexer = Indexer(
        chunker=FixedSizeChunker(),
        embedding_provider=provider,
        vector_store=store,
    )

    retriever = Retriever(
        embedding_provider=provider,
        vector_store=store,
    )

    knowledge = KnowledgeService(
        indexer=indexer,
        retriever=retriever,
    )

    knowledge.add_document(
        Document(
            id="knowledge.python",
            text="Python is used for Sentinel development.",
        )
    )

    manager = OrchestrationManager(
        knowledge=knowledge,
    )

    request = OrchestrationRequest(
        request_id="req.knowledge.context",
        input="Python",
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    context = result.data["context"]

    knowledge_context = context["knowledge"]

    assert len(knowledge_context) == 1

    chunk = knowledge_context[0]

    assert chunk["id"] == "knowledge.python:0"
    assert chunk["document_id"] == "knowledge.python"
    assert chunk["text"] == (
        "Python is used for Sentinel development."
    )

    from sentinel.knowledge.chunker import FixedSizeChunker
    from sentinel.knowledge.embeddings import DummyEmbeddingProvider
    from sentinel.knowledge.indexer import Indexer
    from sentinel.knowledge.knowledge_service import KnowledgeService
    from sentinel.knowledge.retriever import Retriever
    from sentinel.knowledge.vector_store import InMemoryVectorStore

    provider = DummyEmbeddingProvider()
    store = InMemoryVectorStore()

    knowledge = KnowledgeService(
        indexer=Indexer(
            chunker=FixedSizeChunker(),
            embedding_provider=provider,
            vector_store=store,
        ),
        retriever=Retriever(
            embedding_provider=provider,
            vector_store=store,
        ),
    )

    manager = OrchestrationManager(
        knowledge=knowledge,
    )

    request = OrchestrationRequest(
        request_id="req.no.knowledge",
        input="something-that-does-not-exist",
    )

    result = manager.execute(request)

    assert result.success is True
    assert isinstance(result.data, dict)

    context = result.data["context"]

    assert context["knowledge"] == []

def test_execute_unknown_capability_fails_validation() -> None:
    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.unknown.validation",
        input="hello",
        context={
            "capability_id": "does.not.exist",
        },
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)

def test_execute_disabled_capability_fails_validation() -> None:
    capability = EchoCapability()
    capability.disable()

    capabilities = CapabilityManager()
    capabilities.register(capability)

    security, identity = create_authorized_security()

    manager = OrchestrationManager(
        capabilities=capabilities,
        security=security,
        identity=identity,
    )

    request = OrchestrationRequest(
        request_id="req.disabled",
        input="hello",
        context={
            "capability_id": "system.echo",
        },
    )

    with pytest.raises(OrchestrationExecutionError):
        manager.execute(request)