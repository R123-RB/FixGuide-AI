#!/usr/bin/env bash
set -euo pipefail

echo "Starting FixGuide AI local development environment..."

# Start Qdrant (try Docker first, fall back to binary)
if docker info >/dev/null 2>&1; then
    echo "Starting Qdrant via Docker..."
    docker compose -f docker/docker-compose.yml up -d qdrant
elif [ -f "/tmp/qdrant/qdrant" ]; then
    echo "Starting Qdrant binary..."
    /tmp/qdrant/qdrant --config-path /dev/null --uri 127.0.0.1:6333 &
    QDRANT_PID=$!
    echo "Qdrant started with PID $QDRANT_PID"
else
    echo "Qdrant binary not found at /tmp/qdrant/qdrant"
    echo "Download it from: https://github.com/qdrant/qdrant/releases"
    exit 1
fi

# Wait for Qdrant
echo "Waiting for Qdrant to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:6333/healthz >/dev/null 2>&1; then
        echo "Qdrant is ready!"
        break
    fi
    sleep 1
done

# Initialize collection
echo "Initializing Qdrant collection..."
uv run python -c "from fixguide.services.vector_store import init_collection; init_collection(); print('Collection initialized')"

# Ingest sample data if exists
if [ -d "data/raw/self_captured" ]; then
    echo "Ingesting self-captured data..."
    uv run python -c "
from pathlib import Path
from fixguide.config import get_settings
from fixguide.pipelines.ingest import IngestionPipeline
from fixguide.models.domain import ProductCategory
settings = get_settings()
pipe = IngestionPipeline(settings.ingest)
for cat_dir in sorted(Path('data/raw/self_captured').iterdir()):
    if cat_dir.is_dir():
        cat = ProductCategory(cat_dir.name)
        sources = pipe.load_self_captured(cat_dir, cat)
        if sources:
            pipe.run(sources)
" || true
fi

# Start API
echo "Starting API server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
uv run uvicorn fixguide.api.main:app --reload