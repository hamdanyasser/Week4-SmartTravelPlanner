// AtlasBrief wordmark — brass coin with engraved meridians + serif name.
// The visual weight of the topbar comes from the type, not the logo.

export function Brand() {
  return (
    <div className="brand" aria-label="AtlasBrief">
      <div className="brand__mark" aria-hidden />
      <div className="brand__name">
        Atlas<em>Brief</em>
      </div>
    </div>
  );
}
