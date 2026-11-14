# System Health & Functionality Checklist

**Project:** FixGuide AI — Multimodal Generative AI assistant for consumer product disassembly, repair, and reassembly  
**Scope:** Developer and User viewpoints. Each item includes a verification step and a "healthy state" indicator.

---

## 1. Developer's Perspective

Focus: backend stability, API performance, error log monitoring, resource utilization, architecture integrity.

### 1.1 Backend Stability

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| D1 | API server starts and binds to configured port | Run `make serve` (or `make docker-up` + wait for container) then `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/` | Returns `200 OK` within 10 seconds of startup |
| D2 | `/health/` endpoint reports dependencies healthy | `curl http://localhost:8000/health/` and inspect JSON body | JSON returns `status: "healthy"` with all dependency checks (Qdrant, LLM provider, embedding) passing |
| D3 | LangGraph state machine compiles without schema errors | Run `uv run python -c "from fixguide.graph import build_graph; build_graph()"` | Graph builds and renders all nodes (risk_gate → retrieve → generate → verify → vision_check → reassembly → END) |
| D4 | Risk gate hard-blocks unsafe products | POST to `/api/v1/repair/start` with `problem_description` containing "microwave", "gas oven", "CRT", or Li-ion battery; observe response | Request returns `400`/`403` with a refusal message and no repair steps generated |
| D5 | Graph handles transient LLM/vector failures gracefully | Temporarily point config at an unreachable endpoint (or mock a 5xx response) and trigger a repair session | Session enters `error` state with `next_action: "error"`, returns structured error JSON, and does not crash the API process |
| D6 | API is stateless / horizontally scalable | Start two API instances against the same Qdrant/Redis checkpoint backend; send concurrent sessions to both | Both instances serve independent sessions without state corruption; no shared local-file state |
| D7 | Graceful shutdown handling | Send `SIGTERM` to `uvicorn` while a session is in-flight; confirm no partial state written | In-flight request completes or fails cleanly; no traceback dump; process exits with code 0 |

### 1.2 API Performance

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| D8 | Health-check latency | `curl -w "%{time_total}" http://localhost:8000/health/` repeated 10 times; compute p50/p95/p99 | p95 < 200 ms |
| D9 | `/repair/start` end-to-end latency (safe category) | POST a game_controller repair request; measure wall time from request to first step returned | p95 < 10 s (with live LLM) — for local/mock testing, < 2 s |
| D10 | `/repair/verify` vision round-trip | POST a progress photo; measure time to verdict (match/mismatch) | p95 < 15 s |
| D11 | Concurrent session throughput | Use a tool (e.g. `hey`, `wrk`, or a Python `asyncio` client) to fire 20 concurrent `/repair/start` requests | All 20 return `200` with unique `session_id`s; no 5xx errors; error rate < 1% |
| D12 | Request timeout configuration | Send a request with an intentionally slow/mocked LLM (delay > 60 s) | API returns `504` or client-side timeout error cleanly, not a hung connection forever |
| D13 | Payload size limits | POST an oversized base64 image (>10 MB) to `/repair/verify` | Returns `413 Payload Too Large` or validation error; server remains responsive |
| D14 | Embedding/retrieval latency | Run `fixguide.cli eval retrieval` on the ingested corpus | Median hybrid search latency < 1 s; recall@5 ≥ 0.8 on eval set |

### 1.3 Error Log Monitoring

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| D15 | Application log file exists and is written to | `tail -n 50 logs/fixguide.log` while the API is running | New structured log lines (JSON or consistent format) appear per request; no permission errors |
| D16 | Log level is configurable and set appropriately | Inspect `config/settings.yaml` / `.env` for `LOG_LEVEL` | `INFO` in production/staging, `DEBUG` optional in dev; `WARNING`+ for errors only |
| D17 | Errors include correlation/request IDs | Trigger a known error (e.g., malformed JSON body) and inspect `logs/fixguide.log` | Each error entry carries a `request_id` or `session_id` traceable to the failing request |
| D18 | LLM/vision provider errors are logged separately | Force an API-key failure (invalid key in `.env`) and run a repair start | Log records provider name, status code, and error message without exposing the key |
| D19 | No secrets/keys logged | Grep `logs/fixguide.log` for `GROQ_API_KEY`, `sk-`, `Bearer` | Zero matches; keys never appear in log output |
| D20 | Log rotation / retention configured | Check log file size over time or logrotate config | Active log does not grow unbounded; rotated archives exist with retention policy |
| D21 | Alert threshold on error rate | Tail logs during a 5-minute window of normal traffic | Error count (5xx + unhandled exceptions) = 0; any spike > 5 errors/min triggers investigation |

