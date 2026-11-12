import { useEffect, useState, type ReactNode } from "react";
import { useLocation, useParams, useSearchParams } from "react-router-dom";
import { RangeLink as Link } from "../ui/RangeLink";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { safeReturn } from "../sites/PriceAction";
import { createPriceEntryClient, type PriceEntryClient } from "../sites/priceEntryClient";
import { createPricePageClient, type PricePageClient, type PricePageResult, type PriceRowBody } from "../sites/pricePageClient";
import { PriceEntrySlot } from "../sites/SitePriceEntry";
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
const DEFAULT_ENTRY_CLIENT = createPriceEntryClient();

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

/**
 * The page read. `version` re-reads after a PR-3 save; the previous body stays on screen until the new one arrives,
 * so the open row's success note is not replaced by the loading line.
 */
function usePricePage(client: PricePageClient, siteId: string, need: string | null, knownAt: string | null, version: number) {
  const key = `${siteId}|${need ?? ""}|${knownAt ?? ""}`;
  const [state, setState] = useState<{ key: string; result: PricePageResult } | null>(null);
  useEffect(() => {
    let live = true;
    void client.getPrices(siteId, { need, knownAt }).then((result) => {
      if (!live) return;
      // A failed re-read after a save keeps the body (and the success note) already on screen.
      setState((was) =>
        result.status !== "loaded" && was !== null && was.key === key && was.result.status === "loaded"
          ? was
          : { key, result },
      );
    });
    return () => {
      live = false;
    };
  }, [client, siteId, need, knownAt, key, version]);
  return state === null || state.key !== key ? null : state.result;
}

/** The same address without `known_at`: the live view, where a price can be set. */
function liveViewHref(pathname: string, params: URLSearchParams): string {
  const keep = new URLSearchParams(params);
  keep.delete("known_at");
  const text = keep.toString();
  return `${pathname}${text ? `?${text}` : ""}`;
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
 * use, set or not, with History; a `need` opens Part C. PR-3 (D-PRICE.1): when the body's `entry.enabled` is true
 * (entry service on, live view), each entry-key row hosts the inline price form through `renderBelow`; otherwise the
 * page stays read-only and, under `known_at`, says where a price can be set.
 */
export function SitePricesFrame({
  detail,
  client = DEFAULT_CLIENT,
  entryClient = DEFAULT_ENTRY_CLIENT,
  renderBelow,
}: {
  detail: SiteDetailClient;
  client?: PricePageClient;
  entryClient?: PriceEntryClient;
  renderBelow?: (row: PriceRowBody) => ReactNode;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Prices" headingId={SITE_PRICES_HEADING_ID}>
      {(site) => (
        <PricesMain site={site} client={client} entryClient={entryClient} params={params} renderBelow={renderBelow} />
      )}
    </SiteScoped>
  );
}

function PricesMain({
  site,
  client,
  entryClient,
  params,
  renderBelow,
}: {
  site: { site_id: string; site_type: string; display_name: string };
  client: PricePageClient;
  entryClient: PriceEntryClient;
  params: URLSearchParams;
  renderBelow?: (row: PriceRowBody) => ReactNode;
}) {
  const back = safeReturn(params.get("return"));
  const search = rangeSearch(params);
  const { pathname } = useLocation();
  const [version, setVersion] = useState(0);
  const [saved, setSaved] = useState<Record<string, string>>({});
  const result = usePricePage(client, site.site_id, params.get("need"), params.get("known_at"), version);
  const entry = result?.status === "loaded" ? result.value.entry : undefined;
  const focusKey = params.get("key");
  // PR-3: rows of entry keys take the inline form (stored keys only, live view, entry service on).
  const below =
    entry !== undefined && entry.enabled
      ? (row: PriceRowBody) =>
          entry.keys.includes(row.key) && row.stored ? (
            <PriceEntrySlot
              siteId={site.site_id}
              row={row}
              entry={entry}
              client={entryClient}
              openOnArrival={row.key === focusKey}
              savedSummary={saved[row.key] ?? null}
              onSaved={(key, summary) => {
                setSaved((was) => ({ ...was, [key]: summary }));
                setVersion((v) => v + 1);
              }}
              back={back}
              backWords={RETURN_WORDS}
            />
          ) : (
            renderBelow?.(row)
          )
      : renderBelow;
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
      {entry?.live_view ? (
        <p className="site-prices__live" data-prices-live-view>
          {entry.live_view.text}{" "}
          <Link to={liveViewHref(pathname, params)} data-prices-live-link>
            {entry.live_view.link_label}
          </Link>
        </p>
      ) : null}
      <PricesRead result={result} params={params} renderBelow={below} />
    </main>
  );
}
