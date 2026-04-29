# Code Review Notes - AtlasBrief

A plain-language log of what changed and why. New entries go on top.
Read this before diving into the code if you want the project shape and
tradeoffs in human terms.

---

## Day 3 backend agent/auth/persistence/webhook (2026-04-29)

### What changed

Finished the backend submission path without changing the frontend design or
the `TripBriefResponse` / Decision Tension Board contract.

- Added auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`,
  bcrypt password hashing, JWT creation/verification, and current-user
  dependencies.
- Added persistence models: `users`, `agent_runs`, `tool_calls`, and
  `webhook_deliveries`, while keeping the existing RAG document/chunk tables.
- Added the required three tools only:
  `retrieve_destination_knowledge`, `classify_travel_style`, and
  `fetch_live_conditions`.
- Added `backend/app/agent/registry.py` as the explicit allowlist. Unknown
  tool names are refused and tool failures become structured recoverable
  errors.
- Added a small LangGraph agent: extract plan, run the three tools, synthesize
  the existing Decision Tension Board response.
- Added deterministic two-model routing placeholders in `backend/app/llm/` so
  the code records cheap-step and strong-step usage without pretending external
  LLM keys exist.
- Loaded the saved `backend/app/ml/model.joblib` once in FastAPI lifespan and
  used it through the ML tool, with a deterministic rule fallback.
- Added async live-conditions support with Open-Meteo-style weather lookup when
  enabled and deterministic fallback when disabled/unavailable.
- Added Discord webhook delivery with timeout, retry/backoff, and failure
  isolation. Webhook failure does not break the user response.
- Replaced the Day 1 trip-brief stub route with the backend agent path plus
  best-effort persistence and background webhook delivery.
- Added `backend/app/smoke_test.py` to verify the agent/tool/auth/webhook
  shape without requiring Docker/Postgres.

### Why these shapes

The project still needs to be demo-safe on a local machine where Docker and
external provider keys may be missing. That is why the route always prioritizes
returning a valid brief, while DB writes, live weather, LLM providers, and
webhooks degrade into explicit fallbacks instead of crashing.

The agent is intentionally simple and beginner-explainable. It does not invent
tools, stream tokens, or build the full future planner. It only does the
required backend path for the current submission.

### Verification

Commands run:

```powershell
cd backend
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m compileall app
.\.venv\Scripts\python -m app.smoke_test
.\.venv\Scripts\python -m app.rag.smoke_test
```

Smoke output confirmed:

- top pick: Madeira, Portugal,
- tools: `retrieve_destination_knowledge`, `classify_travel_style`,
  `fetch_live_conditions`,
- webhook failure isolated as `failed`.

Route verification with FastAPI `TestClient` confirmed:

- `GET /health` -> 200,
- `POST /api/v1/trip-briefs` -> 200,
- response top pick: Madeira,
- response includes all three tool trace entries.
- `POST /auth/register` with no reachable DB -> clean 503
  `Database is unavailable.`, not a traceback.

Docker/pgvector status:

```powershell
docker compose config --quiet
docker compose up -d db
```

Compose config still passes. Live DB startup remains blocked by the local Docker
Desktop engine pipe being unavailable:
`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`.
The unproven part is live Postgres/pgvector persistence/ingest on this machine,
not the Python fallback path.

### What remains

- Alembic migrations.
- Formal pytest suite, linting, pre-commit, and CI.
- Real provider-backed LLM routing and real provider cost accounting.
- LangSmith trace screenshot.
- Frontend auth flow/tool-trace work and demo video.

---

## Day 2 RAG verification finalization (2026-04-28)

### What I tried

I made a bounded attempt to exercise the real Postgres + pgvector path.

Commands attempted:

```powershell
docker compose config --quiet
docker info --format '{{.ServerVersion}}'
docker compose up -d db
```

Result:

- `docker compose config --quiet` passed.
- Docker daemon access failed before any container could start:
  `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`.
- `docker compose up -d db` failed for the same reason while trying to inspect
  `pgvector/pgvector:pg16`.

### What this means

The blocker is machine-level Docker availability, not RAG Python code. The live
DB path that remains unproven is:

1. start the `pgvector/pgvector:pg16` service,
2. enable `CREATE EXTENSION IF NOT EXISTS vector`,
3. create the RAG tables,
4. ingest markdown chunks into Postgres,
5. run a DB-backed nearest-neighbor retrieval query.

### What I added

Added `backend/app/rag/smoke_test.py`, a small local smoke test that verifies:

- DB/session/model modules import cleanly.
- the markdown corpus loads and chunks,
- deterministic fallback embeddings are produced,
- `backend/app/tools/retrieve_destination_knowledge.py` validates input through
  the current Pydantic schemas,
- fallback retrieval returns results.

Verification command:

```powershell
cd backend
.\.venv\Scripts\python -m app.rag.smoke_test
```

Observed output included 28 documents, 14 destinations, 28 chunks, and a Madeira
top result for the first manual retrieval query.

---

## RAG and database foundation (2026-04-28)

### What changed

Built the Day 2 RAG foundation without touching the frontend, the full agent,
auth, webhooks, or the Decision Tension Board.

- `data/knowledge/` now has 28 markdown destination documents across 14
  destinations. Each document has frontmatter for `destination`,
  `source_title`, and `source_type`.
- `backend/app/rag/chunking.py` loads markdown, validates frontmatter, and
  creates 900-character chunks with 150-character overlap.
- `backend/app/rag/embeddings.py` defines a clean embedding interface and the
  deterministic local fallback provider (`deterministic-hashing-v1`).
- `backend/app/rag/ingest_documents.py` can verify the corpus locally or ingest
  into Postgres/pgvector when the DB is available.
- `backend/app/rag/retriever.py` performs top-k retrieval and includes three
  manual retrieval probes.
- `backend/app/schemas/rag.py` defines Pydantic input/output schemas for RAG.
- `backend/app/tools/retrieve_destination_knowledge.py` is the tool-shaped
  wrapper the future agent will allowlist.
- `backend/app/db/session.py` and `backend/app/db/init_db.py` add the async
  SQLAlchemy foundation and pgvector extension setup.
- `backend/app/models/destination_document.py` and
  `backend/app/models/document_chunk.py` define the source-doc and chunk tables;
  chunks store metadata plus a `Vector(384)` embedding.
- `backend/requirements.txt` now includes SQLAlchemy, asyncpg, and pgvector.

### Why these shapes

**Local fallback first.** Docker/Postgres was not reliable during the previous
foundation audit, so the RAG path must be demo-safe without external services.
The deterministic embedding provider lets us prove ingestion and retrieval
locally while keeping the real pgvector path ready.

**Metadata is stored with every chunk.** The future agent needs more than text;
it needs to know which destination, source title, source type, and chunk index
produced an answer. That is why the schema and database model keep metadata
beside the content and embedding.

**900 characters + 150 overlap.** These source docs are short briefs, not long
articles. A 900-character chunk usually keeps one complete destination idea
together while a 150-character overlap protects context at boundaries.

**No full agent yet.** The retrieval tool exists, but LangGraph/LangChain,
tool allowlisting, model routing, and synthesis are still later phases.

### Verification

```powershell
cd backend
.\.venv\Scripts\python -m compileall app
.\.venv\Scripts\python -m app.rag.ingest_documents
```

Local fallback ingest returned 28 documents, 14 destinations, and 28 chunks.
Manual retrieval probes returned results for Madeira, Slovenia, and Costa Rica
queries using the deterministic fallback index.

---

## Product rename: TripPilot Black -> AtlasBrief (2026-04-27)

### What changed

The product name went from **TripPilot Black** to **AtlasBrief — AI Travel
Briefing Room**. The unique feature name (**Decision Tension Board**) is
unchanged. No architecture, no folder layout, no routes, no module names,
no Python imports moved.

User-facing strings updated:

- `README.md`, `CLAUDE.md`, `CODE_REVIEW_NOTES.md`,
  `REQUIREMENTS_CHECKLIST.md`, `docs/DAY1_CODE_WALKTHROUGH.md` — titles
  and body references.
- `backend/app/config.py` — `app_name` default is now `"AtlasBrief"`.
- `backend/.env.example` and `backend/.env` — `APP_NAME=AtlasBrief`.
- `frontend/index.html` — browser tab title.
- `frontend/package.json` — npm package name (`atlasbrief-frontend`).
- `frontend/src/App.tsx` — eyebrow tag now reads
  `ATLASBRIEF // BRIEFING ROOM`.
