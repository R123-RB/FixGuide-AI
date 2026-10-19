"""Dependency injection for FastAPI."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fixguide.core.retrieval import get_retriever
from fixguide.graph.builder import graph
from fixguide.services.embeddings import EmbeddingClient, get_embedding_client
from fixguide.services.llm import LLMClient, get_llm_client
from fixguide.services.vector_store import get_qdrant_client, init_collection
from fixguide.services.vision import VisionClient, get_vision_client


@lru_cache
def get_graph() -> Any:  # noqa: ANN401
    """Get compiled LangGraph."""
    return graph


@lru_cache
def get_retriever_dep() -> Any:  # noqa: ANN401
    """Get retriever instance."""
    return get_retriever()


@lru_cache
def get_llm_dep() -> LLMClient:
    """Get LLM client."""
    return get_llm_client()


@lru_cache
def get_vision_dep() -> VisionClient:
    """Get vision client."""
    return get_vision_client()


@lru_cache
def get_embedding_dep() -> EmbeddingClient:
    """Get embedding client."""
    return get_embedding_client()


@lru_cache
def get_vector_store_dep() -> Any:  # noqa: ANN401
    """Get vector store client."""
    init_collection()
    return get_qdrant_client()
