// Calm error thread — terracotta hairline, never an alarm. Used when the
// backend returns a real error (an unreachable endpoint falls through to
// demo mode and shows the demo banner instead).

interface ErrorStateProps {
  message: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="thread error reveal reveal--d2" role="alert">
      <span className="thread__dot" aria-hidden />
      <span>Briefing failed · {message}</span>
    </div>
  );
}
