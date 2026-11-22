/**
 * IA-P P3b (spec §5.3, I14): Results, at `/results` (the old Portfolio "What changed" tab). `PageHeader` "Results"
 * with "What changed in this review", then `ProgressPanel` moved verbatim, reading the estate portfolio's page 1 for
 * the window (the range's last 31 days, P0).
 */
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { PageHeader } from "../ui";
import { createEstateClient, type EstateClient, type EstatePortfolioBody, type EstateResult } from "./estateClient";
import { EstateCutoffLine, EstateRefusal, estateHref, queryFromParams } from "./estateShared";
import { barBody, ProgressPanel } from "./EstatePortfolio";
import { PORTFOLIO_PAGE_SIZE } from "./portfolioWords";
import { RESULTS_PATH } from "../shell/operatorSiteRoutes";

export { RESULTS_PATH };

export const RESULTS_TITLE = "Results";
export const RESULTS_SUBTITLE = "What changed in this review";

export function ResultsPage({ client }: { client?: EstateClient }) {
  const reads = useMemo(() => client ?? createEstateClient(), [client]);
  const [params] = useSearchParams();
  const query = queryFromParams(params);
  const key = `${query.from}|${query.to}|${query.known_at ?? ""}`;
  const [read, setRead] = useState<{ key: string; result: EstateResult<EstatePortfolioBody> } | null>(null);
  useEffect(() => {
    let live = true;
    void reads
      .portfolio({ from: query.from, to: query.to, known_at: query.known_at, lens: "all", limit: PORTFOLIO_PAGE_SIZE, cursor: null })
      .then((result) => {
        if (live) setRead({ key, result });
      });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reads, key]);
  const current = read?.key === key ? read.result : null;
  const body = current?.status === "loaded" ? current.value : null;
  return (
    <div className="estate-page estate-portfolio portfolio-v2" data-estate-root="results">
      <PageHeader title={RESULTS_TITLE} subtitle={RESULTS_SUBTITLE} />
      <EstateCutoffLine query={query} body={barBody(body)} windowRefused={current?.status === "refused" && current.code === "INVALID_WINDOW"} />
      {current === null ? (
        <p className="estate-loading">Loading Results…</p>
      ) : current.status === "refused" ? (
        <EstateRefusal code={current.code} copy={current.copy} window={query} firstPage={estateHref(RESULTS_PATH, query)} />
      ) : (
        <ProgressPanel body={current.value} />
      )}
    </div>
  );
}

export function ResultsFrame({ client }: { client?: EstateClient }) {
  return (
    <main aria-label={RESULTS_TITLE}>
      <ResultsPage client={client} />
    </main>
  );
}
