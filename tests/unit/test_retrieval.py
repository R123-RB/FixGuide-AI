"""Unit tests for retrieval."""

from fixguide.core.retrieval import HybridRetriever
from fixguide.models.domain import ProductCategory


def test_retriever_initialization() -> None:
    """Verify HybridRetriever instantiates."""
    retriever = HybridRetriever()
    assert retriever is not None


def test_search_returns_list() -> None:
    """Verify retrieval search returns a non-empty list."""
    retriever = HybridRetriever()
    results = retriever.search(
        "game controller stick drift", ProductCategory.GAME_CONTROLLER, top_k=5
    )
    assert isinstance(results, list)
    assert len(results) > 0
