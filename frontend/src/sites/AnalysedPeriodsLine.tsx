/**
 * PB-1c (D-E5.31, owner-approved): the Cold and EV window bar names the analysed periods that lie inside the requested
 * range, one line under the bar. The line is shown only when the read carries `analysed_periods`.
 *
 * MOCK DEVIATION (v6.9 Site window bar): one added line under the window bar ("Analysed period: ..." or "Analysed
 * periods in this range: n · showing ..."), each period a link to its exact window; "No analysed period in this
 * range" when none lies inside and the read has no assessment. Informed owner; seen at the walkthrough.
 *
 * `href` in the read is an API route (PB-1a review M1), so each link is built here: the page's own address with its
 * `from` and `to` replaced by the period's instants (the shared-range instant form, `ui/sharedRange.ts`).
 */
import { Link, useLocation } from "react-router-dom";

import { analysedPeriodsLead, NO_ANALYSED_PERIOD } from "../ui/productWords";
import type { AnalysedPeriodsRead } from "./coldAssessmentClient";
import { windowText } from "./coldFormat";

/** The page's address with the period's exact window (`from`, `to`; the cutoff and other parameters stay). */
export function periodAddress(pathname: string, search: string, period: { from: string; to: string }): string {
  const params = new URLSearchParams(search);
  params.set("from", period.from);
  params.set("to", period.to);
  return `${pathname}?${params.toString()}`;
}

export function AnalysedPeriodsLine({ read, none }: { read: AnalysedPeriodsRead; none: boolean }) {
  const location = useLocation();
  const periods = read.analysed_periods;
  if (periods === undefined) return null;
  if (periods.length === 0) {
    return none && !read.shown_period ? (
      <p className="site-date-bar site-date-bar--periods" data-analysed-periods="none">
        {NO_ANALYSED_PERIOD}
      </p>
    ) : null;
  }
  const shown = read.shown_period ?? periods[periods.length - 1];
  const link = (p: { from: string; to: string }, key?: string) => (
    <Link key={key} to={periodAddress(location.pathname, location.search, p)} data-analysed-period-link>
      {windowText(p.from, p.to)}
    </Link>
  );
  const others = periods.filter((p) => p.from !== shown.from || p.to !== shown.to);
  return (
    <p className="site-date-bar site-date-bar--periods" data-analysed-periods={periods.length}>
      {analysedPeriodsLead(periods.length)}
      {link(shown)}
      {others.length === 0 ? null : (
        <>
          {" · also "}
          {others.map((p, i) => (
            <span key={`${p.from}|${p.to}`}>
              {i === 0 ? "" : ", "}
              {link(p)}
            </span>
          ))}
        </>
      )}
    </p>
  );
}
