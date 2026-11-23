/**
 * Test-only: an E1 (`/api/portfolio/sites`) stub for route tests that mount `/sites` through `App` (IA-P P4b). Its body is
 * the served mode-`none` fixture with no rows and no notes, so the directory's Sites are the list's rows (D-IAP.35 Q1:
 * directory order, Group from `site_type`) and nothing else lands on the page. Pass `rows` to serve E1 rows too.
 */
import { createEstateClient, type EstateClient, type EstatePortfolioBody } from "../estate/estateClient";
import { loaded } from "../estate/__tests__/estateFixtures";
import type { PortfolioSiteRow, PortfolioSites, PortfolioSitesClient } from "../estate/portfolioSitesClient";
import PORTFOLIO from "../estate/__tests__/fixtures/iap/portfolio.json?raw";
import SITES_NONE from "../estate/__tests__/fixtures/iap/sites-none-2026-11.json?raw";

export function sitesE1(rows: readonly PortfolioSiteRow[] = []): PortfolioSitesClient {
  const body = { ...(JSON.parse(SITES_NONE) as PortfolioSites), rows: [...rows], notes: [] };
  return { fetchSites: () => Promise.resolve({ status: "loaded", body }) };
}

/**
 * Test-only: the app's estate client with its portfolio read (E0) answered from the World A fixture, `waiting_by_site`
 * replaced. Every other read is the default client's, as when a route test passes no estate client.
 */
export function estateE0(waitingBySite: Record<string, number>): EstateClient {
  const body = JSON.parse(PORTFOLIO) as EstatePortfolioBody;
  const value = { ...body, summary: { ...body.summary, waiting_by_site: waitingBySite } };
  return { ...createEstateClient(), portfolio: () => Promise.resolve(loaded(value)) } as EstateClient;
}
