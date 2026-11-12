import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { safeReturn } from "../sites/PriceAction";
import { createPricePageClient, type PricePageClient, type PricePageResult, type PriceRowBody } from "../sites/pricePageClient";
import { SitePricesBody } from "../sites/SitePrices";
import { Breadcrumbs, PageHeader, Panel } from "../ui";
import { coldTabSearch } from "./coldSiteRoutes";
import { evSiteRoutes, evWorkTabHrefs, evWorkTabSearch } from "./evSiteRoutes";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import {
  SITES_PATH,
  siteDetailHref,
  siteFinancialScenariosHref,
  siteFinancialsHref,
  sitePricesHref,
} from "./operatorSiteRoutes";
import { SiteScoped } from "./SiteAnalyticsFrames";

export const SITE_PRICES_HEADING_ID = "site-prices-heading";
/** The plain sign-in line (owner 2026-11-11; rev 5). The page shows the server's copy; this one is for tests. */
export const PRICES_SIGN_IN_TEXT =
  "Prices are set by your AssetOps administrator until sign-in is available.";
export const PRICES_LOADING = "Loading the site's prices.";
// MOCK DEVIATION (D-PRICE.3, deviation 2): `return` is a path with no item name, so no "You came from '...'".
const RETURN_WORDS = "← Back to where you were";
const RANGE_KEPT = "Your date range is kept.";
const DEFAULT_CLIENT = createPricePageClient();

/** The shared range (`from`, `to`, `known_at`) the page was opened with, carried on its Financials links. */
function rangeSearch(params: URLSearchParams): string {
  const keep = new URLSearchParams();
  for (const name of ["from", "to", "known_at"]) {
    const value = params.get(name);
    if (value) keep.set(name, value);
  }
  const text = keep.toString();
  return text ? `?${text}` : "";
}

/** An EV Site's Financials live at its own EV addresses, chosen through the existing `evWorkTabHrefs`. */
function evRoutesOf(site: { site_id: string; site_type: string }) {
  return evWorkTabHrefs(site) === undefined ? null : evSiteRoutes(site.site_id);
}

/** Financials `Overview | Prices | Scenarios` (mock Part B subtabs; default 2: "Assumptions" becomes "Prices"). */
function PricesSubtabs({ site, search }: { site: { site_id: string; site_type: string }; search: string }) {
  const ev = evRoutesOf(site);
  const links: [string, string, string][] = [
    ["overview", "Overview", `${ev?.financials ?? siteFinancialsHref(site.site_id)}${search}`],
    ["prices", "Prices", `${sitePricesHref(site.site_id)}${search}`],
    ["scenarios", "Scenarios", `${ev?.scenarios ?? siteFinancialScenariosHref(site.site_id)}${search}`],
  ];
  return (
    <nav className="site-tabs site-subtabs" aria-label="Financials sections">
      <ol className="site-tabs__list">
        {links.map(([id, label, href]) => (
          <li className="site-tabs__item" key={id}>
            <Link className="site-tabs__link" to={href} data-financials-section={id} aria-current={id === "prices" ? "page" : undefined}>
              {label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

function usePricePage(client: PricePageClient, siteId: string, need: string | null, knownAt: string | null) {
  const key = `${siteId}|${need ?? ""}|${knownAt ?? ""}`;
  const [state, setState] = useState<{ key: string; result: PricePageResult } | null>(null);
  useEffect(() => {
    let live = true;
    void client.getPrices(siteId, { need, knownAt }).then((result) => {
      if (live) setState({ key, result });
    });
    return () => {
      live = false;
    };
  }, [client, siteId, need, knownAt, key]);
  return state === null || state.key !== key ? null : state.result;
}

const REFUSED: Record<Exclude<PricePageResult["status"], "loaded">, string> = {
  not_found: "No prices can be read for this site.",
  invalid: "The date this page was opened with cannot be read.",
  forbidden: "You cannot read this site's prices.",
  unauthenticated: "Sign in to read this site's prices.",
  closed: "The prices cannot be read right now.",
  unavailable: "The prices cannot be read right now.",
};

function PricesRead({
  result,
  params,
  renderBelow,
}: {
  result: PricePageResult | null;
  params: URLSearchParams;
  renderBelow?: (row: PriceRowBody) => ReactNode;
}) {
  if (result === null) return <p>{PRICES_LOADING}</p>;
  if (result.status !== "loaded") {
    return (
      <Panel heading="Prices for this site" headingId={`${SITE_PRICES_HEADING_ID}-refused`}>
        <p data-prices-refused={result.status}>
          {REFUSED[result.status]}
          {result.message ? ` ${result.message}` : ""}
        </p>
      </Panel>
    );
  }
  return <SitePricesBody page={result.value} focusKey={params.get("key")} renderBelow={renderBelow} />;
}

/**
 * PR-2a (BL-68): the read-only Site price page, `/sites/:siteId/financials/prices?key=|need=&from=&to=&known_at=&return=`
 * (default 1). Every unpriced item's `price_action` link lands here (PR-1). It lists every price the Site's figures
 * use, set or not, with History; a `need` opens Part C. Read-only: no form and no Save. PR-3 hosts its inline form
 * through `renderBelow` (see `SitePricesBody`).
 */
export function SitePricesFrame({
  detail,
  client = DEFAULT_CLIENT,
  renderBelow,
}: {
  detail: SiteDetailClient;
  client?: PricePageClient;
  renderBelow?: (row: PriceRowBody) => ReactNode;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Prices" headingId={SITE_PRICES_HEADING_ID}>
      {(site) => <PricesMain site={site} client={client} params={params} renderBelow={renderBelow} />}
    </SiteScoped>
  );
}

function PricesMain({
  site,
  client,
  params,
  renderBelow,
}: {
  site: { site_id: string; site_type: string; display_name: string };
  client: PricePageClient;
  params: URLSearchParams;
  renderBelow?: (row: PriceRowBody) => ReactNode;
}) {
  const back = safeReturn(params.get("return"));
  const search = rangeSearch(params);
  const result = usePricePage(client, site.site_id, params.get("need"), params.get("known_at"));
  return (
    <main aria-labelledby={SITE_PRICES_HEADING_ID} data-site-prices>
      <Breadcrumbs
        trail={[
          { label: "Sites", to: SITES_PATH },
          { label: site.display_name, to: siteDetailHref(site.site_id) },
          { label: "Financials", to: `${evRoutesOf(site)?.financials ?? siteFinancialsHref(site.site_id)}${search}` },
          { label: "Prices" },
        ]}
      />
      <PageHeader
        title={`${site.display_name} · Prices`}
        headingId={SITE_PRICES_HEADING_ID}
        subtitle={result?.status === "loaded" ? result.value.intro : undefined}
      />
      <OperatorSiteTabs
        siteId={site.site_id}
        current="Financials"
        hrefs={evWorkTabHrefs(site)}
        search={coldTabSearch(site, params) ?? evWorkTabSearch(site, params)}
      />
      <PricesSubtabs site={site} search={search} />
      {back ? (
        <div className="site-prices__return">
          <Link to={back} data-price-return>
            {RETURN_WORDS}
          </Link>
          <span>{RANGE_KEPT}</span>
        </div>
      ) : null}
      <PricesRead result={result} params={params} renderBelow={renderBelow} />
    </main>
  );
}
