// AuthPanel — a glass capsule in the topbar that slides down a glass shelf
// when the user wants to sign in or register. Anonymous use is supported by
// the backend, so this stays out of the user's way until they ask.

import { useEffect, useState } from "react";
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

  // Escape closes the open form so the keyboard user can dismiss it.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

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
      // useAuth populated auth.error.
    }
  };

  if (auth.token) {
    return (
      <div className="auth-pill" aria-label="Signed in">
        <span className="auth-pill__label">
          <span className="auth-pill__dot" aria-hidden />
          <span>
            Signed in · <strong>{auth.email ?? "user"}</strong>
          </span>
        </span>
        <button type="button" onClick={auth.signOut}>
          Sign out
        </button>
      </div>
    );
  }

  if (!open) {
    return (
      <div className="auth-pill" aria-label="Authentication">
        <span className="auth-pill__label">
          <span className="auth-pill__dot auth-pill__dot--anon" aria-hidden />
          <span>Anonymous</span>
        </span>
        <button
          type="button"
          onClick={() => {
            setMode("login");
            setOpen(true);
          }}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("register");
            setOpen(true);
          }}
        >
          Register
        </button>
      </div>
    );
  }

  return (
    <section className="auth-form" aria-label="AtlasBrief credentials">
      <header className="auth-form__head">
        <span className="auth-form__eyebrow">
          {mode === "login" ? "Sign in" : "Create account"}
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
            autoComplete={mode === "login" ? "current-password" : "new-password"}
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
            {mode === "login" ? "Need an account?" : "Have an account?"}
          </button>
        </div>
      </form>
    </section>
  );
}
