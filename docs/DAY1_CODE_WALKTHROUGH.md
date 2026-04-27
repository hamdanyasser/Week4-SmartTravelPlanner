# Day 1 Code Walkthrough — AtlasBrief — AI Travel Briefing Room

This document is for **you** — the human who vibe-coded Day 1 and now has to
defend it on Saturday. Every section is written in plain English. If a
sentence sounds clever instead of clear, treat that as a bug in this doc.

Read this top to bottom **once**. Then re-read sections 12 and 14 the night
before review.

---

## 1. What the project currently does

AtlasBrief is a **Smart Travel Planner**. The unique product idea is
the **Decision Tension Board** — instead of just suggesting a destination,
the app shows the *tension* between:

- **Dream Fit** — how well the destination matches the user's vibe.
- **Reality Pressure** — what live conditions (weather, flights) say
  about going *right now*.
- **Final Verdict** — a sentence that names the tradeoff.
- **Why Not the Obvious Pick?** — a counterfactual card explaining the
  destination most people would have guessed, and why we didn't pick it.

**As of Day 1, none of this is real yet.** What works:

1. Open <http://localhost:5173>.
2. Type a trip question (the golden demo query is pre-filled).
3. Click **Generate briefing**.
4. The React app calls `POST http://localhost:8000/api/v1/trip-briefs`.
5. The FastAPI backend returns a **hardcoded** response about Madeira vs.
   Costa Rica — it never reads the query, never calls an LLM, never
   touches a database, never consults any model.
6. The React app renders that response into the four Decision Tension
   Board cards.

That round-trip is the entire Day 1 deliverable. It proves the
**plumbing** works end-to-end before we plug any AI behind it.

---

## 2. What each important file does (one-liner version)

| File | One-line job |
|---|---|
| `docker-compose.yml` | Starts three containers in one command: Postgres, FastAPI, Vite. |
| `backend/Dockerfile` | Recipe for the backend container image. |
| `backend/requirements.txt` | Pinned Python deps. Day 1 has only 4. |
| `backend/.env.example` | Template config for local dev — checked into git. |
| `backend/.env` | Real config, **not** in git. You copy it from `.env.example`. |
| `backend/app/main.py` | Builds the FastAPI app, installs CORS, mounts routers. |
| `backend/app/config.py` | One typed `Settings` class. The only place env vars enter the program. |
| `backend/app/api/routes/health.py` | `GET /health` → `{"status":"ok"}`. |
| `backend/app/api/routes/trip_briefs.py` | `POST /api/v1/trip-briefs` → returns the stub. |
| `backend/app/schemas/trip_brief.py` | Every Pydantic model + the hardcoded stub payload. |
| `frontend/Dockerfile` | Recipe for the frontend container image. |
| `frontend/package.json` | Frontend deps + npm scripts (`dev`, `build`). |
| `frontend/vite.config.ts` | Vite dev-server config. |
| `frontend/tsconfig*.json` | TypeScript compiler settings. |
| `frontend/index.html` | Page shell that loads `src/main.tsx`. |
| `frontend/src/main.tsx` | React entry — mounts `<App />`. |
| `frontend/src/App.tsx` | The whole UI lives here for Day 1. |
| `frontend/src/api/client.ts` | Two `fetch()` wrappers: `postTripBrief` and `fetchHealth`. |
| `frontend/src/api/types.ts` | TypeScript mirror of the backend schema. |
| `frontend/src/styles.css` | Dark "briefing room" styling. |
| `REQUIREMENTS_CHECKLIST.md` | Every brief deliverable mapped to a file path + status. |
| `CODE_REVIEW_NOTES.md` | Plain-language log of what changed and why, newest first. |
| `README.md` | What the project is + how to run the skeleton. |

---

## 3. The full Day 1 request flow

This is the single most important thing to understand on Day 1.

