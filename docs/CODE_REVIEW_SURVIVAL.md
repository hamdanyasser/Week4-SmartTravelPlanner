# AtlasBrief — Code Review Survival Guide

A single-page brief for the Saturday review. Read this before walking
into the room. It is structured so you can defend any line of the
project without paging through code.

---

## 1. 90-second project explanation

> AtlasBrief is an AI travel briefing room. The user shows up with one
> fuzzy travel question — `"two weeks in July, around $1,500, warm,
> hiking, not too touristy, where should I go?"` — and walks out with a
> defended recommendation.
>
> The signature feature is the **Decision Tension Board**. Every
> recommendation surfaces four pieces in this order:
>
> 1. **Dream Fit** (0–100, how well a destination matches the user's
>    vibe — fed by ML + RAG).
> 2. **Reality Pressure** (0–100, inverted: 100 = no pressure, 0 = high
>    — fed by live conditions).
> 3. **Final Verdict** — one paragraph that *names the tradeoff*.
> 4. **Why Not the Obvious Pick?** — a counterfactual explaining the
>    obvious choice we didn't take.
>
> Under the hood: FastAPI + a small LangGraph agent with **exactly three
> allowlisted tools** (RAG, ML, live conditions), Postgres + pgvector
> for embeddings + persistence, JWT auth, Discord webhook with
> isolated failure, and a Vite/React/TypeScript briefing-room UI.

## 2. Full request flow (golden demo query)

1. SPA POSTs `/api/v1/trip-briefs { query }` (Bearer JWT optional).
2. `get_optional_current_user` resolves the user (or `None`).
3. `create_agent_run` writes an `agent_runs` row (best-effort).
4. LangGraph runs `plan_step → tools_step → synthesize_step`.
5. `tools_step` invokes the allowlist registry: `retrieve_destination_knowledge`,
   `classify_travel_style`, `fetch_live_conditions` — each Pydantic-validated.
6. `synthesize_trip_brief` builds the Decision Tension Board, with
   per-tool human-readable trace summaries.
7. `latency_ms` is captured around the agent call.
8. `persist_tool_calls` + `finish_agent_run` save inputs, outputs, and
   final response JSON.
9. `BackgroundTasks` schedules `deliver_discord_webhook` (timeout +
   retry/backoff + isolated failure).
10. Response renders the Hero → Trip DNA → Timeline → Tension Board →
    Memo → Evidence drawer.

## 3. ML flow

- **Dataset.** `data/destinations.csv` — 131 hand-labeled destinations
  with 9 numeric features and 6 labels (Adventure / Relaxation /
  Culture / Budget / Luxury / Family). Single-dominant-style labeling
  rule documented in the README.
- **Trainer.** `backend/app/ml/train_classifier.py` builds three
  `Pipeline(StandardScaler → classifier)` candidates (Logistic
  Regression, Random Forest, Gradient Boosting), runs stratified
  5-fold CV, then `GridSearchCV` over Random Forest. Picks the winner
  by mean macro-F1 (LR at 0.959 currently). Per-class
  `classification_report` uses `cross_val_predict`.
- **Artifact.** `backend/app/ml/model.joblib` is loaded once in the
  FastAPI lifespan and passed into the `classify_travel_style` tool.
- **Fallback.** `fallback_classification` returns a deterministic
  rule-based label if the model fails to load.

## 4. RAG flow

- **Corpus.** `data/knowledge/` — 28 markdown destination documents
  across 14 destinations. Each document has YAML-style frontmatter
  for `destination`, `source_title`, `source_type`.
- **Chunking.** 900 chars with 150-char overlap. Justified in the
  README — short briefs, one coherent travel idea per chunk, overlap
  protects sentences crossing boundaries. Produces 28 chunks.
- **Embeddings.** Default is `deterministic-hashing-v1` (384-dim local
  hashing vector — no network, no secrets). `EMBEDDING_PROVIDER=`
  pluggable for OpenAI/Ollama/external.
- **Storage.** Postgres `document_chunks.embedding` is a
  `pgvector.Vector(384)` with an `ivfflat` cosine index.
