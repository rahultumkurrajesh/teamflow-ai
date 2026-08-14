/** The system strip.
 *
 * A hairline status line pinned to the bottom of every screen, showing whether
 * the API is reachable and the x-request-id of the last response. Your backend
 * middleware already stamps that header on every request, so a person reporting
 * a problem can read the id off the screen and you can find the exact line in
 * the container log.
 *
 * Deliberately quiet: mono, small, low contrast, no animation beyond the colour
 * change of the status dot. It is instrumentation, not decoration.
 */
import { useEffect, useState } from "react";

import { getLastRequestId, ping } from "@/lib/api";

type Health = "checking" | "up" | "down";

const POLL_MS = 30_000;

export function SystemStrip({ trailing }: { trailing?: string }) {
  const [health, setHealth] = useState<Health>("checking");
  const [requestId, setRequestId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      const ok = await ping();
      if (cancelled) return;
      setHealth(ok ? "up" : "down");
      setRequestId(getLastRequestId());
    };

    void check();
    const timer = window.setInterval(check, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const dot =
    health === "up"
      ? "bg-signal"
      : health === "down"
        ? "bg-danger"
        : "bg-ink-3";

  const label =
    health === "up" ? "api up" : health === "down" ? "api unreachable" : "checking";

  return (
    <footer className="border-t border-line bg-paper/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-5 gap-y-1 px-6 py-2 font-mono text-micro uppercase text-ink-3">
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`}
            aria-hidden="true"
          />
          <span>{label}</span>
        </span>
        {requestId && (
          <span className="truncate">
            req {requestId.slice(0, 8)}
          </span>
        )}
        {trailing && <span className="truncate">{trailing}</span>}
      </div>
    </footer>
  );
}