- `docker-compose.yml` — container labels now `atlasbrief_db`,
  `atlasbrief_backend`, `atlasbrief_frontend` (previously `trippilot_*`).

### What was deliberately kept

- **Postgres credentials** (`POSTGRES_USER=trippilot`,
  `POSTGRES_DB=trippilot`, the matching `DATABASE_URL`) — renaming these
  would orphan the existing `pgdata` volume and break authentication on
  any DB that has already been initialised. They are not user-facing.
  We will revisit at first DB migration if needed.
- **Folder layout** (`backend/app/...`, `frontend/src/...`) — never
  carried the brand.
- **Module names and Python imports** — never carried the brand.
- **Routes** (`/health`, `/api/v1/trip-briefs`) — `trip-briefs` is a
  generic noun for the response type, not a brand reference.

### Sanity checks run

- `python -c "from app.main import app; ..."` -> app.title now `AtlasBrief`,
  routes `/health` and `/api/v1/trip-briefs` still mounted.
- `docker compose config --quiet` -> OK.
- `npm run build` -> OK, 32 modules transformed.

---

## ML classifier foundation (2026-04-27)

### What changed

Added the travel-style classifier the brief requires, end to end.

- `data/destinations.csv` — 131 hand-labeled destinations across the six
  classes (Adventure 25, Culture 24, Relaxation 22, Budget 20, Luxury 20,
  Family 20). Each row has 9 numeric features. Labels follow the rule
  "single dominant style", documented in the README.