- **Retriever.** `retrieve_from_db` first, falling back to
  `retrieve_from_local` on failure or absence of a session.

## 5. Agent / tool flow

- **LangGraph** (`backend/app/agent/graph.py`) compiles a 3-node graph:
  `plan → tools → synthesize`.
- **Allowlist** (`backend/app/agent/registry.py`) exposes a frozen set
  of three tool names. Anything not in `TOOL_SPECS` is refused with a
  structured `ToolError`.
- **Pydantic at the boundary.** Every tool input has a Pydantic schema
  (`ClassifyTravelStyleInput`, `FetchLiveConditionsInput`,
  `DestinationKnowledgeQuery`) and every tool output has a Pydantic
  model.
- **Structured failures.** Any tool exception is converted into a
  `ToolExecutionResult(ok=False, error=ToolError(...))` so the
  synthesis step never crashes the user response.
- **Tracing.** `synthesize._summarize_tool` produces tool-specific,
  human-readable trace strings (e.g., `"Predicted Adventure (joblib
  model, confidence 0.93)"`).

## 6. Auth / persistence flow

- **Routes.** `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- **Hashing.** `bcrypt` via `app.auth.hashing`.
- **JWT.** PyJWT, `JWT_SECRET_KEY` from settings; user id in `sub`.
- **Dependencies.** `get_current_user` (required) and
  `get_optional_current_user` (anonymous-friendly) live in
  `backend/app/api/deps.py`.
- **DB session.** Async SQLAlchemy 2.x: `get_engine`, `get_session_factory`,
  `get_session` are all in `backend/app/db/session.py`.
- **Tables.** `users`, `agent_runs`, `tool_calls`,
  `webhook_deliveries`, `destination_documents`, `document_chunks`.
- **Migrations.** Alembic with one initial revision
  (`backend/alembic/versions/0001_initial.py`).

## 7. Webhook flow

- `deliver_discord_webhook` posts a one-line summary to a Discord
  channel via `httpx.AsyncClient`.
- `tenacity.AsyncRetrying` retries on `httpx.HTTPError` / `TimeoutError`
  up to `WEBHOOK_MAX_ATTEMPTS` with exponential backoff.
- Every attempt is recorded as a `webhook_deliveries` row.
- A failure never raises into the user path: it returns a
  `WebhookResult(status="failed", ...)` and the brief is still rendered.

## 8–13. Why these choices

- **Why FastAPI + React + Postgres?** FastAPI gives async, dependency
  injection, and Pydantic at the boundary out of the box. React + Vite
  + TypeScript gives strict typing and a lean SPA. Postgres + pgvector
  keeps embeddings and app data in one DB so we don't run two stores.
- **Why Pydantic?** It is the brief's required boundary. Tool inputs
  and outputs are validated where data crosses trust boundaries, and
  trusted everywhere downstream — fewer try/except blocks, fewer
  silent format bugs.
- **Why `Pipeline` + CV + macro-F1?** The brief is explicit about
  leakage. `Pipeline(StandardScaler → classifier)` re-fits the scaler
  on each training fold, so the validation fold never leaks into the
  scaler's mean/std. Macro-F1 (over per-class F1) is the right metric
  on a six-class problem with mild imbalance.
- **Why pgvector?** It matches the brief, lets us run nearest-neighbor
  retrieval directly in the same DB SQLAlchemy already manages, and
  the `ivfflat` cosine index gives fast retrieval without bringing a
  separate vector DB.
- **Why exactly 3 tools?** The brief specifies it. More tools is
  scope creep that makes the agent harder to defend; fewer leaves
  the Decision Tension Board under-specified.

## 13. What still uses fallback (honest list)

- **Two-model routing**: cheap/strong steps use deterministic local
  routing — token shape and step accounting are real, but no external
  LLM is called. Provider integration is the next phase.
- **Embeddings**: `deterministic-hashing-v1`. Real semantic embeddings
  plug in behind `get_embedding_provider`.
- **Live weather**: gated by `WEATHER_LIVE_ENABLED`. Off in defaults
  for reproducible demos; on, it calls Open-Meteo.
- **pgvector retrieval**: implemented and exercised by tests in code,
  but live ingest+retrieval is environment-blocked on this machine
  because Docker Desktop's pipe is down. Fallback retriever is what's
  proven on this hardware.
- **Webhook**: Discord URL is empty by default → delivery is `skipped`.
- **LangSmith trace screenshot**: capture during the demo.

## 14. 30 likely reviewer questions (with crisp answers)

1. **Why exactly 3 tools?** Brief requires it; allowlist enforces it
   in `registry.py:TOOL_SPECS`.
2. **Where is the allowlist?** `backend/app/agent/registry.py`,
   `ALLOWED_TOOL_NAMES`. Unknown names return a structured
   `ToolError`.
3. **Where do you validate tool inputs?** Pydantic model_validate
   inside `execute_tool`. Each tool has its own schema in
   `backend/app/schemas/`.
4. **What if the agent throws?** The route returns 500 with a generic
   detail; `fail_agent_run` records the error in `agent_runs.error`.
   No silent stub.
5. **What if Postgres is down?** `create_agent_run` returns `None` and
   the brief still renders. RAG falls back to the local index.
6. **What if Discord is down?** `WebhookDelivery` is recorded with
   `status="failed"`; user response is unaffected.
7. **What is Dream Fit fed by?** `classify_travel_style` (ML) plus
   `retrieve_destination_knowledge` (RAG) — built in `synthesize`.
8. **What is Reality Pressure fed by?** `fetch_live_conditions` —
   weather + flight signals → `pressure_score`.
9. **Why is Reality Pressure inverted?** So both axes read
   "higher is better" — symmetric UI.
10. **Why this dataset size (131)?** Brief says 100–200; we picked the
    middle so each label has 20–25 rows.
11. **Why is LR the winner?** Highest mean macro-F1 (0.959 vs RF 0.951
    vs GB 0.943). All experiments are in `results.csv`.
12. **Did you tune?** Yes — `GridSearchCV` over Random Forest with
    three knobs. The brief asks for "at least one"; we tuned the model
    with the most interesting search space on small data.
13. **How do you avoid leakage?** `StandardScaler` is *inside* the
    Pipeline, so it refits per CV fold.
14. **Per-class metrics?** `cross_val_predict` →
    `classification_report`. Honest predictions on held-out folds.
15. **Why 900/150 chunking?** Short briefs; 900 keeps one travel idea
    per chunk; 150 protects boundaries. Per-corpus rationale in README.
16. **What is the embedding dim?** 384 — matches the pgvector column
    and the deterministic provider's default.
17. **Why deterministic embeddings?** Reproducible demos without
    external services; the interface is pluggable.
18. **Cosine similarity proof?** Both vectors are L2-normalized in the
    provider, so dot product equals cosine.
19. **Why pgvector + ivfflat?** Matches the brief; ivfflat with `lists=100`
    is a sane default for a small corpus and keeps retrieval fast.
20. **Where do migrations live?** `backend/alembic/versions/0001_initial.py`.
    `alembic upgrade head` against any reachable DB.
21. **Where do you store JWT secret?** `JWT_SECRET_KEY` env var, read
    only via `get_settings()`. No `os.getenv` elsewhere.
22. **Bcrypt cost?** `bcrypt.gensalt()` defaults (12 rounds).
23. **CORS?** `CORSMiddleware` reads a comma-separated origin list
    from settings; default is `http://localhost:5173`.
