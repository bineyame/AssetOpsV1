/**
 * W5-03a E2: the EV Site Availability page body (v6.9 `availability`), from the selected `/ev/availability` depth
 * read (`.agent/W5-03-build-spec.md` literal ledger, E2 card, closure 2 and the W5-03a pre-flight E2 ruling).
 *
 * A bounded observed-state proxy (`ev-availability/1`): configured scheduled seconds and accepted connector-state
 * seconds are separate facts, Unknown is never availability, and no number certifies physical availability.
 * MOCK DEVIATION (D4) R26/R43-R45: the mock's fixed connector-hours, percentages, 08:00/12:00/16:00 axis, card notes,
 * chart note, bound and next-evidence prose keep their forms with selected values substituted.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, MetricCard, MetricCards, Notice, Panel, StatusBar } from "../ui";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";
import { coldWindowSearch } from "./coldAssessmentClient";
import {
  type AvailabilityConnector,
  type AvailabilitySpan,
  type EvAvailabilityRead,
  type EvDepthClient,
  EV_DEPTH_UNREACHABLE,
  depthStateNotice,
  durationText,
} from "./evDepthClient";

export const AVAILABILITY_LOADING = "Loading the site's connector availability.";
export const EV_DEPTH_REFUSAL_HEADING = "EV depth unavailable";
export const AVAILABILITY_STATUS = "Evidence limited";
export const SCHEDULE_NOT_ESTABLISHED = "Service schedule not established for this window.";
export const SCHEDULE_DECLARED_EMPTY = "No service hours are declared in this window.";
export const AVAILABILITY_EMPTY = "No trustworthy connector-state spans in the selected schedule.";
export const OUTSIDE_SCHEDULE = "Outside scheduled service hours";
export const TELEMETRY_SENTENCE = "A telemetry outage does not prove the charging connector was physically unavailable.";
const STATE_WORD: Record<AvailabilitySpan["state"], string> = { AVAILABLE: "Available", UNAVAILABLE: "Unavailable", UNKNOWN: "Unknown" };

export interface EvDepthRoutes {
  /** The EV Evidence Analysis UI path (no query). */
  analysis: string;
  /** The EV Sessions UI path (no query). */
  sessions: string;
}

/* ---------- formats ---------- */

/** Epoch ms of a strict-UTC wire instant (microsecond fractions truncated to milliseconds). */
export function instantMs(value: string): number {
  return Date.parse(value.replace(/\.(\d{3})\d*Z$/, ".$1Z"));
}

const pad = (n: number) => String(n).padStart(2, "0");

/** `HH:mm` of an epoch ms, in UTC. */
export function hhmm(ms: number): string {
  const d = new Date(ms);
  return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

/** Hours to at most two decimals, trailing zeros dropped (`3600` -> `1`, `2700` -> `0.75`). */
export function hoursText(seconds: number): string {
  return String(Number((seconds / 3600).toFixed(2)));
}

/** Closure 2: `Known-time availability`, one decimal (`0.933333` -> `93.3%`), else `Unknown`. */
export function knownTimeText(ratio: string | null): string {
  return ratio === null ? "Unknown" : `${(Math.round(Number(ratio) * 1000) / 10).toFixed(1)}%`;
}

const pct2 = (ratio: string) => (Number(ratio) * 100).toFixed(2);

/** Closure 2: the full-schedule bound, two decimals each and one percent sign after the range, else `Unknown`. */
export function boundText(lower: string | null, upper: string | null): string {
  return lower === null || upper === null ? "Unknown" : `${pct2(lower)}–${pct2(upper)}%`;
}

const dur = (seconds: number | null) => (seconds === null ? "Unknown" : durationText(seconds));

/** A connector's scheduled occurrences inside the window: its spans unioned (spans cover exactly the schedule). */
function occurrences(row: AvailabilityConnector): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  for (const span of row.spans) {
    const a = instantMs(span.from);
    const b = instantMs(span.to);
    const last = out[out.length - 1];
    if (last !== undefined && a <= last[1]) last[1] = Math.max(last[1], b);
    else out.push([a, b]);
  }
  return out;
}

