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
| 2.2 | Embeddings in Postgres via pgvector | `backend/app/models/document_chunk.py`, `backend/app/rag/ingest_documents.py` | DONE | pgvector table + DB ingest path built; deterministic local fallback verified when Postgres is unavailable. |
| 2.3 | Justified chunk size + overlap | `backend/app/rag/chunking.py`, `README.md` | DONE | 900-character chunks with 150-character overlap; rationale documented in README. |
| 2.4 | Tested retrieval with hand-written queries | `backend/app/rag/retriever.py` | DONE | Three manual retrieval probes pass on the local fallback index. |

## 3. Agent - Exactly 3 Tools

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 3.1 | `retrieve_destination_knowledge` tool | `backend/app/tools/retrieve_destination_knowledge.py` | DONE | Pydantic-validated wrapper around the RAG retriever; full agent wiring comes later. |
| 3.2 | `classify_travel_style` tool | `backend/app/agent/tools/classify.py` | TODO | Calls the loaded ML model. |
| 3.3 | `fetch_live_conditions` tool | `backend/app/agent/tools/live.py` | TODO | Weather + flights via async HTTP. |
| 3.4 | Pydantic input schemas for every tool | `backend/app/agent/tools/schemas.py` | TODO | One schema per tool; validation lives at the boundary. |
| 3.5 | Explicit tool allowlist | `backend/app/agent/registry.py` | TODO | A frozen set of allowed names; anything else is refused. |
| 3.6 | LangGraph/LangChain agent loop | `backend/app/agent/graph.py` | TODO | Graph nodes = router, tool execution, synthesizer. |
| 3.7 | LangSmith tracing screenshot | `README.md`, `docs/trace.png` | TODO | Multi-tool trace screenshot for the README. |
| 3.8 | Genuine cross-tool synthesis | `backend/app/agent/synthesize.py` | TODO | Final node reasons over conflicting signals. |

## 4. Two-Model Routing

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 4.1 | Cheap model for mechanical work | `backend/app/llm/router.py` | TODO | Used later for extraction and RAG query rewriting. |
| 4.2 | Strong model for final synthesis | `backend/app/llm/router.py` | TODO | Used later for the Decision Tension Board verdict. |
| 4.3 | Token + cost logging per step | `backend/app/llm/usage.py`, `db.tool_calls` | TODO | Every LLM call logs prompt/completion tokens and cost. |

## 5. Persistence - Postgres + pgvector + SQLAlchemy

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 5.1 | Async SQLAlchemy 2.x | `backend/app/db/session.py` | DONE | Async engine/session factory and dependency are in place. |
| 5.2 | `users` table | `backend/app/db/models/user.py` | TODO | Owns runs and webhook destinations. |
| 5.3 | `agent_runs` table | `backend/app/db/models/run.py` | TODO | One row per query: who, what, when, final answer. |
| 5.4 | `tool_calls` table | `backend/app/db/models/tool_call.py` | TODO | One row per tool invocation: name, args, result, tokens, cost. |
| 5.5 | `embeddings` table / pgvector chunks | `backend/app/models/document_chunk.py` | IN_PROGRESS | RAG chunks use `Vector(384)` + cosine index; broader app embedding table can be revisited with migrations. |
| 5.6 | Alembic migrations | `backend/alembic/` | TODO | Schema changes are versioned, not improvised. |

## 6. Auth - Sign-Up and Login

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 6.1 | Registration + login routes | `backend/app/api/routes/auth.py` | TODO | `POST /auth/register`, `POST /auth/login`. |
| 6.2 | Password hashing | `backend/app/auth/hashing.py` | TODO | Never store plaintext. |
| 6.3 | JWT sessions | `backend/app/auth/jwt.py` | TODO | Short-lived access token. |
| 6.4 | `current_user` dependency | `backend/app/api/deps.py` | TODO | Protected routes use `Depends(get_current_user)`. |

## 7. React Frontend

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 7.1 | Vite + React + TypeScript shell | `frontend/` | IN_PROGRESS | Day 1 shell with stub backend call. |
| 7.2 | Sign-in flow | `frontend/src/pages/SignIn.tsx` | TODO | Wires to `/auth/login`. |
| 7.3 | Chat-style trip query | `frontend/src/pages/BriefingRoom.tsx` | TODO | Calls `/api/v1/trip-briefs`. |
| 7.4 | Tool-trace visibility | `frontend/src/components/ToolTrace.tsx` | TODO | Shows which tools fired and what they returned. |
| 7.5 | Decision Tension Board UI | `frontend/src/components/TensionBoard.tsx` | TODO | Dream Fit vs Reality Pressure, final verdict, counterfactual. |
| 7.6 | Streaming response | `frontend/src/api/stream.ts` | TODO | Optional but useful for briefing-room feel. |

