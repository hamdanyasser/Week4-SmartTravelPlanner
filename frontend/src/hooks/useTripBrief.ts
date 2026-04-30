// Lifecycle hook for the trip-brief request.
//
// Returns the brief, the loading state, the active timeline stage index,
// and a flag for whether we fell back to the offline demo because the API
// was unreachable.
//
// If `VITE_USE_STREAMING=true` (or the URL contains `?stream=1`), we drive
// the timeline from real backend SSE events instead of the fake-but-honest
// timer. Falls back gracefully to the JSON path on any stream error.

import { useCallback, useEffect, useRef, useState } from "react";
import { postTripBrief } from "../api/client";
import { offlineDemoBrief } from "../api/fallback";
import { streamTripBrief } from "../api/stream";
import type { TripBriefResponse } from "../api/types";

export type BriefMode = "live" | "demo" | "live-stream";

const STREAM_STAGE_TO_INDEX: Record<string, number> = {
  plan: 0,
  "tool:retrieve_destination_knowledge": 1,
  "tool:classify_travel_style": 2,
  "tool:fetch_live_conditions": 3,
  synthesize: 4,
};

const useStreaming = (() => {
  if (import.meta.env.VITE_USE_STREAMING === "true") return true;
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).has("stream");
})();

export interface BriefState {
  brief: TripBriefResponse | null;
  loading: boolean;
  error: string | null;
  mode: BriefMode | null;
  activeStage: number;
  totalStages: number;
  startedAt: number | null;
  finishedAt: number | null;
  reset: () => void;
  submit: (query: string, authHeader?: Record<string, string>) => Promise<void>;
}

const STAGE_INTERVAL_MS = 750;

export function useTripBrief(totalStages: number): BriefState {
  const [brief, setBrief] = useState<TripBriefResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<BriefMode | null>(null);
  const [activeStage, setActiveStage] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [finishedAt, setFinishedAt] = useState<number | null>(null);

  const stageTimer = useRef<number | null>(null);

  const clearTimer = () => {
    if (stageTimer.current !== null) {
      window.clearInterval(stageTimer.current);
      stageTimer.current = null;
    }
  };

  useEffect(() => () => clearTimer(), []);

  const reset = useCallback(() => {
    clearTimer();
    setBrief(null);
    setError(null);
    setMode(null);
    setActiveStage(0);
    setStartedAt(null);
    setFinishedAt(null);
    setLoading(false);
  }, []);

  const runStreaming = useCallback(
    async (query: string, authHeader: Record<string, string>) => {
      let received: TripBriefResponse | null = null;
      for await (const event of streamTripBrief(query, authHeader)) {
        if (event.type === "stage") {
          const idx = STREAM_STAGE_TO_INDEX[event.stage];
          if (idx === undefined) continue;
          if (event.status === "completed" || event.status === "error") {
            setActiveStage((s) => Math.max(s, idx + 1));
          } else {
            setActiveStage((s) => Math.max(s, idx));
          }
        } else if (event.type === "brief") {
          received = event.response;
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }
      if (!received) throw new Error("Stream ended without a brief.");
      return received;
    },
    [],
  );

  const submit = useCallback(
    async (query: string, authHeader: Record<string, string> = {}) => {
      clearTimer();
      setBrief(null);
      setError(null);
      setMode(null);
      setActiveStage(0);
      setLoading(true);
      setStartedAt(Date.now());
      setFinishedAt(null);

      // Fake-but-honest progress (used unless streaming is on): walk the
      // stages while the request is in flight. We stop at the second-to-last
      // stage and let the real result unlock the final two stages.
      if (!useStreaming) {
        const ceiling = Math.max(1, totalStages - 2);
        stageTimer.current = window.setInterval(() => {
          setActiveStage((s) => (s < ceiling ? s + 1 : s));
        }, STAGE_INTERVAL_MS);
      }

      try {
        const result = useStreaming
          ? await runStreaming(query, authHeader)
          : await postTripBrief(query, authHeader);
        clearTimer();
        setBrief(result);
        setMode(useStreaming ? "live-stream" : "live");
        setActiveStage(totalStages);
      } catch (err) {
        clearTimer();
        // Graceful demo fallback when the backend is unreachable.
        const message = err instanceof Error ? err.message : String(err);
        const offline =
          /failed to fetch|networkerror|load failed|503|not_a_function/i.test(
            message,
          );
        if (offline) {
          setBrief(offlineDemoBrief(query));
          setMode("demo");
          setActiveStage(totalStages);
        } else {
          setError(message);
        }
      } finally {
        setLoading(false);
        // `start` is performance.now() — a high-resolution monotonic stamp.
        // We display latency in the Evidence drawer as Math.round(perf.now() - start),
        // and `finishedAt` is a wall-clock stamp for "completed at" UI strings.
        setFinishedAt(Date.now());
      }
    },
    [totalStages, runStreaming],
  );

  return {
    brief,
    loading,
    error,
    mode,
    activeStage,
    totalStages,
    startedAt,
    finishedAt,
    reset,
    submit,
  };
}