/** Pre-flight E2: the mock status muted text from selected counts and schedules. */
export function connectorHoursText(read: EvAvailabilityRead): string {
  const a = read.availability;
  if (a.schedule_state === "NOT_ESTABLISHED" || a.scheduled_seconds === null) return "Scheduled connector-hours unknown";
  const rows = a.connectors;
  const shapes = rows.map((row) => JSON.stringify(occurrences(row)));
  const same = rows.length > 0 && shapes.every((s) => s === shapes[0]) && rows.every((r) => r.scheduled_seconds === rows[0].scheduled_seconds);
  if (same) {
    const each = rows[0].scheduled_seconds ?? 0;
    return `${rows.length} connectors × ${hoursText(each)} scheduled hours = ${hoursText(each * rows.length)} connector-hours`;
  }
  return `${hoursText(a.scheduled_seconds)} scheduled connector-hours across ${rows.length} connectors`;
}

/** Pre-flight E2: the `Known-time availability` card note, mock form with selected hours and coverage. */
export function knownTimeNote(read: EvAvailabilityRead): string {
  const a = read.availability;
  if (a.known_available_seconds === null || a.known_unavailable_seconds === null || a.scheduled_seconds === null) {
    return "Known hours and coverage unknown";
  }
  const known = a.known_available_seconds + a.known_unavailable_seconds;
  const coverage = a.scheduled_seconds > 0 ? `${((known / a.scheduled_seconds) * 100).toFixed(2)}%` : "Unknown";
  return `${hoursText(a.known_available_seconds)} / ${hoursText(known)} known hours; coverage ${coverage}`;
}

const connectorName = (label: string) => (/^connector\b/i.test(label) ? label : `Connector ${label}`);

/* ---------- read ---------- */

