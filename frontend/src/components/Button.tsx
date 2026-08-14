/** Buttons. Two intents only: primary for the one action a screen is for, quiet
 *  for everything else. A screen with two primary buttons has no primary action.
 */
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  intent?: "primary" | "quiet";
  children: ReactNode;
}

const BASE =
  "inline-flex items-center justify-center rounded px-4 py-2 text-small font-medium " +
  "transition-colors duration-100 focus-visible:outline focus-visible:outline-2 " +
  "focus-visible:outline-offset-2 focus-visible:outline-signal " +
  "disabled:cursor-not-allowed disabled:opacity-50 motion-reduce:transition-none";

const INTENT = {
  primary: "bg-signal text-white hover:bg-signal-hover",
  quiet: "border border-line bg-surface text-ink hover:bg-paper",
} as const;

export function Button({
  intent = "primary",
  className = "",
  children,
  ...rest
}: Props) {
  // className is merged rather than spread over: putting {...rest} after a
  // className attribute would silently discard every base style.
  return (
    <button className={`${BASE} ${INTENT[intent]} ${className}`} {...rest}>
      {children}
    </button>
  );
}