```
┌─────────────────────────┐
│  Browser: localhost:5173│
└─────────────┬───────────┘
              │ user clicks "Generate briefing"
              ▼
┌─────────────────────────────────────────────────┐
│  frontend/src/App.tsx                           │
│   handleSubmit() calls postTripBrief(query)     │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  frontend/src/api/client.ts                     │
│   fetch(`${API_BASE_URL}/api/v1/trip-briefs`)   │
│   POST, JSON body: { query }                    │
└─────────────┬───────────────────────────────────┘
              │ HTTP POST → http://localhost:8000
              ▼
┌─────────────────────────────────────────────────┐
│  backend/app/main.py                            │
│   FastAPI app + CORS middleware                 │
│   forwards /api/v1/* to the trip_briefs router  │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  backend/app/api/routes/trip_briefs.py          │
│   create_trip_brief(payload: TripBriefRequest)  │
│     1. Pydantic validates the JSON body         │
│     2. calls example_stub_response(query)       │
│     3. returns TripBriefResponse                │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  backend/app/schemas/trip_brief.py              │
│   example_stub_response() returns the hardcoded │
│   Madeira-vs-Costa-Rica dict                    │
│   TripBriefResponse.model_validate() shapes it  │
└─────────────┬───────────────────────────────────┘
              │ JSON response
              ▼
┌─────────────────────────────────────────────────┐
│  frontend/src/api/client.ts                     │
│   parses JSON, returns typed TripBriefResponse  │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  frontend/src/App.tsx                           │
│   setBrief(result)                              │
│   React re-renders: 4 Decision Tension Board    │
│   cards (Dream Fit, Reality Pressure, Verdict,  │
│   Counterfactual) appear on screen.             │
└─────────────────────────────────────────────────┘
```

**The key insight:** the *shape* of the response is fixed by the Pydantic
models. The frontend can be built, styled, and demoed without the agent
existing yet, because the contract between them is locked.

---

## 4. What `docker-compose.yml` is doing

Compose is a tool that brings up several Docker containers together. Our
file declares **three services** plus **one named volume**.

```yaml
services:
  db:        # Postgres + pgvector. The same DB will eventually hold
             # users, agent_runs, tool_calls, embeddings.
  backend:   # FastAPI on port 8000. Reads ./backend/.env.
             # Mounts ./backend into /app so code edits hot-reload.
  frontend:  # Vite dev server on port 5173. Mounts ./frontend.
             # The /app/node_modules anonymous volume keeps the
             # container's installed deps even though we mount the host.
volumes:
  pgdata:    # Named volume → Postgres data survives container restarts.
```

Things to notice:

- **`env_file: ./backend/.env`** is used by both `db` and `backend`. The
  Postgres container reads `POSTGRES_USER` / `POSTGRES_PASSWORD` /
  `POSTGRES_DB` from the same file the backend reads. One source of truth.
- **`$$POSTGRES_USER`** in the healthcheck is escaped because Compose
  itself does variable substitution; `$$` tells Compose "don't expand
  this — leave the `$` so the shell inside the container expands it".
- **`depends_on: db: condition: service_healthy`** means the backend won't
  even *start* until Postgres reports healthy.
- **`--reload`** on uvicorn means saving a `.py` restarts the server
  automatically. Dev only — would be wrong in production.
- **`--host 0.0.0.0`** makes the dev server bind to all interfaces inside
  the container, so the host machine can reach it. `127.0.0.1` only
  would make it unreachable from outside the container.

The `pgdata` named volume is what keeps your Postgres rows and (later)
embeddings alive across `docker compose down && docker compose up`.

---

## 5. What `backend/app/config.py` does

This is the **only** file allowed to read environment variables.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        case_sensitive=False, extra="ignore",
    )
    app_name: str = "AtlasBrief"   # full product: "AtlasBrief — AI Travel Briefing Room"
    app_env: str = "development"
    app_debug: bool = True
    cors_allow_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://...trippilot..."
