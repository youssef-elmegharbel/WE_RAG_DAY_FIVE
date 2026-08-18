"""Local sentence-transformers embeddings, shared by ingest and query paths.

Embeddings are deliberately not swappable: a Chroma index is built with one
embedding model and cannot be queried with another. Keeping this local means
the index needs no API key and works offline.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from rag.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Load the local embedding model once per process."""
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
