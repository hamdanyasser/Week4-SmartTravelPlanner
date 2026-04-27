# TripPilot Black

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

## Code review notes

Every major change has a plain-language entry in
[`CODE_REVIEW_NOTES.md`](CODE_REVIEW_NOTES.md). Read that file first if you
want to understand why the project is shaped this way.
