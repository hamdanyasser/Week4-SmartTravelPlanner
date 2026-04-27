# Code Review Notes — TripPilot Black

A plain-language log of what changed and why. New entries go on top.
Read this if you want to understand the *shape* of the project before
diving into the code.

---

## Day 1 — Project skeleton (2026-04-27)

### What changed

The repo went from empty to a runnable shell of TripPilot Black. We did not
implement any of the AI features yet — those land in later days. What we
*did* do is build the scaffolding that everything else will plug into,
and we wired up enough end-to-end plumbing to prove the round-trip works.

Files added:

- `REQUIREMENTS_CHECKLIST.md` — a row for every required deliverable in
  the brief, tagged with where it will live and its current status.
- `README.md`, `.gitignore`, `docker-compose.yml`.
- `backend/` — a small FastAPI app:
  - `app/main.py` — builds the FastAPI app, installs CORS, mounts routers,
    and registers a lifespan handler that is empty for now.
  - `app/config.py` — a typed `Settings` class powered by `pydantic-settings`.
  - `app/api/routes/health.py` — `GET /health`.
  - `app/api/routes/trip_briefs.py` — `POST /api/v1/trip-briefs`.
  - `app/schemas/trip_brief.py` — the `TripBriefResponse` Pydantic model
    and a hardcoded golden-demo stub.
  - `Dockerfile`, `requirements.txt`, `.env.example`, `.env`.
- `frontend/` — Vite + React + TypeScript:
  - `src/App.tsx` — a one-page "briefing room" that calls the stub
    endpoint and renders the four Decision Tension Board cards.
  - `src/api/client.ts` + `src/api/types.ts` — a thin fetch wrapper and
    a hand-written mirror of the backend schema.
  - `src/styles.css` — the dark "briefing room" styling.
  - `Dockerfile`, `package.json`, `vite.config.ts`, `tsconfig*.json`.
- `docker-compose.yml` — three services: `db` (Postgres + pgvector),
  `backend` (FastAPI), `frontend` (Vite dev). Postgres data lives in a
  named volume so embeddings will survive restarts.

### Why these specific shapes

**Folder layout — split by concern.** The brief explicitly calls out
"not one 600-line `main.py`". Even on Day 1 we already have separate
modules for routes, schemas, and (soon) agent / ml / rag / db / auth /
webhooks. Each new feature gets a folder; nothing leaks into `main.py`.

**`Settings` via `pydantic-settings`.** The brief's "no magic strings"
rule means *every* env var enters the program through one typed class.
We added `get_settings()` wrapped in `lru_cache` so the rest of the code
gets a singleton without a global. Day 1 only needs four settings, but
the pattern is set.

**Lifespan handler exists but is empty.** Day 1 doesn't need any
process-level singletons yet — but the brief says the DB engine, ML
model, embedding model, and LLM client must live there. So we put the
hook in now, even empty, so the wiring is obvious for whoever adds the
first singleton.

**`TripBriefResponse` shipped before the agent.** The schema *is* the
contract between the agent and the React UI. Locking it on Day 1 means
the frontend can be designed against a stable shape while the ML / RAG /
agent come online behind it. If we'd waited, every backend change would
ripple into the UI.

**`TravelStyle` is an `Enum`.** This is the same six-label set the ML
classifier will predict (Adventure, Relaxation, Culture, Budget, Luxury,
Family). Defining it once here means the frontend, the agent, and the
classifier all share one vocabulary — no string typos drifting between
modules.

**Stub endpoint returns a hardcoded golden-demo payload.** The point of
Day 1 is to prove the round-trip — fetch in the browser → FastAPI route
→ Pydantic-validated response → rendered card. The stub uses Madeira as
the top pick and Costa Rica as the counterfactual. These choices aren't
arbitrary: Madeira is genuinely warm, hiking-rich, and less-touristy in
July; Costa Rica is the "obvious" pick that breaks the $1,500 budget
once flights are factored in. When the real agent goes live, we want to
know whether it can recover something similar.

**Decision Tension Board UI on Day 1.** Even with stub data, the four
cards (Dream Fit / Reality Pressure / Final Verdict / Counterfactual)
are already laid out. This forces every later change to keep producing
data that fits this shape, which is the whole point of the product.

**Docker compose with three services.** A reviewer running
`docker compose up` on Day 1 already gets Postgres (with pgvector
ready), FastAPI, and the React UI. The DB is unused today, but it's the
same database we will use for users / agent runs / tool calls /
embeddings — one DB for everything, as the brief requires.

### What we deliberately did not do

- **No agent, no LLM client, no LangGraph yet.** Those would be wasted
  motion until the schema and skeleton are solid.
- **No SQLAlchemy / Alembic / pgvector code yet.** The DB container is
  up but the backend doesn't connect. We add that the day we add the
  first persisted entity (users), so the work is paid for by a feature.
- **No auth, no webhook, no streaming.** Each is its own day.
- **No tests yet.** The test plan is in `REQUIREMENTS_CHECKLIST.md`;
  tests land alongside the code they cover, starting Day 2.
- **No linter / pre-commit yet.** Same reason — adding lint
  infrastructure with five files of code is busywork. We add it before
  the first feature commit.

### How to verify Day 1

```bash
docker compose up --build
```

- `curl http://localhost:8000/health` → `{"status":"ok"}`
- `curl -X POST http://localhost:8000/api/v1/trip-briefs \
    -H "Content-Type: application/json" \
    -d '{"query":"two weeks in July, $1500, warm, hiking, not too touristy"}'`
  returns a fully-shaped `TripBriefResponse`.
- Open <http://localhost:5173> and click *Generate briefing* — the four
  Decision Tension Board cards render with the stub data.

### What's next (Day 2 preview)

- Stand up SQLAlchemy 2.x async with the first migration.
- Define `users`, `agent_runs`, `tool_calls`, and `embeddings` tables.
- Add the lifespan-managed DB engine and the `get_session` dependency.
- Add the first real test: schema round-trip for `TripBriefResponse`.
- Add `ruff` + `black` + a pre-commit config.
