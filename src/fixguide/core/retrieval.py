"""Hybrid retrieval: BM25 + dense vector search."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fixguide.config import get_settings
from fixguide.models.domain import ProductCategory, RepairChunk


class HybridRetriever:
    """Combines BM25 keyword search with dense vector similarity."""

    def __init__(self) -> None:
        """Initialize the hybrid retriever with settings."""
        self.settings = get_settings()
        self._bm25_index: Any = None
        self._qdrant_client: Any = None

    def _get_qdrant(self) -> Any:  # noqa: ANN401
        if self._qdrant_client is None:
            from fixguide.services.vector_store import get_qdrant_client

            self._qdrant_client = get_qdrant_client()
        return self._qdrant_client

    def _get_bm25(self) -> Any:  # noqa: ANN401
        if self._bm25_index is None:
            self._load_bm25()
        return self._bm25_index

    def _load_bm25(self) -> None:
        """Load BM25 index from JSONL corpus."""
        import json

        from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

        corpus_path = self.settings.ingest.bm25_corpus_path
        documents = []
        metadatas = []

        try:
            with Path(corpus_path).open() as f:
                for line in f:
                    data = json.loads(line)
                    documents.append(data["text"])
                    metadatas.append(data)
        except FileNotFoundError:
            documents = [""]
            metadatas = [{}]

        tokenized = [doc.split() for doc in documents]
        self._bm25_index = BM25Okapi(tokenized)
        self._bm25_metadatas: list[dict[str, Any]] = metadatas

    def search(
        self,
        query: str,
        category: ProductCategory | str | None = None,
        top_k: int | None = None,
    ) -> list[RepairChunk]:
        """Hybrid search combining BM25 and dense vectors."""
        top_k = top_k or self.settings.retrieval.top_k
        settings = self.settings.retrieval

        # Dense vector search
        from fixguide.services.embeddings import get_embedding

        query_vector = get_embedding(query)

        dense_results = []
        try:
            client = self._get_qdrant()
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            query_filter = None
            if category:
                cat_val = category.value if hasattr(category, "value") else str(category)
                query_filter = Filter(
                    must=[FieldCondition(key="category", match=MatchValue(value=cat_val))]
                )

            dense_results = client.query_points(
                collection_name=self.settings.vector_store.qdrant_collection,
                query=query_vector,
                limit=top_k * 2,
                query_filter=query_filter,
                with_payload=True,
            ).points
        except Exception:
            dense_results = []

        # BM25 search
        bm25 = self._get_bm25()
        tokenized_query = query.split()
        bm25_scores = bm25.get_scores(tokenized_query)
        bm25_top_indices = sorted(
            range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
        )[: top_k * 2]

        # Combine and rerank
        combined = {}

        # Add dense results
        for hit in dense_results:
            chunk_id = hit.id
            combined[chunk_id] = {
                "chunk": RepairChunk(**hit.payload),
                "dense_score": hit.score,
                "bm25_score": 0.0,
            }

        # Add BM25 results
        for idx in bm25_top_indices:
            if idx < len(self._bm25_metadatas):
                meta = self._bm25_metadatas[idx]
                chunk_id = meta.get("chunk_id", f"bm25_{idx}")
                if chunk_id not in combined:
                    combined[chunk_id] = {
                        "chunk": RepairChunk(**meta),
                        "dense_score": 0.0,
                        "bm25_score": bm25_scores[idx],
                    }
                else:
                    combined[chunk_id]["bm25_score"] = bm25_scores[idx]

        # Normalize and combine scores
        if combined:
            max_dense = max(v["dense_score"] for v in combined.values()) or 1.0
            max_bm25 = max(v["bm25_score"] for v in combined.values()) or 1.0

            for v in combined.values():
                v["combined_score"] = settings.dense_weight * (
                    v["dense_score"] / max_dense
                ) + settings.bm25_weight * (v["bm25_score"] / max_bm25)

        # Sort by combined score
        sorted_results = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)

        # Rerank if enabled
        if settings.rerank and len(sorted_results) > 1:
            sorted_results = self._rerank(query, sorted_results[: top_k * 2])

        return [r["chunk"] for r in sorted_results[:top_k]]

    def _rerank(self, query: str, results: list[dict]) -> list[dict]:
        """Cross-encoder reranking."""
        try:
            from sentence_transformers import CrossEncoder

            reranker = CrossEncoder(self.settings.retrieval.rerank_model)

            pairs = [(query, r["chunk"].text) for r in results]
            scores = reranker.predict(pairs)

            for r, score in zip(results, scores):
                r["rerank_score"] = float(score)

            return sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
        except Exception:
            return results


# Singleton
_retriever = None


def get_retriever() -> HybridRetriever:
    """Get the singleton hybrid retriever."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
