from sentinel.core.exceptions import SentinelError
from sentinel.knowledge.exceptions import (
    ChunkNotFoundError,
    DocumentNotFoundError,
    EmbeddingError,
    KnowledgeError,
    RetrievalError,
    VectorStoreError,
)


def test_exception_hierarchy():
    assert issubclass(KnowledgeError, SentinelError)
    assert issubclass(DocumentNotFoundError, KnowledgeError)
    assert issubclass(ChunkNotFoundError, KnowledgeError)
    assert issubclass(EmbeddingError, KnowledgeError)
    assert issubclass(VectorStoreError, KnowledgeError)
    assert issubclass(RetrievalError, KnowledgeError)