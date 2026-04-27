# Code Review Notes - TripPilot Black

A plain-language log of what changed and why. New entries go on top.
Read this before diving into the code if you want the project shape and
tradeoffs in human terms.

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

The repo started as a runnable shell of TripPilot Black. It does not implement
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