### 1.4 Resource Utilization (CPU, Memory, Storage)

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| D22 | API process CPU under idle load | `top`/`ps` or Docker stats while API runs with no traffic | CPU < 5% per worker; no spin loops |
| D23 | API process memory under idle load | Check RSS of `uvicorn`/`fixguide.api.main:app` process | RSS stable, no unbounded growth over 30 min idle |
| D24 | Memory under concurrent load | Run 20 concurrent sessions (as in D11) while sampling RSS | Memory growth bounded; no OOM kill; RSS returns toward baseline after sessions complete |
| D25 | Qdrant vector store memory/disk | Query Qdrant `/collections` and check Docker stats for `qdrant` | Collection exists; disk usage < 80% of allocated volume; no OOM |
| D26 | Disk usage for logs and data | `df -h` on the workspace/logs volume; `du -sh logs/ data/` | Logs + data < 80% of partition; `logs/fixguide.log` < 100 MB between rotations |
| D27 | Embedding model loads on correct device | Check `config/settings.yaml` `embedding.device` and logs at startup | Model loads on CPU (default) or configured GPU; startup completes without CUDA errors when CPU-only |
| D28 | Container resource limits (if Dockerized) | `docker compose ps` + `docker stats` | Containers run within declared `mem_limit`/`cpus`; no restart loops |

### 1.5 System Architecture Integrity

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| D29 | Layer separation enforced | Inspect `src/fixguide/` — `core/` imports nothing from `api/` or `services/`; `api/` only depends on `core` + `graph` | No circular imports; `uv run mypy src/` passes |
| D30 | Type checking clean | `make typecheck` | `mypy` exits 0 with no errors |
| D31 | Linting clean | `make lint` | `ruff check` exits 0 |
| D32 | Formatting clean | `make format-check` | `ruff format --check` passes |
| D33 | Configuration centralized | All runtime settings readable from `config/settings.yaml` + `.env` | No hardcoded endpoints, API keys, or model names in `src/` |
| D34 | Environment variables documented | Compare `.env.example` keys against code that reads `os.environ` | Every env var used in code is listed in `.env.example` with a default or note |
| D35 | Prompt templates versioned and valid | Load each `config/prompts/*.yaml` and render with Jinja2 using sample state | All 6 templates (`product_id`, `risk_gate`, `step_generator`, `grounding_verifier`, `vision_verifier`, `reassembly`) render without exceptions |
| D36 | Retrieval weights sum to 1.0 | Read BM25/dense weights from config | BM25 weight + dense weight == 1.0 (e.g., 0.3 / 0.7) |
| D37 | Safety architecture layers present | Trace code path: risk_gate (pre-generation) → grounding_verifier (post-generation) → vision_verifier (runtime) | All three layers implemented and independently testable via `fixguide.cli eval risk-gate`, `eval retrieval`, `eval vision` |
| D38 | Test suite passes | `make test` | `pytest` exits 0; no failures |
| D39 | Evaluation suite passes | `make eval` | All four evals (retrieval, risk-gate, vision, e2e) run and report metrics above defined thresholds |
| D40 | CI pipeline green | Check `.github/workflows` and latest run status | Build, lint, typecheck, and tests pass on push/PR |

---

## 2. User's Perspective

Focus: UI/UX responsiveness, end-to-end functional workflows, feature accessibility, seamlessness of user journey.

### 2.1 UI/UX Responsiveness

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| U1 | Page / initial view loads quickly | Open the frontend/static UI; measure time to first meaningful paint | < 3 s on a standard broadband connection |
| U2 | Form submission acknowledges receipt | Submit the repair-start form (category, problem, skill, tools) | UI shows a loading state immediately; no double-submission on rapid clicks |
| U3 | Step content renders without layout shift | Observe the step card as generation completes | Text/images populate within the card; no jumping or content reflow after render |
| U4 | Photo upload provides feedback | Select and upload a progress photo | Thumbnail preview appears; upload progress indicator shown; success/error toast after completion |
| U5 | Error messages are user-friendly | Trigger an error (e.g., unsupported file type, network loss) | Inline message explains what went wrong in plain language; offers a retry action; no raw stack traces |
| U6 | Navigation between steps is consistent | Advance through ≥3 steps using photo verification | "Next step" replaces current step; step counter increments; back/return behavior predictable |
| U7 | Mobile/responsive layout | Open UI on a mobile viewport (or DevTools device toolbar) | Form fields, buttons, and photo upload are tappable; no horizontal scrolling; readable text |
| U8 | Loading skeletons/spinners during LLM calls | Start a repair and wait for step generation | Skeleton/spinner visible for the entire generation period; UI never appears frozen |

