# AtlasBrief — Architecture

A submission-ready, beginner-friendly map of how a single trip brief flows
through the stack. Read top-to-bottom; everything mirrors the order in
which the code actually runs.

---

## High-level diagram

```
┌──────────────────────┐     fetch (Bearer? optional)       ┌────────────────────────────┐
│   React + Vite SPA   │  ──────────────────────────────►   │  FastAPI (uvicorn)         │
│   /                  │                                    │                            │
│   Cinematic prompt   │                                    │  POST /api/v1/trip-briefs  │
│   Trip DNA panel     │  ◄────────  TripBriefResponse ─────│  GET  /health              │
│   Mission timeline   │                                    │  POST /auth/register       │
│   Decision Tension   │                                    │  POST /auth/login          │
│   Travel memo        │                                    │  GET  /auth/me             │
│   Evidence drawer    │                                    │                            │
└──────────────────────┘                                    └─────────────┬──────────────┘
                                                                          │
                                          ┌───────────────────────────────┼──────────────────────────────┐
                                          │                               │                              │
                                          ▼                               ▼                              ▼
                              ┌──────────────────────┐         ┌─────────────────────┐        ┌────────────────────┐
                              │ LangGraph agent      │         │ SQLAlchemy 2.x async │        │  BackgroundTasks   │
                              │ plan → tools →       │         │  + asyncpg + pgvector│        │  Discord webhook   │
                              │ synthesize           │         │                      │        │  (timeout, retry,  │
                              │                      │         │  users               │        │   isolated failure)│
                              │ Allowlist (registry):│         │  agent_runs          │        └────────────────────┘
                              │ - retrieve_destinat… │         │  tool_calls          │
                              │ - classify_travel_…  │         │  webhook_deliveries  │
                              │ - fetch_live_condit… │         │  destination_documents│
                              └──────────┬───────────┘         │  document_chunks     │
                                         │                     │   (Vector(384) +     │
                                         ▼                     │    ivfflat cosine)   │
                  ┌──────────────────────┴────────────────────┐└──────────┬───────────┘
                  │                      │                    │           │
                  ▼                      ▼                    ▼           ▼
        ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
        │ retrieve_destinat… │  │ classify_travel_…│  │ fetch_live_      │
        │  RAG retriever     │  │  joblib pipeline │  │  conditions      │
        │  pgvector first,   │  │  (LR winner,     │  │  Open-Meteo or   │
        │  local fallback    │  │  rule fallback)  │  │  deterministic   │
        │                    │  │                  │  │  fallback        │
        └─────────┬──────────┘  └─────────┬────────┘  └─────────┬────────┘
                  │                       │                     │
                  ▼                       ▼                     ▼
       ┌──────────────────────┐  ┌────────────────────┐  ┌──────────────────┐
       │ data/knowledge/*.md  │  │ backend/app/ml/    │  │  External weather│
       │ (28 docs / 14 dest.) │  │ model.joblib       │  │  API (HTTP)      │
       │ + DocumentChunk rows │  │ + results.csv      │  │                  │
       └──────────────────────┘  └────────────────────┘  └──────────────────┘
```

## Per-request flow (golden demo query)

1. **HTTP** `POST /api/v1/trip-briefs { query }` lands at
   `backend/app/api/routes/trip_briefs.py`.
2. **Auth dependency** `get_optional_current_user` returns `None` for
   anonymous demos or a `User` row when the SPA forwards a JWT.
3. **Persistence (best-effort)** `create_agent_run` inserts an
   `agent_runs` row in status `started` (or returns `None` if Postgres
   is unavailable).
4. **LangGraph agent** in `backend/app/agent/graph.py`:
   - `plan_step` → `extract_trip_plan` (cheap-model fallback) parses
     traits + destination + counterfactual.
   - `tools_step` runs **exactly three tools** through the
     `execute_tool` allowlist:
     1. `retrieve_destination_knowledge` (RAG — pgvector first, local
        deterministic fallback).
     2. `classify_travel_style` (joblib model loaded once at lifespan,
        rule-based fallback).
     3. `fetch_live_conditions` (Open-Meteo when enabled, deterministic
        otherwise).
   - `synthesize_step` calls `synthesize_trip_brief` to assemble the
     `TripBriefResponse` with Decision Tension Board fields and a
     per-tool human-readable trace.
5. **Latency** is captured around the agent call and written to
   `response.meta.latency_ms`.
6. **Persistence** `persist_tool_calls` and `finish_agent_run` write
   tool inputs/outputs and the final response JSON. DB failures roll
   back without breaking the response.
7. **BackgroundTasks** schedules `deliver_discord_webhook`. The webhook
   has a timeout, a retry-with-backoff (`tenacity`), and is fully
   isolated — any failure becomes a `WebhookDelivery` row with
   `status="failed"`.
8. **Response** `TripBriefResponse` returns to the SPA, which renders
   the Hero, Trip DNA, Mission Timeline, Decision Tension Board,
   Travel Brief Memo, and Evidence Drawer.

## Why this shape

- **Single source of config** (`backend/app/config.py` via
  `pydantic-settings`) so no `os.getenv` is scattered through routes.
- **Lifespan singletons** for the LangGraph agent and the joblib model
  so they load once per process.
- **Pydantic at the boundary** — every tool validates input and shapes
  output as a Pydantic model, which is what the agent allowlist
  enforces.
- **Best-effort persistence + isolated webhook** — the user always
  receives a brief, even when Postgres or Discord is unreachable.
- **Local fallbacks** for RAG, ML, weather, and LLM routing — the demo
  is reproducible without external services.

## What is real vs fallback

| Layer | Real path | Local fallback |
|---|---|---|
| RAG retrieval | pgvector cosine search | deterministic in-memory hash index |
| Embeddings | provider plug-point in place | 384-dim `deterministic-hashing-v1` |
| ML classification | joblib `Pipeline` (LR winner) | rule-based heuristic |
| Live conditions | Open-Meteo HTTP call | hand-tuned deterministic per-destination |
| Two-model routing | provider-keyed clients (future) | deterministic extractor + synthesizer |
| Webhook | Discord HTTP POST | skipped when no URL is set |

The submission deliberately ships *both* paths so the project demos
without external dependencies and graduates to real services by setting
environment variables.
