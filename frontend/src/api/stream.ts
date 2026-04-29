// Server-Sent Events consumer for /api/v1/trip-briefs/stream.
//
// Why fetch + ReadableStream instead of EventSource:
//   - EventSource only supports GET; our endpoint is POST so we can pass a
//     JSON body and Authorization header.
//   - We control parsing, so non-text frames (none today) won't trip us up.
//
// The backend emits one frame per stage with `event:` + `data:` lines. We
// split the buffer on the SSE delimiter (\n\n) and yield each frame as a
// typed StreamEvent so callers don't have to reimplement parsing.

import type { TripBriefResponse } from "./types";

export type StreamEvent =
  | { type: "stage"; stage: string; status: "started" | "completed" | "error"; ok?: boolean; destination?: string }
  | { type: "brief"; response: TripBriefResponse }
  | { type: "done" }
  | { type: "error"; message: string; exc_class?: string };

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function* streamTripBrief(
  query: string,
  authHeader: Record<string, string> = {},
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent, void, void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/trip-briefs/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...authHeader,
    },
    body: JSON.stringify({ query }),
    signal,
  });

  if (!res.ok || !res.body) {
    const text = res.body ? await res.text() : "";
    throw new Error(
      `Trip brief stream failed (${res.status})${text ? `: ${text}` : ""}`,
    );
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Drain every complete frame currently in the buffer.
      let separator = buffer.indexOf("\n\n");
      while (separator >= 0) {
        const frame = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        const parsed = parseFrame(frame);
        if (parsed) yield parsed;
        separator = buffer.indexOf("\n\n");
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function parseFrame(frame: string): StreamEvent | null {
  // Each frame is "event: <name>\ndata: <json>\n" (no trailing blank since
  // the splitter already consumed the delimiter). We tolerate either order.
  const lines = frame.split(/\r?\n/);
  let dataLine = "";
  for (const line of lines) {
    if (line.startsWith("data:")) dataLine = line.slice(5).trim();
  }
  if (!dataLine) return null;
  try {
    return JSON.parse(dataLine) as StreamEvent;
  } catch {
    return null;
  }
}
