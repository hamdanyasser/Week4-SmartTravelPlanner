// Lifecycle hook for the trip-brief request.
//
// Returns the brief, the loading state, the active timeline stage index,
// and a flag for whether we fell back to the offline demo because the API
// was unreachable.

import { useCallback, useEffect, useRef, useState } from "react";
import { postTripBrief } from "../api/client";
import { offlineDemoBrief } from "../api/fallback";
import type { TripBriefResponse } from "../api/types";

export type BriefMode = "live" | "demo";

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

      // Fake-but-honest progress: walk the stages while the request is in
      // flight. We stop at the second-to-last stage and let the real result
      // unlock the final two stages.
      const ceiling = Math.max(1, totalStages - 2);
      stageTimer.current = window.setInterval(() => {
        setActiveStage((s) => (s < ceiling ? s + 1 : s));
      }, STAGE_INTERVAL_MS);

      try {
        const result = await postTripBrief(query, authHeader);
        clearTimer();
        setBrief(result);
        setMode("live");
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
        setFinishedAt(Date.now());
      }
    },
    [totalStages],
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