```

Key ideas:

- **`pydantic-settings`** auto-loads each field from the matching env var
  (case-insensitive). `app_name` ← `APP_NAME`, `database_url` ←
  `DATABASE_URL`, etc. If a required field is missing, the app refuses
  to start — that's better than failing on the third HTTP request.
- **`extra="ignore"`** means extra env vars (like `POSTGRES_USER`, which
  the DB container needs but Python doesn't) are silently ignored, not an
  error.
- **`cors_origins_list`** is a `@property` that splits the
  comma-separated string into a real list.
- **`@lru_cache(maxsize=1) def get_settings()`** is the Python-idiomatic
  singleton: the first call instantiates `Settings()`, every later call
  returns the same instance for free. This is exactly what the brief
  means by "use `lru_cache` on deterministic, expensive functions".

When the brief says **"no `os.getenv` scattered through your code"**, this
is what they mean. Anywhere else in the codebase that needs config does
`get_settings().database_url`, not `os.getenv("DATABASE_URL")`.

---

## 6. What `backend/app/main.py` does

This file is **deliberately small** — the brief calls out "not one
600-line `main.py`" and we are starting on the right side of that.

It does four things, in order:

1. **Defines `lifespan`** — an async context manager. Code before
   `yield` runs on startup, code after runs on shutdown. Day 1 has both
   sides empty. From Day 5 we'll build the DB engine, load the joblib
   ML model, and instantiate the LLM client here, **once per process**.
2. **`create_app()`** — the app factory. It:
   - reads settings via `get_settings()`,
   - constructs the `FastAPI` instance,
   - installs CORS middleware so the browser at `:5173` can call `:8000`,
   - mounts the `health` router (no prefix → `/health`),
   - mounts the `trip_briefs` router with `prefix="/api/v1"` → so the
     route ends up at `/api/v1/trip-briefs`.
3. **`app = create_app()`** — the module-level `app` object that uvicorn
   imports via `app.main:app`.

The factory pattern matters because tests can call `create_app()` to get
a fresh app with overridden dependencies — important once auth and DB
sessions arrive.

---

## 7. What `backend/app/api/routes/health.py` does

Smallest file in the codebase:

```python
@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

It says: "the web layer is up". It does **not** check the database, the
LLM, or anything downstream. That's intentional — health checks should
be fast and not cascade-fail. Docker, load balancers, and humans use this
endpoint to know the process responds at all.

---

## 8. What `backend/app/api/routes/trip_briefs.py` does

The user-facing endpoint. Day 1 version:

```python
@router.post("/trip-briefs", response_model=TripBriefResponse)
async def create_trip_brief(payload: TripBriefRequest) -> TripBriefResponse:
    stub = example_stub_response(payload.query)
    return TripBriefResponse.model_validate(stub)
```

What's happening line by line:

1. **`payload: TripBriefRequest`** — FastAPI sees the type hint, reads
   the JSON body, and validates it against the `TripBriefRequest` model
   *before* the function body runs. Length out of range? Missing
   `query`? FastAPI returns a 422 automatically.
2. **`example_stub_response(payload.query)`** — returns the hardcoded
   Madeira/Costa-Rica dict. Note: it accepts `payload.query` only so the
   echoed `query` field in the response matches what the user sent. The
   *recommendation* itself ignores the query.
3. **`TripBriefResponse.model_validate(stub)`** — round-trips the dict
   through Pydantic so we know the stub matches the schema.
4. **`response_model=TripBriefResponse`** — FastAPI also re-validates on
   the way *out* and uses this model for the OpenAPI docs.

The comment at the top of the file lists the four things this handler
will do once the agent lands: persist the run, invoke the agent, stream
the verdict, fire the webhook.

---

## 9. What `backend/app/schemas/trip_brief.py` does

This is the **contract file**. The whole product depends on these shapes
being right.

It defines:

- **`TravelStyle`** — string `Enum` with the six bootcamp labels
  (Adventure, Relaxation, Culture, Budget, Luxury, Family). Defining
  these once means the frontend, the agent, and the eventual ML
  classifier all use the same vocabulary — no string typos drifting
  between modules.
- **`TripBriefRequest`** — `{ query: str }` with min/max length so the
  agent never receives empty or absurdly-long input.
- **`DreamFitScore`** — score 0–100, `matched_traits: list[str]`,
  `rationale: str`. This is what ML + RAG will produce later.
- **`RealityPressureScore`** — score 0–100, `weather_signal`,
  `flight_signal`, `rationale`. **The score is inverted on purpose**:
  100 = no pressure (smooth sailing), 0 = high pressure (bad weather,
  expensive flights). This way both axes of the UI are "higher is
  better".
- **`DestinationCandidate`** — one card on the board: name, country,
  travel_style, dream_fit, reality_pressure.
- **`CounterfactualCard`** — `{ obvious_pick, why_not_chosen }`.
- **`ToolTraceEntry`** — `{ tool, summary }`. Empty list on Day 1; once
  the agent runs we populate it so the UI can show *which tools fired*.
- **`TripBriefMeta`** — token counts, USD cost, latency, model names.
  Zeroed on Day 1; populated by the LLM-routing layer later.
- **`TripBriefResponse`** — the whole envelope.
- **`example_stub_response(query)`** — the hardcoded payload the route
  returns. The Madeira/Costa-Rica content here is the **golden demo**
  hand-picked answer; the real agent is judged against whether it can
  recover something similar.