24. **Where is the tool trace?** `backend/app/agent/synthesize.py:_summarize_tool`
    and `_trace`. Surfaced in `TripBriefResponse.tools_used`.
25. **Why background webhook?** It must not block the user response.
    `BackgroundTasks` runs after the response is sent.
26. **Two-model routing — is it real?** The shape is real (cheap step
    in `router.py:extract_trip_plan`, strong step in `final_synthesis_usage`).
    The model calls are deterministic placeholders today.
27. **Why React + Vite + TS?** Strict typing, fast dev server, simple
    build, no framework magic.
28. **Why an Evidence drawer?** Code-review credibility — surface
    cost, model split, latency, and webhook state next to the
    user-facing brief.
29. **Why the "cartographer's atlas" palette?** Avoids the default
    indigo/cyan look and reinforces the briefing-room metaphor.
30. **What's the most likely failure mode in a real review?**
    External services unavailable. Every external dependency has a
    deterministic fallback and an honest `used_fallback`/`mode`
    indicator.

## 15. Files I must know cold

- `backend/app/main.py` (lifespan + router mount)
- `backend/app/agent/graph.py` (LangGraph)
- `backend/app/agent/registry.py` (allowlist + execute_tool)
- `backend/app/agent/synthesize.py` (Decision Tension Board)
- `backend/app/api/routes/trip_briefs.py` (route + persistence + webhook)
- `backend/app/api/routes/auth.py` (register/login/me)
- `backend/app/schemas/trip_brief.py` (response contract)
- `backend/app/schemas/tools.py` (tool schemas)
- `backend/app/ml/train_classifier.py` and `backend/app/ml/service.py`
- `backend/app/rag/retriever.py` and `backend/app/rag/embeddings.py`
- `backend/app/webhooks/dispatcher.py`
- `frontend/src/App.tsx`
- `frontend/src/components/DecisionTensionBoard.tsx`
- `frontend/src/hooks/useTripBrief.ts`
- `frontend/src/hooks/useAuth.ts`

