// First-load state when no brief has been generated yet.
//
// We show a quiet "what AtlasBrief is going to do" overview so the page
// doesn't feel empty — three numbered cards that mirror the three tools.

const STEPS: Array<{ n: string; title: string; body: string }> = [
  {
    n: "01",
    title: "We read the question",
    body: "Budget, month, vibe, constraints — extracted into a structured Trip DNA.",
  },
  {
    n: "02",
    title: "Three tools, one decision",
    body: "RAG retrieves destination knowledge, the ML classifier predicts the travel style, live conditions check weather and flights.",
  },
  {
    n: "03",
    title: "We name the tradeoff",
    body: "The Decision Tension Board defends the pick against the obvious one — Dream Fit vs Reality Pressure, with a final verdict.",
  },
];

export function EmptyState() {
  return (
    <section className="empty-grid reveal reveal--d3" aria-label="How AtlasBrief works">
      {STEPS.map((s) => (
        <article className="empty-grid__card" key={s.n}>
          <div className="empty-grid__num">{s.n}</div>
          <h3 className="empty-grid__title">{s.title}</h3>
          <p className="empty-grid__body">{s.body}</p>
        </article>
      ))}
    </section>
  );
}
