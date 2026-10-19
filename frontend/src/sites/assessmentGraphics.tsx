/**
 * The four assessment graphics of T028 presentation checkpoint 2
 * (D-2026-10-04-plain-language-analysis-views, spec section 2): the
 * assessed-period timeline, the estimated fuel range, the reported values used
 * for one assessed part, and record coverage by input.
 *
 * They are views of backend facts. The frontend computes geometry only: every
 * classification, count, bound and sentence arrives from the assessment or its
 * plain reading. Each graphic carries a readable equivalent (a table or text),
 * its units, period, timezone (UTC) and a caption saying whether it shows
 * reported records or the assessed result. Identity is never colour alone:
 * each kind has its own pattern and a text label.
 */
import { useId, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { DataTable } from "../ui";
import { readablePeriod, readableTime } from "./findingPresentation";
import type { CoverageInput, SegmentInputs, Span, TimeWindow } from "./siteAnalyticsClient";
import type { ColdTemperatureRead } from "./coldAssessmentClient";
import { date, deg, hm, num as coldNum, range } from "./coldFormat";

// --- shared -----------------------------------------------------------------------

/** Display labels for the three backend classifications (spec section 4). */
const KIND_WORDS: Record<string, string> = {
  NECESSARY: "Needed",
  CANDIDATE_AVOIDABLE: "Possibly avoidable",
  INDETERMINATE: "Cannot determine",
};

const NOT_RECORDED = "Generator operation not recorded";
const UNCERTAIN = "Start or stop time uncertain";

/** "03:05 UTC" from an ISO time; the date is in the caption. */
function clock(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())} UTC`;
}

/** A round scale maximum at or above `value` (1, 2, 2.5 or 5 times a power of ten). */
export function niceMax(value: number): number {
  if (!(value > 0) || !Number.isFinite(value)) {
    return 1;
  }
  const power = 10 ** Math.floor(Math.log10(value));
  for (const step of [1, 2, 2.5, 5, 10]) {
    if (step * power >= value) {
      return step * power;
    }
  }
  return 10 * power;
}

function num(value: string | null | undefined): number | null {
  if (value === null || value === undefined || value.trim() === "") {
    return null;
  }
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** SVG ids must not carry React's colons. */
function useSvgId(): string {
  return `g${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
}

/** The pattern fills every graphic shares, one per kind. */
function Patterns({ id }: { id: string }) {
  return (
    <defs>
      <pattern id={`${id}-needed`} width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" className="graphic-fill--needed" />
      </pattern>
      <pattern id={`${id}-avoidable`} width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" className="graphic-fill--avoidable" />
        <rect width="2" height="6" className="graphic-ink--light" />
      </pattern>
      <pattern id={`${id}-unknown`} width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" className="graphic-fill--unknown" />
        <path d="M0 0L6 6M6 0L0 6" className="graphic-stroke--light" />
      </pattern>
      <pattern
        id={`${id}-unrecorded`}
        width="6"
        height="6"
        patternUnits="userSpaceOnUse"
        patternTransform="rotate(45)"
      >
        <rect width="6" height="6" className="graphic-fill--paper" />
        <rect width="2" height="6" className="graphic-fill--ink" />
      </pattern>
      <pattern id={`${id}-uncertain`} width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" className="graphic-fill--paper" />
        <circle cx="3" cy="3" r="1.2" className="graphic-fill--ink" />
      </pattern>
    </defs>
  );
}

type Kind = "needed" | "avoidable" | "unknown" | "unrecorded" | "uncertain";

const LEGEND: { kind: Kind; label: string }[] = [
  { kind: "needed", label: "Needed" },
  { kind: "avoidable", label: "Possibly avoidable" },
  { kind: "unknown", label: "Cannot determine" },
  { kind: "unrecorded", label: NOT_RECORDED },
  { kind: "uncertain", label: UNCERTAIN },
];

const LEVEL_KIND: Record<string, Kind> = {
  NECESSARY: "needed",
  CANDIDATE_AVOIDABLE: "avoidable",
  INDETERMINATE: "unknown",
};

function Swatch({ id, kind }: { id: string; kind: Kind }) {
  return (
    <svg className="graphic-swatch" width="14" height="14" aria-hidden="true" focusable="false">
      <rect width="14" height="14" fill={`url(#${id}-${kind})`} className="graphic-outline" />
    </svg>
  );
}

// --- assessed-period timeline ----------------------------------------------------

