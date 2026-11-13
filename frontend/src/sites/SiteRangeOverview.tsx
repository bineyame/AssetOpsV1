/**
 * SR-5b (architect rev 9 §9.4, D-SR.9/D-SR.11): the mini-grid Site Overview over the shared date range. It reads
 * `range-overview` (one estate snapshot, the Portfolio's own selectors) and shows the range by default; one day is the
 * drill-in (`?day=`, the S5-01 board), reached from the day table and the day strip.
 *
 * Layout, after the v69 `mini` (8.18) site-overview skeleton: status line → outcome tiles → day by day → needs
 * attention (the Findings in this range) → next step. Every count, amount and money word is the server's; this file
 * only words the day states (D-E5.46 words, D-SR.50 retired Findings, D-SR.56 late-readings note).
 *
 * MOCK DEVIATION R721: v69 `site-overview` shows one window and has no day table. The range view keeps the skeleton
 *   (status → outcome tiles → needs attention → next step) and adds "Day by day" (a strip and a table) as its range
 *   form (D-SR.9), and it has no Operating context panel: the timeline is one day's, so it stays on the drill-in.
 *
 * The bar: this view declares nothing ("All pages"); the drill-in declares its day through its `FocusPicker`.
 */
import { useEffect, useState, type ReactNode } from "react";

import { DataTable, MetricCard, MetricCards, Panel, StatusBar } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import { dayGapWords } from "../ui/productWords";
import { formatDay } from "../ui/time";
import { rangeParams, type DayRange } from "../ui/sharedRange";
import { analysedDaysMoney, coverageStateWords, gapReasonClause, PARTIAL_MONEY_NOT_ADDED, STILL_PROCESSING } from "../estate/portfolioWords";
import { moneyText } from "../estate/estateFinancialsWords";
import { FINDING_INDEX_DOMAIN, type FindingIndexClient, type FindingIndexResult } from "./findingIndexClient";
import { OverviewRefused } from "./overviewSlots";
import { RowTable } from "./SiteFindingIndex";
import { RETRYING_COPY, STILL_UNAVAILABLE_COPY, TEMPORARILY_UNAVAILABLE } from "./temporarilyUnavailable";
import type { RangeDay, RangeOverviewClient, RangeOverviewRead, SiteRangeOverviewBody } from "./rangeOverviewClient";
import "./rangeOverview.css";

export const RANGE_OVERVIEW_LOADING = "Loading the site's overview for this date range.";
export const RANGE_NO_READINGS = "No readings received in this date range";
export const RANGE_NOT_SHOWN = "This date range can't be shown here";
export const RANGE_DAY_TABLE_HEADING = "Day by day";
export const RANGE_FINDINGS_HEADING = "Findings in this range";
export const RANGE_SEE_ALL_FINDINGS = "See all findings in this range";
export const OPEN_DAY = "Open day";
export const BEFORE_READINGS = "Before readings began";
export const CHECKED_NOTHING = "Checked: nothing to report";
export const CHECKED_NO_CURRENT = "Checked: no current findings";
/** Rows shown in "Findings in this range" (rev 9 §9.4 step 4). */
export const RANGE_FINDINGS_LIMIT = 5;
const NO_VALUE = "–";

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

/** The day's date label: the UTC day names the Site-local day of the same date (D-SR.61), so the date string itself. */
export function rangeDayLabel(day: string): string {
  return formatDay(`${day}T00:00:00Z`, { year: false, timeZone: "UTC" });
}

/** D-SR.50: " · 1 finding no longer supported" when the day meets retired Findings, else "". */
function retiredSuffix(day: RangeDay): string {
  const retired = day.retired_finding_count ?? 0;
  return retired > 0 ? ` · ${plural(retired, "finding", "findings")} no longer supported` : "";
}

/** The D-E5.46 full words of one day's state. */
export function rangeDayWords(day: RangeDay): string {
  switch (day.state) {
    case "FINDINGS":
      return `${plural(day.finding_count ?? 0, "finding", "findings")}${retiredSuffix(day)}`;
    case "CLEAR":
      return retiredSuffix(day) === "" ? CHECKED_NOTHING : `${CHECKED_NO_CURRENT}${retiredSuffix(day)}`;
    case "NOT_EXPECTED":
      // D-SR.56: the server's note replaces the words on the day readings began late.
      return day.note ?? BEFORE_READINGS;
    case "STILL_PROCESSING":
      return STILL_PROCESSING;
    default:
      return dayGapWords(day.state)?.label ?? dayGapWords("NOT_ANALYSED")?.label ?? "Not analysed yet";
  }
}

