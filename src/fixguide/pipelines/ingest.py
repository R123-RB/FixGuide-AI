"""Ingestion pipeline: raw sources → chunked, embedded, indexed corpus."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore[import-not-found]
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

from fixguide.config import IngestSettings, get_settings
from fixguide.models.domain import ProductCategory, RepairChunk
from fixguide.services.vector_store import get_qdrant_client, init_collection


@dataclass
class RawDocument:
    """A raw document pulled from a repair source."""

    source: str
    source_id: str
    category: ProductCategory
    title: str
    url: str | None = None
    text: str = ""
    images: list[str] | None = None
    metadata: dict[str, Any] | None = None


class IngestionPipeline:
    """Orchestrates loading, chunking, embedding, and indexing repair documents."""

    def __init__(self, config: IngestSettings) -> None:
        """Initialize the pipeline with ingestion settings."""
        self.config = config
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
        )
        self.embedder = SentenceTransformer(config.embedding_model)

    def load_ifixit_guide(
        self, guide_id: str, category: ProductCategory | str
    ) -> list[RawDocument]:
        """Load iFixit guide via API."""
        import os

        import httpx

        if isinstance(category, str):
            try:
                category = ProductCategory(category)
            except ValueError:
                category = ProductCategory.GAME_CONTROLLER

        api_key = os.getenv("IFIXIT_API_KEY", "")
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Fetch guide info
        with httpx.Client(timeout=30) as client:
            # Get guide metadata
            info_resp = client.get(
                f"https://www.ifixit.com/api/2.0/guides/{guide_id}",
                headers=headers,
            )
            if info_resp.status_code != 200:
                raise RuntimeError(f"iFixit API error: {info_resp.status_code}")

            guide = info_resp.json()
            title = guide.get("title", f"Guide {guide_id}")

            # Get guide steps
            steps_resp = client.get(
                f"https://www.ifixit.com/api/2.0/guides/{guide_id}/steps",
                headers=headers,
            )
            if steps_resp.status_code != 200:
                raise RuntimeError(f"iFixit steps API error: {steps_resp.status_code}")

            steps_data = steps_resp.json()
            steps = steps_data if isinstance(steps_data, list) else steps_data.get("steps", [])

        # Build text from steps
        text_parts = [f"# {title}\n"]
        for i, step in enumerate(steps, 1):
            step_text = step.get("text", "")
            step_title = step.get("title", "")
            if step_title:
                text_parts.append(f"## Step {i}: {step_title}")
            if step_text:
                text_parts.append(step_text)
            text_parts.append("")

        # Extract tools from steps
        tools = []
        for step in steps:
            for tool in step.get("tools", []):
                tool_name = tool.get("name", "")
                if tool_name and tool_name not in tools:
                    tools.append(tool_name)

        return [
            RawDocument(
                source="ifixit",
                source_id=guide_id,
                category=category,
                title=title,
                text="\n".join(text_parts),
                images=[],
                metadata={
                    "tools": tools,
                    "difficulty": guide.get("difficulty", "beginner"),
                    "estimated_time_minutes": guide.get("time", 30),
                    "url": f"https://www.ifixit.com/guides/{guide_id}",
                },
            )
        ]

    def load_manual_pdf(self, pdf_path: Path, category: ProductCategory | str) -> list[RawDocument]:
        """Load service manual PDF."""
        import pdfplumber

        if isinstance(category, str):
            try:
                category = ProductCategory(category)
            except ValueError:
                category = ProductCategory.GAME_CONTROLLER

        pdf_path = Path(pdf_path)
        text_parts = []
        title = pdf_path.stem.replace("_", " ").title()

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return [
            RawDocument(
                source="manual",
                source_id=pdf_path.stem,
                category=category,
                title=title,
                text="\n".join(text_parts),
                images=[],
                metadata={
                    "tools": [],
                    "difficulty": "intermediate",
                    "estimated_time_minutes": 45,
                },
            )
        ]

    def load_self_captured(
        self, folder: Path, category: ProductCategory | str
    ) -> list[RawDocument]:
        """Load self-captured disassembly data from markdown files."""
        folder = Path(folder)
        docs = []

        # Handle both string and enum category
        if isinstance(category, str):
            try:
                category = ProductCategory(category)
            except ValueError:
                category = ProductCategory.GAME_CONTROLLER

        # If folder doesn't exist, try to find it under data/raw/self_captured/
        if not folder.exists():
            alt_folder = Path("data/raw/self_captured") / folder.name
            if alt_folder.exists():
                folder = alt_folder
            else:
                # Try matching by category name
                cat_name = category.value if hasattr(category, "value") else str(category)
                alt_folder = Path("data/raw/self_captured") / cat_name
                if alt_folder.exists():
                    folder = alt_folder

        # Support both direct .md files and nested category directories
        md_files = list(folder.glob("*.md"))
        if not md_files and folder.exists():
            for sub in folder.iterdir():
                if sub.is_dir():
                    md_files.extend(sub.glob("*.md"))

        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            title = md_file.stem.replace("_", " ").title()
            for line in text.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            tools = []
            in_tools = False
            for line in text.split("\n"):
                if "Tools Required" in line or "Tools" in line:
                    in_tools = True
                    continue
                if in_tools:
                    if line.startswith("#"):
                        break
                    if line.startswith("- "):
                        tools.append(line[2:].strip())

            docs.append(
                RawDocument(
                    source="self_captured",
                    source_id=md_file.stem,
                    category=category,
                    title=title,
                    text=text,
                    images=[],
                    metadata={
                        "tools": tools,
                        "difficulty": "beginner",
                        "estimated_time_minutes": 30,
                    },
                )
            )
        return docs

    def normalize(self, raw: RawDocument) -> RawDocument:
        """Collapse whitespace in a raw document's text."""
        raw.text = re.sub(r"\s+", " ", raw.text).strip()
        return raw

    def chunk(self, raw: RawDocument) -> list[RepairChunk]:
        """Split a raw document into repair chunks."""
        chunks = self.splitter.split_text(raw.text)
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{raw.source_id}:{i}"))
            result.append(
                RepairChunk(
                    chunk_id=chunk_id,
                    source=raw.source,
                    source_id=raw.source_id,
                    category=raw.category,
                    title=raw.title,
                    text=chunk_text,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    images=raw.images or [],
                    metadata=raw.metadata or {},
                )
            )
        return result

    def embed(self, chunks: list[RepairChunk]) -> list[RepairChunk]:
        """Embed chunks and store the vector on each chunk."""
        texts = [c.text for c in chunks]
        vectors = self.embedder.encode(texts, batch_size=32, show_progress_bar=True)
        for chunk, vec in zip(chunks, vectors):
            chunk.embedding = vec.tolist()
        return chunks

    def index(self, chunks: list[RepairChunk]) -> None:
        """Index chunks in Qdrant and append them to the BM25 corpus."""
        init_collection()
        client = get_qdrant_client()
        collection = self.config.qdrant_collection

        points = [
            PointStruct(
                id=c.chunk_id,
                vector=c.embedding if c.embedding is not None else [],
                payload=c.model_dump(exclude={"embedding"}),
            )
            for c in chunks
        ]
        client.upsert(collection_name=collection, points=points)

        bm25_path = Path(self.config.bm25_corpus_path)
        bm25_path.parent.mkdir(parents=True, exist_ok=True)
        with bm25_path.open("a") as f:
            for c in chunks:
                f.write(json.dumps(c.model_dump(exclude={"embedding"})) + "\n")

    def run(self, sources: list[RawDocument] | list[list[RawDocument]]) -> None:
        """Run the full ingestion pipeline for the given sources."""
        all_chunks: list[RepairChunk] = []
        for source in sources:
            if isinstance(source, list):
                for raw in source:
                    raw = self.normalize(raw)
                    chunks = self.chunk(raw)
                    chunks = self.embed(chunks)
                    all_chunks.extend(chunks)
            else:
                raw = self.normalize(source)
                chunks = self.chunk(raw)
                chunks = self.embed(chunks)
                all_chunks.extend(chunks)

        self.index(all_chunks)


app = typer.Typer()


@app.command()
def ifixit(category: ProductCategory, guide_ids: list[str]) -> None:
    """Ingest iFixit guides."""
    settings = get_settings()
    pipe = IngestionPipeline(settings.ingest)
    sources = [pipe.load_ifixit_guide(gid, category) for gid in guide_ids]
    pipe.run(sources)


@app.command()
def pdf(category: ProductCategory, pdf_dir: Path) -> None:
    """Ingest PDF service manuals."""
    settings = get_settings()
    pipe = IngestionPipeline(settings.ingest)
    sources = [pipe.load_manual_pdf(p, category) for p in pdf_dir.glob("*.pdf")]
    pipe.run(sources)


@app.command(name="self_captured")
def self_captured_cmd(category: ProductCategory, folder: Path) -> None:
    """Ingest self-captured disassembly data."""
    settings = get_settings()
    pipe = IngestionPipeline(settings.ingest)
    sources = pipe.load_self_captured(folder, category)
    pipe.run(sources)


if __name__ == "__main__":
    app()