export interface TimelineSegment {
  start: string;
  end: string;
  minutes: number;
  observed: boolean;
  classification: string;
}

/** The assessment facts the timeline draws: `Assessment` and the card projection both fit. */
export interface TimelineSource {
  assessed_window: TimeWindow;
  interval: {
    first_running_observed: string;
    last_running_observed: string;
    last_stopped_before: string | null;
    first_stopped_after: string | null;
    open_start: boolean;
    open_end: boolean;
  };
  segments: TimelineSegment[];
}

export interface TimelineBand {
  kind: "part" | "uncertain-start" | "uncertain-end";
  /** The segment index, for a part. */
  index: number | null;
  start: string;
  end: string;
  /** Position and width as fractions of the drawn period. */
  x: number;
  width: number;
}

export interface TimelineGeometry {
  start: string;
  end: string;
  bands: TimelineBand[];
}

/**
 * Where each supplied span sits on the drawn period: actual time widths, no
 * minimum and no rounding. The period runs from the earliest to the latest
 * supplied time (the assessed window, the parts and the records bracketing
 * the start and stop). Bracketed time between the last record showing the
 * generator off and the first showing it operating (and the reverse at the
 * stop) is its own band, never a part. Returns null when a time is unreadable.
 */
export function timelineGeometry(source: TimelineSource): TimelineGeometry | null {
  const { interval } = source;
  const times = [
    source.assessed_window.start,
    source.assessed_window.end,
    interval.first_running_observed,
    interval.last_running_observed,
    ...source.segments.flatMap((s) => [s.start, s.end]),
  ];
  const ms = times.map((t) => Date.parse(t));
  if (ms.some((t) => Number.isNaN(t))) {
    return null;
  }
  const lo = Math.min(...ms);
  const hi = Math.max(...ms);
  const startIso = times[ms.indexOf(lo)];
  const endIso = times[ms.indexOf(hi)];
  const span = hi - lo;
  const place = (start: string, end: string) => {
    if (span <= 0) {
      return { x: 0, width: 1 };
    }
    const a = Math.max(lo, Date.parse(start));
    const b = Math.min(hi, Date.parse(end));
    return { x: (a - lo) / span, width: Math.max(0, b - a) / span };
  };
  const bands: TimelineBand[] = [];
  const before = interval.last_stopped_before;
  if (before !== null && Date.parse(before) < Date.parse(interval.first_running_observed)) {
    bands.push({
      kind: "uncertain-start",
      index: null,
      start: before,
      end: interval.first_running_observed,
      ...place(before, interval.first_running_observed),
    });
  }
  source.segments.forEach((s, index) => {
    bands.push({ kind: "part", index, start: s.start, end: s.end, ...place(s.start, s.end) });
  });
  const after = interval.first_stopped_after;
  if (after !== null && Date.parse(after) > Date.parse(interval.last_running_observed)) {
    bands.push({
      kind: "uncertain-end",
      index: null,
      start: interval.last_running_observed,
      end: after,
      ...place(interval.last_running_observed, after),
    });
  }
  return { start: startIso, end: endIso, bands };
}

function bandKind(band: TimelineBand, source: TimelineSource): Kind {
  if (band.kind !== "part" || band.index === null) {
    return "uncertain";
  }
  const segment = source.segments[band.index];
  return segment.observed ? (LEVEL_KIND[segment.classification] ?? "unknown") : "unrecorded";
}

function partWord(source: TimelineSource, outcomes: (string | undefined)[], index: number): string {
  return outcomes[index] ?? KIND_WORDS[source.segments[index].classification] ?? "Assessed";
}

export interface AssessedPeriodTimelineProps {
  source: TimelineSource;
  /** The served plain outcome of each part, aligned with `source.segments`. */
  outcomes: (string | undefined)[];
  /** The served plain reason of each part (full form only). */
  reasons?: (string | undefined)[];
  /** Compact: the bar, its period and its text equivalent, without the parts table. */
  compact?: boolean;
  /** Where a part's detail is (Finding Overview: its Analysis with the part selected). */
  partHref?: (index: number) => string;
  /** Analysis: the selected part and how to select another. */
  selected?: number | null;
  onSelect?: (index: number) => void;
  /** The assessment this draws, kept as data for consistency checks. */
  assessmentId?: string;
}

