// Brand mark used in the hero and footer. Tiny on purpose — the visual
// weight of the page comes from the typography, not a heavy logo.

export function Brand() {
  return (
    <div className="brand" aria-label="AtlasBrief">
      <span className="brand__mark" aria-hidden />
      <span className="brand__name">AtlasBrief</span>
      <span className="brand__divider">//</span>
      <span>Briefing Room</span>
    </div>
  );
}
