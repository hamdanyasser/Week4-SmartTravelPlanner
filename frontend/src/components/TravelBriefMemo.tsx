// Executive memo card.
//
// Synthesizes the agent's response into a "premium travel memo" aesthetic
// — the way a private travel concierge would write up a recommendation.
// We pull from the response's verdict + dream-fit rationale + reality
// signals + the runner-up so this section feels load-bearing instead of
// being a duplicate of the Tension Board.

import type { TripBriefResponse } from "../api/types";
import { formatBudget, parseTripDNA } from "../utils/parseQuery";

interface TravelBriefMemoProps {
  brief: TripBriefResponse;
}

export function TravelBriefMemo({ brief }: TravelBriefMemoProps) {
  const dna = parseTripDNA(brief.query);
  const runner = brief.runners_up[0];

  // Pull a couple of "what to expect" lines from the dream-fit rationale and
  // reality signals. We don't invent content — we re-frame what the backend
  // already returned, which keeps this honest at code-review time.
  const expectLines: string[] = [];
  if (brief.top_pick.dream_fit.rationale) {
    expectLines.push(brief.top_pick.dream_fit.rationale);
  }
  expectLines.push(brief.top_pick.reality_pressure.weather_signal);
  expectLines.push(brief.top_pick.reality_pressure.flight_signal);

  const stamp = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });

  return (
    <section className="memo reveal reveal--d2" aria-label="Travel brief memo">
      <header className="memo__head">
        <div className="memo__head-left">
          <div className="memo__eyebrow">Executive trip memo · Confidential</div>
          <h3 className="memo__title">
            Recommendation: {brief.top_pick.name}, {brief.top_pick.country}
          </h3>
          <div className="memo__sub">
            Drafted for {dna.durationLabel ?? "the requested trip"}
            {dna.month ? ` in ${dna.month}` : ""} ·{" "}
            {formatBudget(dna.budgetUsd)} budget
          </div>
        </div>
        <div className="memo__stamp">
          Stamp · {stamp}
          <br />
          Style · {brief.top_pick.travel_style}
        </div>
      </header>

      <div className="memo__grid">
        <div className="memo__section">
          <h4>Why it fits</h4>
          <p>{brief.top_pick.dream_fit.rationale}</p>
        </div>

        <div className="memo__section">
          <h4>What to expect</h4>
          <ul className="memo__list">
            {expectLines.filter(Boolean).map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>

        <div className="memo__section">
          <h4>Risks &amp; tradeoffs</h4>
          <p>{brief.top_pick.reality_pressure.rationale}</p>
        </div>

        <div className="memo__section">
          <h4>Booking advice</h4>
          <p>{brief.top_pick.reality_pressure.flight_signal}</p>
        </div>

        {runner && (
          <div className="memo__section memo__section--wide">
            <h4>Backup option</h4>
            <p>
              <strong>
                {runner.name}, {runner.country}
              </strong>{" "}
              ({runner.travel_style}, Dream Fit{" "}
              {Math.round(runner.dream_fit.score)}, Reality{" "}
              {Math.round(runner.reality_pressure.score)}) —{" "}
              {runner.dream_fit.rationale}
            </p>
          </div>
        )}

        <div className="memo__section memo__section--wide">
          <h4>Budget fit</h4>
          <p>
            {dna.budgetUsd !== null
              ? `Stated budget: ${formatBudget(dna.budgetUsd)}. The Reality Pressure score of ${Math.round(
                  brief.top_pick.reality_pressure.score,
                )} reflects how forgiving the live conditions are against this budget.`
              : `No explicit budget was given, so the agent treated affordability as a soft constraint and weighted Dream Fit (${Math.round(
                  brief.top_pick.dream_fit.score,
                )}) more heavily.`}
          </p>
        </div>
      </div>
    </section>
  );
}