/**
 * The assessed period on a labelled UTC time axis. Parts are drawn at their
 * actual widths from supplied times; unrecorded operation is hatched and
 * labelled; uncertain start/stop time is dotted and never painted as
 * operating or avoidable; an open start or end is marked and explained, never
 * given a time. The full form has a keyboard-usable parts table with the same
 * labels, times and reasons; selection never depends on the pointer.
 */
export function AssessedPeriodTimeline({
  source,
  outcomes,
  reasons,
  compact = false,
  partHref,
  selected = null,
  onSelect,
  assessmentId,
}: AssessedPeriodTimelineProps) {
  const id = useSvgId();
  const geometry = timelineGeometry(source);
  const { interval } = source;
  const period = readablePeriod(source.assessed_window.start, source.assessed_window.end);
  const summary = source.segments
    .map(
      (s, index) =>
        `${clock(s.start)} to ${clock(s.end)}, ${partWord(source, outcomes, index)}${s.observed ? "" : `, ${NOT_RECORDED.toLowerCase()}`}`,
    )
    .join("; ");
  const openNotes: string[] = [];
  if (interval.open_start) {
    openNotes.push(
      `Start not recorded: no record shows the generator off before ${readableTime(interval.first_running_observed)}, so it may have been operating earlier.`,
    );
  }
  if (interval.open_end) {
    openNotes.push(
      `End not recorded: no record shows the generator off after ${readableTime(interval.last_running_observed)}, so when it stopped is not known.`,
    );
  }
  const kinds = new Set<Kind>(geometry === null ? [] : geometry.bands.map((b) => bandKind(b, source)));
  const legend = compact ? LEGEND.filter((l) => kinds.has(l.kind)) : LEGEND;
  return (
    <figure
      className={`assessment-graphic period-timeline${compact ? " period-timeline--compact" : ""}`}
      data-graphic="assessed-period-timeline"
      data-graphic-anchor="assessed-period-timeline"
      data-graphic-assessment={assessmentId}
      data-compact={compact ? "true" : undefined}
    >
      <figcaption className="assessment-graphic__caption" id={`${id}-caption`}>
        {compact
          ? `Assessed period, ${period}`
          : `Assessed period, ${period}. Assessed result from the reported records; times are UTC.`}
      </figcaption>
      {geometry === null ? (
        <p data-timeline-unavailable>The times of this period could not be read, so it is not drawn.</p>
      ) : (
        <>
          <div className="period-timeline__plot">
            {interval.open_start ? (
              <span className="period-timeline__open" data-open-end="start" aria-hidden="true">
                ‹ ?
              </span>
            ) : null}
            <svg
              className="period-timeline__bar"
              viewBox="0 0 1000 24"
              preserveAspectRatio="none"
              role="img"
              aria-label={`Assessed parts of the period: ${summary}${openNotes.length === 0 ? "" : `. ${openNotes.join(" ")}`}`}
              focusable="false"
            >
              <Patterns id={id} />
              <rect x="0" y="0" width="1000" height="24" className="graphic-track" />
              {geometry.bands.map((band) => {
                const kind = bandKind(band, source);
                const isSelected = band.index !== null && band.index === selected;
                return (
                  <rect
                    key={`${band.kind}-${band.start}-${band.index ?? ""}`}
                    x={band.x * 1000}
                    y={kind === "uncertain" ? 6 : 0}
                    width={band.width * 1000}
                    height={kind === "uncertain" ? 12 : 24}
                    fill={`url(#${id}-${kind})`}
                    className={isSelected ? "period-timeline__band is-selected" : "period-timeline__band"}
                    data-band={band.kind}
                    data-band-kind={kind}
                    data-part={band.index ?? undefined}
                    data-x={band.x.toFixed(6)}
                    data-width={band.width.toFixed(6)}
                    onClick={
                      onSelect === undefined || band.index === null
                        ? undefined
                        : () => onSelect(band.index as number)
                    }
                  >
                    <title>
                      {`${clock(band.start)} to ${clock(band.end)}: ${
                        band.index === null ? UNCERTAIN : partWord(source, outcomes, band.index)
                      }`}
                    </title>
                  </rect>
                );
              })}
            </svg>
            {interval.open_end ? (
              <span className="period-timeline__open" data-open-end="end" aria-hidden="true">
                ? ›
              </span>
            ) : null}
          </div>
          <div className="period-timeline__axis" aria-hidden="true">
            <span data-axis-start>{clock(geometry.start)}</span>
            <span data-axis-end>{clock(geometry.end)}</span>
          </div>
          <ul className="graphic-legend" aria-label="Key">
            {legend.map((item) => (
              <li key={item.kind} data-legend={item.kind}>
                <Swatch id={id} kind={item.kind} />
                {item.label}
              </li>
            ))}
          </ul>
        </>
      )}
      {openNotes.map((note) => (
        <p key={note} className="overview-note" data-open-note>
          {note}
        </p>
      ))}
      {compact ? null : (
        <PartsTable
          source={source}
          outcomes={outcomes}
          reasons={reasons}
          partHref={partHref}
          selected={selected}
          onSelect={onSelect}
        />
      )}
    </figure>
  );
}

