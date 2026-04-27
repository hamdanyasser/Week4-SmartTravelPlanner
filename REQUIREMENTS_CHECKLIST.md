# Requirements Checklist — AtlasBrief

This file maps every requirement from the Week 4 Smart Travel Planner brief
to a concrete location in this repo and its current build status.

Statuses: `TODO`, `IN_PROGRESS`, `DONE`.

The "Code review note" column is a one-line beginner-friendly explanation
of what we plan to do and why — the long version goes in `CODE_REVIEW_NOTES.md`.

---

## 1. ML Classifier — destination travel style

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 1.1 | 100–200 destinations, hand-labeled | `data/destinations.csv` | DONE | 131 destinations, 9 features, 6 labels. Labeling rules documented in README §ML. |
| 1.2 | 6 travel-style labels (Adventure, Relaxation, Culture, Budget, Luxury, Family) | `backend/app/schemas/trip_brief.py` (`TravelStyle` enum), `backend/app/ml/train_classifier.py` (`LABELS`) | DONE | The enum from Day 1 is the shared vocabulary; the trainer validates the CSV against it. |
| 1.3 | sklearn `Pipeline` (preprocessing inside) | `backend/app/ml/train_classifier.py` (`build_pipelines`) | DONE | Each candidate is `StandardScaler + classifier` in one Pipeline so CV refits the scaler per fold (no leakage). |
| 1.4 | Compare ≥3 classifiers with k-fold CV | `backend/app/ml/train_classifier.py` (`cross_val_summary`) | DONE | LogReg, RandomForest, GradientBoosting via `StratifiedKFold(k=5)`. |
| 1.5 | Accuracy + macro-F1 mean & std | `backend/app/ml/results.csv` | DONE | Both metrics recorded per model with std. |
| 1.6 | Tune ≥1 model | `backend/app/ml/train_classifier.py` (`tune_random_forest`) | DONE | `GridSearchCV` over `n_estimators × max_depth × min_samples_split`. Justification in README. |
| 1.7 | Per-class metrics (class imbalance honesty) | `backend/app/ml/train_classifier.py` (`per_class_report`) | DONE | `classification_report` on `cross_val_predict` of the winner. |
| 1.8 | `results.csv` — every experiment logged | `backend/app/ml/results.csv` | DONE | One row per candidate per run, plus the tuned variant; `winner=yes` flag. |
| 1.9 | Save best model with joblib | `backend/app/ml/model.joblib` | DONE | Winner is whichever candidate has the highest mean macro-F1 — currently logistic_regression (0.959). |
| 1.10 | Pinned deps + fixed seeds | `backend/requirements.txt`, `backend/app/ml/train_classifier.py` | DONE | `pandas==2.2.3`, `scikit-learn==1.5.2`, `joblib==1.4.2`; `random_state=42` everywhere. |

## 2. RAG Tool

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 2.1 | 10–15 destinations, 20–30 documents | `backend/app/rag/knowledge/` | TODO | One markdown file per source; folder per destination. |
| 2.2 | Embeddings in Postgres via pgvector | `backend/app/rag/index.py` + `db.embeddings` table | TODO | Same DB as users/runs — one truth, one connection pool. |
| 2.3 | Justified chunk size + overlap | `backend/app/rag/chunking.py` | TODO | Chosen by experimenting on hand-written queries; rationale in README. |
| 2.4 | Tested retrieval with hand-written queries | `backend/app/rag/eval_queries.py` | TODO | Smoke tests for retrieval quality before plugging into the agent. |

## 3. Agent — exactly 3 tools

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 3.1 | `retrieve_destination_knowledge` tool | `backend/app/agent/tools/retrieve.py` | TODO | Wraps the RAG retriever. |
| 3.2 | `classify_travel_style` tool | `backend/app/agent/tools/classify.py` | TODO | Calls the loaded ML model. |
| 3.3 | `fetch_live_conditions` tool | `backend/app/agent/tools/live.py` | TODO | Weather + flights via httpx.AsyncClient. |
| 3.4 | Pydantic input schemas for every tool | `backend/app/agent/tools/schemas.py` | TODO | One schema per tool — validation lives at the boundary. |
| 3.5 | Explicit tool allowlist | `backend/app/agent/registry.py` | TODO | A frozen set of allowed names; anything else is refused. |
| 3.6 | LangGraph/LangChain agent loop | `backend/app/agent/graph.py` | TODO | Graph nodes = router + tool exec + synthesizer. |
| 3.7 | LangSmith tracing screenshot | `README.md` + `docs/trace.png` | TODO | Multi-tool trace screenshot for the README. |
| 3.8 | Genuine cross-tool synthesis | `backend/app/agent/synthesize.py` | TODO | Final node reasons over conflicting signals (the Decision Tension Board). |

