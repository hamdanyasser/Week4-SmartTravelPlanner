import { useState } from "react";
import { postTripBrief } from "./api/client";
import type { TripBriefResponse } from "./api/types";

const GOLDEN_DEMO_QUERY =
  "I have two weeks off in July and around $1,500. I want somewhere warm, not too touristy, and I like hiking. Where should I go, when should I book, and what should I expect?";

export default function App() {
  const [query, setQuery] = useState(GOLDEN_DEMO_QUERY);
  const [brief, setBrief] = useState<TripBriefResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await postTripBrief(query);
      setBrief(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="briefing-room">
      <header className="briefing-header">
        <span className="briefing-eyebrow">ATLASBRIEF // BRIEFING ROOM</span>
        <h1>The AI travel briefing room</h1>
        <p className="briefing-subtitle">
          Day 1 skeleton — wired to a stub backend. The Decision Tension Board
          components light up as the real agent comes online.
        </p>
      </header>

      <form className="briefing-form" onSubmit={handleSubmit}>
        <label htmlFor="query">Your trip question</label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={4}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Briefing…" : "Generate briefing"}
        </button>
      </form>

      {error && <div className="briefing-error">{error}</div>}

      {brief && (
        <section className="briefing-output">
          <h2>{brief.top_pick.name}, {brief.top_pick.country}</h2>
          <p className="travel-style-tag">{brief.top_pick.travel_style}</p>

          <div className="tension-grid">
            <div className="tension-card">
              <h3>Dream Fit</h3>
              <div className="score">{brief.top_pick.dream_fit.score}</div>
              <p>{brief.top_pick.dream_fit.rationale}</p>
            </div>

            <div className="tension-card">
              <h3>Reality Pressure</h3>
              <div className="score">{brief.top_pick.reality_pressure.score}</div>
              <p>{brief.top_pick.reality_pressure.rationale}</p>
            </div>
          </div>

          <div className="verdict-card">
            <h3>Final Verdict</h3>
            <p>{brief.final_verdict}</p>
          </div>

          <div className="counterfactual-card">
            <h3>Why not {brief.counterfactual.obvious_pick}?</h3>
            <p>{brief.counterfactual.why_not_chosen}</p>
          </div>
        </section>
      )}
    </div>
  );
}
