/** Unknown route. States what happened and offers the one useful way out. */
import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md py-16 text-center">
      <p className="font-mono text-micro uppercase text-ink-3">404</p>
      <h1 className="mt-2 text-title font-semibold">This page does not exist</h1>
      <p className="mt-2 text-base text-ink-2">
        The link may be out of date, or the section may not be built yet.
      </p>
      <Link
        to="/"
        className="mt-6 inline-block text-base text-signal underline underline-offset-4"
      >
        Back to overview
      </Link>
    </div>
  );
}
