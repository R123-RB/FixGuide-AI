FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
COPY README.md ./
COPY src ./src
COPY config ./config

RUN uv sync --frozen --no-dev

EXPOSE 8000

RUN uv pip install -e .

CMD ["uv", "run", "uvicorn", "fixguide.api.main:app", "--host", "0.0.0.0", "--port", "8000"]