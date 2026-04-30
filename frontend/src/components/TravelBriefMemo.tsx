// Executive Trip Memo — a letterpress vellum card with a slight rotation,
// compass watermark, and six sections (Why it fits / What to expect /
// Risks & tradeoffs / Booking advice / Backup option / Budget fit).
//
// Every line of body copy is reframed from the real schema; we don't invent.

import type { TripBriefResponse } from "../api/types";
import { formatBudget, parseTripDNA } from "../utils/parseQuery";

interface TravelBriefMemoProps {
  brief: TripBriefResponse;
}

function fileTag(name: string, country: string): string {
  const slug = (name + country)
    .replace(/[^A-Za-z0-9]/g, "")
    .slice(0, 3)
    .toUpperCase()
    .padEnd(3, "X");
  return `AB-${new Date().getFullYear()}-${slug}`;
}

export function TravelBriefMemo({ brief }: TravelBriefMemoProps) {
  const top = brief.top_pick;
  const dna = parseTripDNA(brief.query);
  const runner = brief.runners_up[0];
  const stamp = new Date()
    .toLocaleDateString("en-US", { year: "numeric", month: "short", day: "2-digit" })
    .toUpperCase();

  const recipient =
    dna.durationLabel || dna.month || dna.budgetUsd !== null
      ? [
          dna.durationLabel,
          dna.month && `in ${dna.month}`,
          dna.budgetUsd !== null && `${formatBudget(dna.budgetUsd)} budget`,
        ]
          .filter(Boolean)
          .join(", ")
      : "the requested trip";

  return (
    <section className="memo-wrap reveal reveal--d5" aria-label="Executive trip memo">
      <div className="section__rail">
        <span className="num">06</span>
        <span className="div" aria-hidden />
        <span className="tag">Executive memo · for the briefcase</span>
      </div>

      <article className="memo">
        <div className="memo__head">
          <div>
            <div className="memo__title">
              <strong>EXECUTIVE TRIP MEMO</strong> · CONFIDENTIAL
            </div>
            <div className="memo__recipient">
              Drafted for {recipient}.
            </div>
          </div>
          <div className="memo__stamp">
            <div>FILE · {fileTag(top.name, top.country)}</div>
            <div>{stamp}</div>
            <div className="seal">◆ {top.travel_style.toUpperCase()}</div>
          </div>
        </div>

        <div className="memo__grid">
          <div className="memo-section">
            <h5>Why it fits</h5>
            <p>{top.dream_fit.rationale}</p>
          </div>

          <div className="memo-section">
            <h5>What to expect</h5>
            <p>
              {top.reality_pressure.weather_signal}{" "}
              {top.dream_fit.matched_traits.length > 0 && (
                <em>
                  Trip leans into:{" "}
                  {top.dream_fit.matched_traits.join(", ")}.
                </em>
              )}
            </p>
          </div>

          <div className="memo-section">
            <h5>Risks &amp; tradeoffs</h5>
            <p>{top.reality_pressure.rationale}</p>
          </div>

          <div className="memo-section">
            <h5>Booking advice</h5>
            <p>{top.reality_pressure.flight_signal}</p>
          </div>

          <div className="memo-section">
            <h5>Backup option</h5>
            {runner ? (
              <p>
                <strong>
                  {runner.name}, {runner.country}
                </strong>{" "}
                ({runner.travel_style}, Dream Fit{" "}
                {Math.round(runner.dream_fit.score)}, Reality{" "}
                {Math.round(runner.reality_pressure.score)}) —{" "}
                {runner.dream_fit.rationale}
              </p>
            ) : (
              <p>
                <em>
                  No second-place destination cleared the bar this run; the
                  agent is confident in {top.name}.
                </em>
              </p>
            )}
          </div>

          <div className="memo-section">
            <h5>Budget fit</h5>
            <p>
              {dna.budgetUsd !== null ? (
                <>
                  Stated budget: <strong>{formatBudget(dna.budgetUsd)}</strong>.
                  The Reality Pressure score of{" "}
                  {Math.round(top.reality_pressure.score)} reflects how
                  forgiving live conditions are against this budget.
                </>
              ) : (
                <em>
                  No explicit budget was given, so the agent treated
                  affordability as a soft constraint and weighted Dream Fit
                  ({Math.round(top.dream_fit.score)}) more heavily.
                </em>
              )}
            </p>
          </div>
        </div>

        <div className="memo__signature">
          <div className="sig">— AtlasBrief</div>
          <div className="meta">
            <div>Synthesis · {brief.meta.strong_model}</div>
            <div>
              Run latency · {(brief.meta.latency_ms / 1000).toFixed(2)}s
            </div>
            <div>Cost · ${brief.meta.cost_usd.toFixed(4)}</div>
          </div>
        </div>
      </article>
    </section>
  );
}
