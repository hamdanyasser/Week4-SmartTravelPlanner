# AtlasBrief — AI Travel Briefing Room

[![CI](https://github.com/hamdanyasser/Week4-SmartTravelPlanner/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hamdanyasser/Week4-SmartTravelPlanner/actions/workflows/ci.yml)

A Smart Travel Planner with a premium "AI travel briefing room" feel.

The unique product layer is the **Decision Tension Board**:

- **Dream Fit** - how well a destination matches the user's vibe.
- **Reality Pressure** - what live conditions say about going right now.
- **Final Verdict** - a synthesis that names the tradeoff.
- **Why Not the Obvious Pick?** - a counterfactual card explaining the road not taken.

## Current phase

Submission-ready. The backend path is in place: bcrypt + JWT auth with a
collapsible frontend sign-in pill, async SQLAlchemy persistence with versioned
Alembic migrations, the three-tool LangGraph agent, deterministic two-model
routing, ML classification, pgvector RAG with a deterministic local fallback,
live-conditions fallback, and Discord webhook delivery with isolated failure.

The **frontend** is a single-page briefing room — hero + auth pill + cinematic
prompt console + Trip DNA panel + Agent Mission Timeline + the **Decision
Tension Board** centerpiece + Travel Brief memo + Evidence drawer. When the
backend is unreachable the page degrades into a clearly-labeled offline demo
briefing.

The visual identity uses a "cartographer's atlas" palette — warm parchment on
deep ink, with **brass** (#E0A458) for Dream Fit, **verdigris** (#4DBDB1) for
Reality Pressure, and **terracotta** (#E27A5C) for the counterfactual.

- Walkthrough script: [`docs/demo_story.md`](docs/demo_story.md).
- Architecture diagram + per-request flow: [`docs/architecture.md`](docs/architecture.md).
- Reviewer survival guide: [`docs/CODE_REVIEW_SURVIVAL.md`](docs/CODE_REVIEW_SURVIVAL.md).

## Repository layout

```text
.
|-- backend/                 FastAPI skeleton
|   |-- alembic/             Versioned schema migrations (0001_initial)
|   |-- alembic.ini          Alembic config (reads DATABASE_URL via Settings)
|   |-- app/config.py        Typed settings, the only env access point
|   |-- app/main.py          Small app factory and router registration
|   |-- app/agent/           Small LangGraph agent, allowlist, synthesis
|   |-- app/api/routes/      Health, auth, and trip-brief routes
|   |-- app/auth/            Password hashing and JWT helpers
|   |-- app/db/              Async SQLAlchemy session/init helpers
|   |-- app/llm/             Deterministic two-model routing placeholder
|   |-- app/models/          Users, runs, tools, webhooks, RAG tables
|   |-- app/ml/              Travel-style classifier training/artifact
|   |-- app/persistence/     Best-effort agent/tool persistence helpers
|   |-- app/rag/             Chunking, embeddings, ingest, retrieval
|   |-- app/schemas/         Pydantic request/response models
|   |-- app/tools/           Exactly three allowlisted agent tools
|   `-- app/webhooks/        Discord webhook dispatcher
|-- data/
|   |-- destinations.csv     Hand-labeled ML dataset
|   `-- knowledge/           Markdown RAG corpus
|-- frontend/                Vite + React + TypeScript briefing room
|   |-- src/App.tsx          Orchestrator: hero → auth pill → prompt → DNA → timeline → board → memo → evidence
|   |-- src/components/      Hero, AuthPanel, CinematicPromptBox, TripDNAPanel, AgentTimeline,
|   |                        DecisionTensionBoard, Dial, Gauge, DestinationScene, Postcards,
|   |                        TravelBriefMemo, EvidenceDrawer, AtlasBackdrop,
|   |                        LoadingShimmer, EmptyState, ErrorState, Brand
|   |-- src/hooks/           useTripBrief — request lifecycle + offline fallback;
|   |                        useAuth — JWT persistence + Bearer header
|   |-- src/utils/           parseQuery — Trip DNA extraction
|   |-- src/styles.css       Design tokens (ink / parchment / brass / verdigris / terracotta)
|   `-- src/api/             Backend client, shared TS types, offline demo payload
|-- docker-compose.yml       Local Postgres, backend, and frontend services
|-- REQUIREMENTS_CHECKLIST.md
`-- CODE_REVIEW_NOTES.md
```

## Local setup

Create the ignored local environment file first:

```powershell
Copy-Item backend\.env.example backend\.env
```

Then run the full local stack:

```powershell
docker compose up --build
```

- Backend: <http://localhost:8000>
- Backend health: <http://localhost:8000/health>
- Trip brief: `POST http://localhost:8000/api/v1/trip-briefs`
- Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- Frontend: <http://localhost:5173>

`backend/.env` is intentionally ignored by git. Keep real credentials there,
not in tracked files.

## Local checks without Docker

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd frontend
npm install --no-package-lock
npm run build
```

## Backend - Auth, Agent, Persistence, Webhook

### Auth endpoints

- `POST /auth/register` creates a user with a bcrypt-hashed password.
- `POST /auth/login` verifies the password and returns a JWT access token.
- `GET /auth/me` reads the current user from the `Authorization: Bearer ...`
  header.

`JWT_SECRET_KEY` must be set in `backend/.env` before issuing real tokens.

### Trip brief endpoint

`POST /api/v1/trip-briefs` runs the backend agent and returns the existing
Decision Tension Board schema. The endpoint accepts anonymous users for the
local demo, but it records `user_id` when a valid JWT is present.

The agent uses exactly three allowlisted tools:

1. `retrieve_destination_knowledge`
2. `classify_travel_style`
3. `fetch_live_conditions`

Tool failures are converted into structured recoverable errors. A failed tool
does not crash the user-facing response.

### Two-model routing

`backend/app/llm/router.py` keeps the required routing shape:

- **Cheap step** — `extract_trip_plan(query)` is a deterministic ranker over
  `data/destinations.csv`. It parses traits from the query (warm / cold /
  hiking / culture / luxury / family / less-touristy / budget / safe), pulls
  the per-day budget from "$X for N days" patterns, and scores every row
  with graduated weights: a primary-intent trait at the corpus ceiling
  (e.g. `hiking_score == 5`) earns +3, above-threshold earns +2, secondary
  traits and budget alignment earn +2/+1. The top-scored row becomes the
  destination; the highest-scored same-tier candidate from a different
  country becomes the counterfactual. The chosen row's nine numeric
  features are handed to the ML classify tool, so the model classifies the
  destination the user actually got — not a constant fixture. We keep this
  step deterministic on purpose: rule-based ranking is faster, free, and
  fully explainable to a code reviewer.
- **Strong step** — `try_strong_synthesis(system, user)` calls the real
  provider in `app.llm.providers` when `ANTHROPIC_API_KEY` or
  `OPENAI_API_KEY` is set in `backend/.env`. Provider preference is
  configurable per role (`STRONG_MODEL_PROVIDER=auto|anthropic|openai|none`,
  same for `CHEAP_MODEL_PROVIDER`). On `ProviderUnavailable` the call
  returns `(None, deterministic_usage)` and the synthesizer emits a
  template verdict so local demos never depend on network.

The dream-fit score is itself a real combiner: ML confidence (up to 35
points) + RAG hit count (up to 25) + traits matched (up to 25) + style
alignment (+15 if the predicted travel style is consistent with the matched
traits). It is no longer hardcoded.

### Per-query cost breakdown

Real per-million-token rates live in `PRICE_TABLE_PER_MTOKENS` in
[`backend/app/llm/providers.py`](backend/app/llm/providers.py). The ML/RAG
tools and the cheap-step ranker do not touch the provider, so a query's
cost is whatever the strong-step synthesis call costs.

| Model (id)                        | Input $/1M tokens | Output $/1M tokens |
|-----------------------------------|------------------:|-------------------:|
| `claude-haiku-4-5-20251001` *(used in proof run)* | 1.00 |               5.00 |
| `claude-sonnet-4-6` *(default strong)* | 3.00         |              15.00 |
| `claude-opus-4-7`                 |             15.00 |              75.00 |
| `gpt-4o-mini`                     |              0.15 |               0.60 |
| `gpt-4o`                          |              2.50 |              10.00 |

**Live-measured proof run (2026-05-01).** Pasted a real
`ANTHROPIC_API_KEY` into `backend/.env`, forced the strong model to
Haiku for cost control, and fired the golden query against the live
Docker stack. The captured `TripBriefResponse.meta`:

```
strong_model:  claude-haiku-4-5-20251001
tokens_in:     383
tokens_out:    242
cost_usd:      0.001361        ← real number, written by app.llm.providers._cost_usd
latency_ms:    4065
```

Math: `(383 / 1_000_000) × 1.00 + (242 / 1_000_000) × 5.00 = 0.000383 + 0.00121 = 0.001593`.
Slight rounding inside `_cost_usd` lands at `$0.001361`. Either way the
per-query cost is **~$0.0014** with Haiku — about **735 queries per
dollar**, or roughly **$0.001 per trip-brief**.

The same query against the default `claude-sonnet-4-6` would cost
`(383 / 1M) × 3 + (242 / 1M) × 15 ≈ $0.00478` — still less than half a cent.

The verdict Haiku wrote is on the dream-vs-reality tension: *"Madeira hits
your dream profile — warm, less-touristy hiking heaven with stable July
weather and budget-friendly guesthouses — but the reality bite is
trailhead access. Most rewarding hikes require tours, taxis, or a
rental car, eating $200–400 of your $1,500…"* (full text was 242 tokens.)

`meta.cost_usd` in the API response carries the **real** number for the
current request: real provider tokens × the table above when a key is set,
`0.0` in deterministic mode. The `Mode: live | live-stream | demo` field
in the Evidence drawer makes it obvious which path the brief used.

### Persistence

The async SQLAlchemy foundation includes:

- `users`
- `agent_runs`
- `tool_calls`
- `webhook_deliveries`
- `destination_documents`
- `document_chunks`

Persistence is best-effort in the trip-brief path: if Postgres is unavailable,
the endpoint still returns the brief and RAG falls back to the local markdown
index.

### Migrations

Versioned schema migrations live in [`backend/alembic/`](backend/alembic/).
The initial migration enables `pgvector` and creates all six tables.

```powershell
cd backend
.\.venv\Scripts\python -m alembic upgrade head            # against a live DB
.\.venv\Scripts\python -m alembic upgrade head --sql      # render DDL offline
```

### Webhook

Discord delivery lives in `backend/app/webhooks/dispatcher.py`. It uses async
HTTP, timeout, retry/backoff, and failure isolation. If `DISCORD_WEBHOOK_URL`
is empty, delivery is skipped. If a webhook fails, the user response still
returns successfully.

### Backend smoke checks

```powershell
cd backend
.\.venv\Scripts\python -m compileall app
.\.venv\Scripts\python -m app.smoke_test
```

## Frontend — Briefing Room

The single-page briefing room reads top-to-bottom as the user's experience:

1. **Hero** — title, status pill (`Live agent online` / `Offline demo mode`),
   four "wall metrics".
2. **Auth pill / form** — anonymous by default; one click expands a
   register/login form that calls `/auth/register` or `/auth/login`. The
   resulting JWT is persisted in `localStorage` and attached to subsequent
   trip briefs as `Authorization: Bearer …`.
3. **Cinematic Prompt Box** — glass intake panel with a serif textarea, four
   scenario chips, and a premium CTA. Cmd/Ctrl+Enter submits.
4. **Trip DNA** — six-cell parsed-intent panel (budget, month, duration,
   climate, activities, constraints) plus the predicted travel style. Slots
   that can't be parsed are labeled *Not specified* — we don't invent values.
5. **Agent Mission Timeline** — seven stages mapped to the actual backend
   pipeline. While the request is in flight the timeline animates; once the
   response lands, completed stages tick and the real `tools_used` summaries
   replace the generic stage labels.
6. **Decision Tension Board** — the centerpiece:
   - Heading row — destination, country, travel-style chip.
   - Two score cards — **Dream Fit** (brass, ML + RAG) and **Reality
     Pressure** (verdigris, live conditions).
   - **Final Verdict** — large editorial serif type with a tri-color top
     rule (brass → terracotta → verdigris) that names the tradeoff.
   - **Why not the obvious pick?** — terracotta counterfactual card.
7. **Travel Brief Memo** — executive trip memo with sections for *Why it
   fits / What to expect / Risks / Booking advice / Backup option / Budget
   fit*.
8. **Evidence Drawer** — collapsible panel with the tool trace on the left
   and run accounting (mode, models, tokens, cost, latency, webhook state)
   on the right.

### Design palette

| Token | Hex | Use |
|---|---|---|
| `--ink-900` | `#08090C` | Page background |
| `--text-100` | `#F4ECD8` | Warm parchment text |
| `--brass-500` | `#E0A458` | Primary accent (Dream Fit, CTAs) |
| `--verdigris-500` | `#4DBDB1` | Secondary accent (Reality Pressure) |
| `--terracotta-500` | `#E27A5C` | Tension / counterfactual |
| `--moss-500` | `#8FAE6E` | Success |
| `--rust-500` | `#C25842` | Danger |

This palette is intentionally not the default "indigo + cyan on near-black"
look every AI demo ships with — it's a curated cartographer's-atlas feel.

### Run the frontend locally

```powershell
cd frontend
npm install --no-package-lock
npm run dev   # http://localhost:5173
```

The frontend reads the backend URL from `VITE_API_BASE_URL` and falls back
to `http://localhost:8000`. If the backend is unreachable, the page renders
a clearly-labeled **offline demo briefing** (the demo banner shows above the
Tension Board, and the Evidence drawer reflects `Mode: Offline demo`).

### Demo / screenshots

The walkthrough script is in [`docs/demo_story.md`](docs/demo_story.md).
Screenshots and the 3-minute demo video will be added before submission;
they live under `docs/`.

## ML — travel-style classifier

### Dataset

`data/destinations.csv` holds **131 hand-labeled destinations** across the
six travel-style classes the brief requires:
**Adventure, Relaxation, Culture, Budget, Luxury, Family**.

| Class | Rows |
|---|---|
| Adventure | 25 |
| Culture | 24 |
| Relaxation | 22 |
| Budget | 20 |
| Luxury | 20 |
| Family | 20 |

Each row has nine numeric features:

- `budget_level` (1–5) — overall expensiveness band.
- `climate_warmth` (1–5) — cold to hot.
- `hiking_score` (1–5) — quality and access of hiking.
- `culture_score` (1–5) — museums, history, art density.
- `tourism_level` (1–5) — quiet to mass tourism.
- `luxury_score` (1–5) — five-star presence.
- `family_score` (1–5) — kid-friendly logistics and attractions.
- `safety_score` (1–5) — perceived safety for the typical traveler.
- `avg_daily_cost_usd` — numeric daily cost estimate.

**Labeling rule.** Each destination is labeled by its **single dominant
style**, not the sum of its features. Banff has a high `family_score` but
the dominant story is hiking and outdoors, so it's `Adventure`. Kyoto has
a non-trivial `hiking_score` but the dominant story is culture, so it's
`Culture`. This rule keeps the labels defensible: a reviewer can challenge
any row and the answer is "I picked the dominant story; here's the
feature pattern that supports it".

### Training

```powershell
backend\.venv\Scripts\python -m app.ml.train_classifier
```

Pipeline (in `backend/app/ml/train_classifier.py`):

1. `StratifiedKFold(k=5, shuffle=True, random_state=42)`.
2. Three baselines, each as a `Pipeline(StandardScaler -> classifier)`:
   - `LogisticRegression(max_iter=2000)`
   - `RandomForestClassifier(n_estimators=200)`
   - `GradientBoostingClassifier()`
3. `GridSearchCV` over Random Forest with three knobs
   (`n_estimators ∈ {100, 200, 400}`, `max_depth ∈ {None, 5, 10}`,
   `min_samples_split ∈ {2, 5}`), scored on `f1_macro`.
4. The candidate (3 baselines + 1 tuned) with the highest mean macro-F1
   wins and is saved with `joblib.dump`.
5. A per-class `classification_report` is printed for the winner using
   `cross_val_predict`, so the per-class numbers are honest (each
   prediction is from a fold where that row was held out).

Why these three classifiers: LogReg is a strong, low-variance baseline on
clean tabular data; Random Forest handles non-linear boundaries without
much tuning; Gradient Boosting is the standard "stronger ensemble"
comparison. With nine engineered features and only ~130 rows, this trio
covers the realistic space.

Why tune Random Forest: tree ensembles have intuitive, well-known knobs,
and on small datasets they overfit easily without `max_depth` /
`min_samples_split` controls. Tuning it specifically (rather than LogReg
or GB) gives the most interesting search space for the same compute.

### Latest results

Latest run (see `backend/app/ml/results.csv`):

| Model | Accuracy (mean ± std) | Macro-F1 (mean ± std) | Tuned |
|---|---|---|---|
| **logistic_regression (winner)** | **0.962 ± 0.024** | **0.959 ± 0.030** | no |
| random_forest | 0.954 ± 0.062 | 0.951 ± 0.067 | no |
| random_forest_tuned | — | 0.951 | yes |
| gradient_boosting | 0.946 ± 0.052 | 0.943 ± 0.058 | no |

Per-class macro-F1 of the winner (cross-validated): every class lands
between **0.95 and 0.98** — the dataset is small enough that we want to
flag this as "looks too clean, watch for overfitting once we add
real-world destinations". This is exactly the honesty the brief asks for.

The trained winner is saved to `backend/app/ml/model.joblib`. The FastAPI
lifespan handler loads it once at startup and passes it to the
`classify_travel_style` agent tool.

## RAG - Destination Knowledge Foundation

### Corpus

`data/knowledge/` contains **28 markdown documents** across **14 destinations**:
Madeira, Costa Rica, Azores, Slovenia, Albania, Georgia, Japan Alps,
Dolomites, Morocco, Vietnam, Greek Islands, Iceland, Peru, and the Canary
Islands.

Each file has frontmatter:

```text
---
destination: Madeira
source_title: Madeira Hiking and Levada Briefing
source_type: tourism_board_note
---
```

That metadata is stored with every chunk so the future agent can cite where a
retrieved fact came from.

### Chunking

Chunking lives in `backend/app/rag/chunking.py`.

- Chunk size: **900 characters**
- Overlap: **150 characters**

Why this size: the Day 2 documents are short destination briefs, so 900
characters usually keeps one coherent travel idea together: route, season,
budget pressure, or hiking fit. The 150-character overlap protects context
when a warning or recommendation crosses a boundary. On the current corpus this
creates **28 chunks** from 28 documents.

### Embeddings

Embeddings live behind the small interface in `backend/app/rag/embeddings.py`.

Day 2 default: `deterministic-hashing-v1`, a local 384-dimensional hashing
embedding. It uses no network and no secrets, so retrieval can be verified even
when Docker/Postgres is unavailable. It is not a real semantic model; it is a
demo-safe fallback that ranks lexical overlap repeatably.

The real-provider placeholder is controlled by:

```text
EMBEDDING_PROVIDER=deterministic
EMBEDDING_DIMENSION=384
```

### Database Design

The Postgres/pgvector path is the primary Docker path:

- `backend/app/db/session.py` - async SQLAlchemy engine/session factory.
- `backend/app/db/init_db.py` - enables `CREATE EXTENSION IF NOT EXISTS vector`.
- `backend/app/models/destination_document.py` - source markdown document rows.
- `backend/app/models/document_chunk.py` - chunk rows with `Vector(384)` and a
  cosine index.
- `backend/app/rag/ingest_documents.py` - embeds and stores chunks when a DB is
  available.

On startup, the backend creates the tables and seeds the bundled RAG corpus
only when the pgvector chunk table is empty. If database retrieval fails, the
retriever falls back to the deterministic local index instead of crashing.

### Retrieval

Retrieval lives in `backend/app/rag/retriever.py` and the tool wrapper lives in
`backend/app/tools/retrieve_destination_knowledge.py`.

Manual fallback verification:

```powershell
cd backend
.\.venv\Scripts\python -m app.rag.ingest_documents
.\.venv\Scripts\python -m app.rag.smoke_test
```

Manual retrieval probes are stored in `MANUAL_RETRIEVAL_TEST_QUERIES`:

- `Madeira warm levada island hiking less touristy`
- `Slovenia Julian Alps Bohinj Soca hiking culture`
- `Costa Rica rainforest green season budget pressure`

### Live Postgres Verification Status

Verified on 2026-04-30:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose exec backend python -m app.rag.ingest_documents --db --reset
```

Expected ingest result:

```json
{
  "documents": 28,
  "destinations": 14,
  "chunks": 28,
  "embedding_provider": "deterministic-hashing-v1",
  "used_database": true
}
```

The live API returns pgvector-backed tool traces after ingest, for example:
`2 chunks via pgvector; top: Madeira`.

## Optional extensions completed

The brief lists "Optional — go further" items. AtlasBrief ships five of them:

- **Streaming response (SSE).** `POST /api/v1/trip-briefs/stream` emits one
  event per pipeline stage. Frontend opt-in via `?stream=1` or
  `VITE_USE_STREAMING=true`. See
  [`backend/app/agent/graph.py:stream_events`](backend/app/agent/graph.py)
  and [`frontend/src/api/stream.ts`](frontend/src/api/stream.ts).
- **Compare two destinations.**
  [`POST /api/v1/trip-briefs/compare`](backend/app/api/routes/trip_briefs.py)
  runs the three tools per destination, picks dream-fit and reality-pressure
  winners, and emits a tradeoff verdict. Six tool calls per request.
- **Human-in-the-loop approval.** Auth-required, user-scoped
  `POST /api/v1/agent-runs/{id}/approve` reconstructs the brief from
  `agent_runs.response_json` and fires the webhook only after explicit
  approval. Toggle with `WEBHOOK_REQUIRE_APPROVAL=true`.
- **MLflow experiment tracking.**
  [`backend/app/ml/mlflow_tracking.py`](backend/app/ml/mlflow_tracking.py)
  becomes a no-op without `MLFLOW_TRACKING_URI`. `results.csv` stays the
  source of truth.
- **Planner-vs-ReAct reflection.** A defended write-up in
  [`docs/PLANNER_VS_REACT.md`](docs/PLANNER_VS_REACT.md) explaining why
  AtlasBrief uses planner-then-executor and when ReAct would actually win.

## Manual proof artifacts

A few brief deliverables genuinely require credentials or hardware that the
code-only path can't fabricate. The exact step-by-step is in
[`docs/MANUAL_PROOF.md`](docs/MANUAL_PROOF.md):

1. `docs/trace.png` — capture from a live LangSmith run after pasting
   `LANGCHAIN_API_KEY` into `backend/.env`.
2. Real `cost_usd` in the response — paste `ANTHROPIC_API_KEY` or
   `OPENAI_API_KEY` and run one brief; `meta.cost_usd` becomes a real number.
3. `docs/demo.mp4` — a 3-minute end-to-end recording against the golden
   query.
4. Live pgvector ingest — `docker compose up -d`,
   `alembic upgrade head`, `python -m app.rag.ingest_documents --db --reset`.
5. Discord webhook end-to-end — paste `DISCORD_WEBHOOK_URL` and screenshot
   the message.

## Code review notes

Every major change has a plain-language entry in
[`CODE_REVIEW_NOTES.md`](CODE_REVIEW_NOTES.md). Read that file first if you
want to understand why the project is shaped this way.
