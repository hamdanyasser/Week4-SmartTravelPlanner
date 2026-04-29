// The Decision Tension Board — the signature moment of AtlasBrief.
//
// Layout:
//   1. Heading row — destination name + country + travel-style tag
//   2. Two score cards side-by-side: Dream Fit (brass) / Reality Pressure
//      (verdigris). They are the same shape so the user reads them as a
//      single tradeoff.
//   3. The Final Verdict — large editorial type, full-width, with a
//      tri-color top rule (brass → terracotta → verdigris) that visually
//      echoes the two cards above and the counterfactual below.
//   4. The "Why not the obvious pick?" card.

import type { CounterfactualCard, DestinationCandidate } from "../api/types";
import { ScoreCard } from "./ScoreCard";

interface DecisionTensionBoardProps {
  topPick: DestinationCandidate;
  finalVerdict: string;
  counterfactual: CounterfactualCard;
}

export function DecisionTensionBoard({
  topPick,
  finalVerdict,
  counterfactual,
}: DecisionTensionBoardProps) {
  return (
    <section className="tension-board" aria-label="Decision Tension Board">
      <span className="tension-board__eyebrow reveal reveal--d1">
        ◆ Decision Tension Board
      </span>

      <header className="tension-board__heading reveal reveal--d2">
        <div className="tension-board__heading-left">
          <h2 className="tension-board__title">
            {topPick.name},{" "}
            <span className="tension-board__country">{topPick.country}</span>
          </h2>
          <span className="tension-board__style-tag">
            ◆ {topPick.travel_style}
          </span>
        </div>
      </header>

      <div className="tension-board__grid">
        <div className="reveal reveal--d2">
          <ScoreCard
            variant="dream"
            label="Dream Fit"
            source="ML + RAG"
            score={topPick.dream_fit.score}
            rationale={topPick.dream_fit.rationale}
            traits={topPick.dream_fit.matched_traits}
          />
        </div>
        <div className="reveal reveal--d3">
          <ScoreCard
            variant="reality"
            label="Reality Pressure"
            source="Live conditions"
            score={topPick.reality_pressure.score}
            rationale={topPick.reality_pressure.rationale}
            signals={[
              { key: "Weather", text: topPick.reality_pressure.weather_signal },
              { key: "Flights", text: topPick.reality_pressure.flight_signal },
            ]}
          />
        </div>
      </div>

      <div className="verdict reveal reveal--d3">
        <div className="verdict__label">Final Verdict — the tradeoff</div>
        <p className="verdict__body">{finalVerdict}</p>
      </div>

      <div className="counterfactual reveal reveal--d4">
        <div className="counterfactual__label">Why not the obvious pick?</div>
        <h3 className="counterfactual__title">
          The road not taken — <em>{counterfactual.obvious_pick}</em>
        </h3>
        <p className="counterfactual__body">{counterfactual.why_not_chosen}</p>
      </div>
    </section>
  );
}
