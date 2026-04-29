# CLAUDE.md — AtlasBrief — AI Travel Briefing Room

This file is the canonical project briefing. **Future Claude must read this
first**, before touching any code. It captures the product vision, the brief,
the engineering rules, and the operating discipline.

If anything in conversation conflicts with this file, ask the user instead of
guessing.

---

## 1. Product vision

**AtlasBrief — AI Travel Briefing Room** is the Week 4 Smart Travel
Planner project (SE Factory AIE Bootcamp). The product is meant to feel
like a calm executive briefing, not a chat window — the user shows up
with a fuzzy travel idea and walks out with a defended recommendation.

---

## 2. Unique feature — the Decision Tension Board

Every recommendation surfaces four pieces, in this order:

1. **Dream Fit** — how well a destination matches the user's vibe.
   Computed from the **ML classifier** + **RAG** retrieval.
2. **Reality Pressure** — what live conditions (weather, flights, FX) say
   about going *right now*. Score is inverted: 100 = no pressure, 0 = high.
3. **Final Verdict** — one paragraph that **names the tradeoff** between
   Dream Fit and Reality Pressure. The agent must reason across tools, not
   concatenate them.
4. **Why Not the Obvious Pick?** — counterfactual card naming the
   destination most users would have guessed and why we did not pick it.

The schema for this board lives in `backend/app/schemas/trip_brief.py`. The
React UI lives in `frontend/src/App.tsx`. Do not redesign either without
explicit instruction.

---

## 3. Golden demo query

> "I have two weeks off in July and around $1,500. I want somewhere warm,
> not too touristy, and I like hiking. Where should I go, when should I
> book, and what should I expect?"

Every architectural choice is judged against whether it makes this query
work end-to-end, cleanly. Day 1's stub returns a Madeira-vs-Costa-Rica
payload as the hand-picked golden answer the real agent should be able to
recover.

---

## 4. Required Week 4 deliverables

The full mapping (with statuses and code-review notes) lives in
`REQUIREMENTS_CHECKLIST.md`. The short version, which is the spec to defend
on Saturday:

### ML classifier
- Labels (exactly): **Adventure, Relaxation, Culture, Budget, Luxury, Family**.
- **100–200** hand-labeled destinations.
- **`sklearn.Pipeline`** with preprocessing inside (no leakage).
- **3 classifiers** compared with **k-fold cross-validation**.
- Report **accuracy + macro-F1** mean and std.
- Tune **at least one** model (e.g. `GridSearchCV`).
- Per-class metrics (no hiding rare classes behind averages).
- Append every experiment to **`results.csv`**.
- Save the winner with **joblib** as `model.joblib`.
- Pinned deps + fixed `random_state`.

### RAG
- **10–15 destinations**, **20–30 documents** (Wikivoyage / blogs / tourism boards).
- Embeddings stored in **Postgres + pgvector** (same DB as everything else).
- Justify chunk size + overlap + retrieval strategy in the README.
- Sanity-tested with hand-written queries before plugging into the agent.

### Agent — exactly 3 tools
1. `retrieve_destination_knowledge`
2. `classify_travel_style`
3. `fetch_live_conditions`

- Every tool input **and** output validated by Pydantic.
- **Explicit tool allowlist** — anything else is refused even if the model invents it.
- LangGraph or LangChain wiring.
- Genuine cross-tool synthesis (not concatenation).

### Two-model routing
- **Cheap model** (Haiku-class / gpt-4o-mini) for mechanical work
  (argument extraction, RAG query rewriting).
- **Strong model** (Sonnet/Opus class) for the final synthesis.
- **Token + cost logging** per step.

### Persistence
- Postgres + pgvector + SQLAlchemy 2.x **async**.
- Tables at minimum: `users`, `agent_runs`, `tool_calls`, `embeddings`.
- Alembic migrations.

### Auth
- Sign-up + login. Password hashing (bcrypt). JWT sessions.
- `current_user` FastAPI dependency on every protected route.

### Frontend
- React + Vite + TypeScript. Sign-in flow. Chat-style trip query.
- Tool-trace visibility — show what the agent did. Streaming optional.

### Webhook delivery
- Discord / Slack / email / Sheets — your choice.
- Timeout + retry-with-backoff + structured failure logging.
- **Webhook failure must NOT break the user-facing response.**

### Docker
- One-command stack via `docker compose up`.
- Backend, frontend, Postgres+pgvector containers.
- **Named volume** so embeddings survive restarts.

### Documentation
- `README.md` with: architecture diagram, dataset labeling rules, chunking
  rationale, model comparison table, per-query cost breakdown, LangSmith
  trace screenshot, optional extensions list.
- **3-minute demo video** of one end-to-end run.
- `CODE_REVIEW_NOTES.md` updated after every major change.

---

## 5. Engineering rules

These are non-negotiable; the brief calls them out explicitly.

- **Small files, clear names.** No 600-line `main.py`. Split by concern:
  `routes/`, `schemas/`, `agent/`, `ml/`, `rag/`, `db/`, `auth/`,
  `webhooks/`.
- **No secrets committed.** `.env` is local-only. `.env.example` is the
  tracked template.
- **No scattered `os.getenv`.** All config enters through
  `backend/app/config.py` (pydantic-settings). Anywhere else uses
  `get_settings()`.
- **Async where appropriate.** FastAPI routes, tool functions, DB calls
  (SQLAlchemy 2.x async session), HTTP via `httpx.AsyncClient`, async LLM
  SDK methods. No `time.sleep` or `requests.get` in a request path.
- **FastAPI `Depends` for dependencies.** LLM client, DB session, embedding
  model, current user — all injected, not instantiated in handlers.
