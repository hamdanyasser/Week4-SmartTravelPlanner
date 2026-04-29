// Inline error pill — used when the backend returned a real error
// (not just an unreachable endpoint, which falls through to demo mode).

interface ErrorStateProps {
  message: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="error-state reveal" role="alert">
      <span className="error-state__icon" aria-hidden>
        !
      </span>
      <div>
        <div className="error-state__title">Briefing failed</div>
        <p className="error-state__body">{message}</p>
      </div>
    </div>
  );
}