function PartsTable({
  source,
  outcomes,
  reasons,
  partHref,
  selected,
  onSelect,
}: Pick<
  AssessedPeriodTimelineProps,
  "source" | "outcomes" | "reasons" | "partHref" | "selected" | "onSelect"
>) {
  const { interval } = source;
  const rows: ReactNode[] = [];
  if (interval.last_stopped_before !== null &&
    Date.parse(interval.last_stopped_before) < Date.parse(interval.first_running_observed)) {
    rows.push(
      <tr key="uncertain-start" data-timeline-row="uncertain-start">
        <th scope="row">{`${clock(interval.last_stopped_before)} to ${clock(interval.first_running_observed)}`}</th>
        <td>{UNCERTAIN}</td>
        <td>
          The generator started somewhere between a record showing it off and one
          showing it operating.
        </td>
        <td />
      </tr>,
    );
  }
  source.segments.forEach((s, index) => {
    rows.push(
      <tr
        key={`part-${s.start}-${index}`}
        data-timeline-row="part"
        data-analysis-segment={s.classification}
        aria-selected={onSelect === undefined ? undefined : index === selected}
      >
        <th scope="row">{`${clock(s.start)} to ${clock(s.end)} (${s.minutes} min)`}</th>
        <td>
          {partWord(source, outcomes, index)}
          {s.observed ? "" : `; ${NOT_RECORDED.toLowerCase()}`}
        </td>
        <td>{reasons?.[index] ?? "Detail not available for this part of the assessment."}</td>
        <td>
          {onSelect !== undefined ? (
            <button
              type="button"
              className="link-button"
              aria-pressed={index === selected}
              data-select-part={index + 1}
              onClick={() => onSelect(index)}
            >
              {index === selected ? "Values shown" : "Show values"}
            </button>
          ) : partHref !== undefined ? (
            <Link to={partHref(index)} data-part-link={index + 1}>
              Values used
            </Link>
          ) : null}
        </td>
      </tr>,
    );
  });
  if (interval.first_stopped_after !== null &&
    Date.parse(interval.first_stopped_after) > Date.parse(interval.last_running_observed)) {
    rows.push(
      <tr key="uncertain-end" data-timeline-row="uncertain-end">
        <th scope="row">{`${clock(interval.last_running_observed)} to ${clock(interval.first_stopped_after)}`}</th>
        <td>{UNCERTAIN}</td>
        <td>
          The generator stopped somewhere between a record showing it operating
          and one showing it off.
        </td>
        <td />
      </tr>,
    );
  }
  return (
    <div className="period-timeline__table" data-timeline-table>
      <DataTable>
        <caption className="visually-hidden">Assessed parts of the period, times UTC</caption>
        <thead>
          <tr>
            <th scope="col">Time (UTC)</th>
            <th scope="col">Outcome</th>
            <th scope="col">Reason</th>
            <th scope="col">
              <span className="visually-hidden">Values</span>
            </th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </DataTable>
    </div>
  );
}

// --- estimated fuel range --------------------------------------------------------

export interface FuelRangeProps {
  fuel: { status: string; low_litres?: string | null; high_litres?: string | null };
  reading: { label: string; text: string | null; note: string };
  compact?: boolean;
}

/**
 * The backend's fuel bounds as one low-to-high interval on a zero-based litre
 * scale, with both numbers. No midpoint and no distribution. Unavailable or
 * not-applicable fuel shows the backend's reason and no bar at all.
 */
