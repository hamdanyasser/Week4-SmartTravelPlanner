// Shimmer state while the brief is being drafted. The Mission Timeline above
// already carries most of the "in progress" weight, so this is just a few
// quiet bars that hint at the shape of the Tension Board.

export function LoadingShimmer() {
  return (
    <section className="shimmer reveal reveal--d4" aria-busy aria-label="Drafting briefing">
      <div className="shimmer__row" style={{ width: "92%", height: 28 }} />
      <div className="shimmer__row" />
      <div className="shimmer__row" />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 18,
          marginTop: 24,
        }}
      >
        <div className="shimmer__row" style={{ height: 220, borderRadius: 12 }} />
        <div className="shimmer__row" style={{ height: 220, borderRadius: 12 }} />
      </div>
    </section>
  );
}
