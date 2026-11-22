/**
 * IA-P P4b (spec §3 "page by Site-type range matrix", §6 P4b; D-IAP.25, D-IAP.26): a cold-chain Site with no monthly
 * figures (World G's Thika) is named on the Overview, on Outcomes and on the Sites list, on a one-month and a two-month
 * range. Every body is a committed IA-P fixture written by the backend's view (`test_iap_portfolio_period.py` test 10,
 * `test_iap_portfolio_sites.py` test 9).
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import type { DeepDiveMonthBody, DeepDiveMonthClient } from "../deepDiveMonthClient";
import type { EstateClient, EstatePortfolioBody } from "../estateClient";
import type { PeriodResult, PortfolioPeriod, PortfolioPeriodClient } from "../portfolioPeriodClient";
import type { PortfolioSites, PortfolioSitesClient } from "../portfolioSitesClient";
import { loaded } from "./estateFixtures";
import MONTH_G from "./fixtures/iap/month-g-2026-10.json?raw";
import PERIOD_MONTH_G from "./fixtures/iap/period-month-g-2026-10.json?raw";
import PERIOD_PERIOD_G from "./fixtures/iap/period-period-g-2026-09-10.json?raw";
import PORTFOLIO from "./fixtures/iap/portfolio.json?raw";
import SITES_G_OCT from "./fixtures/iap/sites-g-2026-10.json?raw";
import SITES_G_P from "./fixtures/iap/sites-g-2026-09-10.json?raw";

const parse = <T,>(text: string): T => JSON.parse(text) as T;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

const PERIOD: Record<string, string> = { "2026-10-01|2026-10-31": PERIOD_MONTH_G, "2026-09-01|2026-10-31": PERIOD_PERIOD_G };
const SITES: Record<string, string> = { "2026-10-01|2026-10-31": SITES_G_OCT, "2026-09-01|2026-10-31": SITES_G_P };

const period: PortfolioPeriodClient = {
  fetchPeriod: (from, to) => Promise.resolve<PeriodResult>({ status: "loaded", body: parse<PortfolioPeriod>(PERIOD[`${from}|${to}`]) }),
};
const month: DeepDiveMonthClient = { fetchDeepDiveMonth: () => Promise.resolve({ status: "loaded", body: parse<DeepDiveMonthBody>(MONTH_G) }) };
const sites: PortfolioSitesClient = {
  fetchSites: (from, to) => Promise.resolve({ status: "loaded", body: parse<PortfolioSites>(SITES[`${from}|${to}`]) }),
};
const estate = {
  findings: () => Promise.reject(new Error("no findings")),
  actions: () => Promise.reject(new Error("no actions")),
  scope: () => Promise.reject(new Error("no scope")),
  portfolio: () => Promise.resolve(loaded(parse<EstatePortfolioBody>(PORTFOLIO))),
  getOutcomeSummary: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }),
} as unknown as EstateClient;

beforeEach(() => {
  window.sessionStorage.clear();
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

async function textAt(path: string): Promise<string> {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={DIRECTORY} siteDetail={DETAIL} estateIndex={estate} deepDive={month} portfolioPeriod={period} portfolioSites={sites} />
    </MemoryRouter>,
  );
  await settledScreen();
  return document.body.textContent ?? "";
}

describe("IA-P P4b: Thika (cold-chain) is named on every page of the matrix", () => {
  for (const [label, range] of [
    ["one month", "from=2026-10-01&to=2026-10-31"],
    ["two months", "from=2026-09-01&to=2026-10-31"],
  ] as const) {
    it(`Overview, ${label}`, async () => {
      const text = await textAt(`/portfolio?${range}`);
      if (label === "two months") {
        expect(text).toContain("Thika"); // D-IAP.34: in the lead
      } else {
        // One month: 5c's `out` reason sits in the step drawer (D-IAP.25), one click away.
        fireEvent.click(document.querySelector<HTMLElement>('[data-level="L3"] button[aria-haspopup="dialog"]')!);
        expect(screen.getByRole("dialog").textContent).toContain("Thika: not a mini-grid Site, not included.");
      }
    });
    it(`Outcomes, ${label}: Thika's row says why by type`, async () => {
      const text = await textAt(`/portfolio/outcomes?${range}`);
      expect(text).toContain("Thika");
      expect(text).toContain("No monthly figures for cold-chain Sites yet");
    });
    it(`Sites list, ${label}: Thika's row says why by type`, async () => {
      const text = await textAt(`/sites?${range}`);
      expect(text).toContain("Thika");
      expect(text).toContain("No monthly figures for cold-chain Sites yet");
      expect(text).toContain("1 Site without a target is not in this figure");
    });
  }
});
