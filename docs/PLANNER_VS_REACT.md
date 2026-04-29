# Planner-then-Executor vs ReAct — what AtlasBrief actually does, and why

> Optional Week 4 extension. Written after the system was working end-to-end
> so the comparison is grounded in what the agent actually had to do, not in
> abstract preference.

## What we shipped

AtlasBrief is a **planner-then-executor** agent, not a ReAct loop. The graph
is in [backend/app/agent/graph.py](../backend/app/agent/graph.py):

```
plan_step  →  tools_step  →  synthesize_step  →  END
```

- **`plan_step`** runs once (cheap model, deterministic fallback today).
  It produces a small `TripPlan` that names a destination, country, RAG
  query, matched traits, and a feature profile for the classifier.
- **`tools_step`** calls all three allowlisted tools in a fixed order
  (`retrieve_destination_knowledge`, `classify_travel_style`,
  `fetch_live_conditions`). The plan answers every argument up front.
- **`synthesize_step`** runs once (strong model, deterministic fallback
  today). It receives the plan + the three tool outputs and emits the
  Decision Tension Board.

There is no observe-think-act loop. The model never decides "I have enough,
stop"; the graph decides for it.

## What ReAct would have looked like

A ReAct version would replace `tools_step` with a loop:

```
while not done:
    thought, action = llm.step(observation)
    if action == "FINAL":
        break
    observation = run_tool(action.name, action.args)
```

Each iteration the model picks one tool from the allowlist, looks at the
result, and either picks another tool or emits a final answer.

## Why planner-then-executor won here

Three reasons, in order of how strongly they bit:

### 1. The brief locks the tool set to **exactly three** tools.

Re-read item 3 of the brief: "exactly three tools." The interesting
question for AtlasBrief is **how the three results combine**, not which
ones to use. ReAct's strength is choosing tools dynamically. With only
three tools and a strong prior that all three are relevant for every
travel question, ReAct's main lever is gone — every run will end up
calling all three anyway, and we'd be paying extra LLM hops to rediscover
that fact.

### 2. The Decision Tension Board demands **synthesis across tools**, not picking the best one.

Re-read the unique-feature section of [CLAUDE.md](../CLAUDE.md): the
Final Verdict has to *name the tradeoff* between Dream Fit (RAG + ML)
and Reality Pressure (live signals). That's a join over all tools'
outputs, not a max over them. Planner-then-executor maps cleanly: one
synthesis call sees every output and reasons about the tension. ReAct
would need an extra summarize step at the end anyway to do the same
thing — so we'd pay for ReAct iterations *and* the synthesis call.

### 3. Cost, traceability, and tests.

- **Cost.** Planner = 2 LLM calls (cheap plan + strong synthesis). ReAct
  = at least 4 (plan, observe×3, final). With the Week 4 cost-budget
  pressure (one full query has to be cheap enough to defend in the
  README), the doubled hops were not worth it.
- **Traceability.** The brief asks for a multi-tool LangSmith trace.
  Planner-then-executor produces a trace where every node label maps to
  a meaningful step a reviewer can read. ReAct produces N
  thought→action→observation triples, half of which are noise.
- **Tests.** [tests/test_agent_e2e.py](../tests/test_agent_e2e.py) can
  assert "exactly 3 tool results, all allowlisted" because the graph
  guarantees the shape. The same assertion against a ReAct loop is much
  harder to keep stable.

## When ReAct **would** have been right

- If the tool set were larger (≥6) and most tools were irrelevant per
  query — e.g. a calendar tool, a flights tool, a visa tool, a vaccine
  tool, a currency tool, a packing tool. There the win is *not running*
  the irrelevant ones.
- If the user's query needed multi-hop reasoning — "find me three
  destinations under $X that match Y, and then narrow to one based on Z."
  That would justify an explicit observe-then-decide loop. Our compare
  mode handles "two destinations" with a parallel run, not a loop.
- If we cared about resilience to a model that *invents* tools the
  allowlist doesn't have. Our allowlist refuses unknown tools defensively
  ([backend/app/agent/registry.py](../backend/app/agent/registry.py)),
  but a ReAct loop with a re-asking guard would surface that error to the
  model so it can recover. Today we don't need that since the planner is
  deterministic and never invents tools.

## What I would change next time

If the system grew to 5+ tools, I would not switch to ReAct. I would
keep the planner-then-executor shape and let the planner pick a *subset*
of tools by name (still from the allowlist), then the executor fans out
in parallel. That keeps the synthesis step intact and gets the "don't
run irrelevant tools" win without paying for an LLM-driven loop. Two
LLM calls, N tool calls in parallel, one synthesis — that's the shape
that scales.
