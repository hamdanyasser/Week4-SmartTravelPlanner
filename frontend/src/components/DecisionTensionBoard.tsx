// The Decision Tension Board — the signature moment of AtlasBrief.
//
// Reading order, top to bottom:
//   1. Eyebrow strip + destination name + ◆ travel-style wax seal
//   2. Three plain-language summary cards (love it / know / cost) sourced
//      from the real brief — re-frame, don't invent
//   3. Two instruments side-by-side: brass dial (Dream Fit, ML+RAG) and
//      verdigris pressure gauge (Reality Pressure, live conditions)
//   4. Final Verdict — full-width editorial pull-quote with brass drop-cap
//   5. "Why not the obvious pick?" — counterfactual with hairline strike

import type { CounterfactualCard, DestinationCandidate } from "../api/types";
import { Dial } from "./Dial";
import { Gauge } from "./Gauge";

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
  // Plain-language card copy is reframed from the real schema fields so we
  // never invent text. Falls back to the rationale if matched_traits is empty.
  const traits = topPick.dream_fit.matched_traits;
  const loveIt =
    traits.length > 0
      ? `What you asked for — ${traits.join(", ")} — lines up here. ${topPick.dream_fit.rationale}`
      : topPick.dream_fit.rationale;
  const drop = finalVerdict.charAt(0);
  const rest = finalVerdict.slice(1);

  return (
    <section
      className="glass tension reveal reveal--d4"
      aria-label="Decision Tension Board"
    >
      <div className="tension__topline">
        <span className="seam" aria-hidden />
        <span>05 · Decision Tension Board</span>
      </div>

      <header className="tension__head">
        <div className="tension__title-wrap">
          <div>
            <div className="tension__kicker">
              Top pick · a friendly second opinion
            </div>
            <h2 className="tension__title">
              {topPick.name}
              <em>{topPick.country}</em>
            </h2>
            <div className="tension__greet">
              The road that survived both the dream and the reality check.
            </div>
          </div>
        </div>
        <div className="wax-seal">{topPick.travel_style}</div>
      </header>

      <div className="plainline">
        <div className="plainline__card plainline__card--good">
          <div className="plainline__icon">
            <svg
              viewBox="0 0 24 24"
              width="22"
              height="22"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
            >
              <path d="M4 12 l4 4 l12 -12" />
            </svg>
          </div>
          <div>
            <div className="plainline__label">Why you'll love it</div>
            <div className="plainline__text">{loveIt}</div>
          </div>
        </div>

        <div className="plainline__card plainline__card--watch">
          <div className="plainline__icon">
            <svg
              viewBox="0 0 24 24"
              width="22"
              height="22"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7 v6" />
              <circle cx="12" cy="16" r="0.8" fill="currentColor" />
            </svg>
          </div>
          <div>
            <div className="plainline__label">What to know</div>
            <div className="plainline__text">
              {topPick.reality_pressure.weather_signal}
            </div>
          </div>
        </div>

        <div className="plainline__card plainline__card--cost">
          <div className="plainline__icon">
            <svg
              viewBox="0 0 24 24"
              width="22"
              height="22"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
            >
              <path d="M7 7 h10 M7 12 h10 M7 17 h6" />
            </svg>
          </div>
          <div>
            <div className="plainline__label">Budget read</div>
            <div className="plainline__text">
              {topPick.reality_pressure.flight_signal}
            </div>
          </div>
        </div>
      </div>

      <div className="instruments">
        <div className="instr instr--left">
          <div className="instr__label">
            <span className="name">Dream Fit</span>
            <span className="src">ML + RAG</span>
          </div>
          <div className="dial-wrap">
            <Dial value={topPick.dream_fit.score} animateOn />
            <div className="foil-chips">
              {topPick.dream_fit.matched_traits.map((trait) => (
                <span key={trait} className="foil">
                  {trait}
                </span>
              ))}
            </div>
          </div>
          <p className="rationale">{topPick.dream_fit.rationale}</p>
        </div>

        <div className="tri-rule" aria-hidden />

        <div className="instr instr--right">
          <div className="instr__label">
            <span className="name">Reality Pressure</span>
            <span className="src">Live conditions</span>
          </div>
          <div className="dial-wrap dial-wrap--right">
            <Gauge value={topPick.reality_pressure.score} animateOn />
            <div className="signals">
              <div className="signal">
                <span className="src">Weather</span>
                <span className="body">
                  {topPick.reality_pressure.weather_signal}
                </span>
                <span className="meter" aria-hidden>
                  <span style={{ width: "82%" }} />
                </span>
              </div>
              <div className="signal">
                <span className="src">Flights</span>
                <span className="body">
                  {topPick.reality_pressure.flight_signal}
                </span>
                <span className="meter" aria-hidden>
                  <span style={{ width: "68%" }} />
                </span>
              </div>
            </div>
          </div>
          <p className="rationale">{topPick.reality_pressure.rationale}</p>
        </div>
      </div>

      <div className="tri-rule--h" aria-hidden />

      <div className="verdict">
        <div className="verdict__label">Final verdict — the tradeoff</div>
        <p className="verdict__quote">
          <span className="verdict__drop">{drop}</span>
          {rest}
        </p>
      </div>

      <div className="counter">
        <div className="counter__ghost" aria-hidden>
          <svg viewBox="0 0 200 200" fill="none" stroke="#E9C77A" strokeWidth=".5">
            <path
              d="M40 140 Q50 100 70 90 Q90 60 120 65 Q150 75 160 110 Q165 140 150 160 Q120 180 90 175 Q55 170 40 140 Z"
              fill="#E9C77A"
              fillOpacity=".25"
            />
            <circle cx="100" cy="50" r="8" fill="#E9C77A" fillOpacity=".4" />
            <path
              d="M70 110 Q90 100 110 115 Q130 130 150 120"
              stroke="#E9C77A"
              strokeWidth=".6"
            />
          </svg>
        </div>
        <div>
          <div className="counter__label">
            · We considered, then passed on
          </div>
          <div className="counter__pick">{counterfactual.obvious_pick}</div>
        </div>
        <div className="counter__why">
          <span className="lead">The road not taken. </span>
          {counterfactual.why_not_chosen}
        </div>
      </div>
    </section>
  );
}
