/** Create an account, then sign straight in.
 *
 * Registration and sign-in are two API calls, so doing them back to back here
 * saves the person retyping what they just typed. New accounts get the member
 * role from the database default, which is why no role picker appears: letting
 * anyone choose admin at sign-up would make the role meaningless.
 */
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/Button";
import { Field } from "@/components/Field";
import { SystemStrip } from "@/components/SystemStrip";
import { ApiError, request } from "@/lib/api";
import { useAuth } from "@/auth/useAuth";
import type { User } from "@/types";

const MIN_PASSWORD = 8;

export function CreateAccountPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const tooShort = password.length > 0 && password.length < MIN_PASSWORD;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await request<User>("/users", {
        method: "POST",
        body: { email, full_name: fullName, password },
        anonymous: true,
      });
      await signIn(email, password);
      navigate("/", { replace: true });
    } catch (caught) {
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
            <h2 className="text-title font-semibold">Create account</h2>
            <p className="mt-1 text-small text-ink-2">
              You will join as a member. An admin can change that later.
            </p>

            <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
              <Field
                id="full-name"
                label="Full name"
                autoComplete="name"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
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
                autoComplete="new-password"
                required
                hint={`At least ${MIN_PASSWORD} characters.`}
                error={tooShort ? `Use at least ${MIN_PASSWORD} characters.` : undefined}
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

              <Button
                type="submit"
                disabled={busy || !fullName || !email || password.length < MIN_PASSWORD}
                className="w-full"
              >
                {busy ? "Creating account" : "Create account"}
              </Button>
            </form>
          </div>

          <p className="mt-4 text-small text-ink-2">
            Already have an account?{" "}
            <Link to="/sign-in" className="text-signal underline underline-offset-4">
              Sign in
            </Link>
          </p>
        </div>
      </div>
      <SystemStrip />
    </div>
  );
}