`from __future__ import annotations` at the top is a Python 3.10+ trick
that defers type-hint evaluation; lets us reference types before they
are declared.

---

## 10. What `frontend/src/App.tsx` does

The entire Day 1 UI is in one component. It uses four pieces of state:

```tsx
const [query,   setQuery]   = useState(GOLDEN_DEMO_QUERY);
const [brief,   setBrief]   = useState<TripBriefResponse | null>(null);
const [loading, setLoading] = useState(false);
const [error,   setError]   = useState<string | null>(null);
```

- **`query`** — the textarea content. Pre-filled with the golden demo
  query so demos always work even if the user types nothing.
- **`brief`** — the response from the backend, or `null` until the user
  clicks the button.
- **`loading`** — used to disable the button and show "Briefing…".
- **`error`** — populated if the fetch fails; renders a red banner.

`handleSubmit` is the only event handler:

1. `e.preventDefault()` so the form doesn't reload the page.
2. set loading on, error off.
3. `await postTripBrief(query)` — the HTTP call.
4. on success → `setBrief(result)`, on failure → `setError(...)`.
5. `finally` → `setLoading(false)` no matter what.

The render:

- The header (eyebrow + title + subtitle).
- The form (label + textarea + button).
- A red error banner if `error`.
- If `brief` exists, the four cards: title with destination, a tag with
  the travel style, a 2-column grid of `Dream Fit` / `Reality Pressure`,
  the `Final Verdict` card, and the `Why not <obvious_pick>?` card.

Notice it uses `brief.top_pick.dream_fit.score` directly — no defensive
null checks. That's safe because TypeScript + the `if (brief)` guard
make it impossible to render this branch with a missing `brief`.

---

## 11. What `frontend/src/api/client.ts` does

A thin wrapper around `fetch`. Two reasons it exists:

1. **Network code lives outside components.** Later we'll swap `fetch` for
   a streaming client; UI code shouldn't have to change.