export function FuelRange({ fuel, reading, compact = false }: FuelRangeProps) {
  const low = num(fuel.low_litres);
  const high = num(fuel.high_litres);
  if (fuel.status !== "BOUNDED" || low === null || high === null || reading.text === null) {
    return (
      <p
        className="assessment-graphic fuel-range"
        data-graphic="fuel-range"
        data-graphic-anchor="fuel-range"
        data-fuel-unavailable={fuel.status}
      >
        {reading.note}
      </p>
    );
  }
  const max = niceMax(high);
  const x0 = (low / max) * 1000;
  const x1 = (high / max) * 1000;
  return (
    <figure
      className={`assessment-graphic fuel-range${compact ? " fuel-range--compact" : ""}`}
      data-graphic="fuel-range"
      data-graphic-anchor="fuel-range"
      data-fuel-low={(low / max).toFixed(6)}
      data-fuel-high={(high / max).toFixed(6)}
    >
      <figcaption className="assessment-graphic__caption">
        {`${reading.label} (assessed result, litres)`}
      </figcaption>
      <div className="fuel-range__plot">
        <svg viewBox="0 0 1000 20" preserveAspectRatio="none" aria-hidden="true" focusable="false">
          <rect x="0" y="8" width="1000" height="4" className="graphic-track" />
          <rect x={x0} y="2" width={Math.max(x1 - x0, 0)} height="16" className="fuel-range__interval" />
          <rect x={x0 - 1.5} y="0" width="3" height="20" className="graphic-fill--ink" />
          <rect x={x1 - 1.5} y="0" width="3" height="20" className="graphic-fill--ink" />
        </svg>
        <div className="fuel-range__axis" aria-hidden="true">
          <span>0 litres</span>
          <span>{`${max} litres`}</span>
        </div>
      </div>
      <p data-fuel-text>
        <strong>{`Low ${fuel.low_litres} litres`}</strong>
        {" to "}
        <strong>{`high ${fuel.high_litres} litres`}</strong>
      </p>
      <p className="overview-note" data-fuel-note>
        {reading.note}
      </p>
    </figure>
  );
}

// --- reported values for one assessed part ---------------------------------------

const POWER_ROWS: { key: keyof SegmentInputs; label: string }[] = [
  { key: "load_kw", label: "Site demand" },
  { key: "pv_available_kw", label: "Available solar power" },
  { key: "discharge_capability_kw", label: "Available battery output" },
  { key: "generator_kw", label: "Generator output" },
];

const RESERVE_SOURCE: Record<string, string> = {
  policy: "site setting",
  "operator override": "operator instruction",
  "conflicting records": "conflicting records",
};

