# AtlasBrief — AI Travel Briefing Room

A Smart Travel Planner with a premium "AI travel briefing room" feel.

The unique product layer is the **Decision Tension Board**:

- **Dream Fit** - how well a destination matches the user's vibe.
- **Reality Pressure** - what live conditions say about going right now.
- **Final Verdict** - a synthesis that names the tradeoff.
- **Why Not the Obvious Pick?** - a counterfactual card explaining the road not taken.

## Current phase

Day 1 is a local skeleton. It proves that FastAPI and the React frontend can
talk to each other using a stable `TripBriefResponse` contract.

Not implemented yet: ML, RAG, the agent, auth, webhooks, persistence, and
deployment. The UI intentionally keeps the Decision Tension Board concept in
place with stub data so later phases have a clear product shape to fill.

## Repository layout

```text
.
|-- backend/                 FastAPI skeleton
|   |-- app/config.py        Typed settings, the only env access point
|   |-- app/main.py          Small app factory and router registration
|   |-- app/api/routes/      Health and trip-brief routes
|   `-- app/schemas/         Pydantic request/response models
|-- frontend/                Vite + React + TypeScript skeleton
|   `-- src/api/             Thin backend client and shared TS types
|-- docker-compose.yml       Local Postgres, backend, and frontend services
|-- REQUIREMENTS_CHECKLIST.md
`-- CODE_REVIEW_NOTES.md
```

Planned folders like `agent/`, `ml/`, `rag/`, `db/`, `auth/`, and `webhooks/`
do not exist yet. They should be added only when those phases start.

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

## Code review notes

Every major change has a plain-language entry in
[`CODE_REVIEW_NOTES.md`](CODE_REVIEW_NOTES.md). Read that file first if you
want to understand why the project is shaped this way.
