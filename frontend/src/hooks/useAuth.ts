// Tiny auth hook: persists the JWT in localStorage and exposes the
// current "auth header" so the trip-brief client can attach it on demand.
//
// Anonymous use is still supported - the token is just absent. When the
// user signs in, every later trip brief is associated with their account
// in Postgres (visible in agent_runs.user_id and tool_calls.user_id).

import { useCallback, useEffect, useState } from "react";

const TOKEN_STORAGE_KEY = "atlasbrief.access_token";
const EMAIL_STORAGE_KEY = "atlasbrief.user_email";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface AuthState {
  token: string | null;
  email: string | null;
  loading: boolean;
  error: string | null;
  register: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  authHeader: () => Record<string, string>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = String(data.detail);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export function useAuth(): AuthState {
  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined"
      ? window.localStorage.getItem(TOKEN_STORAGE_KEY)
      : null,
  );
  const [email, setEmail] = useState<string | null>(() =>
    typeof window !== "undefined"
      ? window.localStorage.getItem(EMAIL_STORAGE_KEY)
      : null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (email) {
      window.localStorage.setItem(EMAIL_STORAGE_KEY, email);
    } else {
      window.localStorage.removeItem(EMAIL_STORAGE_KEY);
    }
  }, [email]);

  const login = useCallback(async (loginEmail: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await postJson<{ access_token: string }>("/auth/login", {
        email: loginEmail,
        password,
      });
      setToken(data.access_token);
      setEmail(loginEmail);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(
    async (registerEmail: string, password: string) => {
      setLoading(true);
      setError(null);
      try {
        await postJson<unknown>("/auth/register", {
          email: registerEmail,
          password,
        });
        // Auto-login on a successful register so the briefing flow stays
        // single-step for the demo.
        await login(registerEmail, password);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [login],
  );

  const signOut = useCallback(() => {
    setToken(null);
    setEmail(null);
  }, []);

  const authHeader = useCallback((): Record<string, string> => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  return { token, email, loading, error, register, login, signOut, authHeader };
}
