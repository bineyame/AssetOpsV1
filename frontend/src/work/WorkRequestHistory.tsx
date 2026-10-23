/**
 * W6-01d C4: the work request History (v6.9 `wr-history`, `index.html:971`), read from
 * `GET /api/work/requests/{case_id}?site_id={site_code}[&known_at=]` (`global-work-detail-1`). Mock order: breadcrumb,
 * heading with `Open site`, the `Context tabs` row, the date bar, the `wrHeader` mheader, then the one `History`
 * panel with the mock's `Time | Event | By` table. Copy follows `.agent/W6-01-build-spec.md` "C4 pre-flight rulings"
 * (P-C4-1..22), which supersede the earlier C4 card wording.
 *
 * Rows are the selected `work_detail.events` plus the successor `history.revisions` (revision 1 is the CREATED row),
 * ordered by the exact six-digit `recorded_at` strings, then the lowercase `id`. Five authored rows show per page with
 * a client pager inside the panel; the last page ends with the two in-table gaps for the mock's `Site visit started`
 * and `Verification pending` rows, which have no selected event or outcome assessment. A request without its CREATED
 * event is a read failure (503 sentence), never an empty history.
 *
 * MOCK DEVIATION (D2, register R19): the Time cell shows UTC with year and seconds (`20 Oct 2026, 11:59:03 UTC`)
 * instead of the mock's minute-only `6 Oct 19:20`, because the stored writes one second apart would otherwise look
 * tied; each row adds an `Occurrence time` disclosure.
 * MOCK DEVIATION (D4, register R39): the By cell shows `Name not recorded` with a `Stored actor` disclosure of the
 * stored actor kind and ID instead of the mock's example role names; a service ID is never presented as a person.
 */
import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { DataTable, Panel } from "../ui";
import {
  isKnownWorkCaseEvent,
  type GlobalWorkClient,
  type GlobalWorkDetailBody,
  type WorkCaseDetailEvent,
} from "./globalWorkClient";
import { Clamp, SCROLL_TABLE } from "./globalWorkParts";
import { WorkRequestFrame } from "./workRequestShared";

export const HISTORY_PANEL_HEADING = "History";
export const HISTORY_TABLE_HEADING_ID = "work-request-history-heading";
export const HISTORY_COLUMNS = ["Time", "Event", "By"] as const;
export const HISTORY_PAGE_SIZE = 5;
export const NAME_NOT_RECORDED = "Name not recorded";
/** The two in-table gaps on the last page (mock rows `Site visit started` and `Verification pending`). */
export const HISTORY_GAPS = ["Site visit start not recorded", "Verification pending · no outcome assessment recorded"] as const;
/** Minimum column widths (px): Time, Event, By; the table scrolls inside its panel below their sum. */
const MIN_WIDTHS = [210, 340, 200];

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** History-local UTC seconds display, `20 Oct 2026, 11:59:03 UTC`, read from the stored string (no zone math). */
export function historyUtc(instant: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z$/.exec(instant);
  if (m === null) return instant;
  const month = MONTHS[Number(m[2]) - 1];
  if (month === undefined) return instant;
  return `${Number(m[3])} ${month} ${m[1]}, ${m[4]}:${m[5]}:${m[6]} UTC`;
}

/** One authored History row: an event or a successor revision. */
export interface HistoryRow {
  id: string;
  /** `CREATED`, `ASSIGN`, ..., `CORRECTION`, or the raw unknown kind. */
  kind: string;
  recorded_at: string;
  occurred_at: string;
  actor_kind: string;
  actor_id: string;
  /** The Event cell's full text. */
  text: string;
  /** True when the text carries stored free text (clamped with a `Full event text` disclosure). */
  stored: boolean;
  /** The CREATED source incident link, when it has an authorized href. */
  sourceHref: string | null;
}

/** Exact string order: `recorded_at` as supplied, then lowercase `id`; never `Date.parse`. */
export function byRecorded(a: { recorded_at: string; id: string }, b: { recorded_at: string; id: string }): number {
  if (a.recorded_at !== b.recorded_at) return a.recorded_at < b.recorded_at ? -1 : 1;
  const x = a.id.toLowerCase();
  const y = b.id.toLowerCase();
  return x < y ? -1 : x > y ? 1 : 0;
}

