// One score panel on the Decision Tension Board.
//
// Two variants share this component: "dream" (brass) for Dream Fit, and
// "reality" (verdigris) for Reality Pressure. The variant only swaps
// accent colors — the layout is identical so the user can read them as
// two halves of the same decision.

import { useEffect, useState } from "react";

export type ScoreVariant = "dream" | "reality";

interface Signal {
  key: string;
  text: string;
}

interface ScoreCardProps {
  variant: ScoreVariant;
  label: string;
  source: string;
  score: number;
  rationale: string;
  signals?: Signal[];
  traits?: string[];
}

export function ScoreCard({
  variant,
  label,
  source,
  score,
  rationale,
  signals,
  traits,
}: ScoreCardProps) {
  // Animate the bar fill on mount.
  const [renderedScore, setRenderedScore] = useState(0);
  useEffect(() => {
    const t = window.setTimeout(() => setRenderedScore(score), 60);
    return () => window.clearTimeout(t);
  }, [score]);

  return (
    <article
      className={
        variant === "dream"
          ? "score-card score-card--dream"
          : "score-card score-card--reality"
      }
    >
      <header className="score-card__head">
        <span className="score-card__label">{label}</span>
        <span className="score-card__source">{source}</span>
      </header>

      <div className="score-card__score-row">
        <span className="score-card__score">{Math.round(score)}</span>
        <span className="score-card__score-of">/ 100</span>
      </div>

      <div className="score-card__bar">
        <div
          className="score-card__bar-fill"
          style={{ width: `${Math.max(0, Math.min(100, renderedScore))}%` }}
        />
      </div>

      {traits && traits.length > 0 && (
        <div className="score-card__traits">
          {traits.map((t) => (
            <span className="score-card__trait" key={t}>
              {t}
            </span>
          ))}
        </div>
      )}

      <p className="score-card__rationale">{rationale}</p>

      {signals && signals.length > 0 && (
        <div className="score-card__signals">
          {signals.map((s) => (
            <div className="score-card__signal" key={s.key}>
              <span className="score-card__signal-key">{s.key}</span>
              <span>{s.text}</span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