## 4. Two-Model Routing

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 4.1 | Cheap model for mechanical work | `backend/app/llm/router.py` | TODO | Haiku-class for argument extraction + RAG query rewriting. |
| 4.2 | Strong model for final synthesis | `backend/app/llm/router.py` | TODO | Sonnet/Opus for the Decision Tension Board verdict. |
| 4.3 | Token + cost logging per step | `backend/app/llm/usage.py` + `db.tool_calls` | TODO | Every LLM call logs prompt/completion tokens and dollar cost. |

## 5. Persistence — Postgres + pgvector + SQLAlchemy

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 5.1 | Async SQLAlchemy 2.x | `backend/app/db/session.py` | TODO | `AsyncSession` only — no sync sessions in request paths. |
| 5.2 | `users` table | `backend/app/db/models/user.py` | TODO | Owns runs and webhook destinations. |
| 5.3 | `agent_runs` table | `backend/app/db/models/run.py` | TODO | One row per query — who, what, when, final answer. |
| 5.4 | `tool_calls` table | `backend/app/db/models/tool_call.py` | TODO | One row per tool invocation — name, args, result, tokens, cost. |
| 5.5 | `embeddings` table (pgvector) | `backend/app/db/models/embedding.py` | TODO | `Vector(384)` column; index for cosine similarity. |
| 5.6 | Alembic migrations | `backend/alembic/` | TODO | Schema changes are versioned, not improvised. |

## 6. Auth — Sign-Up & Login

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 6.1 | Registration + login routes | `backend/app/api/routes/auth.py` | TODO | `POST /auth/register`, `POST /auth/login`. |
| 6.2 | Password hashing | `backend/app/auth/hashing.py` | TODO | `passlib[bcrypt]` — never store plaintext. |
| 6.3 | JWT sessions | `backend/app/auth/jwt.py` | TODO | Short-lived access token; refresh later if needed. |
| 6.4 | `current_user` dependency | `backend/app/api/deps.py` | TODO | Every protected route uses `Depends(get_current_user)`. |

## 7. React Frontend

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 7.1 | Vite + React + TypeScript shell | `frontend/` | IN_PROGRESS | Day 1 = shell with stub call. |
| 7.2 | Sign-in flow | `frontend/src/pages/SignIn.tsx` | TODO | Wires to `/auth/login`. |
| 7.3 | Chat-style trip query | `frontend/src/pages/BriefingRoom.tsx` | TODO | Calls `/api/v1/trip-briefs`. |
| 7.4 | Tool-trace visibility | `frontend/src/components/ToolTrace.tsx` | TODO | Shows which tools fired and what they returned. |
| 7.5 | Decision Tension Board UI | `frontend/src/components/TensionBoard.tsx` | TODO | Dream Fit vs Reality Pressure → Final Verdict + Counterfactual. |
| 7.6 | Streaming response | `frontend/src/api/stream.ts` | TODO | Optional but worth it for the briefing-room feel. |

## 8. Webhook Delivery

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 8.1 | Send trip plan to a real channel | `backend/app/webhooks/dispatcher.py` | TODO | Discord webhook is the simplest defensible target. |
| 8.2 | Timeout + retry-with-backoff | `backend/app/webhooks/retry.py` | TODO | `tenacity` async retry; 3 attempts, exponential backoff. |
| 8.3 | Failure isolation | `backend/app/webhooks/dispatcher.py` | TODO | Webhook failure is logged but never crashes the user response. |