- `backend/app/ml/__init__.py` — empty package marker.
- `backend/app/ml/train_classifier.py` — the trainer. Loads the CSV,
  builds three `StandardScaler -> classifier` Pipelines (Logistic
  Regression, Random Forest, Gradient Boosting), runs 5-fold stratified
  CV on each, runs `GridSearchCV` on Random Forest, picks the winner by
  mean macro-F1, prints a per-class classification report on
  cross-validated predictions, saves the winner with joblib, and appends
  every experiment to `results.csv`.
- `backend/app/ml/results.csv` — append-only experiment log. New columns:
  `tuned` and `winner` so the run history is self-explanatory.
- `backend/app/ml/model.joblib` — the saved winner pipeline. Currently
  Logistic Regression at mean macro-F1 0.959.
- `backend/requirements.txt` — added `pandas==2.2.3`,
  `scikit-learn==1.5.2`, `joblib==1.4.2` (pinned).
- `.gitignore` — replaced the stale `artifacts/*.joblib` rule with a
  pattern that ignores any future joblib files under `backend/app/ml/`
  *except* the canonical `model.joblib`. The current artifact is small
  enough (2.7 KB) and is a brief deliverable, so it stays tracked.
- `README.md` — added an "ML — travel-style classifier" section
  covering the dataset, labeling rule, pipeline, the three classifiers,
  why we tune Random Forest, and the latest results table.
- `REQUIREMENTS_CHECKLIST.md` — rows 1.1–1.10 moved to DONE.

### Why these shapes

**Pipeline with the scaler inside.** The brief is explicit about leakage.
Putting `StandardScaler` inside the Pipeline means `cross_validate` and
`GridSearchCV` re-fit the scaler on each training fold — the validation
fold never leaks into the scaler's mean/std. This is the cleanest way to
defend against leakage on Saturday.

