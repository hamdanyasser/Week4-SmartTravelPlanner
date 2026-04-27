// Mirrors backend/app/schemas/trip_brief.py.
// Hand-written for Day 1 — once the backend stabilises we will generate
// these from the OpenAPI schema instead of maintaining them by hand.

export type TravelStyle =
  | "Adventure"
  | "Relaxation"
  | "Culture"
  | "Budget"
  | "Luxury"
  | "Family";

export interface DreamFitScore {
  score: number;
  matched_traits: string[];
  rationale: string;
}

export interface RealityPressureScore {
  score: number;
  weather_signal: string;
  flight_signal: string;
  rationale: string;
}

export interface DestinationCandidate {
  name: string;
  country: string;
  travel_style: TravelStyle;
  dream_fit: DreamFitScore;
  reality_pressure: RealityPressureScore;
}

export interface CounterfactualCard {
  obvious_pick: string;
  why_not_chosen: string;
}

export interface ToolTraceEntry {
  tool: string;
  summary: string;
}

export interface TripBriefMeta {
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  latency_ms: number;
  cheap_model: string;
  strong_model: string;
}

export interface TripBriefResponse {
  query: string;
  top_pick: DestinationCandidate;
  runners_up: DestinationCandidate[];
  final_verdict: string;
  counterfactual: CounterfactualCard;
  tools_used: ToolTraceEntry[];
  meta: TripBriefMeta;
}
