// AtlasBrief — single-page briefing room.
//
// This file deliberately reads top-to-bottom as the user's experience:
// hero → auth pill → prompt → trip DNA → mission timeline → tension board →
// memo → evidence. Every section is a small dedicated component.

import { useState } from "react";
import { AuthPanel } from "./components/AuthPanel";
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

  const showEmpty = !trip.brief && !trip.loading && !trip.error;
  const showShimmer = trip.loading && !trip.brief;

  return (
    <div className="app-shell">
      <Hero mode={trip.mode} />

      <AuthPanel auth={auth} />

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
          {trip.mode === "demo" && (
            <div className="demo-banner reveal">
              <span className="demo-banner__dot" aria-hidden />
              Backend unreachable · showing offline demo briefing
            </div>
          )}
          <DecisionTensionBoard
            topPick={trip.brief.top_pick}
            finalVerdict={trip.brief.final_verdict}
            counterfactual={trip.brief.counterfactual}
          />
          <TravelBriefMemo brief={trip.brief} />
          <EvidenceDrawer
            tools={trip.brief.tools_used}
            meta={trip.brief.meta}
            mode={trip.mode}
            startedAt={trip.startedAt}
            finishedAt={trip.finishedAt}
          />
        </>
      )}

      <footer className="footer">
        <span>AtlasBrief · AI travel briefing room</span>
        <span>Built for SE Factory · Week 4 deliverable</span>
      </footer>
    </div>
  );
}
