# FixGuide AI

A multimodal Generative AI assistant for consumer product disassembly, repair, and reassembly.

## Features

- **Multimodal input**: Product image + problem description → repair plan
- **Risk-aware**: Hard safety gate blocks dangerous repairs (mains voltage, gas, Li-ion)
- **Grounded generation**: Every repair step cites source documents (RAG)
- **Interactive verification**: User submits progress photos → vision model confirms step completion
- **Personalized**: Adapts to skill level and available tools
- **Reassembly support**: Generates checklist and final test procedure

## Architecture

```
User Input → Risk Gate → Hybrid Retrieval → Step Generation → Grounding Verifier
                                                              ↓
                                            Vision Verifier ← User Photo
                                                              ↓
                                                    Next Step / Correction
                                                              ↓
                                                    Reassembly Checklist
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for Qdrant)
- Groq API key (for LLM/Vision)

### Installation & Setup

```bash
# 1. Install dependencies
make install
# or
uv sync --extra dev

# 2. Configure environment
cp .env.example .env
# Edit .env and add your valid GROQ_API_KEY

# 3. Start Qdrant (vector DB)
docker run -d --name qdrant-fixguide -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.13.1
# OR use docker compose: make docker-up

# 4. Ingest all sample data
make ingest

# 5. Start API server
make serve
```

The API will be available at [http://localhost:8000](http://localhost:8000).

### Troubleshooting

**Port 8000 already in use:**
```bash
pkill -9 -f uvicorn
make serve
# or use different port: uv run uvicorn fixguide.api.main:app --reload --port 8001
```

**Qdrant connection issues:**
```bash
# Start Qdrant
docker start qdrant-fixguide 2>/dev/null || docker run -d --name qdrant-fixguide -p 6333:6333 qdrant/qdrant:v1.13.1
```

**API key issues:** Update `GROQ_API_KEY` in `.env` with a valid key.

## Project Structure

```
fixguide-ai/
├── config/           # Configuration (YAML) & prompts
├── data/             # Raw, processed, eval datasets
├── src/fixguide/     # Main package
│   ├── core/         # Pure business logic
│   ├── graph/        # LangGraph state machine
│   ├── api/          # FastAPI routes
│   ├── services/     # External clients (LLM, vector DB)
│   ├── pipelines/    # CLI pipelines (ingest, eval, fine-tune)
│   └── utils/        # Helpers
├── tests/            # Unit & integration tests
├── scripts/          # Utility scripts
├── docker/           # Container definitions
└── notebooks/        # Exploration & analysis
```

## API Endpoints

| Method | Endpoint                | Description                          |
| ------ | ----------------------- | ------------------------------------ |
| POST   | `/api/v1/repair/start`  | Start new repair session             |
| POST   | `/api/v1/repair/verify` | Verify progress photo, get next step |
| GET    | `/health/`              | Health check                         |

## Development

```bash
# Run all checks
make lint
make typecheck
make test

# Format code
make format

# Run evaluations
make eval
```

## Configuration

All settings in `config/settings.yaml` (overridable via `.env`):
- LLM provider/model/temperature — **Default: Groq** (`openai/gpt-oss-20b`)
- Vision model — **Default: Groq** (`llava-v1.6-34b-overlay`)
- Embedding model/device — `sentence-transformers/all-mpnet-base-v2` (CPU)
- Vector store (Qdrant/pgvector)
- Retrieval weights (BM25 + dense)
- Risk gate rules
- Generation/verification thresholds

**Supported providers:** `groq`, `openai`, `anthropic`, `vertex`

## Product Categories

| Category            | Risk Level | Example Products                      |
| ------------------- | ---------- | ------------------------------------- |
| Game Controller     | Safe       | Xbox, PlayStation, Switch controllers |
| Wired Headphones    | Safe       | Over-ear, in-ear, gaming headsets     |
| Table Lamp          | Caution    | Desk lamps, bedside lamps             |
| Remote Control      | Safe       | TV, AC, streaming remotes             |
| Table Fan           | Caution    | Desk fans, pedestal fans              |
| Mechanical Keyboard | Safe       | Hot-swap, soldered keyboards          |

## Safety

**Never attempt repair on:**
- Microwave ovens
- Gas appliances
- High voltage equipment (>50V AC)
- CRT monitors
- Damaged lithium batteries

These are hard-blocked by the risk gate.

## License

MIT
# FixGuide-AI
