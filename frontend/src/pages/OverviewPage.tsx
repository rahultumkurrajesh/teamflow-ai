/** Overview: the first screen after signing in.
 *
 * Honest about the state of the build. Projects and tasks do not have endpoints
 * yet, so instead of mocking cards full of invented data, this shows the real
 * account the API returned and what is wired up so far. An empty screen should
 * tell you where you are, not pretend to be full.
 */
import type { ReactNode } from "react";

import { RoleBadge } from "@/components/RoleBadge";
import { useAuth } from "@/auth/useAuth";

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 border-b border-line py-2.5 last:border-0">
      <dt className="w-32 shrink-0 font-mono text-micro uppercase text-ink-3">
        {label}
      </dt>
      <dd className="text-base text-ink">{value}</dd>
    </div>
  );
}

export function OverviewPage() {
  const { user } = useAuth();
  if (!user) return null;

  const joined = new Date(user.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-display font-semibold tracking-tight">
          {user.full_name.split(" ")[0] ?? user.full_name}
        </h1>
        <p className="mt-1 text-base text-ink-2">
          You are signed in. Projects and tasks arrive in the next stage.
        </p>
      </div>

      <section className="rounded-panel border border-line bg-surface p-6 shadow-panel">
        <h2 className="font-mono text-micro uppercase text-ink-3">Account</h2>
        <dl className="mt-3">
          <Row label="Name" value={user.full_name} />
          <Row label="Email" value={user.email} />
          <Row label="Role" value={<RoleBadge role={user.role} />} />
          <Row
            label="User id"
            value={<code className="font-mono text-small text-ink-2">{user.id}</code>}
          />
          <Row label="Joined" value={joined} />
        </dl>
      </section>
    </div>
  );
}