function useAvailabilityRead(client: EvDepthClient, siteCode: string, window: ColdWindowQuery, attempt: number) {
  const key = `${siteCode}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}|${attempt}`;
  const [state, setState] = useState<{ key: string; value: ColdRead<EvAvailabilityRead> } | null>(null);
  useEffect(() => {
    let active = true;
    void client.getAvailability(siteCode, window).then((value) => {
      if (active) setState({ key, value });
    });
    return () => {
      active = false;
    };
    // The key names exactly what is read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state !== null && state.key === key ? state.value : null;
}

export function EvDepthRefusal({ read, onRetry }: { read: Exclude<ColdRead<unknown>, { status: "loaded" }>; onRetry: () => void }) {
  return (
    <div className="page-refusal" role="status" data-page-refusal="ev-depth">
      <p className="page-refusal__title">
        <strong>{EV_DEPTH_REFUSAL_HEADING}</strong>
      </p>
      {read.status === "refused" ? (
        <p data-ev-depth-error>
          <code data-vocabulary-exempt="source-reference">{read.code}</code>
          {read.message === null ? null : <> {read.message}</>}
        </p>
      ) : (
        <p data-ev-depth-error>{read.message ?? EV_DEPTH_UNREACHABLE}</p>
      )}
      <button type="button" className="button" data-ev-depth-retry onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

/* ---------- bars ---------- */

interface Segment {
  key: string;
  width: number;
  state: AvailabilitySpan["state"] | "OUTSIDE";
  from: number;
  to: number;
}

/** Ordered window-aligned segments: one per classified span, blank outside the connector's schedule. */
export function segmentsOf(row: AvailabilityConnector, fromMs: number, toMs: number): Segment[] {
  const total = toMs - fromMs;
  const out: Segment[] = [];
  let cursor = fromMs;
  const push = (state: Segment["state"], a: number, b: number) => {
    if (b > a) out.push({ key: `${state}|${a}`, width: ((b - a) / total) * 100, state, from: a, to: b });
  };
  for (const span of row.spans) {
    const a = Math.max(instantMs(span.from), fromMs);
    const b = Math.min(instantMs(span.to), toMs);
    if (a > cursor) push("OUTSIDE", cursor, a);
    push(span.state, a, b);
    cursor = Math.max(cursor, b);
  }
  push("OUTSIDE", cursor, toMs);
  return out;
}

function ConnectorBar({ row, fromMs, toMs }: { row: AvailabilityConnector; fromMs: number; toMs: number }) {
  const segments = segmentsOf(row, fromMs, toMs);
  const spans = occurrences(row);
  const period = spans.length === 1 ? `${hhmm(spans[0][0])}–${hhmm(spans[0][1])}` : `${hhmm(fromMs)}–${hhmm(toMs)}`;
  return (
    <div className="ev-depth-bars__row" data-ev-bar-row={row.asset_id}>
      <span className="ev-depth-bars__label">{row.label}</span>
      <div className="ev-depth-bars__track">
        {segments.map((s) => (
          <div
            key={s.key}
            className={`ev-depth-bars__segment ev-depth-bars__segment--${s.state.toLowerCase()}`}
            style={{ width: `${s.width}%` }}
            data-ev-segment={s.state}
            aria-label={s.state === "OUTSIDE" ? OUTSIDE_SCHEDULE : undefined}
          />
        ))}
      </div>
      <strong className="ev-depth-bars__period">{period}</strong>
      <span className="visually-hidden" data-ev-span-summary={row.asset_id}>
        {`${row.label}: ${segments
          .map((s) => `${hhmm(s.from)}–${hhmm(s.to)} UTC ${s.state === "OUTSIDE" ? OUTSIDE_SCHEDULE : STATE_WORD[s.state]}`)
          .join("; ")}. ${dur(row.known_available_seconds)} available, ${dur(row.known_unavailable_seconds)} unavailable, ${dur(row.unknown_seconds)} unknown.`}
      </span>
    </div>
  );
}

function StatePanel({ read }: { read: EvAvailabilityRead }) {
  const a = read.availability;
  const from = read.window.from;
  const to = read.window.to;
  const bars = a.schedule_state === "SCHEDULED" && from !== null && to !== null;
  const fromMs = from === null ? 0 : instantMs(from);
  const toMs = to === null ? 0 : instantMs(to);
  const noKnown = a.known_available_seconds === 0 && a.known_unavailable_seconds === 0;
  return (
    <Panel heading="Connector states over the service schedule" headingId="ev-availability-states-heading">
      <div className="legend ev-depth-legend">
        <Badge tone="neutral" className="ev-tone--green">Available</Badge>
        <Badge tone="neutral" className="ev-tone--red">Unavailable</Badge>
        <Badge tone="neutral" className="ev-depth-badge--outline">Unknown</Badge>
      </div>
      {a.schedule_state === "NOT_ESTABLISHED" ? (
        <p className="not-available-yet" data-ev-schedule-state="NOT_ESTABLISHED">
          {SCHEDULE_NOT_ESTABLISHED}
        </p>
      ) : a.schedule_state === "DECLARED_EMPTY" ? (
        <p className="not-available-yet" data-ev-schedule-state="DECLARED_EMPTY">
          {SCHEDULE_DECLARED_EMPTY}
        </p>
      ) : null}
      {bars ? (
        <>
          <div className="ev-depth-bars" data-ev-bars="">
            {a.connectors.map((row) => (
              <ConnectorBar key={row.asset_id} row={row} fromMs={fromMs} toMs={toMs} />
            ))}
          </div>
          <div className="ev-depth-bars__times" data-ev-bar-times="">
            <span>{`${hhmm(fromMs)} UTC`}</span>
            <span>{`${hhmm(fromMs + (toMs - fromMs) / 2)} UTC`}</span>
            <span>{`${hhmm(toMs)} UTC`}</span>
          </div>
          {noKnown ? (
            <p className="not-available-yet" data-ev-availability-empty="">
              {AVAILABILITY_EMPTY}
            </p>
          ) : null}
          {a.connectors.length === 0 ? (
            <p className="chart-note">No selected connector has a service schedule in this window.</p>
          ) : (
            a.connectors.map((row) => (
              <p key={row.asset_id} className="chart-note" data-ev-chart-note={row.asset_id}>
                {`${connectorName(row.label)}: ${dur(row.known_available_seconds)} available, ${dur(row.known_unavailable_seconds)} observed unavailable and ${dur(row.unknown_seconds)} unknown. Spans use accepted transition timestamps.`}
              </p>
            ))
          )}
        </>
      ) : null}
    </Panel>
  );
}

function AvailabilityBody({ read, routes }: { read: EvAvailabilityRead; routes: EvDepthRoutes }) {
  const a = read.availability;
  const state = read.selection.state;
  const notice = depthStateNotice(state);
  const query = coldWindowSearch(read.window);
  const bounded = a.full_lower !== null && a.full_upper !== null && a.scheduled_seconds !== null;
  const missing = a.unknown_seconds !== null && a.unknown_seconds > 0 ? `the missing ${durationText(a.unknown_seconds)}` : "any unknown scheduled time";
  return (
    <>
      <StatusBar label="Connector availability">
        <Badge tone="neutral" className="ev-tone--amber">
          {AVAILABILITY_STATUS}
        </Badge>{" "}
        <span className="muted" data-ev-connector-hours="">
          {connectorHoursText(read)}
        </span>
      </StatusBar>
      {notice === null ? null : <Notice data={{ "data-ev-depth-state-notice": state }}>{notice}</Notice>}
      <MetricCards label="Connector availability">
        <MetricCard label="Known available" value={dur(a.known_available_seconds)} note="State-supported service time" data={{ "data-ev-availability-card": "available" }} />
        <MetricCard label="Known unavailable" value={dur(a.known_unavailable_seconds)} note="Faulted or unavailable state evidenced" data={{ "data-ev-availability-card": "unavailable" }} />
        <MetricCard label="Unknown" value={dur(a.unknown_seconds)} note="No trustworthy state coverage" data={{ "data-ev-availability-card": "unknown" }} />
        <MetricCard label="Known-time availability" value={knownTimeText(a.known_time_ratio)} note={knownTimeNote(read)} data={{ "data-ev-availability-card": "ratio" }} />
      </MetricCards>
      <StatePanel read={read} />
      <div className="panel-pair">
        <Panel heading="Full-schedule availability bound" headingId="ev-availability-bound-heading">
          <div className="metric-value" data-ev-bound="">
            {boundText(a.full_lower, a.full_upper)}
          </div>
          <p className="prose" data-ev-bound-prose="">
            {bounded
              ? `Lower bound: ${dur(a.known_available_seconds)} / ${dur(a.scheduled_seconds)}. Upper bound: (${dur(a.known_available_seconds)} + ${dur(a.unknown_seconds)} unknown) / ${dur(a.scheduled_seconds)}. Unknown time is not silently included as available.`
              : "Unknown time is not silently included as available."}
          </p>
        </Panel>
        <Panel heading="Most useful next evidence" headingId="ev-availability-next-heading">
          <p className="prose" data-ev-next-evidence="">{`Recover the connector status/heartbeat history for ${missing}. ${TELEMETRY_SENTENCE}`}</p>
          <p className="ev-depth-claim">
            <Link to={`${routes.analysis}${query}`} data-ev-lineage="">
              Inspect connector-state lineage ↗
            </Link>
          </p>
        </Panel>
      </div>
    </>
  );
}

export interface EvAvailabilityProps {
  /** The imported Site code (the shell Site token), never the internal UUID. */
  siteCode: string;
  window: ColdWindowQuery;
  client: EvDepthClient;
  routes: EvDepthRoutes;
}

export function EvAvailability({ siteCode, window, client, routes }: EvAvailabilityProps) {
  const [attempt, setAttempt] = useState(0);
  const read = useAvailabilityRead(client, siteCode, window, attempt);
  if (read === null) return <p className="prose">{AVAILABILITY_LOADING}</p>;
  if (read.status !== "loaded") return <EvDepthRefusal read={read} onRetry={() => setAttempt((n) => n + 1)} />;
  return <AvailabilityBody read={read.value} routes={routes} />;
}
