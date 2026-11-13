/**
 * SR-10c (rev 10b.2, D-SR.32/51/70-72): mini-grid Fuel over the whole shared range, from the stored
 * `mini_depth.fuel_day` rows (`GET /api/sites/{code}/fuel-range`, `site-fuel-range-1`). Shown when the Site is not in
 * fuel-check nights mode and the address names no hour.
 *
 * MOCK DEVIATION R727: v69 `fuel` (8.22) is one reconciliation window. Over a range the tab shows the modelled-days
 * line, the modelled expected-use band per day (the tab's existing `ValueBars`) and a day table; each day opens its
 * 12:00 hour on the existing hour page. The v69 rule "Residual, uncertainty and expected-consumption basis stay
 * explicit" holds: the use is labelled modelled, and the residual is never summed ("Residual: not available").
 */
import { useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";

import { Badge, ChartNote, DataTable, Panel, StatusBar, ValueBars } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import { boundText, MINI_LOADING, MiniRangeRefusal } from "./MiniPerformance";
import type { FuelRangeDay, FuelRangeRead, MiniDepthClient, MiniWindowQuery } from "./miniDepthClient";
import { partialHoursText } from "./MiniRenewableRange";
import { gapLine, RangeRetrying, shortLocalDay, useRangeRead } from "./miniRange";

export const FUEL_RANGE_UNAVAILABLE = "SITE_FUEL_RANGE_UNAVAILABLE";
export const FUEL_RESIDUAL_NOT_AVAILABLE = "Residual: not available";
export const BACK_TO_WHOLE_RANGE = "Back to the whole range";

/** Router state an hour link carries, so the hour page can return to the range it came from. */
export interface FuelRangeOrigin {
  wholeRange: string;
}

/** Rev 10b.1 / D-SR.51/70: the state words of a day row. */
export const FUEL_DAY_WORDS: Record<string, string> = {
  ASSESSED: "Assessed",
  NO_ASSESSMENT: "No assessment",
  STILL_PROCESSING: "Still being prepared",
  NO_DATA: "No readings this day",
  NOT_EXPECTED: "Not expected",
};

const GAP_REASON: Record<string, string> = {
  NO_ASSESSMENT: "no assessment",
  STILL_PROCESSING: "still being prepared",
  NO_DATA: "no readings",
  NOT_EXPECTED: "not expected",
};

/** D-SR.51 (3) / D-SR.70: an absent or no-readings row spans its words, never "0 of 0 hours". */
const spansRow = (day: FuelRangeDay): boolean => day.state === "NO_DATA" || !day.stored || day.hours_expected === null;

function partialText(day: FuelRangeDay): string {
  const missing = day.hours_missing ?? 0;
  return partialHoursText(missing);
}

export function MiniFuelRangePage({ read }: { read: FuelRangeRead }): ReactNode {
  const { days, totals } = read;
  const location = useLocation();
  const origin: FuelRangeOrigin = { wholeRange: location.search };
  const line = gapLine(days, (s) => s === "ASSESSED", (s) => GAP_REASON[s] ?? s.toLowerCase());
  return (
    <div data-mini-range="fuel">
      <StatusBar label="Fuel over the range" items data={{ "data-mini-range-status": "fuel" }}>
        <span className="status-strip__item" data-mini-range-line>{`Fuel use modelled on ${line}`}</span>
        {totals.partial ? (
          <span className="status-strip__item" data-mini-range-partial>
            <Badge tone="neutral" className="mini-tone--amber">Partial</Badge>
          </span>
        ) : null}
        <span className="mock-deviation-line mini-inline-deviation" data-mock-deviation="R727">MOCK DEVIATION R727</span>
      </StatusBar>
      <Panel heading="Modelled expected use, per day" headingId="mini-fuel-range-chart-heading">
        <ValueBars
          title="Modelled expected use, per day"
          captionHidden
          items={days.map((day) => ({
            key: day.local_day,
            label: shortLocalDay(day.local_day),
            value: day.expected_use_l === null ? null : day.expected_use_l.high,
            valueText: day.expected_use_l === null ? "—" : boundText(day.expected_use_l, "L"),
          }))}
          unknownText="No figure"
        />
        <ChartNote data={{ "data-mini-range-residual-note": "" }}>{FUEL_RESIDUAL_NOT_AVAILABLE}</ChartNote>
      </Panel>
      <Panel heading="Days in the range" headingId="mini-fuel-range-days-heading" flush>
        <DataTable labelledBy="mini-fuel-range-days-heading">
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th scope="col">Expected use (modelled)</th>
              <th scope="col">Hours assessed</th>
              <th scope="col">State</th>
              <th scope="col">Hour</th>
            </tr>
          </thead>
          <tbody>
            {days.map((day) => (
              <tr key={day.local_day} data-mini-range-day={day.local_day} data-mini-range-state={day.state}>
                <td>{shortLocalDay(day.local_day)}</td>
                {spansRow(day) ? (
                  <td colSpan={3} data-mini-range-span>
                    {FUEL_DAY_WORDS[day.state] ?? FUEL_DAY_WORDS.STILL_PROCESSING}
                  </td>
                ) : (
                  <>
                    <td>{day.expected_use_l === null ? "—" : boundText(day.expected_use_l, "L")}</td>
                    <td>{`${day.hours_assessed} of ${day.hours_expected} hours assessed`}</td>
                    <td>
                      {FUEL_DAY_WORDS[day.state] ?? day.state}
                      {day.partial ? <span data-mini-range-day-partial>{` · ${partialText(day)}`}</span> : null}
                    </td>
                  </>
                )}
                <td>
                  <Link to={day.hour_link} state={origin}>
                    Open the 12:00 hour
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </div>
  );
}

/** The Fuel tab over a shared range: one read, its retry, or its refusal. */
export function MiniFuelRange({
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
  const state = useRangeRead<FuelRangeRead>(
    () =>
      client.getFuelRange === undefined ? Promise.resolve({ status: "unavailable", message: null }) : client.getFuelRange(siteCode, window),
    key,
    FUEL_RANGE_UNAVAILABLE,
    attempt,
    retryDelays,
  );
  if (state.phase === "loading") return <p role="status">{MINI_LOADING}</p>;
  if (state.phase !== "done") return <RangeRetrying phase={state.phase} />;
  if (state.read.status !== "loaded") return <MiniRangeRefusal read={state.read} onRetry={() => setAttempt((n) => n + 1)} />;
  return <MiniFuelRangePage read={state.read.value} />;
}

/** The hour page's way back to the range it was opened from (router state from the range table); nothing otherwise. */
export function BackToWholeRange({
  pageHref,
  deviation = "R727",
}: {
  pageHref: (search: string) => string;
  deviation?: "R726" | "R727";
}): ReactNode {
  const location = useLocation();
  const origin = location.state as Partial<FuelRangeOrigin> | null;
  if (origin === null || typeof origin.wholeRange !== "string" || origin.wholeRange === "") return null;
  return (
    <p className="mini-back-to-range" data-mini-back-to-range>
      <Link to={pageHref(origin.wholeRange)}>{BACK_TO_WHOLE_RANGE}</Link>
      {deviation === "R726" ? (
        <span className="mock-deviation-line mini-inline-deviation" data-mock-deviation="R726">MOCK DEVIATION R726</span>
      ) : (
        <span className="mock-deviation-line mini-inline-deviation" data-mock-deviation="R727">MOCK DEVIATION R727</span>
      )}
    </p>
  );
}
