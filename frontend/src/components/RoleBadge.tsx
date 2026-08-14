/** Role, set in mono because it is system metadata rather than prose. */
import type { Role } from "@/types";

export function RoleBadge({ role }: { role: Role }) {
  const tone =
    role === "admin" ? "bg-state-soft text-state" : "bg-signal-soft text-signal";
  return (
    <span
      className={`rounded px-1.5 py-0.5 font-mono text-micro uppercase ${tone}`}
    >
      {role}
    </span>
  );
}
