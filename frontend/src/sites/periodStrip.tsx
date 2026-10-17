/**
 * W1-UX-03: a small period strip with readable text, for the Evidence and
 * Dispatch screens. Each row is one subject (a source, a needed reading, the
 * generator's blocks); each segment is a stretch of time the read itself
 * returned, placed on the period's own start and end. Nothing is inferred:
 * time the read did not cover is left blank, and a "not known" row is a
 * hatched mark with the words "not known", never an empty or zero bar.
 * Meaning never rests on colour: every row carries its own summary text and
 * the legend names every tone used.
 */
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import "./periodStrip.css";

export type StripTone = "covered" | "gap" | "problem" | "not-known" | "necessary" | "avoidable" | "undetermined" | "marker";

export interface StripSegment {
  key: string;
  /** ISO instants from the read. */
  start: string;
  end: string;
  tone: StripTone;
  /** Readable words for the segment (its accessible name when it is a link). */
  label: string;
  /** An exact selection link, e.g. one assessed block. */
  href?: string;
  selected?: boolean;
}

export interface StripRow {
  key: string;
  label: ReactNode;
  segments: readonly StripSegment[];
  /** Readable text for the row; required, so the graphic is never the only carrier. */
  summary: string;
  /** The whole row is not known: draw the hatched mark. */
  notKnown?: boolean;
}

export interface PeriodStripProps {
  name: string;
  title: string;
  /** The period's own bounds; when either is missing the rows show text only. */
  start: string | null;
  end: string | null;
  rows: readonly StripRow[];
  legend: readonly { tone: StripTone; label: string }[];
  /** Plain axis words, e.g. "08:00 UTC" and "14:00 UTC". */
  startText?: string;
  endText?: string;
}

function ms(instant: string | null): number | null {
  if (instant === null) return null;
  const n = Date.parse(instant);
  return Number.isFinite(n) ? n : null;
}

function place(segment: StripSegment, from: number, to: number): { left: number; width: number } | null {
  const s = ms(segment.start);
  const e = ms(segment.end);
  if (s === null || e === null || to <= from) return null;
  const a = Math.max(from, Math.min(to, s));
  const b = Math.max(from, Math.min(to, e));
  // A zero-length segment is an instant (a "latest taken" marker); it keeps a thin visible width.
  if (b < a || (b === a && s !== e)) return null;
  return { left: ((a - from) / (to - from)) * 100, width: Math.max(((b - a) / (to - from)) * 100, 0.75) };
}

export function PeriodStrip({ name, title, start, end, rows, legend, startText, endText }: PeriodStripProps) {
  const from = ms(start);
  const to = ms(end);
  const drawable = from !== null && to !== null && to > from;
  return (
    <figure className="period-strip" data-period-strip={name}>
      <figcaption className="period-strip__title">{title}</figcaption>
      <ul className="period-strip__rows">
        {rows.map((row) => (
          <li className="period-strip__row" key={row.key} data-period-strip-row={row.key} data-period-strip-known={row.notKnown ? "not-known" : "known"}>
            <span className="period-strip__label">{row.label}</span>
            {drawable ? (
              <span className="period-strip__track">
                {row.notKnown ? (
                  <span className="period-strip__unknown" aria-hidden="true" data-period-strip-mark="not-known" />
                ) : (
                  row.segments.map((segment) => {
                    const at = place(segment, from, to);
                    if (at === null) return null;
                    const style = { left: `${at.left}%`, width: `${at.width}%` };
                    const className = `period-strip__segment period-strip__segment--${segment.tone}${segment.selected ? " period-strip__segment--selected" : ""}`;
                    return segment.href === undefined ? (
                      <span key={segment.key} className={className} style={style} aria-hidden="true" data-period-strip-segment={segment.tone} />
                    ) : (
                      <Link
                        key={segment.key}
                        to={segment.href}
                        className={className}
                        style={style}
                        aria-label={segment.label}
                        aria-current={segment.selected ? "true" : undefined}
                        data-period-strip-segment={segment.tone}
                      />
                    );
                  })
                )}
              </span>
            ) : null}
            <span className="period-strip__summary">{row.summary}</span>
          </li>
        ))}
      </ul>
      {drawable && (startText !== undefined || endText !== undefined) ? (
        <p className="period-strip__axis" aria-hidden="true">
          <span>{startText}</span>
          <span>{endText}</span>
        </p>
      ) : null}
      {legend.length === 0 ? null : (
        <ul className="period-strip__legend" aria-label={`Key: ${legend.map((l) => l.label).join(", ")}`}>
          {legend.map((item) => (
            <li key={item.tone}>
              <span className={`period-strip__swatch period-strip__segment--${item.tone}`} aria-hidden="true" />
              {item.label}
            </li>
          ))}
        </ul>
      )}
    </figure>
  );
}
