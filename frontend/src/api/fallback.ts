// Offline demo fallback for the trip-brief endpoint.
//
// We only use this if the real backend can't be reached. It's flagged
// as `meta.cheap_model = "demo"` so the UI can clearly label it.

import type { TripBriefResponse } from "./types";

export function offlineDemoBrief(query: string): TripBriefResponse {
  return {
    query,
    top_pick: {
      name: "Madeira",
      country: "Portugal",
      travel_style: "Adventure",
      dream_fit: {
        score: 86,
        matched_traits: ["warm", "hiking", "less touristy"],
        rationale:
          "Volcanic island with the levada hiking network. July is dry and 22–26°C, and crowds skew toward the south coast — north and interior trails stay quiet.",
      },
      reality_pressure: {
        score: 72,
        weather_signal: "Stable, dry, ~24°C — no heatwave warnings.",
        flight_signal:
          "Round-trip lands inside the $1,500 budget if booked 4–6 weeks ahead.",
        rationale:
          "Conditions are friendly; the only real pressure is booking timing.",
      },
    },
    runners_up: [
      {
        name: "Slovenia",
        country: "Slovenia",
        travel_style: "Adventure",
        dream_fit: {
          score: 78,
          matched_traits: ["hiking", "less touristy", "mild summer"],
          rationale:
            "Triglav and Bohink give Alpine hiking without Dolomites prices; Ljubljana adds a soft cultural anchor.",
        },
        reality_pressure: {
          score: 68,
          weather_signal: "Warm valleys, cool ridgelines — typical July.",
          flight_signal: "Budget-friendly inbound through Venice or Vienna.",
          rationale: "Reality is forgiving but cross-border legs add friction.",
        },
      },
    ],
    final_verdict:
      "Madeira clears the dream (warm, hiking, off the obvious tourist trail) and survives the reality check (predictable weather, fares within budget). Costa Rica wins on dream but breaks the budget once July flights are factored in.",
    counterfactual: {
      obvious_pick: "Costa Rica",
      why_not_chosen:
        "Hits the warm-and-hiking dream hard, but round-trip flights from Europe in July alone consume most of the $1,500, leaving no budget for two weeks on the ground.",
    },
    tools_used: [
      {
        tool: "retrieve_destination_knowledge",
        summary:
          "Pulled 3 Madeira chunks: levada network, July climate, north-coast quiet zones.",
      },
      {
        tool: "classify_travel_style",
        summary: "Predicted Adventure (warm + hiking + low touristy preference).",
      },
      {
        tool: "fetch_live_conditions",
        summary:
          "July weather: stable, dry, 22–26°C. Flight pressure: medium if booked late.",
      },
    ],
    meta: {
      tokens_in: 0,
      tokens_out: 0,
      cost_usd: 0,
      latency_ms: 0,
      cheap_model: "demo",
      strong_model: "demo",
    },
  };
}
