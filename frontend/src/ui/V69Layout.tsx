import type { ReactNode } from "react";

import { PageHeader } from "./PageHeader";

/**
 * The v69 mock's layout patterns as shared components
 * (`D-2026-10-17-mockup-layout-spec`; CSS in `primitives.css`, "v69 layout
 * patterns"). They carry structure only: every value comes from the screen's
 * selected read, and a value the read cannot support is passed as an honest gap.
 *
 * None of these is a panel. The panel set of a screen is fixed by the v69
 * entry and checked by `src/test/panelStructure.ts`; a metric row or a
 * key-value list never adds a panel slot.
 */

export type MetricTone = "green" | "amber" | "red" | "muted";

export interface MetricCardProps {
  label: ReactNode;
  value: ReactNode;
  note?: ReactNode;
  tone?: MetricTone;
  /** A word value (state, gap) is set smaller, as the mock's assessment metric. */
  word?: boolean;
  /**
   * The mock's `.metric.assessment`: a 3 px top border in the tone colour and a
   * 17 px state word as the value (implies `word`). The value text keeps the
   * body colour; the tone is carried by the border and by the word itself.
   */
  assessment?: boolean;
  /** Extra attributes for tests and evidence, e.g. `{ "data-site-metric": "count" }`. */
  data?: Record<string, string>;
}

/** The mock's `.metric`: label, one large value, one note. */
export function MetricCard({ label, value, note, tone, word = false, assessment = false, data }: MetricCardProps) {
  const className = [
    "v69-metric",
    word || assessment ? "v69-metric--word" : "",
    assessment ? "v69-metric--assessment" : "",
    tone ? `v69-metric--${tone}` : "",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <li className={className} {...data}>
      <div className="v69-metric__label">{label}</div>
      <div className="v69-metric__value">{value}</div>
      {note === undefined ? null : <div className="v69-metric__note">{note}</div>}
    </li>
  );
}

/** The mock's `.cards` row (4 by default; `three` or `five` columns). */
export function MetricCards({
  columns = 4,
  label,
  children,
  data,
}: {
  columns?: 3 | 4 | 5;
  /** Accessible name of the list. */
  label: string;
  children: ReactNode;
  data?: Record<string, string>;
}) {
  const className = ["v69-cards", columns === 3 ? "v69-cards--three" : columns === 5 ? "v69-cards--five" : ""]
    .filter(Boolean)
    .join(" ");
  return (
    <ul className={className} aria-label={label} {...data}>
      {children}
    </ul>
  );
}

/**
 * The mock's `mheader`: a bordered row of labelled cells (Owner, Due / SLA, State,
 * Source, Success criterion) between a status strip and the metric cards. A cell
 * the read cannot support is passed as its gap word, never omitted.
 */