## 8. Webhook Delivery

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 8.1 | Send trip plan to a real channel | `backend/app/webhooks/dispatcher.py` | TODO | Discord webhook is the simplest defensible target. |
| 8.2 | Timeout + retry-with-backoff | `backend/app/webhooks/retry.py` | TODO | Async retry with backoff. |
| 8.3 | Failure isolation | `backend/app/webhooks/dispatcher.py` | TODO | Webhook failure is logged but never crashes the user response. |

## 9. Docker - Whole Stack

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 9.1 | Backend container | `backend/Dockerfile` | IN_PROGRESS | Working skeleton image. |
| 9.2 | Frontend container | `frontend/Dockerfile` | IN_PROGRESS | Working Vite dev image. |
| 9.3 | Postgres + pgvector container | `docker-compose.yml` | IN_PROGRESS | Uses `pgvector/pgvector:pg16`. |
| 9.4 | Named Postgres volume | `docker-compose.yml` | IN_PROGRESS | `pgdata` volume keeps embeddings across restarts. |
| 9.5 | One-command startup | `docker-compose.yml` | IN_PROGRESS | `docker compose up` brings the stack up when Docker is healthy. |

## 10. Engineering Standards

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 10.1 | Async all the way down | Routes/tools/db calls | IN_PROGRESS | Routes and RAG tool are async where they cross app boundaries. |
| 10.2 | FastAPI `Depends` for DI | `backend/app/db/session.py` | IN_PROGRESS | DB session dependency exists; LLM/current_user dependencies still later. |
| 10.3 | Lifespan singletons | `backend/app/main.py` | IN_PROGRESS | Lifespan hook exists; future DB/model loading goes there. |
| 10.4 | `lru_cache` + TTL caches | `backend/app/cache/` | TODO | TTL caches land with live-condition APIs. |
| 10.5 | `pydantic-settings` Settings class | `backend/app/config.py` | IN_PROGRESS | Settings now includes RAG embedding config too. |
| 10.6 | Type hints everywhere | All `.py` files | IN_PROGRESS | New RAG/DB modules are typed. |
| 10.7 | Pydantic at the boundary | `backend/app/schemas/` | IN_PROGRESS | Trip brief and RAG tool schemas exist. |
| 10.8 | Errors + retries + failure isolation | tools + webhook + LLM calls | TODO | Retry wrappers land with external APIs. |
| 10.9 | Modular layout - no giant `main.py` | repo structure | IN_PROGRESS | RAG, DB, models, schemas, and tools are split by concern. |
| 10.10 | Structured JSON logs | `backend/app/logging_config.py` | TODO | Not added yet. |
| 10.11 | Linters + pre-commit | `pyproject.toml`, `.pre-commit-config.yaml` | TODO | Set up before broad feature work. |
| 10.12 | `.env.example` listing every key | `backend/.env.example` | IN_PROGRESS | Template now includes RAG embedding settings. |

## 11. Tests

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 11.1 | Per-tool tests with fake LLM | `backend/tests/test_tools_*.py` | TODO | One test per tool, no network. |
| 11.2 | Pydantic schema valid/invalid tests | `backend/tests/test_schemas.py` | TODO | Lock the boundary contract. |
| 11.3 | End-to-end agent test | `backend/tests/test_agent_e2e.py` | TODO | Golden demo path runs with mocked APIs. |
| 11.4 | GitHub Actions CI | `.github/workflows/ci.yml` | TODO | Tests run on every push. |

## 12. README Deliverables

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 12.1 | Architecture diagram | `README.md`, `docs/architecture.png` | TODO | One diagram showing user to React to FastAPI to tools to DB. |
| 12.2 | Dataset labeling rules | `README.md` | DONE | ML labeling rules documented. |
| 12.3 | Chunking + retrieval rationale | `README.md` | DONE | RAG section explains chunk size, overlap, embeddings, fallback, and top-k retrieval. |
| 12.4 | Model comparison table | `README.md` | DONE | Latest ML table documented. |
| 12.5 | Per-query cost breakdown | `README.md` | TODO | Lands with LLM/tool-call persistence. |
| 12.6 | LangSmith trace screenshot | `README.md`, `docs/trace.png` | TODO | Multi-tool trace. |
| 12.7 | 3-minute demo video | `docs/demo.mp4` or link | TODO | One end-to-end run from UI to webhook. |

## 13. Code Review Discipline

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 13.1 | `CODE_REVIEW_NOTES.md` updated each major change | `CODE_REVIEW_NOTES.md` | IN_PROGRESS | Plain-language log of what changed and why. |
| 13.2 | No giant files; clear naming | repo-wide | IN_PROGRESS | Reviewed every commit. |
