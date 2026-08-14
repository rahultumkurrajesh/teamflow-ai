/** Design tokens for the blueprint direction.
 *
 * Every colour and size the UI uses is named here, so a component never
 * reaches for an arbitrary hex value. The palette is cool and low chroma on
 * purpose: this is an instrument panel, and the only saturated colour in the
 * system is reserved for the primary action and for state that needs attention.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces, coolest to warmest
        paper: "#EEF1F4", // app background, the drawing sheet
        surface: "#FFFFFF", // cards and panels
        line: "#D3DAE3", // hairline rules and borders
        // Ink, for text
        ink: "#111A22", // primary text
        "ink-2": "#465768", // secondary text
        "ink-3": "#7B8B9A", // captions and metadata
        // The one saturated family: deep teal for actions
        signal: {
          DEFAULT: "#155E63",
          hover: "#0F4A4E",
          soft: "#E3EDEE",
        },
        // Amber for role and state badges, never for actions
        state: {
          DEFAULT: "#8A5A11",
          soft: "#F6EEDF",
        },
        danger: {
          DEFAULT: "#8C2F26",
          soft: "#F7E7E5",
        },
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      fontSize: {
        // A deliberately short scale. Five sizes is enough for an app shell,
        // and a short scale is what keeps spacing consistent between screens.
        micro: ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.08em" }],
        small: ["0.8125rem", { lineHeight: "1.25rem" }],
        base: ["0.9375rem", { lineHeight: "1.5rem" }],
        title: ["1.375rem", { lineHeight: "1.75rem", letterSpacing: "-0.01em" }],
        display: ["2rem", { lineHeight: "2.25rem", letterSpacing: "-0.02em" }],
      },
      borderRadius: {
        // Small radii throughout. Blueprints have corners.
        DEFAULT: "3px",
        panel: "5px",
      },
      boxShadow: {
        panel: "0 1px 2px rgba(17, 26, 34, 0.06)",
        lift: "0 2px 10px rgba(17, 26, 34, 0.08)",
      },
    },
  },
  plugins: [],
};
