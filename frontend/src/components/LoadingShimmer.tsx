// Loading state shown next to the timeline while the agent is running.
//
// Uses the shared `.shimmer` class to draw skeleton placeholders for the
// upcoming Decision Tension Board. The shapes match the real layout so the
// transition feels like sliding from "in progress" to "complete" rather
// than a hard page swap.

export function LoadingShimmer() {
  return (
    <section
      className="reveal reveal--d4"
      aria-label="Drafting brief"
      aria-busy
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 18,
        }}
      >
        <span className="hero__status-dot" aria-hidden />
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "var(--text-400)",
          }}
        >
          Drafting Decision Tension Board…
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 18,
          marginBottom: 18,
        }}
      >
        <div className="shimmer" style={{ height: 280 }} />
        <div className="shimmer" style={{ height: 280 }} />
      </div>

      <div
        className="shimmer"
        style={{ height: 140, marginBottom: 18, borderRadius: 16 }}
      />
      <div className="shimmer" style={{ height: 100, borderRadius: 16 }} />
    </section>
  );
}
