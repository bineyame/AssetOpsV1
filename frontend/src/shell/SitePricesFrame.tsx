import { Link, useParams, useSearchParams } from "react-router-dom";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { safeReturn } from "../sites/PriceAction";
import { PageHeader, Panel } from "../ui";
import { UnavailableInline } from "../ui/UnavailableEntry";
import { SiteScoped } from "./SiteAnalyticsFrames";

export const SITE_PRICES_HEADING_ID = "site-prices-heading";
/** The plain sign-in line (owner 2026-11-11; card PR-1): a roadmap fact, never an error. */
export const PRICES_SIGN_IN_TEXT =
  "Prices are set by your AssetOps administrator until sign-in is available. Saving a price from this page comes with sign-in.";

/**
 * PR-1 (BL-68): the target of every `price_action` link, `/sites/:siteId/financials/prices?key=|need=&return=`.
 * The read-only price page (current prices, history) is PR-2a; until it lands this address says so honestly, keeps
 * the reader's way back (`return`), and states who sets prices today. No write path and no form.
 */
export function SitePricesFrame({ detail }: { detail: SiteDetailClient }) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const back = safeReturn(params.get("return"));
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Prices" headingId={SITE_PRICES_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_PRICES_HEADING_ID} data-site-prices>
          <PageHeader title={`${site.display_name} · Prices`} headingId={SITE_PRICES_HEADING_ID} />
          {back ? (
            <p>
              <Link to={back} data-price-return>
                ← Back to where you were
              </Link>
            </p>
          ) : null}
          <Panel heading="Prices for this site" headingId={`${SITE_PRICES_HEADING_ID}-page`}>
            <p>
              <UnavailableInline label="The price page, with every price, where it came from and its history" />
            </p>
            <p data-prices-sign-in>{PRICES_SIGN_IN_TEXT}</p>
          </Panel>
        </main>
      )}
    </SiteScoped>
  );
}