const PAYLOAD_KEY: Readonly<Record<string, string>> = {
  ASSIGN: "assignee",
  COMMENT: "text",
  COMPLETE: "maintenance_record_id",
  CLOSE: "reason",
  REOPEN: "reason",
  CANCEL: "reason",
};

/**
 * The local fail-closed check beside the C2 parser, so a typed body that bypasses it still fails as the 503 read:
 * a CREATED event exists, and every event has its identity and its kind's stored payload string.
 */
export function historyReadable(body: GlobalWorkDetailBody): boolean {
  const events = body.work_detail.events;
  return (
    events.some((e) => e.kind === "CREATED") &&
    events.every((e) => {
      if (typeof e.id !== "string" || e.id === "" || typeof e.kind !== "string" || e.kind === "") return false;
      const key = PAYLOAD_KEY[e.kind];
      return key === undefined || typeof (e.payload as Record<string, unknown> | null)?.[key] === "string";
    })
  );
}

function eventText(event: WorkCaseDetailEvent, body: GlobalWorkDetailBody): { text: string; stored: boolean; sourceHref: string | null } {
  if (!isKnownWorkCaseEvent(event)) return { text: `Event ${event.kind} · meaning not established`, stored: false, sourceHref: null };
  switch (event.kind) {
    case "CREATED": {
      const source = body.links.source_incident;
      return source === null
        ? { text: "Created", stored: false, sourceHref: null }
        : { text: `Raised from ${source.label}`, stored: false, sourceHref: source.href };
    }
    case "ASSIGN":
      return { text: `Assigned to ${event.payload.assignee}`, stored: true, sourceHref: null };
    case "COMMENT":
      return { text: `Commented: ${event.payload.text}`, stored: true, sourceHref: null };
    case "COMPLETE":
      return {
        text: `Completed · outcome not established · maintenance record ${event.payload.maintenance_record_id}`,
        stored: false,
        sourceHref: null,
      };
    case "CLOSE":
      return { text: `Closed: ${event.payload.reason}`, stored: true, sourceHref: null };
    case "REOPEN":
      return { text: `Reopened: ${event.payload.reason}`, stored: true, sourceHref: null };
    case "CANCEL":
      return { text: `Cancelled: ${event.payload.reason}`, stored: true, sourceHref: null };
  }
}

/** The merged authored chronology: selected events plus successor revisions only, in exact string order. */
export function historyRows(body: GlobalWorkDetailBody): HistoryRow[] {
  const events: HistoryRow[] = body.work_detail.events.map((event) => ({
    id: event.id,
    kind: event.kind,
    recorded_at: event.recorded_at,
    occurred_at: event.occurred_at,
    actor_kind: event.actor_kind,
    actor_id: event.actor_id,
    ...eventText(event, body),
  }));
  const corrections: HistoryRow[] = body.history.revisions
    .filter((r) => r.supersedes_revision_id !== null)
    .map((r) => ({
      id: r.id,
      kind: "CORRECTION",
      recorded_at: r.recorded_at,
      occurred_at: r.occurred_at,
      actor_kind: r.actor_kind,
      actor_id: r.actor_id,
      text: `${r.reason === null ? "Correction · reason not recorded" : `Correction: ${r.reason}`}\nTitle: ${r.title}`,
      stored: true,
      sourceHref: null,
    }));
  return [...events, ...corrections].sort(byRecorded);
}

function EventCell({ row }: { row: HistoryRow }) {
  if (row.sourceHref) {
    const label = row.text.slice("Raised from ".length);
    return (
      <>
        {"Raised from "}
        <Link to={row.sourceHref} data-history-source-link>
          {label}
        </Link>
      </>
    );
  }
  if (!row.stored) return <>{row.text}</>;
  return (
    <>
      <Clamp data={{ "data-history-clamp": row.kind }}>{row.text}</Clamp>
      <details className="global-work-details" data-history-full>
        <summary>Full event text</summary>
        {row.text}
      </details>
    </>
  );
}