function ValueBars({
  caption,
  unit,
  max,
  rows,
}: {
  caption: string;
  unit: string;
  max: number;
  rows: { id: string; label: string; value: string | null; note?: string }[];
}) {
  return (
    <div className="value-bars" data-value-bars={unit}>
      <DataTable>
      <caption className="assessment-graphic__caption">{caption}</caption>
      <thead>
        <tr>
          <th scope="col">Input</th>
          <th scope="col">{`Value (${unit})`}</th>
          <th scope="col" className="value-bars__bar-heading">
            <span className="visually-hidden">Bar</span>
            <span aria-hidden="true">{`0 to ${max} ${unit}`}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const n = num(row.value);
          return (
            <tr key={row.id} data-value-row={row.id} data-missing={n === null ? "true" : undefined}>
              <th scope="row">{row.label}</th>
              <td>
                {n === null ? (
                  <span className="value-bars__missing">Not reported</span>
                ) : (
                  `${row.value} ${unit}`
                )}
                {row.note === undefined ? null : <span className="overview-note">{` (${row.note})`}</span>}
              </td>
              <td className="value-bars__bar">
                {n === null ? null : (
                  <svg
                    viewBox="0 0 1000 12"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                    focusable="false"
                    data-bar-width={(Math.min(n, max) / max).toFixed(6)}
                  >
                    <rect x="0" y="0" width="1000" height="12" className="graphic-track" />
                    <rect x="0" y="0" width={(Math.min(n, max) / max) * 1000} height="12" className="graphic-fill--value" />
                  </svg>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
      </DataTable>
    </div>
  );
}

export interface ReportedValuesProps {
  segment: { start: string; end: string; inputs: { at_start?: SegmentInputs; at_end?: SegmentInputs } };
  which: "start" | "end";
  onWhich: (which: "start" | "end") => void;
  /** The part's position in the period, for the caption. */
  partLabel: string;
}

/**
 * The values the assessment used for one part, at its start or end, as
 * reported: separate kW bars on one zero-based scale and the battery charge
 * and reserve on their own 0-100 % scale. Never stacked, subtracted or drawn
 * as a flow; a missing value is "Not reported" with no bar, never a zero bar.
 */
export function ReportedValues({ segment, which, onWhich, partLabel }: ReportedValuesProps) {
  const sides = (["start", "end"] as const).filter(
    (side) => segment.inputs[side === "start" ? "at_start" : "at_end"] !== undefined,
  );
  const current = sides.includes(which) ? which : sides[0];
  const inputs = current === undefined ? undefined : segment.inputs[current === "start" ? "at_start" : "at_end"];
  const when = current === "end" ? segment.end : segment.start;
  return (
    <div
      className="assessment-graphic reported-values"
      data-graphic="reported-values"
      data-graphic-anchor="reported-values"
      data-values-side={current ?? "none"}
      data-values-part-start={segment.start}
    >
      {inputs === undefined ? (
        <p data-values-none>
          {`${partLabel}: no values. Generator operation was not recorded for this part, so the assessment used none.`}
        </p>
      ) : (
        <>
          {sides.length < 2 ? null : (
            <div className="reported-values__switch" role="group" aria-label="Which values to show">
              {sides.map((side) => (
                <button
                  key={side}
                  type="button"
                  className="link-button"
                  aria-pressed={side === current}
                  data-values-switch={side}
                  onClick={() => onWhich(side)}
                >
                  {`Values used at the ${side} of the assessed part`}
                </button>
              ))}
            </div>
          )}
          <div data-segment-values>
            <ValueBars
              caption={`${partLabel}: values used at the ${current} of the assessed part, ${readableTime(when)}, as reported (kilowatts, kW). Separate values on one scale from zero; they are not added together.`}
              unit="kW"
              max={niceMax(Math.max(0, ...POWER_ROWS.map((r) => num(inputs[r.key]) ?? 0)))}
              rows={POWER_ROWS.map((r) => ({ id: r.key, label: r.label, value: inputs[r.key] }))}
            />
            <ValueBars
              caption="Battery charge and the minimum battery reserve, as reported (percent, 0 to 100 %)."
              unit="%"
              max={100}
              rows={[
                { id: "soc_pct", label: "Battery charge", value: inputs.soc_pct },
                {
                  id: "reserve_pct",
                  label: "Minimum battery reserve",
                  value: inputs.reserve_pct,
                  note:
                    inputs.reserve_source === null
                      ? undefined
                      : (RESERVE_SOURCE[inputs.reserve_source] ?? "recorded setting"),
                },
              ]}
            />
          </div>
          <p className="overview-note">
            These are the values the assessment used, not a continuous
            measurement; the record times are on the Evidence page.
          </p>
        </>
      )}
    </div>
  );
}

// --- counts by category (S2-02 Site Evidence outcomes) ---------------------------

export interface CountBarRow {
  key: string;
  label: string;
  count: number;
}

/**
 * One count per row with a bar over the rows' total: counts, never shares of
 * time. Used for what happened to the readings of a Site Evidence period.
 */
export function CountBars({
  rows,
  caption,
  heading,
  graphic,
}: {
  rows: CountBarRow[];
  caption: string;
  heading: string;
  graphic: string;
}) {
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  return (
    <div className="assessment-graphic value-bars" data-graphic={graphic}>
      <DataTable>
        <caption className="assessment-graphic__caption">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">{heading}</th>
            <th scope="col">Count</th>
            <th scope="col" className="value-bars__bar-heading">
              <span className="visually-hidden">Bar</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const share = total === 0 ? 0 : row.count / total;
            return (
              <tr key={row.key} data-evidence-outcome={row.key}>
                <th scope="row">{row.label}</th>
                <td>{row.count}</td>
                <td className="value-bars__bar">
                  <svg viewBox="0 0 1000 12" preserveAspectRatio="none" aria-hidden="true" focusable="false" data-bar-width={share.toFixed(6)}>
                    <rect x="0" y="0" width="1000" height="12" className="graphic-track" />
                    <rect x="0" y="0" width={share * 1000} height="12" className="graphic-fill--value" />
                  </svg>
                </td>
              </tr>
            );
          })}
        </tbody>
      </DataTable>
    </div>
  );
}

// --- record coverage by input ----------------------------------------------------

export interface CoverageByInputProps {
  inputs: CoverageInput[];
  unobserved: Span[];
  /** Plain input names by input id; the served label is the fallback. */
  words: Record<string, string>;
}

/**
 * For each input, how many of the assessed parts of this period had a usable
 * record: a count bar over that denominator, with the named gaps beside it.
 * Zero assessed parts is "Not assessed", never 0 % or 100 %. Unrecorded
 * generator operation is listed separately.
 */
