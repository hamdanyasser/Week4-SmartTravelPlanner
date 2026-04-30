// Quiet "ready to begin" panel shown before the first brief is drafted.
// Says what's about to happen without competing with the brief that will
// soon take its place.

export function EmptyState() {
  return (
    <section className="empty-state reveal reveal--d3" aria-label="Ready">
      <h3>Ask one fuzzy question.</h3>
      <p>
        AtlasBrief routes it through three tools, names the tradeoff, and
        leaves a Decision Tension Board on this desk in about four seconds.
      </p>
    </section>
  );
}
