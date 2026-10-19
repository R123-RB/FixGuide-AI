"""Embedding client for text vectorization."""

from __future__ import annotations

from typing import Any, cast

from fixguide.config import get_settings


class EmbeddingClient:
    """Text embedding client using sentence-transformers."""

    def __init__(self) -> None:
        """Initialize the embedding client with settings."""
        self.settings = get_settings()
        self._model: Any = None

    def _get_model(self) -> Any:  # noqa: ANN401
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.settings.embeddings.model,
                device=self.settings.embeddings.device,
            )
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=self.settings.embeddings.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return cast(list[list[float]], embeddings.tolist())

    def embed_single(self, text: str) -> list[float]:
        """Generate a single text embedding."""
        return cast(list[float], self.embed([text])[0])


_client = None


def get_embedding_client() -> EmbeddingClient:
    """Get the singleton embedding client."""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client


def get_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text."""
    return get_embedding_client().embed_single(text)
