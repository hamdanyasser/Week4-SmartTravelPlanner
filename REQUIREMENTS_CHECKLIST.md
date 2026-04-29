# Requirements Checklist - AtlasBrief

This file maps every requirement from the Week 4 Smart Travel Planner brief
to a concrete location in this repo and its current build status.

Statuses: `TODO`, `IN_PROGRESS`, `DONE`.

The "Code review note" column is a one-line beginner-friendly explanation.
The longer reasoning lives in `CODE_REVIEW_NOTES.md`.

---

## 1. ML Classifier - Destination Travel Style

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 1.1 | 100-200 destinations, hand-labeled | `data/destinations.csv` | DONE | 131 destinations, 9 features, 6 labels. Labeling rules documented in README ML section. |
| 1.2 | 6 travel-style labels | `backend/app/schemas/trip_brief.py`, `backend/app/ml/train_classifier.py` | DONE | The enum from Day 1 is the shared vocabulary; the trainer validates the CSV against it. |
| 1.3 | sklearn `Pipeline` with preprocessing inside | `backend/app/ml/train_classifier.py` | DONE | Each candidate is `StandardScaler + classifier`, so CV refits scaling per fold. |
| 1.4 | Compare at least 3 classifiers with k-fold CV | `backend/app/ml/train_classifier.py` | DONE | Logistic Regression, Random Forest, Gradient Boosting via stratified 5-fold CV. |
| 1.5 | Accuracy + macro-F1 mean and std | `backend/app/ml/results.csv` | DONE | Both metrics are recorded per model with standard deviation. |
| 1.6 | Tune at least one model | `backend/app/ml/train_classifier.py` | DONE | `GridSearchCV` tunes Random Forest. |
| 1.7 | Per-class metrics | `backend/app/ml/train_classifier.py` | DONE | `classification_report` on cross-validated predictions. |
| 1.8 | `results.csv` experiment log | `backend/app/ml/results.csv` | DONE | One row per candidate per run, plus tuned variant and winner flag. |
| 1.9 | Save best model with joblib | `backend/app/ml/model.joblib` | DONE | Current winner is Logistic Regression at mean macro-F1 0.959. |
| 1.10 | Pinned deps + fixed seeds | `backend/requirements.txt`, `backend/app/ml/train_classifier.py` | DONE | ML deps pinned and `random_state=42` is used. |

## 2. RAG Tool

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 2.1 | 10-15 destinations, 20-30 documents | `data/knowledge/` | DONE | 28 markdown docs across 14 destinations, each with destination/source metadata. |
| 2.2 | Embeddings in Postgres via pgvector | `backend/app/models/document_chunk.py`, `backend/app/rag/ingest_documents.py` | IN_PROGRESS | pgvector table + DB ingest path built; live ingest is blocked by Docker daemon unavailability on this machine. |
| 2.3 | Justified chunk size + overlap | `backend/app/rag/chunking.py`, `README.md` | DONE | 900-character chunks with 150-character overlap; rationale documented in README. |
| 2.4 | Tested retrieval with hand-written queries | `backend/app/rag/retriever.py`, `backend/app/rag/smoke_test.py` | DONE | Three manual retrieval probes pass on the local fallback index; smoke test verifies the tool wrapper and schemas. |

## 3. Agent - Exactly 3 Tools

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 3.1 | `retrieve_destination_knowledge` tool | `backend/app/tools/retrieve_destination_knowledge.py` | DONE | Pydantic-validated wrapper around the DB-first/local-fallback RAG retriever. |
| 3.2 | `classify_travel_style` tool | `backend/app/tools/classify_travel_style.py` | DONE | Calls the loaded joblib model and falls back to deterministic rules if the model is unavailable. |
| 3.3 | `fetch_live_conditions` tool | `backend/app/tools/fetch_live_conditions.py` | DONE | Async weather path with deterministic fallback; no `requests.get` in async code. |
| 3.4 | Pydantic input schemas for every tool | `backend/app/schemas/tools.py`, `backend/app/schemas/rag.py` | DONE | Every tool validates input and output at the boundary. |
| 3.5 | Explicit tool allowlist | `backend/app/agent/registry.py` | DONE | Only the three required tool names are accepted. |
| 3.6 | LangGraph/LangChain agent loop | `backend/app/agent/graph.py` | DONE | Small LangGraph flow: extract plan, run three tools, synthesize. |
| 3.7 | LangSmith tracing screenshot | `README.md`, `docs/trace.png` | TODO | Multi-tool trace screenshot for the README. |
| 3.8 | Genuine cross-tool synthesis | `backend/app/agent/synthesize.py` | DONE | Final synthesis names the tension between RAG/ML dream fit and live/fallback reality pressure. |