### 2.2 End-to-End Functional Workflows

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| U9 | Full repair session: start → first step | Select "game_controller", describe drift, choose beginner skill, list tools | Step 1 appears with actionable instruction and at least one source citation |
| U10 | Full repair session: verify → advance | Upload a photo matching the expected state for Step 1 | System advances to Step 2; confirmation message shown |
| U10b | Full repair session: mismatch correction | Upload a photo that does NOT match expected state | System rejects with corrective feedback and regenerates the current step |
| U11 | Full repair session: completion → reassembly | Complete all steps through final node | Reassembly checklist + final test procedure generated and displayed |
| U12 | Safety gate blocks dangerous repair | Choose a hard-blocked product (microwave, gas appliance) | Refusal screen appears with safety explanation; no repair steps offered |
| U13 | Caution category flow | Choose "table lamp" or "table fan" | Warning shown but session proceeds; extra safety steps included |
| U14 | Personalization adapts to skill level | Run same problem with `beginner` vs `experienced` | Beginner gets more granular steps + tool explanations; experienced gets concise steps |
| U15 | Personalization adapts to available tools | Submit session with `available_tools: []` vs full toolkit | Steps reference only available tools or suggest alternatives |
| U16 | Session persistence / resume | Start a session, close/reopen browser (or simulate with same `session_id`) | Session state recovered; user resumes at current step without data loss |
| U17 | Multi-category support | Run the flow for each of the 6 documented categories (game_controller, wired_headphones, lamp, remote_control, keyboard, table_fan) | Each returns category-appropriate steps and citations |

### 2.3 Feature Accessibility

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| U18 | Keyboard navigation | Tab through the entire repair flow without a mouse | All interactive elements (inputs, buttons, upload zone) reachable and activatable via Enter/Space |
| U19 | Screen reader labels | Inspect form fields and buttons for `aria-label`/`aria-labelledby` | Every input has an associated label; image upload zone has descriptive text; status changes announced |
| U20 | Color contrast | Run an accessibility audit (e.g., axe, Lighthouse) on the UI | Contrast ratio ≥ 4.5:1 for normal text; no contrast violations |
| U21 | Image alt text / descriptions | Verify uploaded product images and progress photos | Each image has alt text or a programmatically associated description |
| U22 | Font sizing / zoom | Zoom browser to 200% | UI remains usable; no clipping or overlap; no horizontal scrolling required |
| U23 | Focus indicators | Tab through controls | Visible focus ring/outline on every focused element |
| U24 | Language / locale | Confirm all user-facing strings are externalized | No hardcoded English strings in UI components; i18n-ready structure present |

### 2.4 Seamlessness of Overall User Journey

| # | Checklist Item | Verification Step | Healthy State Indicator |
|---|----------------|-------------------|-------------------------|
| U25 | Onboarding clarity | First-time user opens the app | Purpose of app (repair guidance via image + description) is understandable within 10 seconds; no blank screen |
| U26 | Input guidance | Fill the start form | Placeholders, tooltips, or examples guide category/skill/tool selection; validation prevents clearly invalid submissions |
| U27 | Progress transparency | Mid-repair | User always knows: current step number, total steps (if known), completed steps, and what is expected next |
| U28 | Vision verification guidance | Before uploading a progress photo | UI shows what the photo should capture (e.g., "show the battery connector disconnected") |
| U29 | Error recovery | Hit a failure at any point (network, vision mismatch, safety block) | Clear "try again", "go back", or "start over" options; user never reaches a dead end |
| U30 | End-to-end completion time | Complete a full repair session end-to-end | Total time is reasonable for the task (e.g., < 10 min for a beginner controller repair); user feels guided, not lost |
| U31 | Reassembly output usefulness | Finish a repair and read the reassembly checklist | Checklist is ordered, checkable, and includes a final test procedure; user can verify the repair worked |
| U32 | Cross-session continuity | Start a repair on one device, continue on another (or refresh mid-session) | Progress is retained; no need to re-upload photos or re-describe the problem |
| U33 | No jarring transitions | Move between start → step → verification → completion | Consistent visual theme; animations/transitions smooth; no abrupt full-page reloads mid-flow |

---

## How to Use This Checklist

1. **Developer review**: Run items D1–D40 against a staging or production candidate build. Mark each item Pass/Fail with the observed evidence (command output, log excerpt, metric value).
2. **User review**: Walk through items U1–U33 manually (or via automated UI tests) on the deployed frontend. Record screenshots or session recordings for failures.
3. **Release gate**: A release is healthy only when all critical items (marked implicitly by the safety, stability, and E2E workflow rows) pass; non-critical UI polish items may be tracked as follow-ups.
