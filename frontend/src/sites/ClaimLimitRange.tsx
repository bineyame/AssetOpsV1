/**
 * SR-7b (sequence doc rev 10 §10.3, rev 10a.2 Q7; D-SR.24, D-SR.25): the claim limit over the date range, inside Site
 * Evidence's claim-limit section. One row per day from `claim-limit-range`: the row is `reduce_day` of the one-day
 * projection. A day ceiling is shown only when the server gives one (`current_ceiling`, never invented); a day with no
 * selected window revision is "No assessment for this day" and has no link (NO_SELECTION). Each other row opens the
 * existing one-day section (`day=&revision=`, on the Analysis view), which carries "Back to the whole range".
 */
import type { ReactNode } from "react";

import { RangeLink as Link } from "../ui/RangeLink";
import { DataTable } from "../ui";
import { DEFAULT_SITE_RANGE_CLIENT, type ClaimLimitRangeBody, type ClaimLimitRangeDay, type RangeWindowQuery, type SiteRangeClient } from "./siteRangeClient";
import { RangeNotLoaded, dayWords, useRangeRead } from "./SiteRangeParts";

export const CLAIM_LIMIT_RANGE_NOT_APPLICABLE = "The claim limit over a range is read for mini-grid sites only.";
export const CLAIM_LIMIT_NO_SELECTION = "No assessment for this day";
export const OPEN_THIS_DAY = "Open this day";

const CEILING_WORDS: Record<string, string> = { CANDIDATE_AVOIDABLE: "avoidable", NECESSARY: "necessary" };

/** What one day's readings support, in words (`reduce_day` state; D-SR.25). */
export function claimDayWords(day: ClaimLimitRangeDay): string {
  if (day.state === "NO_SELECTION") return CLAIM_LIMIT_NO_SELECTION;
  if (day.current_ceiling !== null) {
    return `The readings support calling this day's generator operation ${CEILING_WORDS[day.current_ceiling] ?? "classified"}`;
  }
  switch (day.state) {
    case "CONTRADICTORY":
      return "Readings for this day conflict, so no conclusion is drawn";
    case "UNKNOWN":
      return "No current conclusion for this day";
    case "NONE":
      return "No conclusion is supported for this day";
    case "FULL":
    case "LIMITED":
      return "No single conclusion covers the whole day; open the day for each period";
    default:
      return "No conclusion is drawn for this day";
  }
}

/** The row's one-day address: the server link on the Analysis view, where the claim-limit section is. */
function dayHref(link: string): string {
  const [path, query = ""] = link.split("?", 2);
  const params = new URLSearchParams(query);
  params.set("view", "analysis");
  return `${path}?${params.toString()}`;
}

function ClaimLimitRangeTable({ body }: { body: ClaimLimitRangeBody }) {
  const { summary } = body;
  return (
    <div className="claim-limit-range" data-claim-limit-range>
      <p className="claim-limit__summary" data-claim-limit-range-summary>
        {`${summary.days_with_positive_claim} of ${summary.days_requested} days support a conclusion · ${summary.days_indeterminate} undetermined · ${summary.days_without_selection} without an assessment`}
      </p>
      {/* A caption line, not a heading: the panel keeps one heading (v69 `evidence-analysis`). */}
      <p className="claim-limit-range__caption" id="claim-limit-range-heading">
        Claim limit by day
      </p>
      <DataTable labelledBy="claim-limit-range-heading">
        <thead>
          <tr>
            <th scope="col">Day</th>
            <th scope="col">What the readings support</th>
            <th scope="col">Reading gaps</th>
            <th scope="col">Day detail</th>
          </tr>
        </thead>
        <tbody>
          {body.days.map((day) => (
            <tr key={day.day} data-claim-limit-range-day={day.day} data-claim-day-state={day.state}>
              <th scope="row">{dayWords(day.day)}</th>
              <td>{claimDayWords(day)}</td>
              <td>{day.state === "NO_SELECTION" ? "–" : day.gap_count === 0 ? "None" : `${day.gap_count} reading gap${day.gap_count === 1 ? "" : "s"}`}</td>
              <td>{day.link === null ? "–" : <Link to={dayHref(day.link)}>{OPEN_THIS_DAY}</Link>}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

/** The claim limit over the address range: one `claim-limit-range` read. */
export function ClaimLimitRange({
  siteCode,
  window,
  client = DEFAULT_SITE_RANGE_CLIENT,
}: {
  siteCode: string;
  window: RangeWindowQuery;
  client?: SiteRangeClient;
}): ReactNode {
  const key = `${siteCode}|${window.from}|${window.to}|${window.known_at ?? ""}`;
  const { read, retrying } = useRangeRead((onRetrying) => client.getClaimLimitRange(siteCode, window, onRetrying), key);
  return read !== null && read.status === "loaded" ? (
    <ClaimLimitRangeTable body={read.value} />
  ) : (
    <RangeNotLoaded read={read} retrying={retrying} notApplicable={CLAIM_LIMIT_RANGE_NOT_APPLICABLE} name="claim-limit-range" />
  );
}
