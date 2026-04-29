// "Trip DNA" — what the system parsed from the user's question.
//
// This is not a backend feature; it's a transparency surface so the user
// instantly sees that AtlasBrief read their request as a structured intent,
// not a wall of text. The labeled fields mirror the slots that the agent's
// downstream tools actually use (budget, month, duration, climate,
// activities, dislikes), plus the predicted travel style if available.

import { useMemo } from "react";
import { formatBudget, parseTripDNA } from "../utils/parseQuery";
import type { TravelStyle } from "../api/types";

interface TripDNAPanelProps {
  query: string;
  travelStyle: TravelStyle | null;
}

export function TripDNAPanel({ query, travelStyle }: TripDNAPanelProps) {
  const dna = useMemo(() => parseTripDNA(query), [query]);

  const cells: Array<{
    label: string;
    value: string;
    accent?: "cool" | "hot";
    muted?: boolean;
    tags?: string[];
    hotTags?: boolean;
  }> = [
    {
      label: "Budget",
      value: formatBudget(dna.budgetUsd),
      muted: dna.budgetUsd === null,
    },
    {
      label: "Month",
      value: dna.month ?? "Not specified",
      muted: dna.month === null,
    },
    {
      label: "Duration",
      value: dna.durationLabel ?? "Not specified",
      muted: dna.durationLabel === null,
    },
    {
      label: "Climate",
      value: dna.climate ?? "Not specified",
      accent: "hot",
      muted: dna.climate === null,
    },
    {
      label: "Activities",
      value:
        dna.activities.length > 0
          ? dna.activities.join(" · ")
          : "Not specified",
      accent: "cool",
      muted: dna.activities.length === 0,
      tags: dna.activities,
    },
    {
      label: "Constraints",
      value:
        dna.dislikes.length > 0 ? dna.dislikes.join(" · ") : "None detected",
      accent: "hot",
      muted: dna.dislikes.length === 0,
      tags: dna.dislikes,
      hotTags: true,
    },
  ];

  return (
    <section className="dna reveal reveal--d2" aria-label="Trip DNA">
      <div>
        <div className="dna__heading">Trip DNA</div>
        <h2 className="dna__title">What we read from your question.</h2>
        <p className="dna__intro">
          Parsed slots that the agent's tools will use downstream. If a slot
          shows <em>not specified</em>, the agent infers it from context rather
          than guessing on your behalf.
        </p>
        {travelStyle && (
          <div style={{ marginTop: 18 }}>
            <div className="dna__heading">Predicted travel style</div>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 28,
                color: "var(--brass-500)",
                marginTop: 4,
              }}
            >
              {travelStyle}
            </div>
          </div>
        )}
      </div>
      <div className="dna__grid">
        {cells.map((c) => (
          <div
            key={c.label}
            className={
              c.accent === "cool"
                ? "dna__cell dna__cell--cool"
                : c.accent === "hot"
                ? "dna__cell dna__cell--hot"
                : "dna__cell"
            }
          >
            <div className="dna__cell-label">{c.label}</div>
            <div
              className={
                c.muted
                  ? "dna__cell-value dna__cell-value--muted"
                  : "dna__cell-value"
              }
            >
              {c.value}
            </div>
            {c.tags && c.tags.length > 0 && (
              <div className="dna__cell-tags">
                {c.tags.map((t) => (
                  <span
                    key={t}
                    className={c.hotTags ? "dna__tag dna__tag--hot" : "dna__tag"}
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
