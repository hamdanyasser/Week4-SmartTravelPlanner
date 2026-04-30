// Brass dial — Dream Fit's 0–100 score rendered as a physical instrument.
//
// The needle animates from 0 to value with a slight overshoot+settle (the
// transition lives in CSS). When `animateOn` flips true, we delay the value
// write by one tick so the from-state catches.

import { useEffect, useState } from "react";

interface DialProps {
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

export function Dial({ value, animateOn, label = "Dream Fit" }: DialProps) {
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

  const angle = -135 + (v / 100) * 270;

  const ticks = [];
  for (let i = 0; i <= 20; i++) {
    const a = -135 + (i / 20) * 270;
    ticks.push(
      <i
        key={i}
        style={{ transform: `translateX(-50%) rotate(${a}deg)` }}
        className={i % 5 === 0 ? "major" : ""}
      />,
    );
  }

  const numPos = (n: number) => {
    const a = ((-135 + (n / 100) * 270) * Math.PI) / 180;
    const r = 78;
    return {
      left: `calc(50% + ${Math.sin(a) * r}px - 8px)`,
      top: `calc(50% - ${Math.cos(a) * r}px - 8px)`,
    };
  };

  return (
    <div
      className="dial"
      role="img"
      aria-label={`${label} score: ${Math.round(value)} out of 100`}
    >
      <div className="dial__ring" aria-hidden />
      <div className="dial__face" aria-hidden />
      <div className="dial__ticks" aria-hidden>{ticks}</div>
      <div className="dial__num" style={numPos(0)} aria-hidden>0</div>
      <div className="dial__num" style={numPos(50)} aria-hidden>50</div>
      <div className="dial__num" style={numPos(100)} aria-hidden>100</div>
      <div className="dial__needle" style={{ transform: `rotate(${angle}deg)` }} aria-hidden />
      <div className="dial__hub" aria-hidden />
      <div className="dial__readout" aria-hidden>
        {Math.round(v)}
        <em>/100</em>
      </div>
    </div>
  );
}
