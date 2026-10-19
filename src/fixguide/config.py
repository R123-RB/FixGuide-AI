"""Configuration management using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class LLMSettings(BaseSettings):
    """LLM provider and model settings."""

    provider: Literal["groq", "openai", "anthropic", "vertex", "gemini"] = "gemini"
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3


class VisionSettings(BaseSettings):
    """Vision model settings."""

    provider: Literal["groq", "openai", "anthropic", "vertex", "gemini"] = "gemini"
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    max_tokens: int = 2048


class EmbeddingSettings(BaseSettings):
    """Embedding model settings."""

    model: str = "sentence-transformers/all-mpnet-base-v2"
    device: Literal["cuda", "cpu", "mps"] = "cpu"
    batch_size: int = 32


class VectorStoreSettings(BaseSettings):
    """Vector store settings."""

    provider: Literal["qdrant", "pgvector"] = "qdrant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "fixguide_repair_chunks"
    vector_size: int = 768
    distance: str = "Cosine"


class RetrievalSettings(BaseSettings):
    """Hybrid retrieval settings."""

    top_k: int = 10
    bm25_weight: float = 0.3
    dense_weight: float = 0.7
    rerank: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class IngestSettings(BaseSettings):
    """Data ingestion settings."""

    chunk_size: int = 512
    chunk_overlap: int = 64
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    qdrant_collection: str = "fixguide_repair_chunks"
    bm25_corpus_path: str = "data/processed/bm25_corpus.jsonl"
    ifixit_api_key: str = ""


class RiskGateSettings(BaseSettings):
    """Safety risk gate settings."""

    blocked_categories: list[str] = Field(
        default_factory=lambda: [
            "microwave",
            "gas_appliance",
            "high_voltage",
            "crt_monitor",
            "damaged_lithium_battery",
        ]
    )
    caution_keywords: list[str] = Field(
        default_factory=lambda: ["spring", "sharp_edge", "capacitor", "high_temperature"]
    )


class ProductIDSettings(BaseSettings):
    """Product identification settings."""

    confidence_threshold: float = 0.75
    model_path: str = "models/product_classifier"


class GenerationSettings(BaseSettings):
    """Repair step generation settings."""

    max_steps: int = 20
    groundedness_threshold: float = 0.8
    require_citations: bool = True


class VerificationSettings(BaseSettings):
    """Grounding and vision verification settings."""

    vision_model: str = "gpt-4o"
    similarity_threshold: float = 0.7
    max_retries: int = 2


class LoggingSettings(BaseSettings):
    """Logging settings."""

    level: str = "INFO"
    format: Literal["json", "text"] = "json"
    file: str = "logs/fixguide.log"


class Settings(BaseSettings):
    """Top-level application settings."""

    app_name: str = "fixguide-ai"
    app_version: str = "0.1.0"
    env: Literal["development", "staging", "production"] = "development"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    vision: VisionSettings = Field(default_factory=VisionSettings)
    embeddings: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    ingest: IngestSettings = Field(default_factory=IngestSettings)
    risk_gate: RiskGateSettings = Field(default_factory=RiskGateSettings)
    product_id: ProductIDSettings = Field(default_factory=ProductIDSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
    verification: VerificationSettings = Field(default_factory=VerificationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get the cached application settings."""
    return Settings()
