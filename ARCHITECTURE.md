# FixGuide AI — Architecture Documentation

## System Overview

FixGuide AI is a multimodal Generative AI system that guides users through consumer product repair via an interactive, vision-verified step loop.

## Core Design Principles

1. **Safety First**: Hard risk gate before any generation
2. **Grounded Generation**: Every claim must cite source documents
3. **Closed-Loop Verification**: Vision model validates user progress before advancing
4. **Personalization**: Adapts to skill level and available tools
5. **Modularity**: Pure Python core, swappable LLM/vector providers

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Layer                            │
│  POST /repair/start    POST /repair/verify    GET /health       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph State Machine                     │
│  risk_gate → retrieve → generate → verify → vision_check        │
│                    ↑              │              │              │
│                    └──────────────┴──────────────┘              │
│                              │                                   │
│                              ▼                                   │
│                        reassembly → END                          │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   LLM Client    │ │  Vision Client  │ │ Embedding Client│
│ (Groq/OpenAI/   │ │ (Groq/OpenAI/   │ │(sentence-trans.)│
│  Anthropic/     │ │  Anthropic/     │ │                 │
│  Vertex)        │ │  Vertex)        │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Vector Store (Qdrant)                      │
│              Dense vectors + BM25 corpus (hybrid)               │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Session Start
```
User Input (image, category, problem, skill, tools)
         │
         ▼
   Risk Gate (rule-based + LLM)
         │
         ├── BLOCKED/HIGH_RISK → Refuse + explain
         │
         ▼
   Product ID (vision model) → category, brand, model
         │
         ▼
   Hybrid Retrieval (BM25 + dense) → relevant procedure chunks
         │
         ▼
   Step Generation (LLM + RAG context) → Step 1
         │
         ▼
   Grounding Verifier (LLM-as-judge) → verify citations
         │
         ▼
   Return Step 1 to user
```

### 2. Step Verification Loop
```
User submits progress photo
         │
         ▼
   Vision Verifier (compare photo to expected state)
         │
         ├── MATCHES → Advance to next step (retrieve → generate → verify)
         │
         └── MISMATCH → Correction feedback → Regenerate current step
```

### 3. Completion
```
All steps done → Reassembly Node → Checklist + Test Procedure → Complete
```

## State Schema (GraphState)

```python
session_id: str
category: ProductCategory
product_id: str | None
problem_description: str
user_skill_level: "beginner" | "intermediate" | "experienced"
available_tools: list[str]
risk_level: RiskLevel
current_step: int
steps: list[RepairStep]
completed_steps: list[int]
verification_history: list[dict]
is_complete: bool
final_checklist: list[str]

# Graph-specific
messages: list[dict]
next_action: "retrieve" | "generate" | "verify" | "vision_check" | "complete" | "error"
error: str | None
retrieval_results: list[dict]
generation_output: dict | None
verification_result: dict | None
vision_result: dict | None
vision_input: str | None  # base64 image
```

## Prompt Templates

All prompts in `config/prompts/*.yaml` with Jinja2 templating:

| Prompt | Purpose |
|--------|---------|
| `product_id.yaml` | Identify product from image |
| `risk_gate.yaml` | Classify safety risk |
| `step_generator.yaml` | Generate next repair step |
| `grounding_verifier.yaml` | Verify step cites sources |
| `vision_verifier.yaml` | Compare user photo to expected state |
| `reassembly.yaml` | Generate reassembly checklist |

## Retrieval Strategy

**Hybrid Search:**
- BM25 (keyword/exact match) — weight 0.3
- Dense vectors (semantic) — weight 0.7
- Optional cross-encoder rerank

**Filters:** Product category, step number, component type

## Safety Architecture

```
Risk Gate (pre-generation, hard block)
    │
    ├── Rule-based: blocked_categories, caution_keywords
    │
    └── LLM fallback: edge cases
        
Grounding Verifier (post-generation, soft block)
    │
    └── Every claim must trace to source chunk
        
Vision Verifier (runtime, physical validation)
    │
    └── User must demonstrate correct state before advancing
```

## Deployment

### Development
```bash
docker compose -f docker/docker-compose.dev.yml up
```

### Production
```bash
docker compose -f docker/docker-compose.yml up -d
```

### Environment Variables
See `.env.example` for all configuration options.

## Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| API | Horizontal (stateless, LangGraph checkpoints in Redis) |
| Qdrant | Cluster mode, sharding by category |
| LLM | Provider-managed, request batching |
| Embeddings | Batch inference, caching |
| Vision | Provider-managed, async processing |

## Monitoring

Key metrics to track:
- Request latency (p50, p95, p99)
- Risk gate distribution (safe/caution/blocked)
- Grounding verification pass rate
- Vision verification match rate
- Steps per repair session
- Task completion rate
- Error rates by type

## Future Extensions

1. **Multi-step lookahead**: Generate multiple steps, verify in batch
2. **User feedback learning**: RLHF from correction loops
3. **3D/AR guidance**: Overlay instructions on camera feed
4. **Community corpus**: User-contributed procedures with moderation
5. **Offline mode**: Distilled models for edge deployment