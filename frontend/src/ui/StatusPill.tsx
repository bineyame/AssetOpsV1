import "./status-pill.css";

/**
 * UQ-FI-3 (architect-sequence-client-scope-2026-11-11.md rev 7, 7.2): the one status pill for an outcome state, used by
 * the Portfolio and the Site board outcome rows. It maps the state code to the v7.2 sheet's chip look (colour + symbol);
 * the word is the server's `state_label`, never one written here. No `site_type` branch.
 *
 * Looks (D-UQFI.11): Needs attention, Opportunity, Watch and Not measured take exactly portfolio-hifi's looks, no added
 * symbol. On track takes the sheet's Complete look (filled circle). Unknown, No objective and N/A are plain neutral, no
 * symbol; the word tells them apart.
 */
export type StatusLook = "complete" | "partial" | "noreadings" | "notanalysed" | "neutral" | "accent";
type Glyph = "check" | null;

const LOOKS: Readonly<Record<string, { look: StatusLook; glyph: Glyph }>> = {
  NEEDS_ATTENTION: { look: "partial", glyph: null },
  WATCH: { look: "neutral", glyph: null },
  OPPORTUNITY: { look: "accent", glyph: null },
  ON_TRACK: { look: "complete", glyph: "check" },
  UNKNOWN: { look: "neutral", glyph: null },
  NOT_MEASURED: { look: "notanalysed", glyph: null },
  NO_OBJECTIVE: { look: "neutral", glyph: null },
  NOT_APPLICABLE: { look: "neutral", glyph: null },
};
const FALLBACK = { look: "neutral" as StatusLook, glyph: null };

/** The look for a state code; an unrecognised code reads neutral. */
export function statusLook(state: string): { look: StatusLook; glyph: Glyph } {
  return Object.prototype.hasOwnProperty.call(LOOKS, state) ? LOOKS[state] : FALLBACK;
}

function GlyphSvg({ glyph }: { glyph: Glyph }) {
  switch (glyph) {
    case "check":
      return (
        <svg className="status-pill__glyph" viewBox="0 0 12 12" aria-hidden="true" data-status-glyph="check">
          <circle cx="6" cy="6" r="5.5" fill="currentColor" />
          <path d="M3.5 6.2l1.7 1.6L8.6 4.4" fill="none" stroke="var(--status-pill-bg)" strokeWidth="1.6" />
        </svg>
      );
    default:
      return null;
  }
}

export function StatusPill({ state, label, className }: { state: string; label: string; className?: string }) {
  const { look, glyph } = statusLook(state);
  return (
    <span className={`status-pill s-${look}${className ? ` ${className}` : ""}`} data-status-pill={state}>
      <GlyphSvg glyph={glyph} />
      {label}
    </span>
  );
}