## 16. Files I can explain generally

- All `backend/app/models/*.py` (SQLAlchemy mappings, mostly
  declarative).
- `backend/app/persistence/records.py` (best-effort writes around
  agent runs and tool calls).
- `frontend/src/components/*` (small dedicated components, each one
  rendering a slice of `TripBriefResponse`).
- `data/destinations.csv`, `data/knowledge/*.md` (datasets — have a
  reviewer pick a row and defend it via the labeling rule).
- `backend/alembic/versions/0001_initial.py` (initial schema).

## 17. One-page cheat sheet

```
Decision Tension Board    ⇒ Dream Fit · Reality Pressure · Verdict · Counterfactual
3 tools                   ⇒ retrieve_destination_knowledge / classify_travel_style / fetch_live_conditions
ML winner                 ⇒ Logistic Regression, macro-F1 ≈ 0.959 (5-fold CV)
RAG corpus                ⇒ 28 docs / 14 destinations / 28 chunks / 900-150 chunking
Embeddings                ⇒ 384-dim deterministic-hashing-v1 (pluggable)
Persistence               ⇒ 6 tables (users, agent_runs, tool_calls, webhook_deliveries, destination_documents, document_chunks)
Auth                      ⇒ bcrypt + PyJWT + get_(optional_)current_user
Webhook                   ⇒ Discord, async, timeout, retry, isolated failure
LangGraph                 ⇒ plan → tools → synthesize (3 nodes)
Two-model routing         ⇒ deterministic placeholder (real provider keys → real calls)
Migrations                ⇒ alembic upgrade head, 0001_initial
Frontend                  ⇒ React + Vite + TS, strict, 1 build, ~170kB JS gzip ~55kB
```

## 18. 15-question quiz (use to drill yourself)

1. Where is the agent allowlist defined and what happens if a tool name
   is not in it?
2. Which file produces tool trace summaries shown on the timeline?
3. How is leakage prevented in the ML pipeline?
4. What is the macro-F1 of the saved winner and how was it selected?
5. What does `pressure_score=0` mean for Reality Pressure?
6. What's the chunk size and overlap, and why?
7. Where is `Vector(384)` declared and why 384?
8. What happens when Postgres is unreachable during a trip brief?
9. What guarantees a webhook failure cannot break the user response?
10. Which dependency provides the JWT and what algorithm is used?
11. Where is `JWT_SECRET_KEY` read, and where is it allowed to be set?
12. What does `get_optional_current_user` return when no header is sent?
13. Which file is the LangGraph compiled in?
14. Where would you wire a real OpenAI embedding provider?
15. What's the exact route to receive a brief, and what JSON does it
    return?