2. **Typed responses.** It returns `Promise<TripBriefResponse>`, so the
   component never deals with raw JSON.

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
```

`VITE_API_BASE_URL` is set by Compose; the `??` fallback means running
`npm run dev` outside Docker also works.

The `fetch` call itself is straightforward — POST, JSON body, JSON
response. If `res.ok` is false, it reads the body as text and throws an
`Error` that bubbles up to `App.tsx`'s `catch`.

`fetchHealth` exists for future use; nothing calls it yet.

---

## 12. What is still fake / stubbed

Be honest about this in the code review. **All of it is fake on Day 1.**

| Concept | Day 1 reality |
|---|---|
| Recommendation engine | Hardcoded Madeira/Costa-Rica dict in `example_stub_response`. |
| User query handling | The query is echoed but never *read* by the recommender. |
| ML classifier | Not built. `TravelStyle` enum is defined; no model file. |
| RAG retrieval | Not built. No knowledge base, no embeddings table populated. |
| LangGraph / LangChain agent | Not built. No tools, no allowlist, no graph. |
| Two-model routing | `meta.cheap_model` and `meta.strong_model` are both `"stub"`. |
| Token / cost logging | All zeros. |
| Auth (sign-up / login) | Not built. Endpoints are public. |
| Database | Container runs; backend never connects. |
| Webhook delivery | Not built. |
| Streaming response | Not built — single JSON response. |
| Tool trace UI | `tools_used` is always an empty list. |
| Tests | None yet. |
| LangSmith tracing | None yet. |
| Linter / pre-commit | None yet. |

---

## 13. What is still missing from the Week 4 requirements

Cross-reference: full table is in `REQUIREMENTS_CHECKLIST.md`. Here's the
short version of what is **not** done yet, grouped by section of the brief:

1. **ML classifier** — dataset (100–200 destinations), `Pipeline`, 3+
   classifier comparison with k-fold CV, accuracy + macro-F1 mean/std,
   tuning, per-class metrics, `results.csv`, joblib artifact.
2. **RAG** — 10–15 destinations / 20–30 docs, pgvector embeddings,
   chunking + retrieval rationale.
3. **Agent** — three tools (`retrieve_destination_knowledge`,
   `classify_travel_style`, `fetch_live_conditions`), Pydantic input
   schemas per tool, explicit allowlist, LangGraph/LangChain wiring,
   LangSmith trace screenshot.
4. **Two-model routing** — cheap model for tool-arg extraction & RAG
   query rewriting, strong model for synthesis, per-step token & cost
   logging.
5. **Persistence** — async SQLAlchemy 2.x, `users` / `agent_runs` /
   `tool_calls` / `embeddings` tables, Alembic migrations.
6. **Auth** — register, login, password hashing, JWT, `current_user`
   dependency.
7. **Frontend** — sign-in flow, tool-trace visibility, optional
   streaming.
8. **Webhook delivery** — Discord/Slack/Sheets/email with timeout,
   retry-with-backoff, structured failure logging.
9. **Engineering standards still pending** — DI via `Depends`, lifespan
   singletons (the hook exists, nothing in it yet), `lru_cache` /
   TTL caches, `tenacity` retries on external calls, `structlog` JSON
   logs, ruff + black + pre-commit, tests, GitHub Actions CI.
10. **README deliverables** — architecture diagram, dataset labeling
    rules, chunking rationale, model comparison table, per-query cost
    breakdown, LangSmith trace screenshot, 3-minute demo video.

Treat this list as the build plan for Days 2–7.

---

## 14. What you must be able to explain in Saturday code review

If a reviewer asks any of these and you say *"the tutorial said so"*,
you'll lose points. Be ready with a one-sentence answer for each.

1. **Why is `main.py` so small?** Because the brief explicitly forbids
   one giant file. The factory pattern keeps wiring separate from
   feature code.
2. **Why a lifespan handler that's currently empty?** Because
   process-level singletons (DB engine, ML model, LLM client) belong
   there from the start of their existence, not retrofitted later.
3. **Why `pydantic-settings` and not `os.getenv`?** Single typed source
   of truth; the app refuses to start if a required env var is missing,
   which beats failing on the third request.
4. **Why is `get_settings()` wrapped in `lru_cache`?** It's the
   Python-idiomatic singleton — first call instantiates, later calls
   are free. Exactly the kind of place the brief tells us to cache.
5. **Why is `TravelStyle` an enum (not a string)?** So the frontend, the
   agent, and the future ML classifier all share the same vocabulary,
   with typo-checks at compile time on both sides.
6. **Why is the `Reality Pressure` score inverted (100 = good)?** So
   both axes of the Decision Tension Board read "higher is better" —
   easier UI, easier explanation.
7. **Why ship the response schema before the agent?** The schema *is*
   the contract between the agent and the UI. Locking it lets the
   frontend stabilise while ML/RAG/agent come online behind it.
8. **What does `$$POSTGRES_USER` in the compose healthcheck mean?**
   Compose itself does variable substitution; `$$` escapes it so the
   `$` survives into the container shell where it actually expands.
9. **Why is `backend/.env` not tracked in git, but `.env.example` is?**
   `.env` may hold real secrets, so it stays local. `.env.example` is a
   template that documents what keys exist — checked in for reviewers.
10. **What's still stubbed?** Everything AI-shaped: the recommendation
    is a hardcoded dict, no ML model, no RAG, no agent, no DB usage, no
    auth, no webhook, no token accounting. Day 1 is plumbing only.
11. **Why CORS on `http://localhost:5173`?** Browsers refuse cross-origin
    requests by default; we explicitly allow the Vite dev origin, and
    only that origin.
12. **Why a named volume `pgdata`?** So Postgres data (and eventually
    pgvector embeddings) survives `docker compose down`.

---

## Architecture diagram (text form)

```
                          ┌─────────────────────────────┐
                          │        Browser (you)        │
                          └──────────────┬──────────────┘
                                         │
                       http://localhost:5173
                                         │
                          ┌──────────────▼──────────────┐
                          │  frontend container         │
                          │  Vite dev + React + TS      │
                          │  - App.tsx (UI)             │
                          │  - api/client.ts (fetch)    │
                          │  - api/types.ts (TS schema) │
                          └──────────────┬──────────────┘
                                         │
                      POST /api/v1/trip-briefs
                                         │
                          ┌──────────────▼──────────────┐
                          │  backend container          │
                          │  FastAPI + uvicorn          │
                          │  - main.py (factory)        │
                          │  - config.py (Settings)     │
                          │  - api/routes/health.py     │
                          │  - api/routes/trip_briefs.py│
                          │  - schemas/trip_brief.py    │
                          └──────────────┬──────────────┘
                                         │
                              (no traffic yet)
                                         │
                          ┌──────────────▼──────────────┐
                          │  db container               │
                          │  Postgres + pgvector        │
                          │  volume: pgdata             │
                          └─────────────────────────────┘

  Future phases will add:
    - agent/      LangGraph + 3 tools (allowlist, Pydantic-validated)
    - ml/         joblib classifier loaded once at startup
    - rag/        chunker + retriever over pgvector
    - db/         SQLAlchemy 2.x async sessions, Alembic migrations
    - auth/       register / login / JWT / current_user dependency
    - webhooks/   Discord/Slack delivery with retries
```

