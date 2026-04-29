// The Evidence drawer — for technical / code-review credibility.
//
// Two columns:
//   left:  the actual tool trace returned by the agent (RAG retrieval
//          summary, ML classification, live conditions).
//   right: the cost / latency / model accounting from `meta`, plus a
//          webhook delivery indicator.
//
// Collapsed by default so it doesn't compete with the briefing's
// editorial sections, but opens to one click for a reviewer.

import { useState } from "react";
import type { TripBriefMeta, ToolTraceEntry } from "../api/types";
import type { BriefMode } from "../hooks/useTripBrief";

interface EvidenceDrawerProps {
  tools: ToolTraceEntry[];
  meta: TripBriefMeta;
  mode: BriefMode | null;
  startedAt: number | null;
  finishedAt: number | null;
}

function formatLatency(ms: number | null, latencyMeta: number): string {
  if (ms !== null && ms > 0) return `${ms} ms`;
  if (latencyMeta > 0) return `${latencyMeta} ms`;
  return "—";
}

export function EvidenceDrawer({
  tools,
  meta,
  mode,
  startedAt,
  finishedAt,
}: EvidenceDrawerProps) {
  const [open, setOpen] = useState(true);

  const measuredLatency =
    startedAt !== null && finishedAt !== null ? finishedAt - startedAt : null;

  return (
    <section className="evidence reveal reveal--d4" aria-label="Evidence">
      <button
        type="button"
        className="evidence__head"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="evidence__head-left">
          <span>◇</span>
          Evidence drawer · tool traces, cost, delivery
        </span>
        <span className="evidence__chevron" aria-hidden>
          ▸
        </span>
      </button>

      {open && (
        <div className="evidence__body">
          <div className="evidence__panel">
            <h4 className="evidence__panel-title">Tool trace</h4>
            {tools.length === 0 ? (
              <p
                style={{
                  margin: 0,
                  color: "var(--text-500)",
                  fontSize: 13,
                }}
              >
                No tool calls recorded for this run.
              </p>
            ) : (
              tools.map((t) => (
                <div className="tool-row" key={t.tool}>
                  <span className="tool-row__pin" aria-hidden />
                  <div>
                    <span className="tool-row__name">{t.tool}</span>
                    <span className="tool-row__summary">{t.summary}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="evidence__panel">
            <h4 className="evidence__panel-title">Run accounting</h4>
            <div className="metric-row">
              <span className="metric-row__label">Mode</span>
              <span className="metric-row__value metric-row__value--accent">
                {mode === "demo"
                  ? "Offline demo"
                  : mode === "live"
                  ? "Live agent"
                  : "—"}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-row__label">Cheap model</span>
              <span className="metric-row__value">{meta.cheap_model}</span>
            </div>
            <div className="metric-row">
              <span className="metric-row__label">Strong model</span>
              <span className="metric-row__value">{meta.strong_model}</span>
            </div>
            <div className="metric-row">
              <span className="metric-row__label">Tokens in / out</span>
              <span className="metric-row__value">
                {meta.tokens_in} / {meta.tokens_out}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-row__label">Cost</span>
              <span className="metric-row__value">
                {meta.cost_usd === 0
                  ? "$0.0000"
                  : `$${meta.cost_usd.toFixed(4)}`}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-row__label">Latency</span>
              <span className="metric-row__value">
                {formatLatency(measuredLatency, meta.latency_ms)}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-row__label">Webhook</span>
              <span className="metric-row__value">
                {mode === "demo" ? "Skipped (demo)" : "Best-effort, isolated"}
              </span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
