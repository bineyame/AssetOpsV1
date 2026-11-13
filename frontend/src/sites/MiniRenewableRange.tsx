/**
 * SR-8 page (rev 10 §10.4, rev 10a §10a.3, D-SR.27/47/48): mini-grid Renewable over the whole shared range, from the
 * stored `daylight_headroom_kw` day rows (`GET /api/sites/{code}/renewable-range`, `site-renewable-range-1`).
 *
 * MOCK DEVIATION R726: v69 `renewable` is one assessment window (one to five days). Over a range the tab shows the
 * counted-days line, the average, a per-day headroom bar chart (the tab's existing `ValueBars`) and a day table; each
 * day opens the existing one-day page. The figure is the stored day value, "Headroom available in every eligible
 * hour" (min low and min high over the eligible hours, D-SR.48), never the one-day card's envelope.
 */
import { useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";

import { Badge, ChartNote, DataTable, MetricCard, MetricCards, Panel, StatusBar, ValueBars } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import { boundText, MINI_LOADING, MiniRangeRefusal, UNKNOWN } from "./MiniPerformance";
import type { MiniDepthClient, MiniWindowQuery, RenewableRangeDay, RenewableRangeRead } from "./miniDepthClient";
import { gapLine, rangeNumber, RangeRetrying, shortLocalDay, useRangeRead } from "./miniRange";

/** D-SR.48: the per-day and one-day words for the stored figure. */
export const ALL_HOURS_HEADROOM = "Headroom available in every eligible hour";
/** D-SR.48: the totals' words. */
export const AVERAGE_ALL_HOURS_HEADROOM = "Average headroom available in every eligible hour";
export const RENEWABLE_RANGE_UNAVAILABLE = "SITE_RENEWABLE_RANGE_UNAVAILABLE";

/** D-SR.27/47/70: the state words of a day row. */
export const RENEWABLE_DAY_WORDS: Record<string, string> = {
  COUNTED: "Counted",
  EXCLUDED: "Excluded",
  CONFLICT: "Conflicting readings",
  LIMITED: "Evidence limited",
  MISSING_HOUR: "Partial: an hour is missing",
  NO_VALUE: "No headroom figure for this day",
  NOT_ENOUGH_READINGS: "Not enough readings",
  NO_DATA: "No readings this day",
  PENDING: "Still being prepared",
  NOT_EXPECTED: "Not expected",
};

/** The short reason of an uncounted day on the counted-days line. */
const GAP_REASON: Record<string, string> = {
  EXCLUDED: "excluded",
  CONFLICT: "conflicting readings",
  LIMITED: "evidence limited",
  MISSING_HOUR: "an hour is missing",
  NO_VALUE: "no headroom figure",
  NOT_ENOUGH_READINGS: "not enough readings",
  NO_DATA: "no readings",
  PENDING: "still being prepared",
  NOT_EXPECTED: "not expected",
};

/** D-SR.62: the PARTIAL words a range row and the one-day page share. */
export const partialHoursText = (missing: number | null): string =>
  missing !== null && missing > 0
    ? `Partial: ${missing} hour${missing === 1 ? "" : "s"} missing`
    : "Partial: some hours have too few readings"; // D-SR.76 Q3

const band = (low: string | number | null, high: string | number | null) => ({ low: rangeNumber(low), high: rangeNumber(high) });

function bandText(day: RenewableRangeDay): string {
  const b = band(day.low_kw, day.high_kw);
  return b.low === null || b.high === null ? "—" : boundText(b, "kW");
}

function missingHours(day: RenewableRangeDay): number | null {
  if (day.covered_hours === null || day.operating_hours === null) return null;
  const missing = Math.round((day.operating_hours - day.covered_hours) * 100) / 100;
  return missing > 0 ? missing : 0;
}

function hoursText(day: RenewableRangeDay): string {
  if (day.covered_hours === null || day.operating_hours === null) return "—";
  return `${day.covered_hours} of ${day.operating_hours} operating hours covered`;
}

export function MiniRenewableRangePage({ read }: { read: RenewableRangeRead }): ReactNode {
  const { days, totals } = read;
  const location = useLocation();
  const origin = { wholeRange: location.search }; // D-SR.76 Q4: the one-day page's way back
  const line = gapLine(days, (s) => s === "COUNTED", (s) => GAP_REASON[s] ?? s.toLowerCase());
  const average = band(totals.average_low_kw, totals.average_high_kw);
  return (
    <div data-mini-range="renewable">
      <StatusBar label="Renewable over the range" items data={{ "data-mini-range-status": "renewable" }}>
        <span className="status-strip__item" data-mini-range-line>{`Headroom counted on ${line}`}</span>
        {totals.partial ? (
          <span className="status-strip__item" data-mini-range-partial>
            <Badge tone="neutral" className="mini-tone--amber">Partial</Badge>
          </span>
        ) : null}
        <span className="mock-deviation-line mini-inline-deviation" data-mock-deviation="R726">MOCK DEVIATION R726</span>
      </StatusBar>
      <MetricCards label="Renewable over the range summary" columns={2} data={{ "data-mini-cards": "renewable-range" }}>
        <MetricCard
          label={AVERAGE_ALL_HOURS_HEADROOM}
          value={average.low === null || average.high === null ? UNKNOWN : boundText(average, "kW")}
          word={average.low === null || average.high === null}
          note="Low and high averaged separately over the counted days"
          data={{ "data-mini-range-average": "" }}
        />
        <MetricCard label="Days counted" value={`${totals.days_counted} of ${totals.days_requested}`} note="Eligible days with a stored figure" />
      </MetricCards>
      <Panel heading={`${ALL_HOURS_HEADROOM}, per day`} headingId="mini-renewable-range-chart-heading">
        <ValueBars
          title={`${ALL_HOURS_HEADROOM}, per day`}
          captionHidden
          items={days.map((day) => {
            const b = band(day.low_kw, day.high_kw);
            return {
              key: day.local_day,
              label: day.state === "EXCLUDED" ? `${shortLocalDay(day.local_day)} (excluded)` : shortLocalDay(day.local_day),
              value: b.low === null || b.high === null ? null : b.high,
              valueText: bandText(day),
              tone: "headroom" as const,
            };
          })}
          unknownText="No figure"
        />
        <ChartNote>Each bar is the stored day figure: the headroom available in every eligible hour of that day.</ChartNote>
      </Panel>
      <Panel heading="Days in the range" headingId="mini-renewable-range-days-heading" flush>
        <DataTable labelledBy="mini-renewable-range-days-heading">
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th scope="col">{ALL_HOURS_HEADROOM}</th>
              <th scope="col">Eligible hours</th>
              <th scope="col">Hours covered</th>
              <th scope="col">State</th>
            </tr>
          </thead>
          <tbody>
            {days.map((day) => {
              const missing = missingHours(day);
              return (
                <tr key={day.local_day} data-mini-range-day={day.local_day} data-mini-range-state={day.state}>
                  <td>
                    <Link to={day.link} state={origin}>{shortLocalDay(day.local_day)}</Link>
                  </td>
                  <td data-mini-range-band>{bandText(day)}</td>
                  <td>{day.window_hours === null ? "—" : String(day.window_hours)}</td>
                  <td>{hoursText(day)}</td>
                  <td>
                    {RENEWABLE_DAY_WORDS[day.state] ?? day.state}
                    {day.partial || (missing !== null && missing > 0) ? (
                      <span data-mini-range-day-partial>{` · ${partialHoursText(missing)}`}</span>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </DataTable>
      </Panel>
    </div>
  );
}

/** The Renewable tab over a shared range: one read, its retry, or its refusal. */
export function MiniRenewableRange({
  client,
  siteCode,
  window,
  retryDelays,
}: {
  client: MiniDepthClient;
  siteCode: string;
  window: MiniWindowQuery;
  retryDelays?: readonly number[];
}): ReactNode {
  const [attempt, setAttempt] = useState(0);
  const key = `${siteCode}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}`;
  const state = useRangeRead<RenewableRangeRead>(
    () =>
      client.getRenewableRange === undefined
        ? Promise.resolve({ status: "unavailable", message: null })
        : client.getRenewableRange(siteCode, window),
    key,
    RENEWABLE_RANGE_UNAVAILABLE,
    attempt,
    retryDelays,
  );
  if (state.phase === "loading") return <p role="status">{MINI_LOADING}</p>;
  if (state.phase !== "done") return <RangeRetrying phase={state.phase} />;
  if (state.read.status !== "loaded") return <MiniRangeRefusal read={state.read} onRetry={() => setAttempt((n) => n + 1)} />;
  return <MiniRenewableRangePage read={state.read.value} />;
}