export function MetricHeader({ cells, label, data }: { cells: [ReactNode, ReactNode, string?][]; label: string; data?: Record<string, string> }) {
  return (
    <dl className="v69-mheader" aria-label={label} {...data}>
      {cells.map(([term, value, key], index) => (
        <div key={key ?? index} data-mheader-cell={key}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

/** The mock's `.key-values`: term left, value right. */
export function KeyValues({ rows, label }: { rows: [ReactNode, ReactNode, string?][]; label?: string }) {
  return (
    <dl className="v69-key-values" aria-label={label}>
      {rows.map(([term, value, key], index) => (
        <div key={key ?? index} data-key-value={key}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export interface AttentionItem {
  key: string;
  title: ReactNode;
  body: ReactNode;
  action?: ReactNode;
}

/** The mock's numbered `.attention-item` list. */
export function AttentionList({ items, label }: { items: AttentionItem[]; label?: string }) {
  return (
    <ol className="v69-attention" aria-label={label}>
      {items.map((item, index) => (
        <li className="v69-attention__item" key={item.key} data-attention-item={item.key}>
          <span className="v69-attention__rank" aria-hidden="true">
            {index + 1}
          </span>
          <div>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
            {item.action ?? null}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** The mock's `.chart-note`: a small caption line under a visual or list. */
export function ChartNote({ children, data }: { children: ReactNode; data?: Record<string, string> }) {
  return (
    <p className="v69-chart-note" {...data}>
      {children}
    </p>
  );
}

/**
 * The mock's `.big-claim`: the one concise answer line inside its owning
 * panel, only where the mock shows one (e.g. finding:1). A paragraph;
 * it never stands in for a former panel or answer card.
 */
export function BigClaim({
  children,
  data,
}: {
  children: ReactNode;
  data?: Record<string, string>;
}) {
  return (
    <p className="v69-big-claim" {...data}>
      {children}
    </p>
  );
}

/** The mock's `.notice` (amber by default, `blue` for an informational note or neutral pointer). */
export function Notice({
  children,
  tone = "amber",
  data,
}: {
  children: ReactNode;
  tone?: "amber" | "blue";
  data?: Record<string, string>;
}) {
  return (
    <div className={tone === "blue" ? "notice v69-notice v69-notice--blue" : "notice v69-notice"} {...data}>
      {children}
    </div>
  );
}

/**
 * The mock's `.statusbar`: one state line above the panels (not a panel). It
 * renders F1's `.status-strip--line`, so the guard's strip rules apply: every
 * child must be inline (spans, links, a chip-sized control), never a block.
 * Pass a `ProductStatus inline` for a state line.
 */
export function StatusBar({
  children,
  label,
  items = false,
  other,
  action,
  data,
}: {
  children: ReactNode;
  /** Accessible name of the status line (W1-F3). */
  label?: string;
  /**
   * W1-F3: the children are the strip's own items (chips, a spacer, a trailing
   * fact), laid out by the strip's gap, instead of one lead state line.
   */
  items?: boolean;
  other?: ReactNode;
  action?: ReactNode;
  data?: Record<string, string>;
}) {
  return (
    <div className="status-strip status-strip--line v69-statusbar" role="status" aria-label={label} {...data}>
      {items ? children : <span className="status-strip__lead">{children}</span>}
      {other === undefined ? null : <span className="status-strip__item v69-statusbar__other">{other}</span>}
      {items ? null : <span className="status-strip__spacer" aria-hidden="true" />}
      {action === undefined ? null : <span className="status-strip__action">{action}</span>}
    </div>
  );
}

/** W1-F2's name for the same `.notice` (one implementation: `Notice`). */
export const V69Notice = Notice;

export interface TimelineEvent {
  key: string;
  time: ReactNode;
  title: ReactNode;
  detail?: ReactNode;
  tone?: "danger" | "gap";
}

/** The mock's causal `.timeline` strip: time, event, source in sequence. */
export function CausalTimeline({ events, label }: { events: TimelineEvent[]; label: string }) {
  return (
    <ol className="v69-timeline" aria-label={label}>
      {events.map((event) => (
        <li
          key={event.key}
          className={["v69-timeline__event", event.tone ? `v69-timeline__event--${event.tone}` : ""]
            .filter(Boolean)
            .join(" ")}
          data-timeline-event={event.key}
        >
          <span>{event.time}</span>
          <strong>{event.title}</strong>
          {event.detail === undefined ? null : <span>{event.detail}</span>}
        </li>
      ))}
    </ol>
  );
}

/**
 * The per-screen description under a Site page's heading, from the v69 mock's
 * screen subtitles (`screens.js`). F2-F5 add their screens here; a mock subtitle
 * that states illustrative values (site ratings, a window) is not copied.
 */
export const SITE_SCREEN_DESCRIPTIONS = {
  foundation: "Definition, topology and controls · stored configuration for the period shown",
  readiness: "Definition, commissioning and gateway readiness",
  sld: "Foundation · single line diagram",
  mini: "Overview · operating objectives for the selected period",
  dispatch: "Performance · source coordination and generator support",
  analysis: "Performance · analytical method, input comparison and uncertainty",
  // The mock's "capability readiness and claim ceilings" is not read here (no capability assessment; "claim" is on the
  // W1 vocabulary list, D-2026-10-16-w1-ux), so the description says what the page does show.
  evidence: "Evidence · accepted readings and what is missing",
  "evidence-analysis": "Evidence · accepted records and how limits are set",
  changes: "Configuration change · the stored policy change and its decision path",
  sitework: "Site-scoped work · the same managed records as global queues",
  recommendation: "Proposed intervention and declared success criterion",
  action: "Current intervention and outcome state",
  verification: "Target and guardrails · outcome from accepted evidence",
  // W2-01: the cold screens' mock subtitle states illustrative ratings and a policy band, so only its shape is kept.
  "cold-foundation": "Cold room · stored configuration for the period shown",
  "cold-readiness": "Definition, commissioning and gateway readiness",
  "cold-sld": "Cold room · single line diagram",
  // W1-F5a: Health and the carry-1 site-level screens (sitefindings, financials, assumptions).
  health: "Health · site-level asset-condition summary",
  sitefindings: "Findings · conclusions about this site and the limits of their evidence",
  financials: "Financials · what the site's technical behaviour means in money",
  assumptions: "Financials · assumptions and their history",
} as const;

export interface SitePageHeaderProps {
  /** The site's display name from the read; the route's Site ID when the name is unknown. */
  siteName: string;
  /** The Site ID shown in the provenance badge. */
  siteId: string;
  /** The read's source mode label (e.g. "Demonstration data"); omitted when not read. */
  mode?: string | null;
  /** The screen description, usually from `SITE_SCREEN_DESCRIPTIONS`. */
  description: ReactNode;
  headingId?: string;
  /** Omit the provenance badge, e.g. on a refusal where the Site ID would only repeat the title. */
  hideBadge?: boolean;
}

/**
 * The mock's Site page heading (W1-F1 fix round 1): the site name as the level-1
 * heading, a provenance badge beside it (`.prov-tag`), and the screen's
 * description below. Provenance is never status or health.
 */
export function SitePageHeader({ siteName, siteId, mode, description, headingId, hideBadge = false }: SitePageHeaderProps) {
  return (
    <PageHeader
      title={siteName}
      headingId={headingId}
      badge={
        hideBadge ? undefined : (
          <span className="prov-tag" data-site-provenance={mode ?? "not-read"}>
            {mode === undefined || mode === null ? siteId : `${mode} · ${siteId}`}
          </span>
        )
      }
      subtitle={description}
    />
  );
}
