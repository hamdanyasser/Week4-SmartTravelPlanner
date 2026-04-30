# Manual Proof Runbook

This file lists every brief deliverable that genuinely needs credentials,
external services, or human recording — i.e. things a code-only session
cannot finish — and gives you the **exact** sequence of commands to capture
each artifact. Each step is small, ordered, and self-contained.

When a step is finished, the corresponding `REQUIREMENTS_CHECKLIST.md` row
flips from `PROOF_PENDING` to `DONE`.

---

## Prerequisites (do once)

```bash
# 1. Local environment file. Edit only the keys you have.
cp backend/.env.example backend/.env

# 2. Backend venv with dev deps.
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt -r requirements-dev.txt

# 3. Frontend deps.
cd ../frontend
npm install
```

---

## 1. Capture `docs/trace.png` — LangSmith multi-tool trace

**What it proves:** Brief item 3 (agent tracing) and 12.6 (README screenshot).

```bash
# 1. Get a free LangSmith API key from smith.langchain.com.
#    Paste it into backend/.env:
LANGCHAIN_API_KEY=ls__your_real_key_here
LANGCHAIN_PROJECT=atlasbrief

# 2. Start the backend (deterministic synthesis is fine; we just need a run).
cd backend
./.venv/Scripts/python -m uvicorn app.main:app --port 8000

# 3. In a second terminal, fire the golden query against the live API.
curl -s -X POST http://localhost:8000/api/v1/trip-briefs \
  -H "Content-Type: application/json" \
  -d '{"query":"Two weeks in July, $1,500, warm, hiking, not too touristy"}' \
  | python -m json.tool

# 4. Open https://smith.langchain.com — the run will appear under the
#    `atlasbrief` project. Open it, expand the tool calls, screenshot the
#    full trace tree.

# 5. Save the screenshot as docs/trace.png. Commit it.
```

Only this final PNG is missing — the wiring (`backend/app/tracing.py`) is
already shipped and is exercised by `tests/test_tracing.py`.

---

## 2. Real provider cost in `meta.cost_usd`

**What it proves:** Brief item 4 (two-model routing) and 12.5 (cost
breakdown numbers in the README).

```bash
# 1. Paste an Anthropic key (preferred) or OpenAI key into backend/.env:
ANTHROPIC_API_KEY=sk-ant-your-real-key
# or:
OPENAI_API_KEY=sk-your-real-key

# (Optional) Force a provider explicitly:
STRONG_MODEL_PROVIDER=anthropic

# 2. Restart the backend so Settings re-reads .env.
cd backend
./.venv/Scripts/python -m uvicorn app.main:app --port 8000

# 3. Run the golden query and pick out meta.cost_usd:
curl -s -X POST http://localhost:8000/api/v1/trip-briefs \
  -H "Content-Type: application/json" \
  -d '{"query":"Two weeks in July, $1,500, warm, hiking, not too touristy"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print('cost_usd =', d['meta']['cost_usd'])"

# Expected output (approximate, depends on tokens used):
#   cost_usd = 0.0026
```

If the table in `README.md` § Per-query cost breakdown shows a stale or
estimated number, replace it with the value you observed.

---

## 3. Record `docs/demo.mp4` — 3-minute end-to-end demo

**What it proves:** Brief deliverable item "3-minute demo video".

Suggested 3-minute beat sheet (script lives in
[`docs/demo_story.md`](demo_story.md)):

| Time   | Beat                                                                  |
|--------|-----------------------------------------------------------------------|
| 0:00 – 0:20 | Open `http://localhost:5173`. The hero, status pill, and prompt console are visible. Read the eyebrow tag aloud. |
| 0:20 – 0:35 | Type / paste the golden query: *"I have two weeks off in July and around $1,500. I want somewhere warm, not too touristy, and I like hiking."* |
| 0:35 – 0:55 | Submit (Cmd/Ctrl+Enter). Show the Trip DNA panel filling in and the Mission Timeline animating through the seven stages. |
| 0:55 – 1:35 | The Decision Tension Board appears — point out Dream Fit (84) on brass, Reality Pressure on verdigris, the Final Verdict, and the counterfactual (Costa Rica / Monteverde). |
| 1:35 – 2:00 | Scroll to the Travel Brief Memo — show "Why it fits", "Risks", "Booking advice". |
| 2:00 – 2:30 | Open the Evidence Drawer — read the three tool summaries, point out the real `cost_usd` and `latency_ms`. |
| 2:30 – 2:50 | Cut to a Discord channel showing the webhook that fired. (Skip if no webhook is configured.) |
| 2:50 – 3:00 | Cut to the LangSmith run page showing the trace. Save. |

```bash
# Recording tools that work fine: macOS built-in screen recorder, OBS,
# Loom (export to mp4), Windows Game Bar (Win+G).
# Save the file as docs/demo.mp4 in the repo, or paste a public link
# into README.md § Demo / screenshots.
```

---

## 4. Live Postgres + pgvector ingest

**What it proves:** Brief items 2.2, 5.5, 9.x — RAG embeddings are actually
in pgvector, the pgvector chunk table is non-empty after ingest, and
`docker compose up` works on a fresh clone.

```bash
# 1. Bring up the full stack.
docker compose up -d --build

# 2. Apply the initial migration (creates all six tables + pgvector).
docker compose exec backend python -m alembic upgrade head

# 3. Ingest the bundled 28-document corpus into pgvector.
docker compose exec backend python -m app.rag.ingest_documents --db --reset

# 4. Verify with a real retrieval call.
curl -s -X POST http://localhost:8000/api/v1/trip-briefs \
  -H "Content-Type: application/json" \
  -d '{"query":"warm hiking less touristy island"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d['tools_used'][0]['summary'])"

# Expected: "<N> chunks via pgvector; top: <Destination>; ..."
```

If you see `via local fallback`, the DB write didn't land; double-check
`DATABASE_URL` and the alembic step.

---

## 5. Discord webhook end-to-end

**What it proves:** Brief item 8 — webhook delivery to a real channel.

```bash
# 1. In Discord: Server Settings → Integrations → Webhooks → New webhook.
#    Copy the URL; paste into backend/.env:
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# 2. Restart the backend. Run any trip brief.
# 3. The Decision Tension Board will appear in the chosen Discord channel
#    within a few seconds. Screenshot the message; commit as
#    docs/webhook.png if you want to keep the proof.
```

Webhook failure is intentionally isolated from the user response — see
`backend/app/webhooks/dispatcher.py` and the smoke test
`backend/app/smoke_test.py` for the failure-injection coverage.

---

## 6. Production JWT rotation

The shipped `JWT_SECRET_KEY` default is intentionally a labelled
development placeholder so the demo runs out of the box. Before any
non-local deploy:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Paste the output as JWT_SECRET_KEY in your environment.
```
