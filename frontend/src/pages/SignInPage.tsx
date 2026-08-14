/** Sign in.
 *
 * The form does no credential validation beyond "both fields filled", because
 * the only authority on whether a password is correct is the server. Guessing
 * client-side would just mean two sources of truth disagreeing.
 *
 * On success the person returns to wherever they were headed before the
 * redirect, which ProtectedRoute stashed in location state.
 */
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/Button";
import { Field } from "@/components/Field";
import { SystemStrip } from "@/components/SystemStrip";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/auth/useAuth";

export function SignInPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  if (user) return <Navigate to={from} replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await signIn(email, password);
      navigate(from, { replace: true });
    } catch (caught) {
      // The server returns one message for unknown email and wrong password, on
      // purpose, so this reflects that rather than inventing a more specific one.
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not reach the server. Check that the API is running.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-display font-semibold tracking-tight">TeamFlow</h1>
            <p className="mt-1 font-mono text-micro uppercase text-ink-3">
              project workspace
            </p>
          </div>

          <div className="rounded-panel border border-line bg-surface p-6 shadow-panel">
            <h2 className="text-title font-semibold">Sign in</h2>
            <p className="mt-1 text-small text-ink-2">
              Use the email and password for your workspace account.
            </p>

            <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
              <Field
                id="email"
                label="Email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Field
                id="password"
                label="Password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              {error && (
                <div
                  role="alert"
                  className="rounded border border-danger/30 bg-danger-soft px-3 py-2 text-small text-danger"
                >
                  {error}
                </div>
              )}

              <Button type="submit" disabled={busy || !email || !password} className="w-full">
                {busy ? "Signing in" : "Sign in"}
              </Button>
            </form>
          </div>

          <p className="mt-4 text-small text-ink-2">
            No account yet?{" "}
            <Link
              to="/create-account"
              className="text-signal underline underline-offset-4"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
      <SystemStrip />
    </div>
  );
}
