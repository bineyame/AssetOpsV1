/**
 * IA-P P7 (packet-IA-P3 §8.4): on `/portfolio/outcomes` the Outcomes tab and the shell's "Waiting for you" read the
 * estate portfolio's page 1 through the one shared cache key `(client, "portfolio", range)`, so the URL is requested once.
 */
import { cleanup, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient } from "../../sites/siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import type { EstateClient, EstatePortfolioBody, EstatePortfolioQuery } from "../estateClient";
import type { PortfolioSites, PortfolioSitesClient } from "../portfolioSitesClient";
import { loaded } from "./estateFixtures";
import PORTFOLIO from "./fixtures/iap/portfolio.json?raw";
import SITES_OCT from "./fixtures/iap/sites-2026-10.json?raw";

beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };
const e1: PortfolioSitesClient = { fetchSites: () => Promise.resolve({ status: "loaded", body: JSON.parse(SITES_OCT) as PortfolioSites }) };

describe("one portfolio page-1 read per range", () => {
  it.each(["/portfolio/outcomes", "/portfolio/demand-and-capacity"])("%s requests page 1 once (the tab and the shell share it)", async (path) => {
    const firstPages: EstatePortfolioQuery[] = [];
    const client = {
      findings: () => Promise.reject(new Error("no findings")),
      actions: () => Promise.reject(new Error("no actions")),
      scope: () => Promise.reject(new Error("no scope")),
      portfolio: (query: EstatePortfolioQuery) => {
        if (query.cursor === null) firstPages.push(query);
        return Promise.resolve(loaded(JSON.parse(PORTFOLIO) as EstatePortfolioBody));
      },
      getOutcomeSummary: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }),
    } as unknown as EstateClient;
    render(
      <MemoryRouter initialEntries={[`${path}?from=2026-10-01&to=2026-10-31`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={{ listSites: () => Promise.resolve({ status: "loaded", sites: [] }) }} siteDetail={DETAIL} estateIndex={client} portfolioSites={e1} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(document.querySelector('[data-estate-root="portfolio"]')).not.toBeNull();
    expect(document.querySelector("[data-estate-loading]")).toBeNull();
    expect(firstPages).toHaveLength(1);
  });
});