type DayTone = "amber" | "green" | "gray" | "blue" | "none";

function dayTone(day: RangeDay): DayTone {
  switch (day.state) {
    case "FINDINGS":
      return "amber";
    case "CLEAR":
      return "green";
    case "NOT_EXPECTED":
      return "none";
    case "STILL_PROCESSING":
    case "NOT_ANALYSED":
      return "blue";
    default:
      return "gray";
  }
}

/** One day's money in words: the summed amount, or why there is none. */
export function rangeDayMoney(day: RangeDay): string {
  if (day.money_state === "SUMMED") return moneyText(day.money, "outward") ?? NO_VALUE;
  if (day.money_state === "WITHHELD") return "Not counted: day not analysed";
  const reason = PARTIAL_MONEY_NOT_ADDED[day.money_state] ?? PARTIAL_MONEY_NOT_ADDED.NO_ELIGIBLE_LINES;
  return reason.charAt(0).toUpperCase() + reason.slice(1);
}

/** No reading arrived on any day of the range (every day is "no readings" or before readings began). */
export function rangeHasNoReadings(body: SiteRangeOverviewBody): boolean {
  return body.days.length > 0 && body.days.every((d) => d.state === "NO_READINGS" || (d.state === "NOT_EXPECTED" && d.note === undefined));
}

/** The status line: the coverage state in plain words, then the days analysed and the gap days (D-E5.46 label). */
export function rangeStatusLine(body: SiteRangeOverviewBody): string {
  if (rangeHasNoReadings(body)) return RANGE_NO_READINGS;
  const days = body.coverage.days;
  const state = coverageStateWords(body.coverage.state);
  if (days === null || days === undefined) return state;
  const clause = gapReasonClause(days);
  return `${state} · ${days.checked} of ${days.requested} days analysed${clause ? ` · ${clause}` : ""}`;
}

/** The money tile's note: the PARTIAL label when the Site is partly analysed, else the card's own detail. */
function moneyNote(body: SiteRangeOverviewBody): string | null {
  const partial = body.money.partial;
  if (body.status === "PARTIAL" && partial !== null) {
    const days = { checked: partial.analysed_days, requested: partial.requested_days, gaps: partial.gaps };
    const amount = partial.amount === null ? null : moneyText(partial.amount, "outward");
    if (amount !== null) return analysedDaysMoney(amount, days);
    const reason = PARTIAL_MONEY_NOT_ADDED[partial.state] ?? PARTIAL_MONEY_NOT_ADDED.NO_ELIGIBLE_LINES;
    const clause = gapReasonClause(days);
    return `${reason.charAt(0).toUpperCase()}${reason.slice(1)} · ${days.checked} of ${days.requested} days analysed${clause ? ` · ${clause}` : ""}`;
  }
  return body.money.card.detail;
}

function quantityText(body: SiteRangeOverviewBody): string | null {
  const q = body.money.quantity;
  if (q === null) return null;
  return q.low === q.high ? `${q.low} ${q.unit} at stake` : `${q.low}–${q.high} ${q.unit} at stake`;
}

const known = (n: number | null | undefined): string => (n === null || n === undefined ? "Not known yet" : String(n));

function Tiles({ body }: { body: SiteRangeOverviewBody }) {
  const empty = rangeHasNoReadings(body);
  const f = body.findings;
  const a = body.actions;
  const quantity = quantityText(body);
  const note = moneyNote(body);
  return (
    <MetricCards label="Outcomes in this date range" data={{ "data-range-tiles": "" }}>
      <MetricCard
        label="Fuel cost at stake"
        value={empty ? NO_VALUE : body.money.card.display_value ?? "No supported value"}
        note={empty ? undefined : [note, quantity].filter(Boolean).join(" · ") || undefined}
        data={{ "data-range-tile": "money", "data-range-money-state": body.money.card.state }}
      />
      <MetricCard
        label="Findings"
        value={empty ? NO_VALUE : known(f.count)}
        note={empty ? undefined : `Confirmed ${known(f.confirmed)} · Not yet confirmed ${known(f.not_confirmed)}`}
        data={{ "data-range-tile": "findings" }}
      />
      <MetricCard
        label="Actions"
        value={empty ? NO_VALUE : known(a.open)}
        note={empty ? undefined : `Open · Awaiting verification ${known(a.awaiting_verification)}`}
        data={{ "data-range-tile": "actions" }}
      />
      <MetricCard
        label="Days analysed"
        value={empty ? NO_VALUE : `${body.dispatch.days_analysed} of ${body.dispatch.days_requested}`}
        note={
          empty || (body.dispatch.days_with_retired_findings ?? 0) === 0
            ? undefined
            : `${plural(body.dispatch.days_with_retired_findings ?? 0, "day", "days")} with a finding no longer supported`
        }
        data={{ "data-range-tile": "days" }}
      />
    </MetricCards>
  );
}

