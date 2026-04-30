// Evidence drawer — a fixed mission-control rail at the bottom of the page.
// Closed by default (just the handle pokes up); opens to a teletype tool
// trace + run-meta grid. Mode LED shows live/demo/idle.

import { useState } from "react";
import type { ToolTraceEntry, TripBriefMeta } from "../api/types";
import type { BriefMode } from "../hooks/useTripBrief";

interface EvidenceDrawerProps {
  tools: ToolTraceEntry[];
  meta: TripBriefMeta;
  mode: BriefMode | null;
  startedAt: number | null;
  finishedAt: number | null;
}

function modeClass(mode: BriefMode | null): string {
  if (mode === "demo") return "demo";
  if (mode === "live" || mode === "live-stream") return "live";
  return "idle";
}

function modeLabel(mode: BriefMode | null): string {
  if (mode === "demo") return "Demo mode";
  if (mode === "live-stream") return "Live · streaming";
  if (mode === "live") return "Live agent";
  return "Standing by";
}

export function EvidenceDrawer({
  tools,
  meta,
  mode,
  startedAt,
  finishedAt,
}: EvidenceDrawerProps) {
  const [open, setOpen] = useState(false);
  const measured =
    startedAt !== null && finishedAt !== null ? finishedAt - startedAt : null;
  const latencyMs = measured ?? meta.latency_ms ?? 0;
  const latencyLabel = latencyMs > 0 ? `${(latencyMs / 1000).toFixed(2)}` : "—";

  return (
    <div
      className={"evidence" + (open ? " open" : "")}
      aria-label="Evidence drawer"
    >
      <button
        type="button"
        className="evidence__handle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="left">
          <span className="grip" aria-hidden />
          <span>Evidence drawer · raw tool trace</span>
        </span>
        <span className="led-row">
          <span className={`led-mode ${modeClass(mode)}`}>
            <span className="led-pill" aria-hidden />
            <span>{modeLabel(mode)}</span>
          </span>
          <span style={{ color: "var(--graphite-2)" }}>
            {open ? "▾ Close" : "▴ Open"}
          </span>
        </span>
      </button>

      {open && (
        <div className="evidence__body">
          <div className="evidence__col">
            <h6>Tools used · {tools.length} / 3 logged</h6>
            <div className="teletype">
              {tools.length === 0 ? (
                <div className="tt-empty">
                  No tool calls recorded for this run.
                </div>
              ) : (
                tools.map((row) => (
                  <div
                    key={row.tool}
                    className={"tt-row" + (mode === "demo" ? " demo" : "")}
                  >
                    <span className="led-mini" aria-hidden />
                    <span className="tool">{row.tool}</span>
                    <span className="summary">{row.summary}</span>
                    <span className="latency" />
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="evidence__col">
            <h6>Run meta · cost &amp; latency</h6>
            <div className="meta-grid">
              <div className="meta-cell">
                <div className="k">Tokens in</div>
                <div className="v">{meta.tokens_in.toLocaleString()}</div>
              </div>
              <div className="meta-cell">
                <div className="k">Tokens out</div>
                <div className="v">{meta.tokens_out.toLocaleString()}</div>
              </div>
              <div className="meta-cell">
                <div className="k">Cost</div>
                <div className="v">
                  ${meta.cost_usd.toFixed(4)} <em>USD</em>
                </div>
              </div>
              <div className="meta-cell">
                <div className="k">Latency</div>
                <div className="v">
                  {latencyLabel}
                  <em>s</em>
                </div>
              </div>
              <div className="meta-cell">
                <div className="k">Cheap model</div>
                <div className="v" style={{ fontSize: 13 }}>
                  {meta.cheap_model}
                </div>
              </div>
              <div className="meta-cell">
                <div className="k">Strong model</div>
                <div className="v" style={{ fontSize: 13 }}>
                  {meta.strong_model}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
