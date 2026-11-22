/**
 * IA-P P3b (spec §3; D-IAP.2, D-IAP.15 to D-IAP.19): the `/portfolio` frame. The Overview is 5c's screen on the
 * top-bar range. It reads E2 (`GET /api/portfolio/period`) for the address's whole range (a whole-range page, P0) and
 * renders by E2's mode:
 * - `month`: 5c's month screen for E2's month (`served[0]`), its ‹ › links and notes from E2;
 * - `period`: the period hub (`PortfolioPeriod.tsx`);
 * - `none`: the header, E2's notes, the link to the latest served month, then L2 (MOCK DEVIATION MD-IAP-11).
 * It declares E2's `shown` to the top bar (SR-4c) only when `shown` is not null. The browser does no date arithmetic.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, useSearchParams } from "react-router-dom";

import { RangeLink as Link } from "../ui/RangeLink";
import { useDeclareRangeSpan } from "../ui/rangeFocus";
import { linkBound, readSharedRange } from "../ui/sharedRange";
import { DD_COPY, DdHead, DdNotes, DdQueue, DeepDiveMonthPage, monthRangeHref } from "./DeepDiveMonth";
import type { DeepDiveMonthClient } from "./deepDiveMonthClient";
import type { EstateClient } from "./estateClient";
import { createPortfolioPeriodClient, type PeriodResult, type PortfolioPeriodClient } from "./portfolioPeriodClient";
import { DECISIONS_TITLE, PortfolioPeriod } from "./PortfolioPeriod";
import { DECISIONS_PATH } from "./portfolioWords";
import "./deepDiveMonth.css";

/** spec §6 P3b: the Overview's loading line while E2 is read. */
export const OVERVIEW_LOADING = "Preparing the figures…";

type Read = { key: string; result: PeriodResult };

/** An old `/portfolio?lens=X` address is Act first's: the Decisions list with its facet (IA-P P2), before any read. */
export function PortfolioOverview(props: { period?: PortfolioPeriodClient; month?: DeepDiveMonthClient; estate?: EstateClient }) {
  const [params] = useSearchParams();
  if (params.get("lens") !== null) return <Navigate replace to={`${DECISIONS_PATH}?${params.toString()}`} />;
  return <Overview {...props} />;
}

function Overview({
  period,
  month,
  estate,
}: {
  period?: PortfolioPeriodClient;
  month?: DeepDiveMonthClient;
  estate?: EstateClient;
}) {
  const reads = useMemo(() => period ?? createPortfolioPeriodClient(), [period]);
  const [params] = useSearchParams();
  // P0: the Overview is a whole-range page; links and E2 carry the address's whole range, never the 31-day window.
  // E2 takes days; the address may hold the instant form of the same range (the entry fill writes it).
  const range = readSharedRange(params);
  const from = range.status === "set" ? range.from : (linkBound(params, "from") ?? "");
  const to = range.status === "set" ? range.to : (linkBound(params, "to") ?? "");
  const [attempt, setAttempt] = useState(0);
  const key = `${from}|${to}|${attempt}`;
  const [read, setRead] = useState<Read | null>(null);

  useEffect(() => {
    let live = true;
    void reads.fetchPeriod(from, to).then((result) => {
      if (live) setRead({ key, result });
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);

  const current = read !== null && read.key === key ? read.result : null;
  const body = current?.status === "loaded" ? current.body : null;
  // SR-4c (D-IAP.18): declared only when the months counted differ from the range.
  useDeclareRangeSpan(body?.shown?.from ?? null, body?.shown?.to ?? null);

  let page: ReactNode;
  if (body !== null && body.mode === "month") {
    page = <DeepDiveMonthPage key={body.served[0]} client={month} estate={estate} month={body.served[0]} nav={body.nav} notes={body.notes} />;
  } else if (body !== null && body.mode === "period" && body.body !== null) {
    page = <PortfolioPeriod operator={null} periodWords={body.period_words ?? ""} notes={body.notes} body={body.body} estate={estate} />;
  } else {
    let content: ReactNode;
    if (current === null) {
      content = <p className="dd-state">{OVERVIEW_LOADING}</p>;
    } else if (current.status === "refused") {
      content =
        current.httpStatus === 401 ? (
          <p className="dd-state">{DD_COPY.signIn}</p>
        ) : (
          <div className="dd-state">
            <p>{current.text ?? DD_COPY.unreadable}</p>
            {current.httpStatus !== 422 ? (
              <button type="button" className="dd-button" onClick={() => setAttempt((n) => n + 1)}>
                {DD_COPY.tryAgain}
              </button>
            ) : null}
          </div>
        );
    } else {
      // Mode `none` (MD-IAP-11): no figure exists for a range without a served whole month; L1 and L3 are omitted.
      content = (
        <div data-level="L2">
          <DdQueue title={DECISIONS_TITLE} actions={null} estate={estate} />
        </div>
      );
    }
    page = (
      <section data-shape="hub" className="dd-month" data-overview-mode={body?.mode ?? undefined}>
        <DdHead operator={null}>
          {body !== null ? <DdNotes notes={body.notes} /> : null}
          {body?.suggest ? (
            <p className="dd-period">
              <Link to={monthRangeHref(body.suggest, params)} data-overview-suggest>
                {body.suggest.text}
              </Link>
            </p>
          ) : null}
        </DdHead>
        {content}
      </section>
    );
  }
  return <main aria-label="Portfolio">{page}</main>;
}
