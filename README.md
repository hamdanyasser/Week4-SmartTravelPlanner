# TripPilot Black

A Smart Travel Planner with a premium "AI travel briefing room" feel.

The unique product layer is the **Decision Tension Board**:

- **Dream Fit** — how well a destination matches the user's vibe (ML + RAG).
- **Reality Pressure** — what live conditions (weather, flights) say about going *right now*.
- **Final Verdict** — a synthesis that names the tradeoff instead of hiding it.
- **Why Not the Obvious Pick?** — a counterfactual card explaining the road not taken.

This is the SE Factory AIE Bootcamp Week 4 project. The product framing is mine;
the engineering requirements come from the brief and are tracked in
[`REQUIREMENTS_CHECKLIST.md`](REQUIREMENTS_CHECKLIST.md).

## Golden demo query

> "I have two weeks off in July and around $1,500. I want somewhere warm,
> not too touristy, and I like hiking. Where should I go, when should I book,
> and what should I expect?"

Every architectural choice is judged against whether it makes this query
work end-to-end, cleanly.

## Repository layout

```
.
├── backend/         FastAPI + agent + ML + RAG + DB
├── frontend/        Vite + React + TypeScript
├── docker-compose.yml
├── REQUIREMENTS_CHECKLIST.md
└── CODE_REVIEW_NOTES.md
```

Backend modules are split by concern (`api/`, `agent/`, `ml/`, `rag/`, `db/`,
`auth/`, `webhooks/`) — there is no giant `main.py`.

## Running the Day 1 skeleton

```bash
docker compose up --build
```

- Backend: <http://localhost:8000>
- Backend health: <http://localhost:8000/health>
- Stub trip brief: `POST http://localhost:8000/api/v1/trip-briefs`
- Frontend: <http://localhost:5173>

Day 1 is a **skeleton**. The agent, ML model, RAG, auth, and webhook
are stubbed — see `REQUIREMENTS_CHECKLIST.md` for what's still TODO.

## Code review notes

Every major change has a plain-language entry in
[`CODE_REVIEW_NOTES.md`](CODE_REVIEW_NOTES.md). Read that file first if
you want to understand *why* something is shaped the way it is.
