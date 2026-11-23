/**
 * IA-P P3b (spec §3, `spec-period.md` P.5; D-IAP.17): the Overview's mode `period`, two or more served whole months.
 * It renders E2's body as given, in 5c's hub shape and classes: L1 the lead and the four tiles (summed by the
 * server), L2 the Decisions rows and Actions in hand, L3 "Month by month" (one row per whole month, its one link
 * setting the range to that month) and the outcome cards. MOCK DEVIATION MD-IAP-10: "Month by month" stands where the
 * month's bridge and cash stand; each row opens that month's full bridge (one click).
 */
import { useSearchParams } from "react-router-dom";

import { DataTable } from "../ui";
import { RangeLink as Link } from "../ui/RangeLink";
import { DdHead, DdNotes, Lines, DdOutcomes, DdQueue, DdTiles, monthRangeHref } from "./DeepDiveMonth";
import { useDrawers } from "../ui/Drawer";
import type { EstateClient } from "./estateClient";
import type { PeriodBody } from "./portfolioPeriodClient";
import "./deepDiveMonth.css";

/** The panel title of the Overview's L2 Decisions rows outside mode `month` (the menu label, a reused word). */
export const DECISIONS_TITLE = "Decisions";

function Lead({ body }: { body: PeriodBody }) {
  return (
    <div className="dd-lead">
      <p className="dd-headline">
        {body.headline.text}{" "}
        {body.headline.evidence.map((e, i) => (
          <span key={i} className="dd-chip dd-chip--headline" data-dd-word>
            {e}
          </span>
        ))}
      </p>
      <p role="status" className="dd-status">
        {body.status_line}
      </p>
      {body.fresh !== null ? <p className="dd-fresh">{body.fresh}</p> : null}
      {body.notices.map((notice) => (
        <p key={notice} className="dd-notice">
          {notice}
        </p>
      ))}
      {/* D-IAP.34 (MD-IAP-16): the Sites left out, named with why: 5c's own drawer lines, since the period has no step drawer. */}
      {body.out.length > 0 ? (
        <div data-dd-out>
          <Lines lines={body.out} className="dd-lines dd-lines--note" />
        </div>
      ) : null}
    </div>
  );
}

function MonthByMonth({ months }: { months: PeriodBody["months"] }) {
  const [params] = useSearchParams();
  const [first, ...rest] = months.columns;
  return (
    <section className="dd-section" aria-labelledby="dd-months-h" data-period-months>
      <h2 id="dd-months-h">{months.title}</h2>
      <DataTable labelledBy="dd-months-h" stickyFirstColumn>
          <thead>
            <tr>
              <th scope="col">{first}</th>
              {rest.map((c) => (
                <th key={c} scope="col">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {months.rows.map((row) => (
              <tr key={row.month} data-period-month={row.month}>
                <th scope="row">
                  <Link to={monthRangeHref(row, params)}>{row.month_words}</Link>
                  {row.sites !== null ? (
                    <>
                      {" "}
                      <small className="dd-meta dd-meta--line">{row.sites}</small>
                    </>
                  ) : null}
                </th>
                <td data-label={rest[0]}>{row.contribution}</td>
                <td data-label={rest[1]}>
                  {row.gap ?? ""}
                  {row.gap_word !== null ? (
                    <>
                      {" "}
                      <span className="dd-chip" data-dd-word>
                        {row.gap_word}
                      </span>
                    </>
                  ) : null}
                </td>
                <td data-label={rest[2]}>
                  {row.driver ?? ""}
                  {row.driver_heading !== null ? (
                    <>
                      {" "}
                      <small className="dd-meta dd-meta--line">{row.driver_heading}</small>
                    </>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
      </DataTable>
    </section>
  );
}

export function PortfolioPeriod({
  operator,
  periodWords,
  notes,
  body,
  estate,
}: {
  operator: string | null;
  periodWords: string;
  notes: readonly string[];
  body: PeriodBody;
  estate?: EstateClient;
}) {
  const api = useDrawers();
  return (
    <section data-shape="hub" className="dd-month" data-overview-mode="period">
      <DdHead operator={operator}>
        <div className="dd-nav">
          <b className="dd-nav__current">{periodWords}</b>
        </div>
        <DdNotes notes={notes} />
      </DdHead>
      <div data-level="L1">
        <Lead body={body} />
        <DdTiles tiles={body.tiles} />
      </div>
      <div data-level="L2">
        <DdQueue title={DECISIONS_TITLE} actions={body.actions} estate={estate} />
      </div>
      <div data-level="L3">
        <MonthByMonth months={body.months} />
        <DdOutcomes cards={body.outcomes} na={null} api={api} />
      </div>
    </section>
  );
}
