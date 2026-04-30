// Mission Timeline — a brass rail with seven station stops, a moving spark
// during work, a warm trail behind completed stages, an engraved tick on
// done stages, and a stopwatch on the right.
//
// The seven stages are exact and ordered to match the backend pipeline:
//   intent extraction → 3 tools (RAG, ML, live) → synthesis → drafting →
//   webhook delivery.

import type { ToolTraceEntry } from "../api/types";

export interface TimelineStage {
  key: string;
  label: string;
  sublabel: string;
}

export const TIMELINE_STAGES: TimelineStage[] = [
  {
    key: "intake",
    label: "Understanding the request",
    sublabel: "Cheap model · intent extraction",
  },
  {
    key: "retrieve_destination_knowledge",
    label: "Retrieving destination knowledge",
    sublabel: "Tool · pgvector RAG",
  },
  {
    key: "classify_travel_style",
    label: "Classifying travel style",
    sublabel: "Tool · ML pipeline",
  },
  {
    key: "fetch_live_conditions",
    label: "Checking live conditions",
    sublabel: "Tool · weather + flights",
  },
  {
    key: "tension",
    label: "Resolving Dream vs Reality",
    sublabel: "Strong model · synthesis",
  },
  {
    key: "brief",
    label: "Drafting the executive brief",
    sublabel: "Strong model · structured",
  },
  {
    key: "webhook",
    label: "Delivering the webhook copy",
    sublabel: "Async · isolated failure",
  },
];

interface AgentTimelineProps {
  activeStage: number;
  loading: boolean;
  tools?: ToolTraceEntry[];
  startedAt: number | null;
  finishedAt: number | null;
}

export function AgentTimeline({
  activeStage,
  loading,
  tools,
  startedAt,
  finishedAt,
}: AgentTimelineProps) {
  const total = TIMELINE_STAGES.length;
  const elapsed =
    startedAt !== null && finishedAt !== null
      ? finishedAt - startedAt
      : startedAt !== null
      ? Date.now() - startedAt
      : null;

  const status = loading
    ? "Running"
    : finishedAt
    ? "Complete"
    : "Standing by";

  const sparkIdx = Math.min(activeStage, total - 1);
  const sparkPct = ((sparkIdx + 0.5) / total) * 100;
  const trailPct = (Math.min(activeStage, total) / total) * 100;
  const showSpark = loading || activeStage > 0;

  return (
    <section
      className="glass section reveal reveal--d3"
      aria-label="Agent mission timeline"
    >
      <div className="rail-wrap">
        <div className="rail-head">
          <div>
            <div className="section__rail" style={{ margin: 0 }}>
              <span className="num">04</span>
              <span
                className="div"
                style={{ flex: "0 0 80px" }}
                aria-hidden
              />
              <span className="tag">Agent · Mission Timeline</span>
            </div>
            <div className="title">The agent thinking, in public.</div>
          </div>
          <div className="meter">
            <span>
              {Math.min(activeStage, total)} / {total}
            </span>
            <span
              style={{
                color:
                  status === "Running"
                    ? "var(--brass-3)"
                    : status === "Complete"
                    ? "var(--verdigris-3)"
                    : "var(--graphite-2)",
              }}
            >
              · {status}
            </span>
            <span className="stopwatch">
              {elapsed !== null ? `${(elapsed / 1000).toFixed(2)}s` : "—"}
            </span>
          </div>
        </div>

        <div className="rail">
          <div className="rail__track" />
          <div className="rail__trail" style={{ width: `${trailPct}%` }} />
          {showSpark && (
            <div className="rail__spark" style={{ left: `${sparkPct}%` }} />
          )}
          <div className="rail__stops">
            {TIMELINE_STAGES.map((stage, i) => {
              const status =
                i < activeStage
                  ? "done"
                  : i === activeStage && (loading || activeStage < total)
                  ? "active"
                  : "pending";
              const matchedTool = tools?.find((t) => t.tool === stage.key);
              return (
                <div key={stage.key} className={`stop ${status}`}>
                  <span className="stop__num">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="stop__bullet" aria-hidden />
                  <span className="stop__caption">
                    <span className="lbl">
                      {matchedTool ? matchedTool.summary : stage.label}
                    </span>
                    <span className="sub">{stage.sublabel}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
