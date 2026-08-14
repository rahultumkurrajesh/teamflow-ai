/** A labelled input.
 *
 * The label is a real <label> tied to the input by id, so clicking it focuses
 * the field and screen readers announce the pair. Errors are wired with
 * aria-describedby and aria-invalid rather than only turning the border red,
 * because colour alone is not an error message.
 */
import type { InputHTMLAttributes } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  hint?: string;
  error?: string;
}

export function Field({ id, label, hint, error, ...rest }: Props) {
  // rest deliberately excludes className: this component owns its input styles.
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block font-mono text-micro uppercase text-ink-2"
      >
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`w-full rounded border bg-surface px-3 py-2 text-base text-ink
          placeholder:text-ink-3 focus:outline focus:outline-2 focus:outline-offset-0
          ${error ? "border-danger focus:outline-danger" : "border-line focus:outline-signal"}`}
        {...rest}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="text-small text-ink-3">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="text-small text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
