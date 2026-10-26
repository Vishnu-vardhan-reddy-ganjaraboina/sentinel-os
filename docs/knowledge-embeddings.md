# Multilingual Knowledge Embeddings

Sentinel OS supports an optional local sentence-transformer embedding provider
for semantic knowledge retrieval. The default provider remains `dummy`, so
the additional dependency is not required for a standard installation.

## Installation

Install Sentinel OS with the optional semantic dependencies:

```powershell
python -m pip install -e ".[semantic]"
```

This installs the `sentence-transformers` dependency. The configured model
may need to be downloaded the first time it is loaded. An initial download
requires network access unless the model is already available locally.

## Configuration

Add an `embedding` section under `knowledge` in your Sentinel configuration. Merge this example into your existing configuration file and preserve any other settings already under `knowledge`:

```yaml
knowledge:
  embedding:
    provider: sentence-transformers
    model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    device: cpu
    batch_size: 32
```

Configuration options:

- `provider`: `dummy` or `sentence-transformers`. Defaults to `dummy`.
- `model`: model name or supported model path. Defaults to
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- `device`: model execution device. Defaults to `cpu`.
- `batch_size`: number of texts processed per batch. Defaults to `32`
  and must be a positive integer.

The default model is multilingual. It generates normalized embeddings locally
after the model has been loaded.

## Default behavior

Without an explicit provider setting, Sentinel uses `dummy`. This preserves
the lightweight default installation and avoids loading a transformer model.

Selecting `sentence-transformers` requires the optional dependency. If it is
missing, Sentinel reports an installation instruction rather than silently
switching providers.

## Operational considerations

- Model loading can consume additional memory and startup time.
- CPU execution is the default; a compatible alternative device can be
  configured when supported by the installed runtime.
- The first model load may require downloading model files.
- Keep the embedding model consistent for documents being indexed and queries
  being retrieved. If you change models, verify compatibility with existing
  stored vectors and reindex knowledge where necessary.
- Do not enable remote model code execution unless the project explicitly
  reviews and changes its model-loading security policy.
