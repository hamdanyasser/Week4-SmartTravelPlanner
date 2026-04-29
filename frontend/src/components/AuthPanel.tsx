// AuthPanel — minimal sign-in surface tucked above the prompt console.
//
// AtlasBrief works anonymously by design (the trip-brief route accepts
// anonymous users for the demo), so this panel is small and collapsible.
// When signed in, the JWT is attached to subsequent /api/v1/trip-briefs
// requests so each run is associated with a user in Postgres.

import { useState } from "react";
import type { AuthState } from "../hooks/useAuth";

interface AuthPanelProps {
  auth: AuthState;
}

type Mode = "login" | "register";

export function AuthPanel({ auth }: AuthPanelProps) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLocalError(null);
    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters.");
      return;
    }
    try {
      if (mode === "login") {
        await auth.login(email.trim().toLowerCase(), password);
      } else {
        await auth.register(email.trim().toLowerCase(), password);
      }
      setPassword("");
      setOpen(false);
    } catch {
      // useAuth already populated auth.error.
    }
  };

  if (auth.token) {
    return (
      <section className="auth-pill" aria-label="Signed in">
        <span className="auth-pill__dot" aria-hidden />
        Signed in as <strong>{auth.email ?? "user"}</strong>
        <button
          type="button"
          className="auth-pill__sign-out"
          onClick={auth.signOut}
        >
          Sign out
        </button>
      </section>
    );
  }

  if (!open) {
    return (
      <section className="auth-pill" aria-label="Sign in">
        <span className="auth-pill__dot auth-pill__dot--anon" aria-hidden />
        Browsing anonymously
        <button
          type="button"
          className="auth-pill__sign-out"
          onClick={() => {
            setMode("login");
            setOpen(true);
          }}
        >
          Sign in
        </button>
        <button
          type="button"
          className="auth-pill__sign-out"
          onClick={() => {
            setMode("register");
            setOpen(true);
          }}
        >
          Register
        </button>
      </section>
    );
  }

  return (
    <section className="auth-form" aria-label="AtlasBrief credentials">
      <header className="auth-form__head">
        <span className="auth-form__eyebrow">
          {mode === "login" ? "SIGN IN" : "CREATE ACCOUNT"}
        </span>
        <button
          type="button"
          className="auth-form__close"
          onClick={() => setOpen(false)}
          aria-label="Close"
        >
          ×
        </button>
      </header>

      <form className="auth-form__body" onSubmit={submit}>
        <label className="auth-form__label">
          Email
          <input
            className="auth-form__input"
            type="email"
            value={email}
            autoComplete="email"
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
          />
        </label>
        <label className="auth-form__label">
          Password
          <input
            className="auth-form__input"
            type="password"
            value={password}
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            placeholder="At least 8 characters"
          />
        </label>

        {(localError || auth.error) && (
          <p className="auth-form__error">{localError ?? auth.error}</p>
        )}

        <div className="auth-form__row">
          <button
            type="submit"
            className="auth-form__submit"
            disabled={auth.loading}
          >
            {auth.loading
              ? "Working…"
              : mode === "login"
              ? "Sign in"
              : "Register"}
          </button>
          <button
            type="button"
            className="auth-form__switch"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login"
              ? "Need an account? Register"
              : "Have an account? Sign in"}
          </button>
        </div>
      </form>
    </section>
  );
}
