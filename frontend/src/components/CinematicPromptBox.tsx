// Trip Brief Console — modeled like a piece of mission-control hardware.
// The textarea is a serif teleprompter; the four chips are punched-card
// scenario presets; the CTA is a brushed-brass key.

interface CinematicPromptBoxProps {
  query: string;
  onChange: (next: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

const SCENARIO_CHIPS: Array<{ label: string; prompt: string }> = [
  {
    label: "Two weeks in July, $1,500, warm + hiking",
    prompt:
      "I have two weeks off in July and around $1,500. I want somewhere warm, not too touristy, and I like hiking. Where should I go, when should I book, and what should I expect?",
  },
  {
    label: "10 days in October, food + culture, $2,500",
    prompt:
      "Ten days in October, around $2,500, I want strong food and culture, museums and night markets, no big resorts. Where should I go and what should I plan around?",
  },
  {
    label: "Family trip in March, mild weather, $3,000",
    prompt:
      "We are a family of four, looking for a relaxing March trip with mild weather, easy logistics, and no long flights. Budget around $3,000.",
  },
  {
    label: "Solo trekking in September, $1,800",
    prompt:
      "Solo trip in September, $1,800, I want serious mountain trekking, low tourism, and a couple of cultural anchor cities at the start or end.",
  },
];

export function CinematicPromptBox({
  query,
  onChange,
  onSubmit,
  loading,
}: CinematicPromptBoxProps) {
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading || query.trim().length < 10) return;
    onSubmit();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (loading || query.trim().length < 10) return;
      onSubmit();
    }
  }

  return (
    <form
      className="glass section reveal reveal--d1"
      onSubmit={handleSubmit}
      aria-label="Trip Brief Console"
    >
      <header className="console__head">
        <span className="left">
          <span
            className="led"
            style={
              loading
                ? {
                    background: "#E9C77A",
                    boxShadow:
                      "0 0 0 3px rgba(232,199,122,.18), 0 0 10px #E9C77A",
                  }
                : undefined
            }
          />
          <span>02 · Intake // Trip Brief Console</span>
        </span>
        <span className="right">
          <span>{loading ? "Drafting" : "Ready"}</span>
        </span>
      </header>

      <div className="console__body">
        <div className="prompt-input">
          <textarea
            aria-label="Travel question"
            className="prompt-textarea"
            value={query}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your trip in plain words — month, budget, vibe, things you'd love or want to avoid…"
            rows={5}
            spellCheck
          />
          <div className="prompt-ruler">
            <span>
              {query.trim().length} chars · auto-parsed into Trip DNA
            </span>
            <span className="kbd">
              <kbd>⌘</kbd>
              <kbd>↵</kbd>
              <span>&nbsp;Submit briefing</span>
            </span>
          </div>
        </div>

        <aside className="console__aside">
          <h4>Scenario presets</h4>
          <div className="chips">
            {SCENARIO_CHIPS.map((chip, i) => (
              <button
                type="button"
                className="chip"
                key={chip.label}
                onClick={() => onChange(chip.prompt)}
                disabled={loading}
              >
                <span className="chip__num">
                  · {String(i + 1).padStart(2, "0")}
                </span>
                <span className="chip__punch" aria-hidden />
                <span>{chip.label}</span>
              </button>
            ))}
          </div>
        </aside>
      </div>

      <footer className="cta-row">
        <span className="helper-line">
          ⌘/Ctrl + ↵ to submit · the agent thinks in public for ~4 seconds
        </span>
        <button type="submit" className="brass-key" disabled={loading}>
          {loading ? "Drafting briefing…" : "Generate briefing"}
          <span className="arrow" aria-hidden>
            →
          </span>
        </button>
      </footer>
    </form>
  );
}
