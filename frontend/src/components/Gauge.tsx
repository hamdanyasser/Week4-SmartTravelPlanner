// Verdigris semi-circle pressure gauge — Reality Pressure 0–100.
// Score is inverted (100 = calm, 0 = storm) so the face shifts to a
// rust-warn finish below 40.

import { useEffect, useState } from "react";

interface GaugeProps {
  value: number;
  animateOn: boolean;
  label?: string;
}

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

export function Gauge({ value, animateOn, label = "Reality Pressure" }: GaugeProps) {
  const [v, setV] = useState(0);

  useEffect(() => {
    if (!animateOn) {
      setV(0);
      return;
    }
    if (prefersReducedMotion()) {
      setV(value);
      return;
    }
    const t = window.setTimeout(() => setV(value), 100);
    return () => window.clearTimeout(t);
  }, [value, animateOn]);

  const angle = -90 + (v / 100) * 180;
  const warn = v < 40;

  return (
    <div
      className="gauge"
      role="img"
      aria-label={`${label} score: ${Math.round(value)} out of 100 (higher means calmer conditions)`}
    >
      <div className="gauge__ring" aria-hidden />
      <div className={"gauge__face" + (warn ? " warn" : "")} aria-hidden />
      <div className="gauge__arc" aria-hidden />
      <div className="gauge__needle" style={{ transform: `rotate(${angle}deg)` }} aria-hidden />
      <div className="gauge__hub" aria-hidden />
      <div className="gauge__readout" aria-hidden>
        {Math.round(v)}
        <em>/100</em>
      </div>
      <div className="gauge__poles" aria-hidden>
        <span>Storm</span>
        <span>Calm</span>
      </div>
    </div>
  );
}