export function CoverageByInput({ inputs, unobserved, words }: CoverageByInputProps) {
  return (
    <div className="assessment-graphic coverage-by-input" data-graphic="coverage-by-input" data-graphic-anchor="coverage-by-input">
      <div className="value-bars" data-coverage-table>
        <DataTable>
        <caption className="assessment-graphic__caption">
          Reported records for this assessed period: for each input, the number
          of assessed parts of this period that had a usable record. Counts of
          parts, not shares of elapsed time. Times are UTC.
        </caption>
        <thead>
          <tr>
            <th scope="col">Input</th>
            <th scope="col">Assessed parts of this period with a usable record</th>
            <th scope="col" className="value-bars__bar-heading">
              <span className="visually-hidden">Bar</span>
            </th>
            <th scope="col">Missing records</th>
          </tr>
        </thead>
        <tbody>
          {inputs.map((input) => {
            const assessed = input.evaluated_segments > 0;
            const share = assessed ? Math.min(input.usable_segments, input.evaluated_segments) / input.evaluated_segments : null;
            return (
              <tr key={input.input} data-coverage-input={input.input} data-coverage-assessed={assessed ? "true" : "false"}>
                <th scope="row">{words[input.input] ?? input.label}</th>
                <td>
                  {assessed
                    ? `${input.usable_segments} of ${input.evaluated_segments}`
                    : "Not assessed"}
                </td>
                <td className="value-bars__bar">
                  {share === null ? null : (
                    <svg
                      viewBox="0 0 1000 12"
                      preserveAspectRatio="none"
                      aria-hidden="true"
                      focusable="false"
                      data-bar-width={share.toFixed(6)}
                    >
                      <rect x="0" y="0" width="1000" height="12" className="graphic-track" />
                      <rect x="0" y="0" width={share * 1000} height="12" className="graphic-fill--value" />
                    </svg>
                  )}
                </td>
                <td>
                  {input.gaps.length === 0
                    ? "None"
                    : input.gaps.map((g) => `${readablePeriod(g.start, g.end)} (${g.minutes} min)`).join("; ")}
                </td>
              </tr>
            );
          })}
        </tbody>
        </DataTable>
      </div>
      {unobserved.length === 0 ? null : (
        <ul className="cell-list" data-coverage-unobserved-list>
          {unobserved.map((span) => (
            <li key={`gen-${span.start}`} data-coverage-unobserved>
              {`${NOT_RECORDED}: ${readablePeriod(span.start, span.end)} (${span.minutes} min)`}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ---------- W2-03: cold temperature chart (policy band, sampled points, explicit gaps) ---------- */

const CHART_W = 640;
const CHART_H = 220;
const PAD = { l: 40, r: 12, t: 12, b: 26 };
const BRIDGE_MS = 10 * 60 * 1000;

export function ColdTemperatureChart({ read, label }: { read: ColdTemperatureRead; label: string }) {
  const from = date(read.window.from);
  const to = date(read.window.to);
  const points = read.points
    .map((p) => ({ t: date(p.at), v: coldNum(p.value), p }))
    .filter((x): x is { t: Date; v: number; p: (typeof read.points)[number] } => x.t !== null && x.v !== null);
  if (from === null || to === null || points.length === 0) {
    return (
      <p className="not-available-yet v69-chart-note" data-panel-gap="cold-temperature-chart">
        No accepted chamber probe reading in this window, so no temperature line is drawn.
      </p>
    );
  }
  const low = coldNum(read.policy?.low_deg_c);
  const high = coldNum(read.policy?.high_deg_c);
  const values = [...points.map((x) => x.v), ...(low === null ? [] : [low]), ...(high === null ? [] : [high])];
  const yMin = Math.floor(Math.min(...values) - 1);
  const yMax = Math.ceil(Math.max(...values) + 1);
  const x = (t: Date) => PAD.l + ((t.getTime() - from.getTime()) / (to.getTime() - from.getTime())) * (CHART_W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + ((yMax - v) / (yMax - yMin)) * (CHART_H - PAD.t - PAD.b);
  const segments: string[] = [];
  let current: string[] = [];
  points.forEach((pt, i) => {
    if (i > 0 && pt.t.getTime() - points[i - 1].t.getTime() > BRIDGE_MS) {
      segments.push(current.join(" "));
      current = [];
    }
    current.push(`${x(pt.t).toFixed(1)},${y(pt.v).toFixed(1)}`);
  });
  segments.push(current.join(" "));
  const ticks: Date[] = [];
  for (let t = Math.ceil(from.getTime() / 900000) * 900000; t < to.getTime(); t += 900000) ticks.push(new Date(t));
  const step = yMax - yMin > 8 ? 2 : 1;
  const yTicks: number[] = [];
  for (let v = Math.ceil(yMin / step) * step; v <= yMax; v += step) yTicks.push(v);
  // The confirmed excursion's span, from its latest possible start to its latest end (or the window end while open).
  const x0 = read.excursions[0] === undefined ? null : date(read.excursions[0].start_bounds.latest ?? read.excursions[0].start_bounds.earliest);
  const x1 = read.excursions[0] === undefined ? null : (date(read.excursions[0].end_bounds.latest) ?? to);
  const excursion =
    x0 === null || x1 === null
      ? null
      : {
          x0: x(x0),
          x1: x(x1),
          label: `${read.excursions[0].direction === "LOW" ? "Below" : "Above"} policy ${range(read.excursions[0].duration_bounds.low, read.excursions[0].duration_bounds.high, "min").replace(/^At least/, "at least")}`,
        };
  return (
    <figure className="assessment-graphic cold-chart" data-cold-chart="temperature">
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} role="img" aria-label={label} preserveAspectRatio="xMidYMid meet">
        {low !== null && high !== null ? (
          <rect className="cold-chart__band" x={PAD.l} y={y(high)} width={CHART_W - PAD.l - PAD.r} height={Math.max(0, y(low) - y(high))} />
        ) : null}
        {read.gaps.map((gap) => {
          const a = date(gap.start);
          const b = date(gap.end);
          if (a === null || b === null) return null;
          return (
            <rect key={`${gap.start}-${gap.end}`} className="cold-chart__gap" data-cold-gap-shade={gap.start ?? ""} x={x(a)} y={PAD.t} width={Math.max(2, x(b) - x(a))} height={CHART_H - PAD.t - PAD.b}>
              <title>{`No usable reading ${hm(gap.start)}–${hm(gap.end)}`}</title>
            </rect>
          );
        })}
        {yTicks.map((v) => (
          <g key={`y-${v}`}>
            <line className="cold-chart__grid" x1={PAD.l} x2={CHART_W - PAD.r} y1={y(v)} y2={y(v)} />
            <text className="cold-chart__axis" x={PAD.l - 4} y={y(v) + 4} textAnchor="end">{`${v}°`}</text>
          </g>
        ))}
        {excursion === null ? null : (
          <g data-cold-excursion-shade>
            <rect className="cold-chart__excursion" x={excursion.x0} y={PAD.t} width={Math.max(2, excursion.x1 - excursion.x0)} height={CHART_H - PAD.t - PAD.b} />
            <text className="cold-chart__excursion-label" x={(excursion.x0 + excursion.x1) / 2} y={PAD.t + 12} textAnchor="middle">
              {excursion.label}
            </text>
          </g>
        )}
        {[low, high].map((v) =>
          v === null ? null : <line key={`limit-${v}`} className="cold-chart__limit" x1={PAD.l} x2={CHART_W - PAD.r} y1={y(v)} y2={y(v)} />,
        )}
        {segments.map((s) => (
          <polyline key={s} className="cold-chart__line" points={s} />
        ))}
        {points.map((pt) => (
          <circle
            key={pt.p.evidence_id}
            className={high !== null && pt.v > high ? "cold-chart__point cold-chart__point--out" : low !== null && pt.v < low ? "cold-chart__point cold-chart__point--out" : "cold-chart__point"}
            cx={x(pt.t)}
            cy={y(pt.v)}
            r={3.5}
            data-cold-point={pt.p.at}
          >
            <title>{`${hm(pt.p.at)} · ${deg(pt.v)}`}</title>
          </circle>
        ))}
        {ticks.map((t) => (
          <text key={t.toISOString()} className="cold-chart__axis" x={x(t)} y={CHART_H - 8} textAnchor="middle">
            {`${hm(t.toISOString())} UTC`}
          </text>
        ))}
      </svg>
      <figcaption className="cold-chart__legend">
        <span className="cold-chart__key cold-chart__key--line">Chamber temperature</span>
        <span className="cold-chart__key cold-chart__key--band">Policy band</span>
        {read.gaps.length > 0 ? <span className="cold-chart__key cold-chart__key--gap">No usable reading</span> : null}
      </figcaption>
    </figure>
  );
}