/** Rows of 7 cells when the range is longer than 14 days (the strip wraps by week), else one row. */
function stripRows(days: RangeDay[]): RangeDay[][] {
  if (days.length <= 14) return [days];
  const rows: RangeDay[][] = [];
  for (let i = 0; i < days.length; i += 7) rows.push(days.slice(i, i + 7));
  return rows;
}

/**
 * SR-5b/SR-5c: the range's days, a strip of state cells above a table. Each cell and each row opens the day
 * (`dayHref`, the range carried by `RangeLink`). Used by the range Overview and by Performance › Dispatch.
 */
export function RangeDayTable({
  body,
  dayHref,
  headingId,
  name,
}: {
  body: SiteRangeOverviewBody;
  dayHref: (day: string) => string;
  /** The heading the table is labelled by (the enclosing panel's). */
  headingId: string;
  /** A data name, so two pages' tables are told apart in tests and evidence. */
  name: string;
}) {
  return (
    <div className="range-days" data-range-days={name}>
      <div className="range-strip" role="group" aria-label="Days in this range">
        {stripRows(body.days).map((row) => (
          <div className="range-strip__row" key={row[0]?.day ?? "empty"}>
            {row.map((d) => (
              <Link
                key={d.day}
                to={dayHref(d.day)}
                className={`range-strip__cell tone-${dayTone(d)}`}
                aria-label={`${rangeDayLabel(d.day)}: ${rangeDayWords(d)}`}
                data-range-strip-day={d.day}
                data-range-day-state={d.state}
              >
                {d.day.slice(8).replace(/^0/, "")}
              </Link>
            ))}
          </div>
        ))}
      </div>
      <DataTable labelledBy={headingId}>
        <thead>
          <tr>
            <th scope="col">Day</th>
            <th scope="col">What we found</th>
            <th scope="col">Fuel cost at stake</th>
            <th scope="col">
              <span className="visually-hidden">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {body.days.map((d) => (
            <tr key={d.day} data-range-day={d.day} data-range-day-state={d.state}>
              <th scope="row">{rangeDayLabel(d.day)}</th>
              <td>
                <span className={`range-state tone-${dayTone(d)}`} aria-hidden="true" />
                <span data-range-day-words>{rangeDayWords(d)}</span>
              </td>
              <td data-range-day-money={d.money_state}>{rangeDayMoney(d)}</td>
              <td>
                <Link to={dayHref(d.day)} data-range-open-day={d.day}>
                  {OPEN_DAY}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

export const RANGE_MONEY_HEADING = "Fuel cost at stake in this range";
export const PRICES_VALID_NOW = "Prices valid now";
const RANGE_MONEY_LOADING = "Loading the fuel cost at stake for this date range.";

/**
 * SR-5d (rev 9 §9.4): mini-grid Financials' range money: the `range-overview` money card (the Portfolio card's words,
 * with the PARTIAL label) and the days that carry money, each linking to its drill-in day. Refusals in the read's words.
 * MOCK DEVIATION R723: v69 `site-financials` (mini-grid) shows assumptions only; this block and the "Prices valid now"
 * heading are the range form (D-SR.9).
 */
export function RangeMoneyBlock({ state, dayHref }: { state: RangeOverviewState; dayHref: (day: string) => string }) {
  const { read, retrying } = state;
  const headingId = "site-financials-range-money-heading";
  if (read?.status !== "loaded" || retrying) {
    return (
      <Panel heading={RANGE_MONEY_HEADING} headingId={headingId}>
        <RangeReadState read={read} retrying={retrying} loading={RANGE_MONEY_LOADING} title="Fuel cost at stake unavailable" />
      </Panel>
    );
  }
  const body = read.value;
  const empty = rangeHasNoReadings(body);
  const note = empty ? null : [moneyNote(body), quantityText(body)].filter(Boolean).join(" · ") || null;
  const priced = body.days.filter((d) => d.money !== null);
  return (
    <Panel heading={RANGE_MONEY_HEADING} headingId={headingId}>
      <div data-range-money data-range-money-state={body.money.card.state}>
        <MetricCards label="Fuel cost at stake in this date range">
          <MetricCard
            label="Fuel cost at stake"
            value={empty ? NO_VALUE : body.money.card.display_value ?? "No supported value"}
            note={note ?? undefined}
            data={{ "data-range-tile": "money" }}
          />
        </MetricCards>
        {empty ? (
          <p data-range-money-days="none">{RANGE_NO_READINGS}</p>
        ) : priced.length === 0 ? (
          <p data-range-money-days="none">No day in this range has a fuel cost at stake.</p>
        ) : (
          <ul className="range-money-days" aria-label="Fuel cost at stake by day">
            {priced.map((d) => (
              <li key={d.day} data-range-money-day={d.day}>
                {rangeDayLabel(d.day)}: {rangeDayMoney(d)} ·{" "}
                <Link to={dayHref(d.day)} data-range-open-day={d.day}>
                  {OPEN_DAY}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}

export interface RangeOverviewLinks {
  /** The one-day board for a day (`?day=`); `RangeLink` carries the range. */
  day: (day: string) => string;
  /** The Site Findings page (the range carried). */
  findings: string;
  /** One Finding at a revision. */
  finding: (findingId: string, revisionId?: string | null) => string;
  /** Performance › Dispatch at one day (the Finding row's Domain cell). */
  dispatch?: (day: string, intervalRevisionId: string | null) => string;
}

const FINDINGS_HEADING_ID = "site-range-findings-heading";

/** The range's Finding list, read once for both "Findings in this range" and the Next step panel. */
function useRangeFindings(client: FindingIndexClient | undefined, siteCode: string, window: { from: string; to: string }) {
  const [read, setRead] = useState<FindingIndexResult | null>(null);
  useEffect(() => {
    let active = true;
    setRead(null);
    if (client === undefined) return undefined;
    void client
      .getFindingIndex(siteCode, { domain: FINDING_INDEX_DOMAIN, from: window.from, to: window.to, limit: RANGE_FINDINGS_LIMIT, cursor: null })
      .then((result) => {
        if (active) setRead(result);
      });
    return () => {
      active = false;
    };
  }, [client, siteCode, window.from, window.to]);
  return read;
}

function FindingsInRange({ read, links }: { read: FindingIndexResult | null; links: RangeOverviewLinks }) {
  const all = (
    <p>
      <Link to={links.findings} data-range-all-findings>
        {RANGE_SEE_ALL_FINDINGS} →
      </Link>
    </p>
  );
  if (read === null) return <p data-range-findings="loading">Loading the findings in this range.</p>;
  if (read.status !== "loaded") {
    return (
      <>
        <p data-range-findings="unavailable">The findings in this range could not be listed here.</p>
        {all}
      </>
    );
  }
  const rows = read.value.rows.slice(0, RANGE_FINDINGS_LIMIT);
  return (
    <>
      {rows.length === 0 ? (
        <p data-range-findings="none">{read.value.rows_statement ?? "No findings in this range."}</p>
      ) : (
        <RowTable
          rows={rows}
          labelledBy={FINDINGS_HEADING_ID}
          links={{ scope: () => links.findings, finding: links.finding, dispatch: links.dispatch }}
        />
      )}
      {all}
    </>
  );
}

function NextStepInRange({ first, links }: { first: { id: string; revision: string } | null; links: RangeOverviewLinks }) {
  if (first === null) return <p data-overview-next="none">No supported next action in this range.</p>;
  return (
    <div className="v69-prose" data-overview-next="finding">
      <h3>Review the first finding in this range</h3>
      <p className="overview-next__actions">
        <Link className="button" to={links.finding(first.id, first.revision)} data-overview-next-finding={first.id}>
          Open the finding
        </Link>
      </p>
    </div>
  );
}

function Loaded({
  body,
  siteCode,
  window,
  findingIndex,
  links,
}: {
  body: SiteRangeOverviewBody;
  siteCode: string;
  window: { from: string; to: string };
  findingIndex?: FindingIndexClient;
  links: RangeOverviewLinks;
}) {
  const findings = useRangeFindings(findingIndex, siteCode, window);
  const row = findings?.status === "loaded" ? findings.value.rows[0] : undefined;
  const first = row === undefined ? null : { id: row.finding_id, revision: row.finding_revision_id };
  return (
    <div className="site-window-overview site-range-overview" data-overview-state="range" data-range-site={body.site.site_code}>
      <StatusBar label="This date range" data={{ "data-range-status": body.status }}>
        <span data-range-status-line>{rangeStatusLine(body)}</span>
      </StatusBar>
      <Tiles body={body} />
      <Panel
        heading={RANGE_DAY_TABLE_HEADING}
        headingId="site-range-days-heading"
        description="Each day of the range; open a day to see what happened on it"
      >
        <RangeDayTable body={body} dayHref={links.day} headingId="site-range-days-heading" name="overview" />
      </Panel>
      <div className="panel-pair">
        <Panel heading={RANGE_FINDINGS_HEADING} headingId={FINDINGS_HEADING_ID} description="Needs attention: the first findings in this range">
          {findingIndex === undefined ? (
            <p>
              <Link to={links.findings} data-range-all-findings>
                {RANGE_SEE_ALL_FINDINGS} →
              </Link>
            </p>
          ) : (
            <FindingsInRange read={findings} links={links} />
          )}
        </Panel>
        <Panel heading="Next step" headingId="site-overview-next-heading">
          <NextStepInRange first={first} links={links} />
        </Panel>
      </div>
    </div>
  );
}

/** Reads `range-overview` for a range; `retrying` is set while a 503 unavailable answer is being retried. */
export interface RangeOverviewState {
  read: RangeOverviewRead | null;
  retrying: boolean;
  window: { from: string; to: string };
}

/** Reads `range-overview` for a range; nothing is read while `range` or `client` is null (the hook stays mounted). */
export function useRangeOverview(
  client: RangeOverviewClient | null | undefined,
  siteCode: string,
  range: (DayRange & { known_at: string | null }) | null,
): RangeOverviewState {
  const [read, setRead] = useState<RangeOverviewRead | null>(null);
  const [retrying, setRetrying] = useState(false);
  const query = range === null ? null : rangeParams(range);
  const from = query?.get("from") ?? "";
  const to = query?.get("to") ?? "";
  const knownAt = query?.get("known_at") ?? null;
  useEffect(() => {
    let active = true;
    setRead(null);
    setRetrying(false);
    if (client === null || client === undefined || from === "") return undefined;
    void client
      .getRangeOverview(siteCode, { from, to, known_at: knownAt }, () => {
        if (active) setRetrying(true);
        return active;
      })
      .then((result) => {
        if (!active) return;
        setRetrying(false);
        setRead(result);
      });
    return () => {
      active = false;
    };
  }, [client, siteCode, from, to, knownAt]);
  return { read, retrying, window: { from, to } };
}

/** The read's waiting, refused and unavailable states, in the page's words; null when the body is loaded. */
export function RangeReadState({
  read,
  retrying,
  loading,
  title,
}: {
  read: RangeOverviewRead | null;
  retrying: boolean;
  loading: string;
  title: string;
}): ReactNode {
  if (retrying) {
    return (
      <p role="status" data-temporarily-unavailable>
        {RETRYING_COPY}
      </p>
    );
  }
  if (read === null) return <p>{loading}</p>;
  if (read.status === "loaded") return null;
  if (read.status === "refused" && read.code === TEMPORARILY_UNAVAILABLE) {
    return <OverviewRefused name="temporarily-unavailable" title={title} reason={<span data-temporarily-unavailable>{STILL_UNAVAILABLE_COPY}</span>} />;
  }
  if (read.status === "refused" && read.httpStatus === 422) {
    return <OverviewRefused name="invalid-range" title={RANGE_NOT_SHOWN} reason="Choose another date range in the bar above." />;
  }
  return (
    <OverviewRefused
      name="unavailable"
      title={title}
      reason="The overview for this date range could not be read. This is a statement about the read, not about the site's evidence."
    />
  );
}

/** A 404 answer: the range read does not know this Site (e.g. one that is not imported); the page keeps its one-day form. */
export const rangeNotKnown = (state: RangeOverviewState): boolean =>
  !state.retrying && state.read?.status === "refused" && state.read.httpStatus === 404;

export interface SiteRangeOverviewProps {
  siteCode: string;
  /** The `useRangeOverview` state (the caller owns the read, so a 404 can fall back without remounting the page). */
  state: RangeOverviewState;
  links: RangeOverviewLinks;
  findingIndex?: FindingIndexClient;
}

export function SiteRangeOverview({ siteCode, state, links, findingIndex }: SiteRangeOverviewProps) {
  const { read, retrying, window } = state;
  if (read?.status === "loaded" && !retrying) {
    return <Loaded body={read.value} siteCode={siteCode} window={window} findingIndex={findingIndex} links={links} />;
  }
  return <RangeReadState read={read} retrying={retrying} loading={RANGE_OVERVIEW_LOADING} title="Overview unavailable" />;
}