## 9. Docker — Whole Stack

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 9.1 | Backend container | `backend/Dockerfile` | IN_PROGRESS | Day 1 = working skeleton image. |
| 9.2 | Frontend container | `frontend/Dockerfile` | IN_PROGRESS | Day 1 = working Vite dev image. |
| 9.3 | Postgres + pgvector container | `docker-compose.yml` | IN_PROGRESS | Use `pgvector/pgvector:pg16` image. |
| 9.4 | Named Postgres volume | `docker-compose.yml` | IN_PROGRESS | `pgdata` volume — embeddings survive restarts. |
| 9.5 | One-command startup | `docker-compose.yml` | IN_PROGRESS | `docker compose up` brings everything up. |

## 10. Engineering Standards

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 10.1 | Async all the way down | All routes/tools/db calls | IN_PROGRESS | Day 1 routes are already `async def`. |
| 10.2 | FastAPI `Depends` for DI | `backend/app/api/deps.py` | TODO | LLM client, DB session, current user — all injected. |
| 10.3 | Lifespan singletons | `backend/app/main.py` | IN_PROGRESS | Day 1 sets up the lifespan handler shell. |
| 10.4 | `lru_cache` + TTL caches | `backend/app/cache/` | TODO | TTL on weather; `lru_cache` on settings. |
| 10.5 | `pydantic-settings` Settings class | `backend/app/config.py` | IN_PROGRESS | Day 1 ships a typed Settings — no `os.getenv` elsewhere. |
| 10.6 | Type hints everywhere | All `.py` files | IN_PROGRESS | Enforced by ruff later; we start clean. |
| 10.7 | Pydantic at the boundary | `backend/app/schemas/` | IN_PROGRESS | `TripBriefResponse` ships Day 1. |
| 10.8 | Errors + retries + failure isolation | tools + webhook + LLM calls | TODO | `tenacity` async wrapper + structured tool-error returns. |
| 10.9 | Modular layout — no giant `main.py` | repo structure | IN_PROGRESS | Routes/services/models/agent each get their own module. |
| 10.10 | Structured JSON logs (`structlog`) | `backend/app/logging_config.py` | TODO | No `print` statements anywhere. |
| 10.11 | Linters + pre-commit (ruff, black) | `pyproject.toml`, `.pre-commit-config.yaml` | TODO | Set up before we ship the first PR. |
| 10.12 | `.env.example` listing every key | `backend/.env.example` | IN_PROGRESS | Day 1 stub; grows as we add services. |

## 11. Tests

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 11.1 | Per-tool tests with fake LLM | `backend/tests/test_tools_*.py` | TODO | One test per tool, no network. |
| 11.2 | Pydantic schema valid/invalid tests | `backend/tests/test_schemas.py` | TODO | Lock the boundary contract. |
| 11.3 | End-to-end agent test (mocked APIs) | `backend/tests/test_agent_e2e.py` | TODO | Golden demo path runs in CI. |
| 11.4 | GitHub Actions CI | `.github/workflows/ci.yml` | TODO | Tests run on every push. |

## 12. README Deliverables

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 12.1 | Architecture diagram | `README.md` + `docs/architecture.png` | TODO | One diagram showing user → React → FastAPI → agent → tools → DB. |
| 12.2 | Dataset labeling rules | `README.md` | TODO | Written as we label, not after. |
| 12.3 | Chunking + retrieval rationale | `README.md` | TODO | Why this chunk size, why this k. |
| 12.4 | Model comparison table | `README.md` | TODO | From `results.csv`. |
| 12.5 | Per-query cost breakdown | `README.md` | TODO | From `db.tool_calls` aggregation. |
| 12.6 | LangSmith trace screenshot | `README.md` + `docs/trace.png` | TODO | Multi-tool trace. |
| 12.7 | 3-minute demo video | `docs/demo.mp4` (or link) | TODO | One end-to-end run from UI to webhook. |

## 13. Code Review Discipline

| # | Required item | Where it lives | Status | Code review note |
|---|---|---|---|---|
| 13.1 | `CODE_REVIEW_NOTES.md` updated each major change | `CODE_REVIEW_NOTES.md` | IN_PROGRESS | Plain-language log of what changed and why. |
| 13.2 | No giant files; clear naming | repo-wide | IN_PROGRESS | Reviewed every commit. |
