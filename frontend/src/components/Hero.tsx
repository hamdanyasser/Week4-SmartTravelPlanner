// The hero — eyebrow, kinetic word-by-word title, italic subtitle, wall
// metrics. The status pill and brand mark live in the topbar (App.tsx),
// not here, so this section is purely editorial.

const METRICS: Array<{ label: string; value: string; em?: string; hint: string }> = [
  {
    label: "Briefings drafted",
    value: "1",
    em: "in this session",
    hint: "Across 14 destinations · 6 travel styles",
  },
  {
    label: "Tools online",
    value: "3",
    em: "/ 3",
    hint: "RAG · ML · Live conditions",
  },
  {
    label: "RAG corpus",
    value: "14",
    em: "destinations",
    hint: "Markdown chunks · pgvector cosine",
  },
  {
    label: "Decision board",
    value: "Dream",
    em: "vs Reality",
    hint: "Closing argument · road not taken",
  },
];

export function Hero() {
  // The kinetic title — every word fades up on its own beat.
  const line1 = ["From", "a", "vague"];
  const line2 = ["to", "a", "defended"];

  return (
    <section className="hero" aria-label="AtlasBrief introduction">
      <div className="hero__eyebrow">
        <span className="seam" aria-hidden />
        <span>01 · The atlas wakes up</span>
      </div>

      <h1 className="hero__head">
        {line1.map((w, i) => (
          <span
            key={`a${i}`}
            className="word"
            style={{ animationDelay: `${0.1 * i}s` }}
          >
            {w}
            &nbsp;
          </span>
        ))}
        <em className="word" style={{ animationDelay: "0.4s" }}>
          travel wish
        </em>
        <br />
        <span className="arrow word" style={{ animationDelay: "0.6s" }}>
          ▶
        </span>
        {line2.map((w, i) => (
          <span
            key={`b${i}`}
            className="word"
            style={{ animationDelay: `${0.7 + 0.1 * i}s` }}
          >
            {" "}
            {w}
          </span>
        ))}
        <em className="word" style={{ animationDelay: "1.05s" }}>
          {" "}
          brief.
        </em>
      </h1>

      <p className="hero__sub">
        AtlasBrief routes a fuzzy human question through a research agent — RAG
        over fourteen destinations, an ML classifier over six travel styles,
        and live weather + flight signals — and returns the tradeoff between
        Dream Fit and Reality Pressure, then names the road not taken.
      </p>

      <dl className="metrics">
        {METRICS.map((m) => (
          <div className="metric" key={m.label}>
            <dt className="metric__label">{m.label}</dt>
            <dd className="metric__value">
              {m.value}
              {m.em && <em>{m.em}</em>}
            </dd>
            <div className="metric__hint">{m.hint}</div>
          </div>
        ))}
      </dl>
    </section>
  );
}
