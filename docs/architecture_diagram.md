# AtlasBrief — Architecture Diagram

A high-density rendering of the live system. Every box maps to a real
file in this repo; every arrow maps to a real call.

To present this visually, open
[`docs/architecture_diagram.html`](architecture_diagram.html) in a
browser — that's the styled, screenshot-ready version (warm parchment +
brass / verdigris / terracotta palette, matching the rest of the
product). The Mermaid graph below renders inline on GitHub for
reviewers who prefer to read the source.

---

```mermaid
flowchart TD
    classDef frontend fill:#d5dded,stroke:#2d3a52,color:#0e1116,stroke-width:1.5px
    classDef backend  fill:#f4dfb6,stroke:#c98a3b,color:#0e1116,stroke-width:1.5px
    classDef agent    fill:#ddd0ee,stroke:#6b4a8a,color:#0e1116,stroke-width:1.5px
    classDef rag      fill:#ddd0ee,stroke:#6b4a8a,color:#0e1116,stroke-width:1.5px
    classDef ml       fill:#f4dfb6,stroke:#c98a3b,color:#0e1116,stroke-width:1.5px
    classDef live     fill:#c2e6e1,stroke:#2f8b80,color:#0e1116,stroke-width:1.5px
    classDef llm      fill:#f4cdbf,stroke:#c25a3f,color:#0e1116,stroke-width:1.5px
    classDef db       fill:#c2e6e1,stroke:#2f8b80,color:#0e1116,stroke-width:1.5px
    classDef hook     fill:#f4cdbf,stroke:#c25a3f,color:#0e1116,stroke-width:1.5px
    classDef obs      fill:#1a1f29,stroke:#1a1f29,color:#f7f2e6,stroke-width:1.5px

    User([👤 User · browser])
    FE["React + Vite + TS<br/>Decision Tension Board · Evidence Drawer<br/><i>localhost:5173</i>"]
    User --> FE

    API["FastAPI backend<br/>POST /api/v1/trip-briefs<br/>auth · async SQLAlchemy · DI · lifespan<br/><i>localhost:8000</i>"]
    FE -->|"JSON + JWT (optional)"| API

    Agent["LangGraph agent<br/>plan ▸ tools ▸ synthesize<br/><b>explicit tool allowlist</b>"]
    API --> Agent

    Plan["Deterministic ranker<br/>data/destinations.csv<br/>(cheap step · no model hop)"]
    Agent --> Plan

    RAG["📚 retrieve_destination_knowledge<br/>900-char chunks · 150 overlap<br/>top-k cosine retrieval"]
    ML["🧠 classify_travel_style<br/>scikit-learn Pipeline<br/>(StandardScaler → LogReg)<br/>macro-F1 0.959"]
    Live["🌤 fetch_live_conditions<br/>async httpx · TTLCache 600s<br/>retry · timeout"]

    Plan --> RAG
    Plan --> ML
    Plan --> Live

    PG[("Postgres 16 + pgvector<br/>document_chunks · Vector(384)<br/>cosine ivfflat index")]
    Joblib[/"backend/app/ml/model.joblib<br/>loaded once at startup"/]
    OpenMeteo(("Open-Meteo API"))

    RAG -.->|embed query · top-k| PG
    ML  -.->|predict_proba| Joblib
    Live -.->|GET /forecast| OpenMeteo

    Synth["Synthesizer<br/>Dream Fit · Reality Pressure · Verdict · Counterfactual"]
    RAG  --> Synth
    ML   --> Synth
    Live --> Synth

    Strong["Strong-step LLM router<br/>Anthropic Haiku/Sonnet · OpenAI<br/>real tokens_in · tokens_out · cost_usd"]
    Synth --> Strong

    Tables[("users · agent_runs · tool_calls<br/>webhook_deliveries<br/>destination_documents · document_chunks")]
    Strong --> API
    API -->|"persist (best-effort)<br/>Alembic-versioned"| Tables

    LangSmith[["LangSmith trace<br/>(when LANGCHAIN_API_KEY set)"]]
    Agent -.->|automatic via env vars| LangSmith

    Hook["Discord webhook<br/>async · timeout · retry+backoff<br/><b>failure isolated</b>"]
    API -. background task .-> Hook
    Hook -.-> Tables

    Brief>"User receives: Decision Tension Board<br/>+ Travel Brief Memo + Evidence Drawer"]
    API ==> Brief
    Brief --> User

    class User,FE,Brief frontend
    class API backend
    class Agent,Plan agent
    class RAG rag
    class ML ml
    class Live live
    class Synth,Strong llm
    class PG,Tables,Joblib,OpenMeteo db
    class Hook hook
    class LangSmith obs
```

---

## What every layer does — file map