**Three classifiers, side-by-side.** LogReg is a low-variance baseline,
Random Forest handles non-linear feature interactions without much
tuning, Gradient Boosting is the standard stronger ensemble comparison.
Picking exactly these three is defensible on a 131-row tabular problem.

**Tune Random Forest specifically.** Tree ensembles have intuitive knobs
(`n_estimators`, `max_depth`, `min_samples_split`), and on small datasets
they over-fit without those controls. Tuning RF gives the most
interesting search space for the same compute.

**Winner selection by macro-F1, not "always save the tuned one".** The
brief says "save the winner" — so the script picks the actual winner
across all four candidates (3 baselines + 1 tuned). This run, untuned
Logistic Regression beats the tuned Random Forest (0.959 vs 0.951). The
script is honest about that and saves the LR pipeline.

**`cross_val_predict` for the per-class report.** Each prediction comes
from a fold where the row was held out, so the per-class numbers are
honest — not a self-evaluation on training data.

**Dataset under `data/` at repo root, not under `backend/app/ml/data/`.**
Hands-on instruction from the user. The trainer resolves the path from
its own location (`Path(__file__).resolve().parents[2] / "data" / ...`)
so it works whether you run it from the repo root or from `backend/`.

**Single dominant-style labeling rule.** Every destination is labeled by
its single dominant story, even when other features are non-trivial.
Banff has a high `family_score` but is `Adventure`. Kyoto has some
hiking but is `Culture`. This rule keeps labels defensible row by row.

### What we deliberately did not do

- No deep tuning of LogReg or GB. The brief says "tune at least one";
  we did. Doing all three would be busywork on a 131-row dataset.
- No SMOTE / class-weight rebalancing. The dataset is mildly imbalanced
  (Adventure 25 vs Family 20) but the per-class F1 floor is already
  ~0.95. Adding rebalancing now would be solving a non-problem.
- No feature engineering beyond the nine documented features.
- No pickling of the entire training script's state — only the fitted
  pipeline.
- No FastAPI integration yet. The model is on disk; loading it in the
  lifespan handler and exposing it via `Depends()` lands when we wire up
  the `classify_travel_style` agent tool.
- No tests for the trainer. Coming when we set up `pytest` + ruff/black
  in the next milestone.

### How to verify

```powershell
backend\.venv\Scripts\python -m app.ml.train_classifier
```

Should print three baseline rows, one tuned row, the winner's per-class
report, and "Saving winner (logistic_regression) to ...". Re-running
appends new rows to `results.csv` without overwriting old ones.

To smoke-test the saved model on the golden-demo profile (warm + hiking
+ less touristy + mid budget):

```powershell
cd backend
.\.venv\Scripts\python -c "import joblib, pandas as pd; m = joblib.load('app/ml/model.joblib'); print(m.predict(pd.DataFrame([{'budget_level':3,'climate_warmth':4,'hiking_score':5,'culture_score':3,'tourism_level':3,'luxury_score':2,'family_score':3,'safety_score':5,'avg_daily_cost_usd':120}])))"
```

Expected output: `['Adventure']` — which is what Madeira (the golden
top-pick) would land under.

---

## Foundation audit fixes (2026-04-27)

### What I checked

- `docker compose config` parses successfully.
- The backend starts locally with Uvicorn.
- `GET /health` returns `{"status":"ok"}`.
- `POST /api/v1/trip-briefs` returns the stub `TripBriefResponse`.
- The frontend builds with `npm run build`.
- The frontend client points at the backend through `VITE_API_BASE_URL`, with a
  local `http://localhost:8000` fallback for Day 1 development.
- `backend/.env` is ignored and not tracked.
- `backend/.env.example` exists.
- `main.py` is small and only wires the app together.
- No runtime `os.getenv` calls are scattered outside settings.

Full `docker compose up --build` was attempted, but Docker Desktop failed while
pulling the `pgvector/pgvector:pg16` image with a containerd input/output error
before the app containers could start. The compose file itself validates with
`docker compose config --quiet`, and the backend/frontend were verified locally.

### What I fixed

