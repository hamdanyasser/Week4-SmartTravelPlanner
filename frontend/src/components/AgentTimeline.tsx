// Visual narrative of what the agent is doing.
//
// During a request the timeline animates through the seven stages every
// ~750ms (driven by useTripBrief) and stops one stage short of "done"; once
// the API responds, it jumps to the final stage. After the response, each
// completed stage shows a tick.
//
// The list is ordered to match the actual backend pipeline: extract intent
// (cheap model), three tool calls in the documented order, synthesis (strong
// model), and webhook delivery.

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
    label: "Resolving Dream vs Reality tension",
    sublabel: "Strong model · synthesis",
  },
  {
    key: "brief",
    label: "Drafting the executive brief",
    sublabel: "Strong model · structured output",
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

function formatRelative(elapsedMs: number): string {
  if (elapsedMs < 0) return "—";
  if (elapsedMs < 1000) return `${elapsedMs}ms`;
  return `${(elapsedMs / 1000).toFixed(2)}s`;
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

  return (
    <section className="timeline reveal reveal--d3" aria-label="Agent timeline">
      <header className="timeline__head">
        <span className="timeline__title">Agent · Mission Timeline</span>
        <span className="timeline__counter">
          {Math.min(activeStage, total)} / {total} ·{" "}
          {loading ? "Running" : finishedAt ? "Complete" : "Idle"}
        </span>
      </header>

      <ol className="timeline__list">
        {TIMELINE_STAGES.map((stage, i) => {
          const status =
            i < activeStage
              ? "done"
              : i === activeStage && (loading || activeStage < total)
              ? "active"
              : "pending";

          const matchedTool = tools?.find((t) => t.tool === stage.key);

          return (
            <li
              key={stage.key}
              className={
                status === "done"
                  ? "timeline__item timeline__item--done"
                  : status === "active"
                  ? "timeline__item timeline__item--active"
                  : "timeline__item timeline__item--pending"
              }
            >
              <span className="timeline__bullet" aria-hidden />
              <span>
                <span className="timeline__label">
                  {matchedTool ? matchedTool.summary : stage.label}
                </span>
                <span className="timeline__sublabel">{stage.sublabel}</span>
              </span>
              <span className="timeline__time">
                {status === "done" && elapsed !== null
                  ? formatRelative(
                      Math.round((elapsed * (i + 1)) / total),
                    )
                  : status === "active"
                  ? "…"
                  : ""}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
