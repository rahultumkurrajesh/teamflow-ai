/** Gate for signed-in routes.
 *
 * Three states, not two. While the boot-time session check is still running the
 * answer is "not yet", and rendering a redirect during that window is the bug
 * that logs returning users out on every refresh.
 *
 * The attempted path is passed along in location state so sign-in can return
 * the person to where they were going instead of dumping them on a dashboard.
 */
import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "@/auth/useAuth";
import type { Role } from "@/types";

const RANK: Record<Role, number> = { member: 0, admin: 1 };

interface Props {
  children: ReactNode;
  /** Minimum role. Mirrors require_role on the backend, and is a convenience
   *  for the interface only: the server is still the thing enforcing it. */
  minRole?: Role;
}

export function ProtectedRoute({ children, minRole }: Props) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <p className="font-mono text-micro uppercase text-ink-3">
          Checking session
        </p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />;
  }

  if (minRole && RANK[user.role] < RANK[minRole]) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
