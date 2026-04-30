// Postcards from the candidate set — the agent's shortlist as little tilted
// passport-stamp cards. Sourced strictly from the real brief: the top pick
// (chosen), the first runner-up (backup, if any), and the counterfactual
// (skipped). Backgrounds are picked deterministically from the destination
// name so they stay consistent across renders.

import type { TripBriefResponse } from "../api/types";

interface PostcardsProps {
  brief: TripBriefResponse;
}

const PALETTES: Array<{ bg: string }> = [
  { bg: "linear-gradient(180deg,#2a3a86 0%, #5b3a8c 35%, #c97a8a 65%, #E9C77A 100%)" },
  { bg: "linear-gradient(180deg,#0e1124 0%, #1f5d54 50%, #6FBFB2 100%)" },
  { bg: "linear-gradient(180deg,#1a1f3a 0%, #7a5cba 50%, #D77556 100%)" },
  { bg: "linear-gradient(180deg,#070912 0%, #2a6f66 45%, #e9b26a 100%)" },
  { bg: "linear-gradient(180deg,#1a0f1a 0%, #8a3722 50%, #E9C77A 100%)" },
];

function paletteFor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 9973;
  return PALETTES[h % PALETTES.length].bg;
}

interface CardSpec {
  title: string;
  country: string;
  rot: string;
  bg: string;
  stamp: string;
}

export function Postcards({ brief }: PostcardsProps) {
  const cards: CardSpec[] = [];

  cards.push({
    title: brief.top_pick.name,
    country: `${brief.top_pick.country} · top pick`,
    rot: "-1.2deg",
    bg: paletteFor(brief.top_pick.name),
    stamp: "VISA\nGRANT\n✓",
  });

  const runner = brief.runners_up[0];
  if (runner) {
    cards.push({
      title: runner.name,
      country: `${runner.country} · backup`,
      rot: "0.6deg",
      bg: paletteFor(runner.name),
      stamp: "PASS\nVERIFY\nOK",
    });
  }

  if (brief.counterfactual.obvious_pick) {
    cards.push({
      title: brief.counterfactual.obvious_pick,
      country: "obvious pick · skipped",
      rot: "1.8deg",
      bg: paletteFor(brief.counterfactual.obvious_pick),
      stamp: "NOT\nCHOSEN\n×",
    });
  }

  if (cards.length === 0) return null;

  return (
    <section className="section reveal reveal--d4" aria-label="Postcards from the candidate set">
      <div className="section__rail">
        <span className="num">·</span>
        <span className="div" aria-hidden />
        <span className="tag">Postcards from the candidate set</span>
      </div>

      <div className="postcard-strip">
        {cards.map((c) => (
          <div
            key={c.title + c.country}
            className="postcard"
            style={{ ["--rot" as string]: c.rot } as React.CSSProperties}
          >
            <div className="postcard__sky" style={{ background: c.bg }} />
            <div className="postcard__sun" />
            <div className="postcard__hills" />
            <div className="postcard__country">{c.country}</div>
            <div className="postcard__title">{c.title}</div>
            <div className="postcard__stamp">
              {c.stamp.split("\n").map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
