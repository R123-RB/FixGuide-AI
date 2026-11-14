.PHONY: install dev test lint format typecheck clean docker-build docker-up docker-down validate pre-commit

# Install all dependencies
install:
	uv sync --all-extras

# Install core dependencies only (faster)
install-core:
	uv sync --no-dev

# Install pre-commit hooks
pre-commit:
	pre-commit install

# Start development environment (Qdrant + API with reload)
dev:
	./scripts/run_local.sh

# Run tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-cov:
	uv run pytest tests/ --cov=fixguide --cov-report=term-missing

# Run linting
lint:
	uv run ruff check src/ tests/

# Auto-fix linting issues
lint-fix:
	uv run ruff check --fix src/ tests/

# Format code
format:
	uv run ruff format src/ tests/

# Check formatting
format-check:
	uv run ruff format --check src/ tests/

# Type checking
typecheck:
	uv run mypy src/

# Run validation script
validate:
	uv run python scripts/validate.py

# Clean build artifacts
clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Build Docker image
docker-build:
	docker build -f docker/Dockerfile -t fixguide-ai .

# Start Docker services
docker-up:
	docker compose -f docker/docker-compose.yml up -d

# Start Docker services (dev)
docker-up-dev:
	docker compose -f docker/docker-compose.dev.yml up -d

# Stop Docker services
docker-down:
	docker compose -f docker/docker-compose.yml down

# Ingest sample data
ingest:
	uv run python -m fixguide.pipelines.ingest self_captured game_controller data/raw/self_captured/game_controller/
	uv run python -m fixguide.pipelines.ingest self_captured wired_headphones data/raw/self_captured/wired_headphones/
	uv run python -m fixguide.pipelines.ingest self_captured lamp data/raw/self_captured/lamp/
	uv run python -m fixguide.pipelines.ingest self_captured remote_control data/raw/self_captured/remote_control/
	uv run python -m fixguide.pipelines.ingest self_captured keyboard data/raw/self_captured/keyboard/
	uv run python -m fixguide.pipelines.ingest self_captured table_fan data/raw/self_captured/table_fan/

# Run evaluation
eval:
	uv run python -m fixguide.cli eval retrieval
	uv run python -m fixguide.cli eval risk-gate
	uv run python -m fixguide.cli eval vision
	uv run python -m fixguide.cli eval e2e

# Start API server directly
serve:
	uv run uvicorn fixguide.api.main:app --reload

# Start API server (production)
serve-prod:
	uv run uvicorn fixguide.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Help
help:
	@echo "FixGuide AI - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install all dependencies"
	@echo "  make install-core  - Install core dependencies only"
	@echo "  make pre-commit    - Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  make dev           - Start full dev environment (Qdrant + API)"
	@echo "  make serve         - Start API server with reload"
	@echo "  make validate      - Run validation script"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run ruff linter"
	@echo "  make lint-fix      - Auto-fix linting issues"
	@echo "  make format        - Format code with ruff"
	@echo "  make typecheck     - Run mypy type checking"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start services (prod)"
	@echo "  make docker-up-dev - Start services (dev)"
	@echo "  make docker-down   - Stop services"
	@echo ""
	@echo "Data:"
	@echo "  make ingest        - Ingest all sample data"
	@echo "  make eval          - Run all evaluations"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Clean build artifacts"