/** Projects: intentionally an empty state.
 *
 * The tables exist in Postgres but there are no project endpoints yet, so this
 * screen says exactly that rather than showing placeholder rows. An empty screen
 * is an invitation to act, or, when there is nothing to act on, a clear
 * statement of what is coming.
 */
export function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display font-semibold tracking-tight">Projects</h1>
        <p className="mt-1 text-base text-ink-2">
          Nothing here yet.
        </p>
      </div>

      <div className="rounded-panel border border-dashed border-line bg-surface p-8 text-center">
        <p className="text-base text-ink-2">
          The project and task tables are in the database, but the endpoints that
          read and write them are not built yet.
        </p>
        <p className="mt-2 font-mono text-micro uppercase text-ink-3">
          next: projects, tasks, comments
        </p>
      </div>
    </div>
  );
}
