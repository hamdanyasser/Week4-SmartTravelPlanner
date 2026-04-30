// Trip DNA — six specimen vitrines (budget · month · duration · climate ·
// activities · constraints) and an optional seventh card with the predicted
// travel style once the ML classifier has spoken. Each cell reveals via a
// clip-path ink-blot and tilts on hover.

import { useMemo } from "react";
import { formatBudget, parseTripDNA } from "../utils/parseQuery";
import type { TravelStyle } from "../api/types";

interface TripDNAPanelProps {
  query: string;
  travelStyle: TravelStyle | null;
}

interface Cell {
  key: string;
  label: string;
  value: string;
  tone: "" | "hot" | "cool";
  muted: boolean;
  tags?: string[];
  hotTags?: boolean;
}

export function TripDNAPanel({ query, travelStyle }: TripDNAPanelProps) {
  const dna = useMemo(() => parseTripDNA(query), [query]);

  const cells: Cell[] = [
    {
      key: "budget",
      label: "Budget",
      value: formatBudget(dna.budgetUsd),
      tone: "",
      muted: dna.budgetUsd === null,
    },
    {
      key: "month",
      label: "Month",
      value: dna.month ?? "Not specified",
      tone: "",
      muted: dna.month === null,
    },
    {
      key: "duration",
      label: "Duration",
      value: dna.durationLabel ?? "Not specified",
      tone: "",
      muted: dna.durationLabel === null,
    },
    {
      key: "climate",
      label: "Climate",
      value: dna.climate ?? "Not specified",
      tone: "hot",
      muted: dna.climate === null,
    },
    {
      key: "activities",
      label: "Activities",
      value:
        dna.activities.length > 0 ? dna.activities.join(" · ") : "Not specified",
      tone: "cool",
      muted: dna.activities.length === 0,
      tags: dna.activities,
    },
    {
      key: "constraints",
      label: "Constraints",
      value:
        dna.dislikes.length > 0 ? dna.dislikes.join(" · ") : "None detected",
      tone: "hot",
      muted: dna.dislikes.length === 0,
      tags: dna.dislikes,
      hotTags: true,
    },
  ];

  return (
    <section className="section reveal reveal--d2" aria-label="Trip DNA">
      <div className="section__rail">
        <span className="num">03</span>
        <span className="div" aria-hidden />
        <span className="tag">Trip DNA · what we read from your wish</span>
      </div>

      <div className="dna">
        {cells.map((c, i) => (
          <div
            key={c.key}
            className={
              "specimen" +
              (c.tone ? ` ${c.tone}` : "") +
              (c.muted ? " unspec" : "")
            }
            style={
              {
                "--idx": i,
                "--bx": `${15 + ((i * 23) % 70)}%`,
                "--by": `${20 + ((i * 37) % 60)}%`,
              } as React.CSSProperties
            }
          >
            <div className="label">{c.label}</div>
            <div className="value">
              {c.muted ? <em>{c.value}</em> : c.value}
            </div>
            {c.tags && c.tags.length > 0 && (
              <div className="dna-tags">
                {c.tags.map((t) => (
                  <span
                    key={t}
                    className={c.hotTags ? "dna-tag dna-tag--hot" : "dna-tag"}
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}
            <div className="pip">· {String(i + 1).padStart(2, "0")}</div>
          </div>
        ))}

        {travelStyle && (
          <div
            className="specimen predicted"
            style={
              {
                "--idx": cells.length,
                "--bx": "70%",
                "--by": "30%",
              } as React.CSSProperties
            }
          >
            <div className="label">Predicted travel style · ML</div>
            <div className="value">{travelStyle}</div>
            <div className="pip">· 07</div>
          </div>
        )}
      </div>
    </section>
  );
}