- **Lifespan for singleton resources.** DB engine, ML model (joblib),
  embedding model, LLM client — created once on startup, disposed on
  shutdown, exposed via `Depends()`.
- **Structured errors for external failures.** Every external call
  (LLM, tool API, webhook) has a timeout + retry-with-backoff + structured
  log. Tool failures inside the agent loop return as structured errors so
  the LLM can reason about them.
- **Webhook failure must not break the user response.** Fire-and-log; the
  user sees their answer regardless.
- **Update `CODE_REVIEW_NOTES.md` after every major change.** Newest entry
  on top, plain language, explain *why*.
- **Commit after every stable milestone.** Conventional-commit style:
  `chore:`, `docs:`, `feat:`, `fix:`.
- **Beginner-explainable code.** Prefer clarity over cleverness.

---

## 6. Current status

- Backend app exists with small `main.py`, health route, auth routes, and an
  agent-backed `POST /api/v1/trip-briefs` route.
- The `TripBriefResponse` schema remains the locked frontend contract for the
  Decision Tension Board.
- Frontend shell exists and was not redesigned for the backend completion work.
- Docker Compose config validates, but live containers cannot start on this
  machine while Docker Desktop's `dockerDesktopLinuxEngine` pipe is missing.
- `backend/.env` is **not** tracked (verified). `backend/.env.example` is the
  tracked template.

**ML classifier shipped:**
- `data/destinations.csv` - 131 hand-labeled rows, 9 features, 6 labels.
- `backend/app/ml/train_classifier.py` - Pipeline, 3 baselines, k-fold CV,
  GridSearchCV on RF, per-class report, joblib save.
- `backend/app/ml/results.csv` - every experiment logged.
- `backend/app/ml/model.joblib` - current winner: Logistic Regression at mean
  macro-F1 0.959.
- FastAPI lifespan loads the joblib model once and the ML tool falls back to
  deterministic rules if loading fails.

**RAG foundation shipped:**
- `data/knowledge/` - 28 markdown destination documents across 14 destinations.
- `backend/app/rag/chunking.py` - markdown frontmatter parsing and
  900-character chunks with 150-character overlap.
- `backend/app/rag/embeddings.py` - deterministic local 384-dimensional
  embedding fallback plus a future real-provider interface.
- `backend/app/rag/ingest_documents.py` - local fallback ingest verification
  and Postgres/pgvector ingest path.
- `backend/app/rag/retriever.py` - top-k retrieval with DB-first/local-fallback
  behavior and three manual retrieval probes.
- `backend/app/tools/retrieve_destination_knowledge.py` - allowlisted tool
  wrapper around RAG retrieval.
- Live Postgres/pgvector ingest is still environment-blocked here because
  Docker Desktop is not reachable. `backend/app/rag/smoke_test.py` verifies the
  deterministic fallback path.

**Backend agent/auth/persistence/webhook shipped:**
- Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, bcrypt,
  JWT, `get_current_user`, and `get_optional_current_user`.
- Persistence models: `users`, `agent_runs`, `tool_calls`,
  `webhook_deliveries`, plus existing RAG document/chunk models.
- Agent: small LangGraph flow in `backend/app/agent/graph.py`.
- Exactly three tools: `retrieve_destination_knowledge`,
  `classify_travel_style`, `fetch_live_conditions`.
- Tool allowlist: `backend/app/agent/registry.py`.
- Two-model routing fallback: `backend/app/llm/router.py`, with token/cost
  metadata in `TripBriefResponse.meta`.
- Webhook: Discord dispatcher with async timeout, retry/backoff, and failure
  isolation.
- Smoke verification: `backend/app/smoke_test.py` covers auth hashing/JWT,
  tool allowlist, agent path, local RAG fallback, ML tool path, and webhook
  failure isolation.

**What is still missing**:
- Alembic migrations.
- Formal pytest suite, linter, pre-commit, and CI.
- Real provider-backed LLM routing and real provider cost accounting.
- LangSmith tracing screenshot.
- Frontend auth flow/tool-trace enhancements.
- Demo video.

The full status table lives in `REQUIREMENTS_CHECKLIST.md`.

---

## 7. Workflow for future Claude tasks

When given a new task, follow this order — every time:

1. **Read `CLAUDE.md`** (this file). It has the rules and the current state.
2. **Read `REQUIREMENTS_CHECKLIST.md`** to see what's TODO / IN_PROGRESS / DONE.
3. **Read `CODE_REVIEW_NOTES.md`** (top entries) to see the most recent decisions.
4. **Make only the requested changes.** Do not redesign, refactor neighbors, or
   pre-build features for future days. If the user says "Day N only", respect
   it.
5. **Run relevant checks** when possible:
   - `git status`
   - `docker compose config` (compose syntax check)
   - frontend build (`npm run build`) when frontend changed
   - backend import / start when backend changed
   - training script when ML changed
6. **Fix only errors caused by the change.** Don't sweep the codebase.
7. **Update `CODE_REVIEW_NOTES.md`** (newest entry on top) explaining what
   changed and why, in beginner-friendly language.
8. **Update `REQUIREMENTS_CHECKLIST.md`** if any status moved (TODO →
   IN_PROGRESS → DONE).
9. **Commit** with a conventional-commit message.
10. **Report** back to the user with: a short summary, commands run, what
    passed, what failed, and the commit hash.

When in doubt, ask.

---

## Quick links

- [REQUIREMENTS_CHECKLIST.md](REQUIREMENTS_CHECKLIST.md) — full status table
- [CODE_REVIEW_NOTES.md](CODE_REVIEW_NOTES.md) — change log (newest on top)
- [docs/DAY1_CODE_WALKTHROUGH.md](docs/DAY1_CODE_WALKTHROUGH.md) — line-level Day 1 explainer
- [README.md](README.md) — public-facing project README
