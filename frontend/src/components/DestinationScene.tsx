// The cinematic backdrop layer behind the Decision Tension Board — sunset
// sky, drifting clouds, three mountain layers, ocean shimmer, a faint
// "levada" water line, and birds. Designed to evoke an atmospheric island
// sunset rather than literally render any one destination.

export function DestinationScene() {
  return (
    <div className="madeira-scene" aria-hidden>
      <div className="ms-sky" />
      <div className="ms-sun" />
      <div className="ms-clouds">
        <span style={{ top: "22%", left: "12%", width: "180px", animationDelay: "0s" }} />
        <span style={{ top: "32%", left: "58%", width: "140px", animationDelay: "-12s" }} />
        <span style={{ top: "18%", left: "78%", width: "100px", animationDelay: "-22s" }} />
      </div>
      <svg
        className="ms-layer ms-mtn-far"
        viewBox="0 0 1200 400"
        preserveAspectRatio="none"
      >
        <path
          d="M0 280 L80 220 L160 250 L260 180 L360 230 L480 170 L580 220 L700 160 L820 210 L940 180 L1080 230 L1200 200 L1200 400 L0 400 Z"
          fill="rgba(91,58,140,.55)"
        />
      </svg>
      <svg
        className="ms-layer ms-mtn-mid"
        viewBox="0 0 1200 400"
        preserveAspectRatio="none"
      >
        <path
          d="M0 320 L120 240 L220 280 L340 200 L460 270 L600 180 L740 260 L880 210 L1020 280 L1140 230 L1200 260 L1200 400 L0 400 Z"
          fill="rgba(31,93,84,.85)"
        />
      </svg>
      <svg
        className="ms-layer ms-cliffs"
        viewBox="0 0 1200 400"
        preserveAspectRatio="none"
      >
        <path
          d="M0 360 L60 300 L140 340 L240 280 L380 330 L520 270 L660 320 L820 280 L980 330 L1100 290 L1200 320 L1200 400 L0 400 Z"
          fill="rgba(14,17,36,.95)"
        />
      </svg>
      <div className="ms-ocean">
        <span />
        <span />
        <span />
      </div>
      <svg className="ms-levada" viewBox="0 0 1200 400" preserveAspectRatio="none" fill="none">
        <path
          d="M -20 350 Q 200 320 350 340 T 700 330 T 1100 350 T 1240 340"
          stroke="rgba(232,199,122,.55)"
          strokeWidth="1.4"
          strokeDasharray="3 4"
        />
      </svg>
      <svg className="ms-birds" viewBox="0 0 200 60" preserveAspectRatio="none">
        <path
          d="M 10 30 q 5 -6 10 0 q 5 -6 10 0"
          stroke="#f1ecdd"
          strokeWidth=".8"
          fill="none"
          opacity=".7"
        />
        <path
          d="M 40 20 q 4 -5 8 0 q 4 -5 8 0"
          stroke="#f1ecdd"
          strokeWidth=".7"
          fill="none"
          opacity=".5"
        />
      </svg>
      <div className="ms-haze" />
    </div>
  );
}
