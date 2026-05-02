// The fixed atmospheric layer that sits behind every section.
//
// Five cooperating pieces:
//   - aurora veil (drifting purple/teal northern-lights wash)
//   - starfield (90 twinkling pinpricks)
//   - celestial atlas globe (engraved + holographic, parallaxed by the cursor)
//   - drifting brass dust motes
//
// The mouse-parallax offset is owned by App.tsx and forwarded as CSS variables
// (`--mx`, `--my`) so this component stays pure-render.

import { useMemo } from "react";

interface AtlasBackdropProps {
  parallax: { x: number; y: number };
  thinking: boolean;
}

export function AtlasBackdrop({ parallax, thinking }: AtlasBackdropProps) {
  return (
    <div
      className="atlas-stage"
      style={
        {
          "--mx": `${parallax.x}px`,
          "--my": `${parallax.y}px`,
        } as React.CSSProperties
      }
    >
      <div className="aurora-veil" />
      <Starfield />
      <AtlasGlobe thinking={thinking} />
      <BrassDust />
    </div>
  );
}

function AtlasGlobe({ thinking }: { thinking: boolean }) {
  return (
    <div className={"atlas-globe" + (thinking ? " thinking" : "")} aria-hidden>
      <svg viewBox="-600 -600 1200 1200" fill="none">
        <defs>
          <radialGradient id="globeFace" cx="35%" cy="30%" r="80%">
            <stop offset="0%" stopColor="#1d2334" />
            <stop offset="50%" stopColor="#11141C" />
            <stop offset="100%" stopColor="#070a10" />
          </radialGradient>
          <radialGradient id="globeRim" cx="50%" cy="50%" r="50%">
            <stop offset="92%" stopColor="rgba(232,199,122,0)" />
            <stop offset="96%" stopColor="rgba(232,199,122,.55)" />
            <stop offset="100%" stopColor="rgba(232,199,122,0)" />
          </radialGradient>
          <radialGradient id="haze" cx="50%" cy="50%" r="55%">
            <stop offset="60%" stopColor="rgba(232,199,122,0)" />
            <stop offset="100%" stopColor="rgba(63,143,132,.18)" />
          </radialGradient>
          <linearGradient id="brassStroke" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f5dfa1" />
            <stop offset="50%" stopColor="#C8A24A" />
            <stop offset="100%" stopColor="#6d5520" />
          </linearGradient>
        </defs>

        <circle cx="0" cy="0" r="560" fill="url(#haze)" />

        <g className="ring">
          <circle cx="0" cy="0" r="520" stroke="rgba(232,199,122,.18)" strokeWidth="0.8" />
          <g stroke="rgba(232,199,122,.45)" strokeWidth="0.6">
            {Array.from({ length: 60 }).map((_, i) => {
              const a = (i * 6 * Math.PI) / 180;
              const r1 = 510;
              const r2 = i % 5 === 0 ? 528 : 520;
              return (
                <line
                  key={i}
                  x1={Math.cos(a) * r1}
                  y1={Math.sin(a) * r1}
                  x2={Math.cos(a) * r2}
                  y2={Math.sin(a) * r2}
                />
              );
            })}
          </g>
          {[12, 47, 88, 134, 180, 233, 290, 333].map((deg, i) => {
            const a = (deg * Math.PI) / 180;
            return (
              <circle
                key={i}
                cx={Math.cos(a) * 540}
                cy={Math.sin(a) * 540}
                r="1.4"
                fill="#E9C77A"
              />
            );
          })}
        </g>

        <circle cx="0" cy="0" r="480" fill="url(#globeFace)" />
        <circle cx="0" cy="0" r="480" fill="url(#globeRim)" />

        <g stroke="rgba(232,199,122,.18)" strokeWidth="0.6" fill="none">
          {[-60, -40, -20, 0, 20, 40, 60].map((lat, i) => {
            const ry = 480 * Math.cos((lat * Math.PI) / 180);
            const cy = 480 * Math.sin((lat * Math.PI) / 180);
            return (
              <ellipse
                key={i}
                cx="0"
                cy={cy}
                rx="480"
                ry={Math.abs(ry) * 0.18}
              />
            );
          })}
        </g>

        <g className="ring--rev" stroke="rgba(232,199,122,.16)" strokeWidth="0.6" fill="none">
          {[0, 18, 36, 54, 72, 90, 108, 126, 144, 162].map((lon, i) => {
            const rx = 480 * Math.abs(Math.cos((lon * Math.PI) / 180));
            return <ellipse key={i} cx="0" cy="0" rx={rx} ry="480" />;
          })}
        </g>

        <g fill="rgba(232,199,122,.14)" stroke="rgba(232,199,122,.35)" strokeWidth="0.5">
          <path d="M -180 -120 Q -120 -180 -60 -150 Q -10 -130 -40 -80 Q -90 -50 -160 -70 Q -200 -90 -180 -120 Z" />
          <path d="M 60 40 Q 130 10 180 60 Q 220 130 160 170 Q 90 180 50 130 Q 30 80 60 40 Z" />
          <path d="M -240 80 Q -200 60 -180 100 Q -170 150 -210 160 Q -250 140 -240 80 Z" />
          <path d="M 200 -180 Q 240 -200 280 -160 Q 290 -120 250 -100 Q 210 -120 200 -180 Z" />
        </g>

        <g className="ring" stroke="rgba(111,191,178,.5)" strokeWidth="0.4" fill="rgba(111,191,178,.7)">
          {[
            [-220, -180], [-160, -130], [-100, -160], [-40, -90],
            [120, -200], [180, -140], [260, -80], [300, -160],
            [-260, 40], [-180, 80], [-100, 60], [40, 140],
            [120, 180], [200, 120], [280, 180],
          ].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="1.6" />
          ))}
          <line x1="-220" y1="-180" x2="-160" y2="-130" />
          <line x1="-160" y1="-130" x2="-100" y2="-160" />
          <line x1="-100" y1="-160" x2="-40" y2="-90" />
          <line x1="120" y1="-200" x2="180" y2="-140" />
          <line x1="180" y1="-140" x2="260" y2="-80" />
          <line x1="-260" y1="40" x2="-180" y2="80" />
          <line x1="-180" y1="80" x2="-100" y2="60" />
          <line x1="40" y1="140" x2="120" y2="180" />
          <line x1="120" y1="180" x2="200" y2="120" />
        </g>

        <ellipse cx="0" cy="0" rx="480" ry="480" stroke="url(#brassStroke)" strokeWidth="1.2" fill="none" opacity=".7" />

        <g stroke="rgba(232,199,122,.15)" fill="none" strokeWidth="0.5">
          <ellipse cx="0" cy="0" rx="380" ry="120" transform="rotate(20)" />
          <ellipse cx="0" cy="0" rx="420" ry="160" transform="rotate(-25)" />
        </g>

        <g fill="none" strokeWidth="1.2" strokeLinecap="round">
          <path
            d="M -180 -100 Q -60 -260 100 -120"
            stroke="#E9C77A"
            opacity=".85"
            strokeDasharray="600"
            strokeDashoffset="600"
          >
            <animate attributeName="stroke-dashoffset" from="600" to="0" dur="3.5s" begin="0s" fill="freeze" />
            <animate attributeName="opacity" values="0;1;1;.4" dur="6s" begin="0s" repeatCount="indefinite" />
          </path>
          <path
            d="M 100 -120 Q 220 0 80 130"
            stroke="#6FBFB2"
            opacity=".7"
            strokeDasharray="600"
            strokeDashoffset="600"
          >
            <animate attributeName="stroke-dashoffset" from="600" to="0" dur="3.2s" begin="1.2s" fill="freeze" />
            <animate attributeName="opacity" values="0;.9;.9;.3" dur="6s" begin="1.2s" repeatCount="indefinite" />
          </path>
          <path
            d="M -200 80 Q -100 200 80 130"
            stroke="#c97a8a"
            opacity=".7"
            strokeDasharray="600"
            strokeDashoffset="600"
          >
            <animate attributeName="stroke-dashoffset" from="600" to="0" dur="3.4s" begin="2.4s" fill="freeze" />
            <animate attributeName="opacity" values="0;.9;.9;.3" dur="6s" begin="2.4s" repeatCount="indefinite" />
          </path>
        </g>

        {[[-180, -100], [100, -120], [80, 130], [-200, 80]].map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="3" fill="#E9C77A">
              <animate attributeName="r" values="3;7;3" dur="2.4s" begin={`${i * 0.6}s`} repeatCount="indefinite" />
              <animate attributeName="opacity" values="1;.2;1" dur="2.4s" begin={`${i * 0.6}s`} repeatCount="indefinite" />
            </circle>
            <circle cx={x} cy={y} r="1.6" fill="#fff1c8" />
          </g>
        ))}

        <g stroke="#E9C77A" strokeWidth="0.8" fill="none">
          <line x1="-8" y1="0" x2="8" y2="0" />
          <line x1="0" y1="-8" x2="0" y2="8" />
          <circle cx="0" cy="0" r="3" fill="#E9C77A" opacity=".4" />
        </g>
      </svg>
    </div>
  );
}