- `docker-compose.yml` no longer hardcodes the local Postgres password. The
  database and backend now read local environment values from `backend/.env`.
  This keeps tracked config clean while preserving the local Docker workflow.
- `backend/.env.example` now includes the Postgres variables needed by Docker
  Compose: `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.
- `backend/app/config.py` now uses the same local database placeholder as
  `.env.example`, so the defaults do not drift from documented setup.
- The frontend TypeScript build no longer leaves generated `vite.config.js`,
  `vite.config.d.ts`, or root `*.tsbuildinfo` files in the repo. Build metadata
  is directed into `node_modules/.tmp`, and `*.tsbuildinfo` is ignored as a
  backstop.
- `README.md` now matches the actual Day 1 files. It no longer claims planned
  `agent/`, `ml/`, `rag/`, `db/`, `auth/`, or `webhooks/` folders already
  exist.

### What I deliberately did not change

- No ML, RAG, agent, auth, webhook, Supabase, or deployment work.
- No app redesign.
- No removal of the Decision Tension Board.
- No fake production secrets. `backend/.env` stays local and untracked.

---

## Day 1 - Project skeleton (2026-04-27)

### What changed

The repo started as a runnable shell of AtlasBrief. It does not implement
AI features yet. Its purpose is to prove the local round trip:

React form -> FastAPI route -> Pydantic response -> Decision Tension Board UI.

Files and folders in the Day 1 skeleton:

- `REQUIREMENTS_CHECKLIST.md` - a row for every required deliverable in the
  brief, with current status.
- `README.md`, `.gitignore`, `docker-compose.yml`.
- `backend/` - a small FastAPI app:
  - `app/main.py` - creates the FastAPI app, installs CORS, and mounts routers.
  - `app/config.py` - typed settings via `pydantic-settings`.
  - `app/api/routes/health.py` - `GET /health`.
  - `app/api/routes/trip_briefs.py` - `POST /api/v1/trip-briefs`.
  - `app/schemas/trip_brief.py` - request/response models and the Day 1 stub.
  - `Dockerfile`, `requirements.txt`, `.env.example`.
- `frontend/` - Vite + React + TypeScript:
  - `src/App.tsx` - one-page briefing room UI.
  - `src/api/client.ts` and `src/api/types.ts` - backend client and TS schema
    mirror.
  - `src/styles.css` - current dark briefing-room styling.
  - `Dockerfile`, `package.json`, `vite.config.ts`, `tsconfig*.json`.

### Why these shapes

**Small `main.py`.** The app entry point only builds the FastAPI app, registers
middleware, and mounts routers. Route logic and schemas live elsewhere so future
phases do not pile into one file.

**Settings through one module.** Environment-backed values enter through
`backend/app/config.py`. This keeps env handling discoverable and prevents
configuration from scattering across route code.

**`TripBriefResponse` before the real agent.** The response schema is the
contract between the future agent and the React UI. Locking the shape early lets
the frontend prove the Decision Tension Board without pretending ML or RAG
already exists.

**Stub endpoint.** The Day 1 endpoint returns a hardcoded golden-demo payload
for Madeira versus Costa Rica. That is intentional scaffolding, not the final
recommendation engine.

**Docker Compose.** The local stack includes Postgres with pgvector, FastAPI,
and Vite. The database is present for later phases but the backend does not
connect to it yet.

### What remains for later phases

- Add persistence only when the first stored entity lands.
- Add ML only when the Decision Tree phase starts.
- Add RAG and the agent only after the local API and UI contract stay stable.
- Add tests, linting, and formatting infrastructure before broad feature work.

### How to verify the skeleton

```powershell
Copy-Item backend\.env.example backend\.env
docker compose up --build
```

Then verify:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod `
  -Uri http://localhost:8000/api/v1/trip-briefs `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"query":"two weeks in July, 1500 budget, warm hiking, not too touristy"}'
```

Open <http://localhost:5173> and generate the briefing. The four Decision
Tension Board sections should render from the stub response.