---

## 10-question mini quiz

Cover the answers, attempt them, then check.

1. **Q.** What does `lifespan` in `main.py` do?
   **A.** Runs code on app startup and shutdown — where future
   singletons (DB engine, ML model, LLM client) will live.

2. **Q.** Why is `Settings.cors_allow_origins` stored as a string and
   exposed via a `cors_origins_list` property?
   **A.** Env vars are always strings; the property splits the
   comma-separated string into a list when CORS needs it.

3. **Q.** What is the *only* file allowed to read environment variables?
   **A.** `backend/app/config.py`. Everything else calls `get_settings()`.

4. **Q.** What does `@lru_cache(maxsize=1)` on `get_settings` give us?
   **A.** A cached singleton — first call builds `Settings()`, every
   later call returns the same instance for free.

5. **Q.** What HTTP method does the trip-briefs endpoint use, and what
   path does it live at?
   **A.** `POST /api/v1/trip-briefs`.

6. **Q.** Where does Pydantic validate the incoming request body?
   **A.** In the route's type hint: `payload: TripBriefRequest` — FastAPI
   validates *before* the function body runs.

7. **Q.** Why is the `Reality Pressure` score inverted (100 = good)?
   **A.** So both Decision Tension Board axes read "higher is better".

8. **Q.** What three services does `docker-compose.yml` start?
   **A.** `db` (Postgres + pgvector), `backend` (FastAPI), `frontend`
   (Vite dev).

9. **Q.** Why does the compose healthcheck use `$$POSTGRES_USER` (double
   dollar)?
   **A.** Compose escapes its own variable substitution; `$$` survives
   into the container shell so the shell can expand it there.

10. **Q.** What is the *only* real thing that runs end-to-end on Day 1?
    **A.** The HTTP round-trip: form → fetch → FastAPI route → Pydantic
    validation → hardcoded stub response → React render. Everything else
    (ML, RAG, agent, DB, auth, webhook) is not implemented yet.

---

## Files I MUST know cold (review-critical)

You will be asked specifically about these. Re-read each one before the
review.

- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/api/routes/trip_briefs.py`
- `backend/app/schemas/trip_brief.py`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `docker-compose.yml`

For each, you should be able to:

- Open the file from memory and recall the rough shape.
- Explain *why* it exists (not what it contains line by line).
- Name one decision you would defend if challenged.

## Files I can explain generally

You don't need to memorise these. Knowing their *role* is enough.

- `backend/Dockerfile` — Python 3.11 slim, installs `requirements.txt`,
  runs uvicorn.
- `frontend/Dockerfile` — Node 20 alpine, installs npm deps, runs
  `npm run dev`.
- `backend/requirements.txt` — 4 pinned deps: fastapi, uvicorn,
  pydantic, pydantic-settings.
- `frontend/package.json` — react/react-dom + vite + typescript.
- `frontend/vite.config.ts`, `tsconfig*.json` — Vite + TS config.
- `frontend/src/main.tsx` — React mount; one-liner.
- `frontend/src/styles.css` — visual design only; no logic.
- `frontend/src/api/types.ts` — hand-mirrored TS version of the
  backend schema.
- `backend/app/api/routes/health.py` — `GET /health` → `{"status":"ok"}`.
- `.gitignore`, `backend/.env.example`, `backend/.dockerignore`,
  `frontend/.dockerignore` — git/Docker hygiene.

---

## How to use this document

- **Today:** read it once, end to end.
- **Mid-week:** when you change a file, update the relevant section.
- **Friday night:** re-read sections 12, 13, 14, and the quiz. Take the
  quiz cold. If you score below 8/10, re-read section 3.
- **Saturday morning:** open every file in §"Files I MUST know cold"
  and skim it once.