function AuthoredRow({ row }: { row: HistoryRow }) {
  return (
    <tr data-history-row={row.kind} data-history-id={row.id}>
      <td>
        <span className="work-history-time" data-history-time>
          {historyUtc(row.recorded_at)}
        </span>
        <details className="global-work-details" data-history-occurred>
          <summary>Occurrence time</summary>
          {`Occurred ${historyUtc(row.occurred_at)}`}
        </details>
      </td>
      <td className="work-history-event" data-history-event>
        <EventCell row={row} />
      </td>
      <td>
        <span className="work-history-by" data-history-by>
          {NAME_NOT_RECORDED}
        </span>
        <details className="global-work-details" data-history-actor>
          <summary>Stored actor</summary>
          {`${row.actor_kind} · ${row.actor_id}`}
        </details>
      </td>
    </tr>
  );
}

/** The client pager inside the panel; paging issues no read and adds no URL state. */
function HistoryPager({ index, total, onPage }: { index: number; total: number; onPage: (index: number) => void }) {
  const last = Math.ceil(total / HISTORY_PAGE_SIZE) - 1;
  const a = index * HISTORY_PAGE_SIZE + 1;
  const b = Math.min(total, a + HISTORY_PAGE_SIZE - 1);
  return (
    <nav className="global-work-pager" aria-label="History pages" data-global-work-pager>
      <span data-global-work-showing>{`Showing ${a}–${b} of ${total}`}</span>
      {index > 0 ? (
        <button type="button" className="link-button" data-global-work-previous onClick={() => onPage(index - 1)}>
          Previous
        </button>
      ) : null}
      {index < last ? (
        <button type="button" className="link-button" data-global-work-next onClick={() => onPage(index + 1)}>
          Next
        </button>
      ) : null}
    </nav>
  );
}

/** The paged table; it mounts per loaded read, so a new read, Reload or another case/cutoff starts on page 1. */
function HistoryTable({ body }: { body: GlobalWorkDetailBody }) {
  const rows = historyRows(body);
  const [index, setIndex] = useState(0);
  const last = Math.max(0, Math.ceil(rows.length / HISTORY_PAGE_SIZE) - 1);
  const page = Math.min(index, last);
  const visible = rows.slice(page * HISTORY_PAGE_SIZE, (page + 1) * HISTORY_PAGE_SIZE);
  const gaps: ReactNode =
    page === last
      ? HISTORY_GAPS.map((gap) => (
          <tr key={gap} data-history-gap={gap}>
            <td>—</td>
            <td className="work-history-event">{gap}</td>
            <td>—</td>
          </tr>
        ))
      : null;
  return (
    <>
      <p className="global-work-scroll-hint" data-global-work-scroll-hint>
        {SCROLL_TABLE}
      </p>
      <DataTable labelledBy={HISTORY_TABLE_HEADING_ID}>
        <colgroup>
          {MIN_WIDTHS.map((width, i) => (
            <col key={i} style={{ width: `${width}px` }} />
          ))}
        </colgroup>
        <thead>
          <tr>
            {HISTORY_COLUMNS.map((h) => (
              <th key={h} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visible.map((row) => (
            <AuthoredRow key={row.id} row={row} />
          ))}
          {gaps}
        </tbody>
      </DataTable>
      {rows.length > HISTORY_PAGE_SIZE ? <HistoryPager index={page} total={rows.length} onPage={setIndex} /> : null}
    </>
  );
}

function HistoryPanel({ body }: { body: GlobalWorkDetailBody | null }) {
  return (
    <Panel heading={HISTORY_PANEL_HEADING} headingId={HISTORY_TABLE_HEADING_ID}>
      {body === null ? null : (
        <HistoryTable key={`${body.selected.case_id}|${body.selected.known_at}`} body={body} />
      )}
    </Panel>
  );
}

/** The routed frame (`WORK_REQUEST_HISTORY_ROUTE_PATH`): the shared request frame with the History tab. */
export function WorkRequestHistoryFrame({ client }: { client?: GlobalWorkClient }) {
  return (
    <WorkRequestFrame client={client} rootClass="work-request--history global-work--history" tab="history" accept={historyReadable}>
      {(body) => <HistoryPanel body={body} />}
    </WorkRequestFrame>
  );
}
