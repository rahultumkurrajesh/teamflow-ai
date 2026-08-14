/** Frame for every signed-in screen: masthead, content, system strip.
 *
 * The masthead carries the product name, the current user with their role, and
 * sign out. Navigation is a single row of links rather than a sidebar, because
 * at four sections a sidebar is a container looking for content.
 */
import { NavLink, Outlet } from "react-router-dom";

import { RoleBadge } from "@/components/RoleBadge";
import { SystemStrip } from "@/components/SystemStrip";
import { useAuth } from "@/auth/useAuth";

const NAV = [
  { to: "/", label: "Overview" },
  { to: "/projects", label: "Projects" },
] as const;

export function AppShell() {
  const { user, signOut } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-baseline gap-3">
            <span className="text-title font-semibold tracking-tight">
              TeamFlow
            </span>
            <span className="font-mono text-micro uppercase text-ink-3">
              project workspace
            </span>
          </div>

          {user && (
            <div className="flex items-center gap-3">
              <span className="hidden text-small text-ink-2 sm:inline">
                {user.full_name}
              </span>
              <RoleBadge role={user.role} />
              <button
                onClick={signOut}
                className="rounded px-2 py-1 text-small text-ink-2 underline decoration-line
                  underline-offset-4 hover:text-ink focus-visible:outline focus-visible:outline-2
                  focus-visible:outline-offset-2 focus-visible:outline-signal"
              >
                Sign out
              </button>
            </div>
          )}
        </div>

        <nav className="mx-auto max-w-5xl px-6">
          <ul className="flex gap-6">
            {NAV.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    `-mb-px inline-block border-b-2 py-2 text-small transition-colors duration-100
                     motion-reduce:transition-none focus-visible:outline focus-visible:outline-2
                     focus-visible:outline-offset-2 focus-visible:outline-signal ${
                       isActive
                         ? "border-signal text-ink"
                         : "border-transparent text-ink-2 hover:text-ink"
                     }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        <Outlet />
      </main>

      <SystemStrip trailing={user ? `role ${user.role}` : undefined} />
    </div>
  );
}
