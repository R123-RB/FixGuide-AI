"""Vector store client for Qdrant/pgvector."""

from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient

from fixguide.config import get_settings

_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> Any:  # noqa: ANN401
    """Get or create Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(
            host=settings.vector_store.qdrant_host,
            port=settings.vector_store.qdrant_port,
        )
    return _qdrant_client


def init_collection() -> None:
    """Initialize the Qdrant collection if it doesn't exist."""
    from qdrant_client.models import Distance, VectorParams

    client = get_qdrant_client()
    settings = get_settings()

    collections = client.get_collections().collections
    if settings.vector_store.qdrant_collection not in [c.name for c in collections]:
        client.create_collection(
            collection_name=settings.vector_store.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.vector_store.vector_size,
                distance=Distance.COSINE,
            ),
        )
