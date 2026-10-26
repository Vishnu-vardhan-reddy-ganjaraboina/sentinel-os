from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from sentinel.knowledge.sentence_transformer_embeddings import (
    SentenceTransformerEmbeddingProvider,
)


@pytest.fixture
def model_factory(monkeypatch):
    model = Mock()
    model.get_embedding_dimension.return_value = 3
    model.encode.return_value = SimpleNamespace(
        tolist=lambda: [[0.6, 0.8, 0.0]]
    )

    factory = Mock(return_value=model)
    module = ModuleType("sentence_transformers")
    module.SentenceTransformer = factory
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)

    return factory, model


def test_provider_loads_configured_model(model_factory):
    factory, _ = model_factory

    provider = SentenceTransformerEmbeddingProvider(
        "test-model",
        device="cpu",
    )

    factory.assert_called_once_with(
        "test-model",
        device="cpu",
        trust_remote_code=False,
    )
    assert provider.dimension() == 3


def test_embed_returns_vector(model_factory):
    _, model = model_factory
    provider = SentenceTransformerEmbeddingProvider("test-model")

    assert provider.embed("hello") == [0.6, 0.8, 0.0]
    model.encode.assert_called_once()


def test_embed_many_returns_vectors(model_factory):
    _, model = model_factory
    model.encode.return_value = SimpleNamespace(
        tolist=lambda: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    )
    provider = SentenceTransformerEmbeddingProvider("test-model")

    assert provider.embed_many(["hello", "world"]) == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]


def test_embed_many_empty_input(model_factory):
    _, model = model_factory
    provider = SentenceTransformerEmbeddingProvider("test-model")

    assert provider.embed_many([]) == []
    model.encode.assert_not_called()


def test_embeddings_are_requested_normalized(model_factory):
    _, model = model_factory
    provider = SentenceTransformerEmbeddingProvider("test-model")

    provider.embed("hello")

    assert model.encode.call_args.kwargs["normalize_embeddings"] is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"model_name": ""},
        {"device": ""},
        {"batch_size": 0},
        {"batch_size": -1},
    ],
)
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        SentenceTransformerEmbeddingProvider(**kwargs)


def test_embed_rejects_non_string(model_factory):
    provider = SentenceTransformerEmbeddingProvider("test-model")

    with pytest.raises(TypeError):
        provider.embed(123)


def test_embed_many_rejects_invalid_input(model_factory):
    provider = SentenceTransformerEmbeddingProvider("test-model")

    with pytest.raises(TypeError):
        provider.embed_many("hello")

    with pytest.raises(TypeError):
        provider.embed_many(["hello", 123])


def test_invalid_model_dimension(monkeypatch):
    model = Mock()
    model.get_embedding_dimension.return_value = None
    module = ModuleType("sentence_transformers")
    module.SentenceTransformer = Mock(return_value=model)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)

    with pytest.raises(RuntimeError, match="invalid dimension"):
        SentenceTransformerEmbeddingProvider("test-model")


def test_embed_many_rejects_wrong_number_of_vectors(model_factory):
    _, model = model_factory
    model.encode.return_value = SimpleNamespace(
        tolist=lambda: [[0.6, 0.8, 0.0]]
    )
    provider = SentenceTransformerEmbeddingProvider("test-model")

    with pytest.raises(RuntimeError, match="unexpected number of vectors"):
        provider.embed_many(["hello", "world"])


def test_missing_optional_dependency_has_install_instructions(monkeypatch):
    monkeypatch.delitem(sys.modules, "sentence_transformers", raising=False)

    original_import = __import__

    def import_without_sentence_transformers(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("simulated missing optional dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", import_without_sentence_transformers)

    with pytest.raises(ImportError, match="sentence-transformers>=5,<6"):
        SentenceTransformerEmbeddingProvider("test-model")
