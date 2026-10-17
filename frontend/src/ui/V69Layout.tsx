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
 * The per-screen description under a Site page's heading, from the v69 mock's
 * screen subtitles (`screens.js`). F2-F5 add their screens here; a mock subtitle
 * that states illustrative values (site ratings, a window) is not copied.
 */
export const SITE_SCREEN_DESCRIPTIONS = {
  foundation: "Definition, topology and controls · stored configuration for the period shown",
  readiness: "Definition, commissioning and gateway readiness",
  sld: "Foundation · single line diagram",
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
}

/**
 * The mock's Site page heading (W1-F1 fix round 1): the site name as the level-1
 * heading, a provenance badge beside it (`.prov-tag`), and the screen's
 * description below. Provenance is never status or health.
 */
export function SitePageHeader({ siteName, siteId, mode, description, headingId }: SitePageHeaderProps) {
  return (
    <PageHeader
      title={siteName}
      headingId={headingId}
      badge={
        <span className="prov-tag" data-site-provenance={mode ?? "not-read"}>
          {mode === undefined || mode === null ? siteId : `${mode} · ${siteId}`}
        </span>
      }
      subtitle={description}
    />
  );
}
