import type { ReactNode } from "react";

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
  /** Extra attributes for tests and evidence, e.g. `{ "data-site-metric": "count" }`. */
  data?: Record<string, string>;
}

/** The mock's `.metric`: label, one large value, one note. */
export function MetricCard({ label, value, note, tone, word = false, data }: MetricCardProps) {
  const className = ["v69-metric", word ? "v69-metric--word" : "", tone ? `v69-metric--${tone}` : ""]
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

/** The mock's `.statusbar`: one line of state badges and short facts; not a panel. */
export function StatusBar({
  children,
  label,
  data,
}: {
  children: ReactNode;
  /** Accessible name of the status line. */
  label?: string;
  data?: Record<string, string>;
}) {
  return (
    <div className="v69-statusbar" role="group" aria-label={label} {...data}>
      {children}
    </div>
  );
}

/**
 * The mock's `.big-claim`: the one answer sentence inside its owning panel.
 * Rendered as an h3 by default so it stays a findable heading without adding
 * an h2 panel slot.
 */
export function BigClaim({
  children,
  as = "h3",
  data,
}: {
  children: ReactNode;
  as?: "h3" | "p";
  data?: Record<string, string>;
}) {
  const Tag = as;
  return (
    <Tag className="v69-big-claim" {...data}>
      {children}
    </Tag>
  );
}

/** The mock's `.notice` (amber by default, `blue` for an informational note). */
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
    <div className={tone === "blue" ? "v69-notice v69-notice--blue" : "v69-notice"} {...data}>
      {children}
    </div>
  );
}
