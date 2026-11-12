/**
 * W3-01 commit 3: pieces shared by the four estate Finding lens roots and the estate Actions root - the one
 * date/cutoff bar (spec S17), the URL query state, the Site basis-state chip (Run 12 ruling 3), the coverage
 * limitation sentence and the refusal view. Nothing here reads a mock value.
 */
import type { ReactNode } from "react";
import { RangeLink as Link } from "../ui/RangeLink";
import { Notice } from "../ui";
import { formatDayTime } from "../ui/time";
import { TimeZoneNote } from "../ui/TimeZoneNote";
import { rangeWindow, validDay } from "../shell/sharedRange";
import {
  FIRST_PAGE_CODES,
  WINDOW_NOT_VALID,
  invalidWindowCopy,
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
  // SR-1 (SR.3): the shared range's short day form (`to` included) reads as the same UTC window as the instant form,
  // so both address forms make the same request. Any other value is passed on unchanged for the server to judge.
  const from = params.get("from");
  const to = params.get("to");
  const days = from !== null && to !== null && validDay(from) && validDay(to) ? rangeWindow({ from, to }) : null;
  return {
    from: days?.from ?? from ?? fallback.from,
    to: days?.to ?? to ?? fallback.to,
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

/** A wire instant as `1 Nov 2026, 02:09` (POLISH §3 Times: delegates to `ui/time.ts`; the bar's note says UTC). */
export function utcInstant(wire: string): string {
  return formatDayTime(wire);
}

export const EARLIER_CUTOFF = "Showing an earlier point in time.";
/** POLISH §3.1 / Addendum 7 Q5 (R652): the closed disclosure that holds the earlier-cutoff picker. */
export const EARLIER_POINT_SUMMARY = "View an earlier point in time";
export const PARTIAL_COVERAGE = "Some sites are not yet assessed; estate totals are unknown.";
export const PENDING_EVIDENCE = "New evidence is being assessed.";
export const PARTIAL_TOTALS = "Some sites have no selected result; totals are unknown.";

/**
 * The cutoff line (Commit-3 r1 ruling L2, POLISH §3.1 and Addendum 7 Q5): no response yet reads `Latest information`
 * for an omitted cutoff; a loaded live page one reads `Latest information, as of {time}`; an explicit cutoff or a
 * cursor continuation is pinned and reads `Information as of {time}`.
 */
function cutoffBarText(query: Pick<EstateQuery, "known_at"> & { cursor?: string | null }, body: EstateEnvelope | null): string {
  if (body === null) return query.known_at ? `Information as of ${utcInstant(query.known_at)}` : "Latest information";
  const at = utcInstant(body.window.known_at);
  return query.known_at || query.cursor ? `Information as of ${at}` : `Latest information, as of ${at}`;
}

/**
 * SR-1/SR-2: every estate page's range is set in the shell's shared bar (the per-page `EstateDateBar` form is gone, so
 * no page shows two date controls). The page keeps only the read's cutoff line here - the effective
 * cutoff, the earlier-cutoff words, `Window not valid` for a refused window (never the dates) and the UTC note.
 */
export function EstateCutoffLine({
  query,
  body,
  windowRefused = false,
}: {
  query: Pick<EstateQuery, "known_at" | "cursor">;
  body: EstateEnvelope | null;
  windowRefused?: boolean;
}) {
  return (
    <p className="site-date-bar estate-date-bar estate-cutoff-line" data-estate-cutoff-line>
      {windowRefused ? (
        <span className="site-date-bar__window" data-estate-window>
          {WINDOW_NOT_VALID}
        </span>
      ) : null}
      <span className="site-date-bar__cutoff" data-estate-cutoff>
        {cutoffBarText(query, body)}
      </span>
      {body?.status === "HISTORICAL" ? (
        <span className="estate-date-bar__historical" data-estate-historical>
          {EARLIER_CUTOFF}
        </span>
      ) : null}
      <TimeZoneNote />
    </p>
  );
}

const SITE_STATE_WORDS: Readonly<Partial<Record<EstateSiteState, { text: string; tone: string }>>> = {
  PENDING_RECOMPUTE: { text: PENDING_EVIDENCE, tone: "amber" },
  STALE_SOURCE: { text: "This result may miss newer readings.", tone: "amber" },
  HISTORICAL: { text: "Earlier evidence cutoff", tone: "neutral" },
  UNKNOWN: { text: "Not yet assessed", tone: "amber" },
  // COV-PARTIAL MOCK DEVIATION R622: the mock has no day gaps.
  PARTIAL: { text: "Incomplete days", tone: "amber" },
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
  // COV-PARTIAL MOCK DEVIATION R622: the mock has no day gaps.
  if (states.has("PARTIAL")) out.push("Some sites have incomplete days.");
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

/**
 * A refused or unreadable read: the refusal table's exact UI copy, with a page-one link where it asks for one. An
 * `INVALID_WINDOW` refusal uses the shared cross-card window sentence classified from the page query (Q14).
 */
export function EstateRefusal({
  code,
  copy,
  firstPage,
  window,
}: {
  code: string;
  copy: string;
  firstPage: string;
  window?: Pick<EstateQuery, "from" | "to">;
}) {
  const text = code === "INVALID_WINDOW" && window !== undefined ? invalidWindowCopy(window) : copy;
  return (
    <div className="notice v69-notice" data-page-refusal={code}>
      {code === "INVALID_WINDOW" ? <strong className="notice__title" data-refusal-title>Window cannot be read</strong> : null}
      <p>{text}</p>
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
