/**
 * SR-7a (sequence doc rev 10 §10.3, rev 10a.2 Q8; D-SR.26, D-SR.45): the mini-grid Service tab over the date range.
 * One row per Site-local day of the range (`window_days`, D-SR.45 J1) from `service-range`: the stored
 * `critical_served` day value only. Served and not-served energy are shown for counted days (SERVED_ALL, SHORTFALL);
 * every other state spans the row in words, never a zero. A counted PARTIAL day is flagged (D-SR.45 J2). No all-load or
 * interruption figure is invented over the range: those cards exist per hour, one click away ("Open the 12:00 hour").
 * The range view declares nothing to the date-range bar (D-SR.57); the hour page's FocusPicker is its only declarer.
 *
 * MOCK DEVIATION R725: v69 `service` (screen 8.21) is one selected hour; over a range the tab is a day table with the
 * hour page as its drill-in.
 */
import type { ReactNode } from "react";

import { RangeLink as Link } from "../ui/RangeLink";
import { DataTable, Panel, StatusBar } from "../ui";
import { DEFAULT_SITE_RANGE_CLIENT, type RangeWindowQuery, type ServiceRangeBody, type ServiceRangeDay, type SiteRangeClient } from "./siteRangeClient";
import { OPEN_NOON_HOUR, RangeNotLoaded, dayWords, gapDaysText, useRangeRead, useWholeRangeState } from "./SiteRangeParts";

export const SERVICE_RANGE_NOT_APPLICABLE = "Critical service over a range is read for mini-grid sites only.";
export const SERVICE_RANGE_OPEN_A_DAY = "Delivered load and interruptions: open a day.";
export const SERVICE_NO_VALUE = "No critical-load figure for this day";

/** Full words per day state (the gap words follow the build sheet's gap table; D-SR.26 for NO_VALUE). */
export const SERVICE_DAY_WORDS: Record<string, string> = {
  SERVED_ALL: "All critical load served",
  SHORTFALL: "Shortfall: some critical load not served",
  NO_VALUE: SERVICE_NO_VALUE,
  NO_READINGS: "No readings received for this day",
  NOT_ENOUGH_READINGS: "Not enough readings received to analyse this day",
  STILL_PROCESSING: "Still being prepared",
  NOT_EXPECTED: "Before this Site's readings began",
};

/** Short reasons for the status line's day groups. */
const SHORT_REASON: Record<string, string> = {
  NO_VALUE: "no critical-load figure",
  NO_READINGS: "no readings",
  NOT_ENOUGH_READINGS: "not enough readings",
  STILL_PROCESSING: "still being prepared",
  NOT_EXPECTED: "before readings began",
};

const COUNTED = new Set(["SERVED_ALL", "SHORTFALL"]);

const KWH = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const kwh = (value: string | number | null): string => (value === null ? "–" : `${KWH.format(Number(value))} kWh`);
const hours = (value: number | null): string => (value === null ? "–" : `${KWH.format(value)} h`);

function ServiceRangeStatus({ body }: { body: ServiceRangeBody }) {
  const { totals } = body;
  const gaps = body.days
    .filter((d) => !COUNTED.has(d.state))
    .map((d) => ({ day: d.local_day, reason: SHORT_REASON[d.state] ?? "no usable result" }));
  const partialDays = body.days.filter((d) => COUNTED.has(d.state) && d.partial).length;
  const lead =
    totals.days_counted === 0
      ? "No day in this range has a critical-service figure"
      : `${kwh(totals.served_kwh)} critical load served, ${kwh(totals.unserved_kwh)} not served, for ${totals.days_counted} of ${totals.days_requested} days analysed`;
  return (
    <StatusBar label="Critical service over the range" items data={{ "data-service-range-status": "" }}>
      <span className="status-strip__item" data-service-range-summary>
        {`${lead}${gapDaysText(gaps)}`}
      </span>
      {partialDays > 0 ? (
        <span className="status-strip__item" data-service-partial-days>
          {`${partialDays} ${partialDays === 1 ? "day was" : "days were"} only partly covered`}
        </span>
      ) : null}
    </StatusBar>
  );
}

function stateCell(day: ServiceRangeDay): ReactNode {
  const words = SERVICE_DAY_WORDS[day.state] ?? "No usable result for this day";
  if (!day.partial) return words;
  return (
    <>
      {words}
      <span className="mini-cited" data-service-day-partial>{` · Partial day: ${hours(day.covered_hours)} of ${hours(day.operating_hours)} covered`}</span>
    </>
  );
}

function ServiceDayTable({ body }: { body: ServiceRangeBody }) {
  const wholeRange = useWholeRangeState();
  return (
    <Panel
      heading="Critical service by day"
      headingId="mini-service-range-days-heading"
      description="Critical load served and not served on each Site-local day of the date range."
      flush
    >
      <DataTable labelledBy="mini-service-range-days-heading">
        <thead>
          <tr>
            <th scope="col">Day</th>
            <th scope="col">Served</th>
            <th scope="col">Not served</th>
            <th scope="col">Hours covered</th>
            <th scope="col">State</th>
            <th scope="col">Hour detail</th>
          </tr>
        </thead>
        <tbody>
          {body.days.map((day) => (
            <tr key={day.local_day} data-service-range-day={day.local_day} data-service-day-state={day.state}>
              <th scope="row">{dayWords(day.local_day)}</th>
              {COUNTED.has(day.state) ? (
                <>
                  <td>{kwh(day.served_kwh)}</td>
                  <td>{kwh(day.unserved_kwh)}</td>
                  <td>{`${hours(day.covered_hours)} of ${hours(day.operating_hours)}`}</td>
                  <td>{stateCell(day)}</td>
                </>
              ) : (
                <td colSpan={4} data-panel-gap="service-range-day">
                  <span className="not-available-yet">{stateCell(day)}</span>
                </td>
              )}
              <td>
                <Link to={day.hour_link} state={wholeRange}>
                  {OPEN_NOON_HOUR}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </Panel>
  );
}

export function MiniServiceRangePage({ body }: { body: ServiceRangeBody }) {
  return (
    <>
      <ServiceRangeStatus body={body} />
      <ServiceDayTable body={body} />
      <p className="mini-cited" data-service-range-open-a-day>
        {SERVICE_RANGE_OPEN_A_DAY}
      </p>
    </>
  );
}

/** The Service tab over the range: one `service-range` read for the address range. */
export function MiniServiceRange({
  siteCode,
  window,
  client = DEFAULT_SITE_RANGE_CLIENT,
}: {
  siteCode: string;
  window: RangeWindowQuery;
  client?: SiteRangeClient;
}): ReactNode {
  const key = `${siteCode}|${window.from}|${window.to}|${window.known_at ?? ""}`;
  const { read, retrying } = useRangeRead((onRetrying) => client.getServiceRange(siteCode, window, onRetrying), key);
  return (
    <div className="mini-range" data-mini-range="service">
      {read !== null && read.status === "loaded" ? (
        <MiniServiceRangePage body={read.value} />
      ) : (
        <RangeNotLoaded read={read} retrying={retrying} notApplicable={SERVICE_RANGE_NOT_APPLICABLE} name="service-range" />
      )}
    </div>
  );
}