function Starfield() {
  const stars = useMemo(
    () =>
      Array.from({ length: 90 }).map(() => ({
        left: Math.random() * 100,
        top: Math.random() * 100,
        size: 0.8 + Math.random() * 1.6,
        op: 0.3 + Math.random() * 0.6,
        dur: (2.5 + Math.random() * 4).toFixed(2) + "s",
        delay: (Math.random() * 4).toFixed(2) + "s",
      })),
    [],
  );
  return (
    <div className="starfield" aria-hidden>
      {stars.map((s, i) => (
        <i
          key={i}
          style={{
            left: s.left + "%",
            top: s.top + "%",
            width: s.size + "px",
            height: s.size + "px",
            opacity: s.op,
            animation: `twinkle ${s.dur} ease-in-out ${s.delay} infinite`,
          }}
        />
      ))}
    </div>
  );
}

function BrassDust() {
  const motes = useMemo(
    () =>
      Array.from({ length: 24 }).map(() => ({
        left: Math.random() * 100,
        top: 50 + Math.random() * 60,
        dx: Math.random() * 40 - 20 + "px",
        dy: -(120 + Math.random() * 200) + "px",
        dur: 8 + Math.random() * 14 + "s",
        delay: -Math.random() * 14 + "s",
      })),
    [],
  );
  return (
    <div className="dust" aria-hidden>
      {motes.map((m, i) => (
        <i
          key={i}
          style={
            {
              left: m.left + "%",
              top: m.top + "%",
              "--dx": m.dx,
              "--dy": m.dy,
              animationDuration: m.dur,
              animationDelay: m.delay,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
}
