// The prompt input — modeled less as a form, more as a console.
//
// Glass panel with an "INTAKE" header strip, a serif text area for the
// query, smart example chips that prefill the textarea, and a single
// premium CTA. The chips are intentionally written as scenarios, not
// keywords, so a reviewer immediately understands what kinds of questions
// the agent answers.

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
    <form className="prompt reveal reveal--d1" onSubmit={handleSubmit}>
      <header className="prompt__head">
        <span className="prompt__head-left">
          <span className="prompt__sigil" aria-hidden />
          Intake // Trip Brief Console
        </span>
        <span className="prompt__head-right">
          {loading ? "Briefing in progress" : "Ready"}
        </span>
      </header>

      <div className="prompt__body">
        <textarea
          aria-label="Travel question"
          className="prompt__textarea"
          value={query}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your trip in plain words — month, budget, vibe, things you'd love or want to avoid…"
          rows={4}
          spellCheck
        />
      </div>

      <div className="prompt__chips" aria-label="Scenario presets">
        {SCENARIO_CHIPS.map((chip) => (
          <button
            type="button"
            className="prompt__chip"
            key={chip.label}
            onClick={() => onChange(chip.prompt)}
            disabled={loading}
          >
            <span className="prompt__chip-icon" aria-hidden>
              ◇
            </span>
            {chip.label}
          </button>
        ))}
      </div>

      <footer className="prompt__footer">
        <span className="prompt__hint">
          Cmd / Ctrl + Enter to submit · {query.trim().length} chars
        </span>
        <button type="submit" className="prompt__cta" disabled={loading}>
          {loading ? "Drafting brief…" : "Generate briefing"}
          <span className="prompt__cta-arrow" aria-hidden>
            →
          </span>
        </button>
      </footer>
    </form>
  );
}
