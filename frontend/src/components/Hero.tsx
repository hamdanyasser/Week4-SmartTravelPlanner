// Top frame of the briefing room.
//
// Shows the brand, the live/demo system status, the editorial title, and
// four "wall metrics" that make the surface feel like a control room
// landing rather than a dashboard.

import { Brand } from "./Brand";
import type { BriefMode } from "../hooks/useTripBrief";

interface HeroProps {
  mode: BriefMode | null;
}

const METRICS: Array<{ label: string; value: string }> = [
  { label: "Briefings drafted", value: "1 in session" },
  { label: "Tools online", value: "3 / 3" },
  { label: "RAG corpus", value: "14 destinations" },
  { label: "Decision board", value: "Dream vs Reality" },
];

export function Hero({ mode }: HeroProps) {
  const statusLabel =
    mode === "demo"
      ? "Offline demo mode"
      : mode === "live"
      ? "Live agent online"
      : "Standing by";

  return (
    <header className="hero reveal">
      <div className="hero__nav">
        <Brand />
        <span className="hero__status">
          <span
            className={
              mode === "demo"
                ? "hero__status-dot hero__status-dot--demo"
                : "hero__status-dot"
            }
            aria-hidden
          />
          {statusLabel}
        </span>
      </div>

      <h1 className="hero__title">
        From a vague <em>travel wish</em>
        <br />
        to a defended brief.
      </h1>
      <p className="hero__subtitle">
        AtlasBrief is your AI travel briefing room. Ask one fuzzy question;
        leave with a recommendation, the tradeoff that decided it, and the
        runner-up you didn't take — pulled from RAG, an ML classifier, and live
        conditions.
      </p>

      <dl className="hero__metrics">
        {METRICS.map((m) => (
          <div className="hero__metric" key={m.label}>
            <dt className="hero__metric-label">{m.label}</dt>
            <dd className="hero__metric-value">{m.value}</dd>
          </div>
        ))}
      </dl>
    </header>
  );
}
