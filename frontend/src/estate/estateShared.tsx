/**
 * W3-01 commit 3: pieces shared by the four estate Finding lens roots and the estate Actions root - the one UTC
 * date/cutoff bar (spec S17), the URL query state, the Site basis-state chip (Run 12 ruling 3), the coverage
 * limitation sentence and the refusal view. Nothing here reads a mock value.
 */
import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Notice } from "../ui";
import {
  FIRST_PAGE_CODES,
  type EstateEnvelope,
  type EstateQuery,
  type EstateSiteState,
  type EstateStateFilter,
} from "./estateClient";
import "./estate.css";

const DAY_MS = 24 * 60 * 60 * 1000;

/** `YYYY-MM-DDT00:00:00Z` for a UTC midnight. */
function midnight(ms: number): string {
  return `${new Date(ms).toISOString().slice(0, 10)}T00:00:00Z`;
}

/** S17: first load is the last seven complete UTC days ending at today's 00:00 UTC; `known_at` omitted (live). */
export function defaultWindow(now: number = Date.now()): { from: string; to: string } {
  const today = Date.UTC(new Date(now).getUTCFullYear(), new Date(now).getUTCMonth(), new Date(now).getUTCDate());
  return { from: midnight(today - 7 * DAY_MS), to: midnight(today) };
}

const STATE_FILTERS: readonly EstateStateFilter[] = ["all", "supported", "unconfirmed", "no_longer_supported", "merged"];

/** The query a page reads from its URL: `from,to,known_at` (S17), `state` (Findings) and `cursor`. */
export function queryFromParams(params: URLSearchParams, now?: number): EstateQuery & { state: EstateStateFilter } {
  const fallback = defaultWindow(now);
  const state = params.get("state");
  return {
    from: params.get("from") ?? fallback.from,
    to: params.get("to") ?? fallback.to,
    known_at: params.get("known_at"),
    cursor: params.get("cursor"),
    state: STATE_FILTERS.includes(state as EstateStateFilter) ? (state as EstateStateFilter) : "all",
  };
}

/** An app href on `path` keeping the window and cutoff; `state`/`cursor` only when given (page one otherwise). */
export function estateHref(
  path: string,
  query: Pick<EstateQuery, "from" | "to" | "known_at">,
  extra: { state?: EstateStateFilter; cursor?: string | null } = {},
): string {
  const params = new URLSearchParams();
  params.set("from", query.from);
  params.set("to", query.to);
  if (query.known_at) params.set("known_at", query.known_at);
  if (extra.state && extra.state !== "all") params.set("state", extra.state);
  if (extra.cursor) params.set("cursor", extra.cursor);
  return `${path}?${params.toString()}`;
}

/** A wire UTC instant as `YYYY-MM-DD HH:MM:SS UTC`. */
export function utcInstant(wire: string): string {
  return `${wire.slice(0, 10)} ${wire.slice(11, 19)} UTC`;
}

/** The last included day of a half-open `[from, to)` whole-day window. */
function lastDay(to: string): string {
  return new Date(Date.parse(to) - 1).toISOString().slice(0, 10);
}

export const EARLIER_CUTOFF = "This is an earlier evidence cutoff.";
export const PARTIAL_COVERAGE = "Some sites are not yet assessed; estate totals are unknown.";
export const PENDING_EVIDENCE = "New evidence is being assessed.";
export const PARTIAL_TOTALS = "Some sites have no selected result; totals are unknown.";

/**
 * The cutoff literal (Commit-3 r1 ruling L2): no response yet reads `latest` for an omitted cutoff; a loaded live
 * page one adds the read-time suffix; a cursor continuation is pinned by its cursor and has no suffix.
 */
function cutoffBarText(query: Pick<EstateQuery, "known_at"> & { cursor?: string | null }, body: EstateEnvelope | null): string {
  if (body === null) return `Evidence cutoff ${query.known_at ? utcInstant(query.known_at) : "latest"}`;
  const shown = `Evidence cutoff ${utcInstant(body.window.known_at)}`;
  return query.known_at || query.cursor ? shown : `${shown} (latest at read time)`;
}

/**
 * The one UTC date/cutoff bar (S17, Run 12 ruling 3). It shows the request window and the effective cutoff the
 * read reports; a historical top-level read (an explicit earlier cutoff, or a page two read after its cutoff)
 * says `This is an earlier evidence cutoff.`. Changing the window or cutoff restarts at page one.
 */