## 4. Two-Model Routing

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 4.1 | Cheap model for mechanical work | `backend/app/llm/router.py` | DONE | Deterministic fallback extractor keeps the cheap-model step shape until a provider key is added. |
| 4.2 | Strong model for final synthesis | `backend/app/llm/router.py`, `backend/app/agent/synthesize.py` | DONE | Deterministic fallback synthesizer keeps the strong-model step shape until a provider key is added. |
| 4.3 | Token + cost logging per step | `backend/app/schemas/llm.py`, `backend/app/agent/synthesize.py`, `backend/app/models/agent_run.py` | DONE | Usage metadata is recorded per routing step where available and surfaced in `TripBriefResponse.meta`. |

## 5. Persistence - Postgres + pgvector + SQLAlchemy

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 5.1 | Async SQLAlchemy 2.x | `backend/app/db/session.py` | DONE | Async engine/session factory and dependency are in place. |
| 5.2 | `users` table | `backend/app/models/user.py` | DONE | Stores registered users and bcrypt password hashes. |
| 5.3 | `agent_runs` table | `backend/app/models/agent_run.py` | DONE | One row per query: optional user, status, response JSON, token/cost metadata. |
| 5.4 | `tool_calls` table | `backend/app/models/tool_call.py` | DONE | One row per tool invocation with args, output, status, and structured error text. |
| 5.5 | `embeddings` table / pgvector chunks | `backend/app/models/document_chunk.py` | IN_PROGRESS | RAG chunks use `Vector(384)` + cosine index; live table creation awaits a reachable Docker/Postgres environment. |
| 5.6 | Alembic migrations | `backend/alembic/` | DONE | `alembic.ini`, `alembic/env.py`, and `versions/0001_initial.py` create all six tables and enable pgvector; `alembic upgrade head --sql` renders valid offline DDL. |

## 6. Auth - Sign-Up and Login

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 6.1 | Registration + login routes | `backend/app/api/routes/auth.py` | DONE | `POST /auth/register`, `POST /auth/login`, and `GET /auth/me`. |
| 6.2 | Password hashing | `backend/app/auth/hashing.py` | DONE | Bcrypt hashes passwords; plaintext is never stored. |
| 6.3 | JWT sessions | `backend/app/auth/jwt.py` | DONE | JWT access tokens use `JWT_SECRET_KEY` from settings. |
| 6.4 | `current_user` dependency | `backend/app/api/deps.py` | DONE | Provides required and optional user dependencies through FastAPI `Depends`. |

## 7. React Frontend

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 7.1 | Vite + React + TypeScript shell | `frontend/` | DONE | Briefing-room shell with hero, prompt console, Trip DNA, timeline, tension board, memo, evidence drawer. |
| 7.2 | Sign-in flow | `frontend/src/components/AuthPanel.tsx`, `frontend/src/hooks/useAuth.ts` | DONE | Collapsible AuthPanel above the prompt console handles `/auth/register` and `/auth/login`; the JWT is persisted in localStorage and sent as a Bearer header on subsequent trip briefs. Anonymous use still works. |
| 7.3 | Chat-style trip query | `frontend/src/components/CinematicPromptBox.tsx` | DONE | Premium intake console with serif textarea, scenario chips, Cmd/Ctrl+Enter submit. |
| 7.4 | Tool-trace visibility | `frontend/src/components/AgentTimeline.tsx`, `frontend/src/components/EvidenceDrawer.tsx` | DONE | Mission timeline animates the seven backend stages and shows the real `tools_used` summaries when the response lands; Evidence drawer surfaces tool calls and run accounting. |
| 7.5 | Decision Tension Board UI | `frontend/src/components/DecisionTensionBoard.tsx` | DONE | Dream Fit (brass) vs Reality Pressure (verdigris) score cards, editorial Final Verdict with tri-color top rule, terracotta counterfactual card. |
| 7.6 | Streaming response | `frontend/src/api/stream.ts` | TODO | Optional. Current build animates a fake-but-honest progress timeline; real streaming would unlock per-stage updates. |

## 8. Webhook Delivery

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 8.1 | Send trip plan to a real channel | `backend/app/webhooks/dispatcher.py` | DONE | Discord webhook delivery is implemented and skipped safely when no URL is configured. |
| 8.2 | Timeout + retry-with-backoff | `backend/app/webhooks/dispatcher.py` | DONE | Uses async HTTP timeout plus retry/backoff. |
| 8.3 | Failure isolation | `backend/app/webhooks/dispatcher.py`, `backend/app/smoke_test.py` | DONE | Webhook failure is verified not to crash the user response path. |

