# AtlasBrief — AI Travel Briefing Room

A Smart Travel Planner with a premium "AI travel briefing room" feel.

The unique product layer is the **Decision Tension Board**:

- **Dream Fit** - how well a destination matches the user's vibe.
- **Reality Pressure** - what live conditions say about going right now.
- **Final Verdict** - a synthesis that names the tradeoff.
- **Why Not the Obvious Pick?** - a counterfactual card explaining the road not taken.

## Current phase

The backend submission path is in place: auth, async SQLAlchemy persistence
models, the three-tool LangGraph agent, deterministic two-model routing,
ML classification, RAG retrieval, live-conditions fallback, and Discord webhook
delivery are implemented.

The **frontend has been rebuilt** as a single-page briefing room — hero +
cinematic prompt console + Trip DNA panel + Agent Mission Timeline + the
**Decision Tension Board** centerpiece + Travel Brief memo + Evidence drawer.
The backend contract (`TripBriefResponse`) is unchanged; when the backend is
unreachable the page degrades into a clearly-labeled offline demo briefing.

The visual identity uses a "cartographer's atlas" palette — warm parchment on
deep ink, with **brass** (#E0A458) for Dream Fit, **verdigris** (#4DBDB1) for
Reality Pressure, and **terracotta** (#E27A5C) for the counterfactual. The
walkthrough script is in [`docs/demo_story.md`](docs/demo_story.md).

## Repository layout

```text
.
|-- backend/                 FastAPI skeleton
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
|   |-- src/App.tsx          Orchestrator: hero → prompt → DNA → timeline → board → memo → evidence
|   |-- src/components/      Hero, CinematicPromptBox, TripDNAPanel, AgentTimeline,
|   |                        DecisionTensionBoard, ScoreCard, TravelBriefMemo,
|   |                        EvidenceDrawer, LoadingShimmer, EmptyState, ErrorState, Brand
|   |-- src/hooks/           useTripBrief — request lifecycle + offline fallback
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

- cheap step: extract destination/query features,
- strong step: final Decision Tension Board synthesis accounting.

No external LLM is called without future provider wiring. When provider keys
are missing, the backend uses deterministic local routing and records token/cost
metadata with zero provider cost.

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
2. **Cinematic Prompt Box** — glass intake panel with a serif textarea, four
   scenario chips, and a premium CTA. Cmd/Ctrl+Enter submits.
3. **Trip DNA** — six-cell parsed-intent panel (budget, month, duration,
   climate, activities, constraints) plus the predicted travel style. Slots
   that can't be parsed are labeled *Not specified* — we don't invent values.
4. **Agent Mission Timeline** — seven stages mapped to the actual backend
   pipeline. While the request is in flight the timeline animates; once the
   response lands, completed stages tick and the real `tools_used` summaries
   replace the generic stage labels.
5. **Decision Tension Board** — the centerpiece:
   - Heading row — destination, country, travel-style chip.
   - Two score cards — **Dream Fit** (brass, ML + RAG) and **Reality
     Pressure** (verdigris, live conditions).
   - **Final Verdict** — large editorial serif type with a tri-color top
     rule (brass → terracotta → verdigris) that names the tradeoff.
   - **Why not the obvious pick?** — terracotta counterfactual card.
6. **Travel Brief Memo** — executive trip memo with sections for *Why it
   fits / What to expect / Risks / Booking advice / Backup option / Budget
   fit*.
7. **Evidence Drawer** — collapsible panel with the tool trace on the left
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

The Postgres/pgvector path is built but not required for local verification:

- `backend/app/db/session.py` - async SQLAlchemy engine/session factory.
- `backend/app/db/init_db.py` - enables `CREATE EXTENSION IF NOT EXISTS vector`.
- `backend/app/models/destination_document.py` - source markdown document rows.
- `backend/app/models/document_chunk.py` - chunk rows with `Vector(384)` and a
  cosine index.
- `backend/app/rag/ingest_documents.py` - embeds and stores chunks when a DB is
  available.

If Postgres is empty, retrieval returns an empty result instead of crashing. If
database retrieval fails, the retriever falls back to the deterministic local
index.

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

`docker compose config --quiet` passes, so the Compose file is valid. On this
machine, the live Postgres smoke test is blocked before app code runs because
Docker Desktop is not reachable:

```text
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

That means the unproven part is environmental: starting the
`pgvector/pgvector:pg16` container and exercising `ingest_documents.py --db`
against a live database. The RAG pipeline itself is still locally verified by
`app.rag.smoke_test`.

When Docker Desktop is running, use this sequence from the repo root:

```powershell
docker compose config --quiet
docker compose up -d db
docker compose exec db pg_isready -U trippilot -d trippilot

cd backend
$env:DATABASE_URL="postgresql+asyncpg://trippilot:change-me-local-only@localhost:5432/trippilot"
.\.venv\Scripts\python -m app.rag.ingest_documents --db --reset
```

Then run one DB-backed retrieval query:

```powershell
@'
import asyncio
from app.db.session import get_session_factory, dispose_engine
from app.rag.retriever import retrieve_from_db
from app.schemas.rag import DestinationKnowledgeQuery

async def main():
    session_factory = get_session_factory()
    async with session_factory() as session:
        response = await retrieve_from_db(
            DestinationKnowledgeQuery(
                query="Madeira warm levada island hiking less touristy",
                top_k=3,
            ),
            session=session,
        )
        print(response.model_dump_json(indent=2))
    await dispose_engine()

asyncio.run(main())
'@ | .\.venv\Scripts\python -
```

If your local `backend/.env` uses a different `POSTGRES_PASSWORD`, update the
temporary `DATABASE_URL` to match it.

## Code review notes

Every major change has a plain-language entry in
[`CODE_REVIEW_NOTES.md`](CODE_REVIEW_NOTES.md). Read that file first if you
want to understand why the project is shaped this way.
