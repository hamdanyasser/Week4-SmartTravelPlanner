// AtlasBrief — single-page briefing room.
//
// Reads top-to-bottom as the user's experience:
//   atlas backdrop (fixed) → topbar (brand · status · auth) → hero →
//   intake console → trip DNA → mission timeline → tension board →
//   executive memo → footer · evidence drawer.
//
// The atmosphere layer (AtlasBackdrop) is fixed behind everything;
// cursor position is tracked here and pushed in as parallax props so
// it stays a single source of truth. Reduced-motion users skip it.

import { useEffect, useState } from "react";
import { AtlasBackdrop } from "./components/AtlasBackdrop";
import { AuthPanel } from "./components/AuthPanel";
import { Brand } from "./components/Brand";
import { CinematicPromptBox } from "./components/CinematicPromptBox";
import { DecisionTensionBoard } from "./components/DecisionTensionBoard";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { Hero } from "./components/Hero";
import { LoadingShimmer } from "./components/LoadingShimmer";
import { TIMELINE_STAGES, AgentTimeline } from "./components/AgentTimeline";
import { TravelBriefMemo } from "./components/TravelBriefMemo";
import { TripDNAPanel } from "./components/TripDNAPanel";
import { useAuth } from "./hooks/useAuth";
import { useTripBrief } from "./hooks/useTripBrief";

const GOLDEN_DEMO_QUERY =
  "I have two weeks off in July and around $1,500. I want somewhere warm, not too touristy, and I like hiking. Where should I go, when should I book, and what should I expect?";

export default function App() {
  const [query, setQuery] = useState(GOLDEN_DEMO_QUERY);
  const trip = useTripBrief(TIMELINE_STAGES.length);
  const auth = useAuth();
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  // Mouse parallax for the celestial atlas. Bypassed by reduced-motion users.
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }
    const onMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * -24;
      const y = (e.clientY / window.innerHeight - 0.5) * -16;
      setParallax({ x, y });
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  const showEmpty = !trip.brief && !trip.loading && !trip.error;
  const showShimmer = trip.loading && !trip.brief;
  const isThinking = trip.loading;

  const statusLabel =
    trip.mode === "demo"
      ? "Offline demo mode"
      : trip.mode === "live"
      ? "Live agent online"
      : trip.loading
      ? "Drafting briefing"
      : trip.error
      ? "Tool failure · recovering"
      : "Standing by";

  const statusClass =
    trip.mode === "demo"
      ? "status-pill demo"
      : trip.error
      ? "status-pill error"
      : !trip.brief && !trip.loading
      ? "status-pill idle"
      : "status-pill";

  return (
    <>
      <AtlasBackdrop parallax={parallax} thinking={isThinking} />

      <div className="app-shell">
        <header className="topbar">
          <Brand />
          <div className="topbar__right">
            <div className={statusClass}>
              <span className="dot" aria-hidden />
              <span>{statusLabel}</span>
            </div>
            <AuthPanel auth={auth} />
          </div>
        </header>

        <Hero />

        <CinematicPromptBox
          query={query}
          onChange={setQuery}
          onSubmit={() => trip.submit(query, auth.authHeader())}
          loading={trip.loading}
        />

        <TripDNAPanel
          query={query}
          travelStyle={trip.brief?.top_pick.travel_style ?? null}
        />

        {trip.error && <ErrorState message={trip.error} />}

        {trip.mode === "demo" && (
          <div className="thread demo reveal reveal--d2">
            <span className="thread__dot" aria-hidden />
            <span>Backend unreachable · showing offline demo briefing</span>
          </div>
        )}

        <AgentTimeline
          activeStage={trip.activeStage}
          loading={trip.loading}
          tools={trip.brief?.tools_used}
          startedAt={trip.startedAt}
          finishedAt={trip.finishedAt}
        />

        {showEmpty && <EmptyState />}
        {showShimmer && <LoadingShimmer />}

        {trip.brief && (
          <>
            <DecisionTensionBoard
              topPick={trip.brief.top_pick}
              finalVerdict={trip.brief.final_verdict}
              counterfactual={trip.brief.counterfactual}
            />
            <TravelBriefMemo brief={trip.brief} />
          </>
        )}

        <footer className="footer">
          <span>AtlasBrief · Private travel briefing room</span>
          <span>Built for SE Factory · Week 4 deliverable</span>
        </footer>
      </div>

      {trip.brief && (
        <EvidenceDrawer
          tools={trip.brief.tools_used}
          meta={trip.brief.meta}
          mode={trip.mode}
          startedAt={trip.startedAt}
          finishedAt={trip.finishedAt}
        />
      )}
    </>
  );
}
