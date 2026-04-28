# AtlasBrief — AI Travel Briefing Room

A Smart Travel Planner with a premium "AI travel briefing room" feel.

The unique product layer is the **Decision Tension Board**:

- **Dream Fit** - how well a destination matches the user's vibe.
- **Reality Pressure** - what live conditions say about going right now.
- **Final Verdict** - a synthesis that names the tradeoff.
- **Why Not the Obvious Pick?** - a counterfactual card explaining the road not taken.

## Current phase

The local skeleton is working, the ML classifier foundation is built, and the
Day 2 RAG foundation is now in place.

Still not implemented yet: the full agent, auth, webhooks, user persistence,
LLM routing, and deployment. The UI intentionally keeps the Decision Tension
Board concept in place with stub data so later phases have a clear product
shape to fill.

## Repository layout

```text
.
|-- backend/                 FastAPI skeleton
|   |-- app/config.py        Typed settings, the only env access point
|   |-- app/main.py          Small app factory and router registration
|   |-- app/api/routes/      Health and trip-brief routes
|   |-- app/db/              Async SQLAlchemy session/init helpers
|   |-- app/models/          RAG document + chunk tables
|   |-- app/ml/              Travel-style classifier training/artifact
|   |-- app/rag/             Chunking, embeddings, ingest, retrieval
|   |-- app/schemas/         Pydantic request/response models
|   `-- app/tools/           Tool wrappers for the future agent
|-- data/
|   |-- destinations.csv     Hand-labeled ML dataset
|   `-- knowledge/           Markdown RAG corpus
|-- frontend/                Vite + React + TypeScript skeleton
|   `-- src/api/             Thin backend client and shared TS types
|-- docker-compose.yml       Local Postgres, backend, and frontend services
|-- REQUIREMENTS_CHECKLIST.md
`-- CODE_REVIEW_NOTES.md
```

Planned folders like `agent/`, `auth/`, `llm/`, and `webhooks/` do not exist
yet. They should be added only when those phases start.

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
- Stub trip brief: `POST http://localhost:8000/api/v1/trip-briefs`
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

The trained winner is saved to `backend/app/ml/model.joblib`. From Day 5
the FastAPI lifespan handler will load it once at startup and expose it
via a `Depends()` to the `classify_travel_style` agent tool.

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