## 9. Docker - Whole Stack

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 9.1 | Backend container | `backend/Dockerfile` | IN_PROGRESS | Working skeleton image. |
| 9.2 | Frontend container | `frontend/Dockerfile` | IN_PROGRESS | Working Vite dev image. |
| 9.3 | Postgres + pgvector container | `docker-compose.yml` | IN_PROGRESS | Compose config passes; live container start is blocked here because Docker Desktop is not reachable. |
| 9.4 | Named Postgres volume | `docker-compose.yml` | IN_PROGRESS | `pgdata` volume keeps embeddings across restarts. |
| 9.5 | One-command startup | `docker-compose.yml` | IN_PROGRESS | `docker compose up` is configured; live startup still needs a running Docker daemon. |

## 10. Engineering Standards

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 10.1 | Async all the way down | Routes/tools/db/webhook calls | DONE | Trip brief, auth, tools, DB, and webhook paths use async interfaces where they cross app boundaries. |
| 10.2 | FastAPI `Depends` for DI | `backend/app/db/session.py`, `backend/app/api/deps.py` | DONE | DB session and current-user dependencies are wired through FastAPI. |
| 10.3 | Lifespan singletons | `backend/app/main.py` | DONE | Lifespan creates the agent and loads the joblib model once per process. |
| 10.4 | `lru_cache` + TTL caches | `backend/app/cache/` | TODO | TTL caches land with live-condition APIs. |
| 10.5 | `pydantic-settings` Settings class | `backend/app/config.py` | DONE | Settings includes app, DB, RAG, auth, routing, live conditions, and webhook config. |
| 10.6 | Type hints everywhere | All `.py` files | IN_PROGRESS | New RAG/DB modules are typed. |
| 10.7 | Pydantic at the boundary | `backend/app/schemas/` | DONE | Trip brief, auth, RAG, LLM usage, and tool schemas validate API/tool boundaries. |
| 10.8 | Errors + retries + failure isolation | tools + webhook + LLM calls | DONE | Tool errors are structured and webhook failures never break the trip-brief response. |
| 10.9 | Modular layout - no giant `main.py` | repo structure | DONE | Agent, auth, DB, LLM, ML, RAG, schemas, tools, persistence, and webhooks are split by concern. |
| 10.10 | Structured JSON logs | `backend/app/logging_config.py` | TODO | Not added yet. |
| 10.11 | Linters + pre-commit | `pyproject.toml`, `.pre-commit-config.yaml` | TODO | Set up before broad feature work. |
| 10.12 | `.env.example` listing every key | `backend/.env.example` | DONE | Template lists app, DB, RAG, auth, routing, weather, and webhook settings. |

## 11. Tests

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 11.1 | Per-tool tests with fake LLM | `backend/app/smoke_test.py` | IN_PROGRESS | Smoke script verifies all three allowlisted tools through the agent without external services. |
| 11.2 | Pydantic schema valid/invalid tests | `backend/app/smoke_test.py` | IN_PROGRESS | Smoke script exercises current schemas; formal pytest coverage is still future work. |
| 11.3 | End-to-end agent test | `backend/app/smoke_test.py` | IN_PROGRESS | Golden demo path runs through the LangGraph agent with deterministic fallbacks. |
| 11.4 | GitHub Actions CI | `.github/workflows/ci.yml` | TODO | Tests run on every push. |

## 12. README Deliverables

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 12.1 | Architecture diagram | `docs/architecture.md`, `README.md` | DONE | ASCII architecture diagram + per-request flow + real-vs-fallback table in `docs/architecture.md`. |
| 12.2 | Dataset labeling rules | `README.md` | DONE | ML labeling rules documented. |
| 12.3 | Chunking + retrieval rationale | `README.md` | DONE | RAG section explains chunk size, overlap, embeddings, fallback, and top-k retrieval. |
| 12.4 | Model comparison table | `README.md` | DONE | Latest ML table documented. |
| 12.5 | Per-query cost breakdown | `TripBriefResponse.meta`, `backend/app/models/agent_run.py` | IN_PROGRESS | Deterministic routing records zero-cost token metadata; real provider pricing still awaits provider integration. |
| 12.6 | LangSmith trace screenshot | `README.md`, `docs/trace.png` | TODO | Multi-tool trace. |
| 12.7 | 3-minute demo video | `docs/demo.mp4` or link | TODO | One end-to-end run from UI to webhook. |

## 13. Code Review Discipline

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 13.1 | `CODE_REVIEW_NOTES.md` updated each major change | `CODE_REVIEW_NOTES.md` | DONE | Plain-language log is updated for backend agent/auth/persistence/webhook work. |
| 13.2 | No giant files; clear naming | repo-wide | DONE | Backend pieces are split into small modules by concern. |
