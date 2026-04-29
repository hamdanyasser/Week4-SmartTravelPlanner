# AtlasBrief — Demo Story

A 3-minute walkthrough script for the Saturday demo. The point is to make
AtlasBrief feel like a **briefing room**, not a chatbot.

---

## 0:00 — Opening frame

> "AtlasBrief is an AI travel briefing room. The user shows up with a fuzzy
> travel idea and walks out with a defended recommendation."

Open the app at <http://localhost:5173>. Land on the hero:

- The title — *"From a vague travel wish to a defended brief."* — sets the
  tone in editorial serif type.
- The status pill in the top-right says **Live agent online** (or
  **Offline demo mode** if the backend is unreachable).
- The four "wall metrics" under the hero make it feel like a control room
  rather than a form.

---

## 0:30 — The intake console

> "The user enters one fuzzy travel question — no checkboxes, no dropdowns."

Highlight the **Cinematic Prompt Box**:

- Glass panel with an `INTAKE // TRIP BRIEF CONSOLE` strip.
- Pre-filled with the **golden demo query**:
  *"I have two weeks off in July and around $1,500. I want somewhere warm,
  not too touristy, and I like hiking…"*
- Four scenario chips for other plausible questions (October food trip,
  family in March, solo trekking).

Click **Generate briefing**.

---

## 0:45 — Trip DNA — "we read your question"

While the request is in flight, the **Trip DNA** panel above shows the
parsed slots:

| Budget | Month | Duration | Climate | Activities | Constraints |
|---|---|---|---|---|---|
| $1,500 | July | 2 weeks | Warm | Hiking | Less touristy |

Talk track:

> "Before the agent runs, AtlasBrief surfaces what it actually understood
> from the question — not as a debug log, but as a transparency surface
> the user can read."

Once the response lands, the **Predicted travel style** section lights up
with the ML prediction (e.g. "Adventure").

---

## 1:00 — Mission timeline — show the work

The **Agent Mission Timeline** animates through seven stages:

1. Understanding the request *(cheap model, intent extraction)*
2. Retrieving destination knowledge *(RAG, pgvector)*
3. Classifying travel style *(ML pipeline)*
4. Checking live conditions *(weather + flights)*
5. Resolving Dream vs Reality tension *(strong model, synthesis)*
6. Drafting the executive brief *(strong model, structured output)*
7. Delivering the webhook copy *(async, isolated failure)*

> "Every stage maps to actual backend work — three tools, two-model
> routing, webhook delivery. When the response lands, completed stages
> tick green, and the tool-trace summary from the backend replaces the
> generic stage label."

---

## 1:30 — The Decision Tension Board (the moment)

This is the signature shot. Pause here.

- **Top:** the destination name, country, and travel-style chip.
- **Two scorecards side-by-side:**
  - **Dream Fit** — brass accent, ML + RAG sourced.
    Shows the score, a 0–100 progress bar, the matched traits, and the
    rationale.
  - **Reality Pressure** — verdigris accent, live-conditions sourced.
    Shows the score, the same bar shape, and the weather + flight signals.
- **Below them, the Final Verdict** — large editorial serif type with a
  tri-color top rule (brass → terracotta → verdigris) that visually echoes
  the two cards above and the counterfactual below. The verdict *names
  the tradeoff*.
- **Below the verdict, the counterfactual** — *"Why not Costa Rica?"*

> "This is the part of AtlasBrief I think no other team will have. It's not
> a card grid — it's a defended recommendation."

---

## 2:00 — Travel brief memo

Scroll to the **Executive Trip Memo** — a parchment-feel summary with:

- Recommendation header (destination, country, style stamp, date stamp).
- *Why it fits* / *What to expect* / *Risks & tradeoffs* / *Booking advice*.
- Backup option — the runner-up destination with its own scores.
- Budget fit paragraph that explicitly references the parsed budget.

> "If a paying customer wanted to forward this to their travel agent, this
> is the memo they'd send."

---

## 2:30 — Evidence drawer (technical credibility)

Scroll to the **Evidence drawer** — collapsed by default, click to open.

Left column — **Tool trace**:
- `retrieve_destination_knowledge` — returned RAG snippets.
- `classify_travel_style` — predicted label.
- `fetch_live_conditions` — weather + flight signals.

Right column — **Run accounting**:
- Mode (Live / Offline demo).
- Cheap model + Strong model.
- Tokens in / out, cost USD, latency ms.
- Webhook state (Best-effort, isolated).

> "For code review, we surface the cost per query, the model split, and
> the webhook state right next to the user-facing brief."

---

## 3:00 — Closing frame

> "AtlasBrief is one URL. One question goes in, a briefing room comes back —
> defended by an ML classifier, RAG over a hand-curated corpus, and live
> conditions, with the tradeoff named and the obvious pick refuted."

End on the hero scrolled back to the top.

---

## Failure modes to demo (optional)

- **Offline demo:** stop the backend → retry → the page shows the
  `Offline demo mode` pill in the hero, the demo banner above the Tension
  Board, and the Evidence drawer marks `Mode: Offline demo`. The product
  never breaks.
- **Webhook off:** clear `DISCORD_WEBHOOK_URL` → the brief still renders;
  the Evidence drawer reflects the delivery state.
