# Live verification runbook

This is the one-page sequence to take AtlasBrief from "all code green" to
"a reviewer just watched a real Decision Tension Board land via the
docker stack with real provider tokens and a LangSmith trace."

Run it from the repo root in Git Bash (or any POSIX shell). PowerShell
equivalents are noted only where the syntax differs.

## 0. Prereqs (one-time)

- Docker Desktop is responsive (`docker info` returns within 10s).
- `backend/.env` has at least `JWT_SECRET_KEY` and the Postgres creds
  (`backend/.env.example` lists every field with comments).
- `docker-compose.override.yml` exists if **and only if** your dev
  machine has the standard ports already taken. It is gitignored so it
  will not affect a clean-machine reviewer.

## 1. Bring up the stack

```bash
docker compose up -d --build
docker compose ps               # all three should be `running` / `healthy`
```

Standard ports (clean machine): db `5432`, backend `8000`, frontend `5173`.
This-dev-machine ports (override file): db `5434`, backend `8001`, frontend `5174`.

## 2. Run the migrations

```bash
# pick the right host port for your machine:
export DATABASE_URL='postgresql+asyncpg://trippilot:change-me-local-only@localhost:5432/trippilot'
backend/.venv/Scripts/alembic.exe upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema`.

## 3. Ingest RAG documents into pgvector

```bash
backend/.venv/Scripts/python.exe -m app.rag.ingest_documents --db --reset
```

Expected JSON: `documents=28, destinations=14, chunks≈55, used_database=true`.

## 4. End-to-end smoke

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/v1/trip-briefs \
  -H 'Content-Type: application/json' \
  -d '{"query":"Two weeks in July, $1500, warm hiking, not too touristy."}' \
  | tee docs/sample_brief.json | head -40
```

Expected: a `TripBriefResponse` with `top_pick.name = "Madeira"` and
`tools_used` listing all three allowlisted tools.

## 5. Flip on real provider routing

Paste **either** key into `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...      # preferred (cheap+strong on one provider)
# or
OPENAI_API_KEY=sk-...
```

Then restart the backend container:

```bash
docker compose restart backend
```

The next `POST /trip-briefs` will:
- call the real strong model for the synthesis step
- record real `meta.tokens_in / tokens_out / cost_usd`
- log `llm.strong.ok` with provider + model + cost in the JSON logs

## 6. Flip on LangSmith tracing

Paste:

```
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=atlasbrief
```

Restart backend (`docker compose restart backend`). The startup log
will print `langsmith.enabled` and the next agent run will appear at
https://smith.langchain.com under project `atlasbrief`. Screenshot a
multi-tool trace and save as `docs/trace.png`.

## 7. Capture cost numbers for the README

After step 5 has fired at least once, the most recent
`agent_runs.cost_usd` row holds the real per-query cost. Pull it:

```bash
docker compose exec db psql -U trippilot -d trippilot -c \
  "SELECT id, tokens_in, tokens_out, cost_usd FROM agent_runs ORDER BY id DESC LIMIT 5"
```

Paste the row into the README's Per-Query Cost section.

## 8. Demo video

Record a 3-minute end-to-end run from the React UI through to the
Discord webhook. Save as `docs/demo.mp4` (or upload + link from the
README).
