// Thin fetch wrapper. We keep network code out of components so that
// later we can swap fetch for a streaming client without touching the UI.

import type { TripBriefResponse } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function postTripBrief(query: string): Promise<TripBriefResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/trip-briefs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Trip brief request failed (${res.status}): ${text}`);
  }

  return (await res.json()) as TripBriefResponse;
}

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return (await res.json()) as { status: string };
}