export function EstateDateBar({
  query,
  body,
  onApply,
}: {
  query: Pick<EstateQuery, "from" | "to" | "known_at" | "cursor">;
  body: EstateEnvelope | null;
  onApply: (next: Pick<EstateQuery, "from" | "to" | "known_at">) => void;
}) {
  const [first, setFirst] = useState(query.from.slice(0, 10));
  const [last, setLast] = useState(lastDay(query.to));
  const [cutoff, setCutoff] = useState(query.known_at ? query.known_at.slice(0, 19) : "");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!first || !last) return;
    const to = midnight(Date.parse(`${last}T00:00:00Z`) + DAY_MS);
    onApply({ from: `${first}T00:00:00Z`, to, known_at: cutoff ? `${cutoff.length === 16 ? `${cutoff}:00` : cutoff}Z` : null });
  };
  const cutoffText = cutoffBarText(query, body);
  return (
    <form className="site-date-bar estate-date-bar" onSubmit={submit} data-estate-date-bar>
      <span className="site-date-bar__window" data-estate-window>
        Window {query.from.slice(0, 10)} to {lastDay(query.to)} (UTC days)
      </span>
      <span className="site-date-bar__cutoff" data-estate-cutoff>
        {cutoffText}
      </span>
      {body?.status === "HISTORICAL" ? (
        <span className="estate-date-bar__historical" data-estate-historical>
          {EARLIER_CUTOFF}
        </span>
      ) : null}
      <label className="v69-chip-field">
        From{" "}
        <input className="v69-chip-control" type="date" value={first} onChange={(e) => setFirst(e.target.value)} />
      </label>
      <label className="v69-chip-field">
        to (included){" "}
        <input className="v69-chip-control" type="date" value={last} onChange={(e) => setLast(e.target.value)} />
      </label>
      <label className="v69-chip-field">
        Evidence cutoff (UTC){" "}
        <input
          className="v69-chip-control"
          type="datetime-local"
          step={1}
          value={cutoff}
          onChange={(e) => setCutoff(e.target.value)}
        />
      </label>
      <button className="v69-chip" type="submit">
        Show
      </button>
    </form>
  );
}

const SITE_STATE_WORDS: Readonly<Partial<Record<EstateSiteState, { text: string; tone: string }>>> = {
  PENDING_RECOMPUTE: { text: PENDING_EVIDENCE, tone: "amber" },
  STALE_SOURCE: { text: "This result may miss newer readings.", tone: "amber" },
  HISTORICAL: { text: "Earlier evidence cutoff", tone: "neutral" },
  UNKNOWN: { text: "Not yet assessed", tone: "amber" },
};

/**
 * A row's Site basis-state chip (Run 12 ruling 3): the literal stored basis state, never the page-two response
 * label. CURRENT and NOT_APPLICABLE show no chip.
 */
export function SiteStateChip({ state }: { state: EstateSiteState }) {
  const words = SITE_STATE_WORDS[state];
  if (words === undefined) return null;
  return (
    <span className={`estate-chip estate-chip--${words.tone}`} data-estate-site-state={state}>
      {words.text}
    </span>
  );
}

/**
 * The source limitation placed immediately before a page's static notice: earlier cutoff, then pending, stale
 * and incomplete coverage, from the response's top-level `status` and its Site coverage states.
 */
export function limitationSentences(body: EstateEnvelope, partial: string): string[] {
  const states = new Set(body.coverage.sites.map((site) => site.state));
  const out: string[] = [];
  if (body.status === "HISTORICAL") out.push(EARLIER_CUTOFF);
  if (states.has("PENDING_RECOMPUTE")) out.push(PENDING_EVIDENCE);
  if (states.has("STALE_SOURCE")) out.push("Some sites' results may miss newer readings.");
  if (body.coverage.state !== "COMPLETE") out.push(partial);
  return out;
}

export function LimitationNotice({ sentences }: { sentences: string[] }) {
  if (sentences.length === 0) return null;
  return (
    <Notice data={{ "data-estate-limitation": "" }}>
      {sentences.map((sentence) => (
        <span key={sentence} className="estate-limitation__line">
          {sentence}{" "}
        </span>
      ))}
    </Notice>
  );
}

/** A refused or unreadable read: the refusal table's exact UI copy, with a page-one link where it asks for one. */
export function EstateRefusal({ code, copy, firstPage }: { code: string; copy: string; firstPage: string }) {
  return (
    <div className="notice v69-notice" data-page-refusal={code}>
      <p>{copy}</p>
      {FIRST_PAGE_CODES.has(code) ? (
        <p>
          <Link to={firstPage}>First page</Link>
        </p>
      ) : null}
    </div>
  );
}

/** Next page / first page links under a table (the cursor is opaque and passed back unchanged). */
export function Pager({ next, first, paged }: { next: string | null; first: string; paged: boolean }): ReactNode {
  if (next === null && !paged) return null;
  return (
    <p className="estate-pager" data-estate-pager>
      {paged ? <Link to={first}>First page</Link> : null}
      {paged && next !== null ? " · " : null}
      {next !== null ? <Link to={next}>Next page</Link> : null}
    </p>
  );
}