| # | Layer | File / location |
|---|---|---|
| 1 | Frontend (React + Vite) | [`frontend/src/App.tsx`](../frontend/src/App.tsx), [`frontend/src/components/DecisionTensionBoard.tsx`](../frontend/src/components/DecisionTensionBoard.tsx) |
| 2 | FastAPI route | [`backend/app/api/routes/trip_briefs.py`](../backend/app/api/routes/trip_briefs.py) |
| 3 | LangGraph agent | [`backend/app/agent/graph.py`](../backend/app/agent/graph.py), allowlist [`registry.py`](../backend/app/agent/registry.py) |
| 4a | Cheap step (deterministic ranker) | [`backend/app/llm/router.py`](../backend/app/llm/router.py) |
| 4b | RAG tool · pgvector | [`backend/app/tools/retrieve_destination_knowledge.py`](../backend/app/tools/retrieve_destination_knowledge.py), retriever [`backend/app/rag/retriever.py`](../backend/app/rag/retriever.py) |
| 4c | ML tool · joblib | [`backend/app/tools/classify_travel_style.py`](../backend/app/tools/classify_travel_style.py), trainer [`backend/app/ml/train_classifier.py`](../backend/app/ml/train_classifier.py) |
| 4d | Live-conditions tool | [`backend/app/tools/fetch_live_conditions.py`](../backend/app/tools/fetch_live_conditions.py), TTL cache [`backend/app/cache/ttl.py`](../backend/app/cache/ttl.py) |
| 5 | Synthesizer + strong step | [`backend/app/agent/synthesize.py`](../backend/app/agent/synthesize.py), providers [`backend/app/llm/providers.py`](../backend/app/llm/providers.py) |
| 6 | Persistence (Postgres + pgvector) | [`backend/app/db/`](../backend/app/db/), [`backend/app/models/`](../backend/app/models/), Alembic [`backend/alembic/versions/0001_initial.py`](../backend/alembic/versions/0001_initial.py) |
| 7 | Discord webhook | [`backend/app/webhooks/dispatcher.py`](../backend/app/webhooks/dispatcher.py) |
| 8 | LangSmith tracing | [`backend/app/tracing.py`](../backend/app/tracing.py) |

---

## 3-minute talk script (rehearsed against this diagram)

**0:00 – 0:25 · Frame.**
> "AtlasBrief takes a fuzzy travel question and returns a *defended*
> recommendation. The signature output is the **Decision Tension Board** —
> Dream Fit, Reality Pressure, Final Verdict, Counterfactual. One query
> in, one tradeoff named."

**0:25 – 0:55 · Frontend → backend.** *(point to layers 1 + 2)*
> "The user lands on a React + Vite single-page briefing room and submits
> one query. It hits a single FastAPI endpoint. Auth is bcrypt + JWT but
> optional — the demo path stays anonymous. Everything is async — no
> `requests.get`, no `time.sleep` in the request path. Pydantic validates
> at every boundary."

**0:55 – 1:50 · Agent + three tools.** *(point to layers 3, 4)*
> "The route hands off to a small LangGraph agent: plan, tools,
> synthesize. The planner is a deterministic ranker over our 131-row
> destinations CSV — no model hop for mechanical work. It picks the
> destination, the counterfactual, and the feature profile.
>
> Three tools fire, exactly the three the brief asks for, behind an
> explicit allowlist. **RAG** retrieves from 28 markdown briefs across
> 14 destinations, embeddings stored in Postgres + pgvector with a
> cosine ivfflat index. **ML classifier** is a scikit-learn pipeline,
> StandardScaler plus Logistic Regression, mean macro-F1 0.959 on
> stratified 5-fold CV — loaded once at startup via FastAPI lifespan.
> **Live conditions** is an async Open-Meteo lookup behind a TTL cache
> with stampede protection. If a tool fails, the failure is structured
> and the LLM can reason about it — the request never crashes."

**1:50 – 2:20 · Two-model routing + cost.** *(point to layer 5)*
> "Cheap step is deterministic. Strong step calls real Anthropic Haiku
> or Sonnet — or OpenAI — when a key is set; falls back to a
> deterministic verdict otherwise. We log real `tokens_in`,
> `tokens_out`, and `cost_usd` per request. Live-measured with Haiku:
> $0.001361 per query. LangSmith captures the full multi-tool trace
> when the key is in `.env`."

**2:20 – 2:50 · Persistence + webhook.** *(point to layers 6, 7)*
> "Six tables in Postgres, async SQLAlchemy 2.x, schema versioned with
> Alembic that enables pgvector before creating the chunk table. The
> `pgdata` named volume keeps embeddings and history across restarts.
> After the response is sent, a background task fires a Discord webhook
> with timeout, retry, and backoff. Webhook failure never breaks the
> user response — that's tested in `tests/test_webhook.py`."

**2:50 – 3:00 · Close.**
> "One Docker command — `docker compose up` — brings up the whole
> stack. CI runs ruff plus 58 pytest tests on every push. That's
> AtlasBrief."
