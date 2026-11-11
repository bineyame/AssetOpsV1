/**
 * SR-2 (demo-critical): moving pages onto the shared range must not change any API request for the same range or
 * day, so the demo's pre-built responses (`tools/demo_combined.py` `prebuilt_routes`, which derives each request from
 * the `story_links` web link with `URLSearchParams` encoding) and the demo-script links keep matching. Each case opens
 * a story-link address in the whole App with the real clients and records the URLs the page fetches.
 */
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";
import { COLD_SITE } from "../../sites/__tests__/coldWorkFixtures";
import { EV_SITE } from "../../sites/__tests__/evWorkFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import type { SiteDetailClient } from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";

let urls: string[] = [];

// Recorded from main's (bfb2376f5) page sources (see the SR-2b describe below). The stubbed 503 stops each board at
// its first read, so the outcome-board request (built from the served day or the same window) is not reached here.
const DAY = "from=2026-11-03T00%3A00%3A00Z&to=2026-11-04T00%3A00%3A00Z";
const PERIOD = "from=2026-11-03T06%3A00%3A00Z&to=2026-11-03T09%3A30%3A00Z";
const NIGHTS = "from=2026-10-25T00%3A00%3A00Z&to=2026-11-05T00%3A00%3A00Z";
const SITE_KOBO = ["/api/sites/KOBO-001/overview?date=2026-11-03"];
const SITE_KISIWA = ["/api/sites/KISIWA-001/overview?date=2026-10-29"];
const cold = (w: string) => ["backup-chain", "evidence", "overview", "temperature"].map((r) => `/api/sites/COLD-LAB-001/cold/${r}?${w}`);
const SITE_COLD_DAY = cold(DAY);
const SITE_COLD_PERIOD = cold(PERIOD);
const SITE_EV_DAY = [
  `/api/sites/EV-LAB-001/ev/evidence/analysis?${DAY}&limit=200`,
  `/api/sites/EV-LAB-001/ev/evidence?${DAY}`,
  `/api/sites/EV-LAB-001/ev/financials?${DAY}`,
  `/api/sites/EV-LAB-001/ev/overview?${DAY}`,
];
const SITE_KISIWA_FINDINGS = [
  `/api/sites/KISIWA-001/finding-index?domain=mini-grid-dispatch&${NIGHTS}`,
  `/api/sites/KISIWA-001/fuel-findings?${NIGHTS}`,
];
const SITE_KISIWA_SERVICE = [
  "/api/sites/KISIWA-001/performance/mini/capabilities",
  "/api/sites/KISIWA-001/performance/mini/service?from=2026-10-31T09%3A00%3A00Z&to=2026-10-31T10%3A00%3A00Z",
];

beforeEach(() => {
  urls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      urls.push(typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url);
      return Promise.resolve(new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } }));
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function requestsAt(path: string): Promise<string[]> {
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} />
    </MemoryRouter>,
  );
  await settledScreen();
  view.unmount();
  return urls;
}

/** A Site page in the whole App: the Site detail is the fixture of the page's type; every other read is the real client. */
async function siteRequestsAt(path: string, site: SiteDetailReadModel): Promise<string[]> {
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site }) };
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDetail={detail} />
    </MemoryRouter>,
  );
  await settledScreen();
  view.unmount();
  return urls.filter((u) => u.startsWith("/api/sites/")).sort();
}

const as = (site: SiteDetailReadModel, code: string): SiteDetailReadModel => ({ ...site, site_id: code }) as SiteDetailReadModel;

describe("SR-2b the demo's Site board requests are byte-identical", () => {
  // `tools/demo_combined.py` story_links shapes. The strings are main's (bfb2376f5) requests for these addresses,
  // recorded by running this test on main's page sources before SR-2b changed them.
  it.each([
    ["Kobo day board, old date= link", "/sites/KOBO-001?date=2026-11-03", as(HYBRID_MINI_GRID_SITE, "KOBO-001"), SITE_KOBO],
    ["Kisiwa day board, old date= link", "/sites/KISIWA-001?date=2026-10-29", as(HYBRID_MINI_GRID_SITE, "KISIWA-001"), SITE_KISIWA],
    ["Cold whole day", "/sites/COLD-LAB-001?from=2026-11-03T00:00:00Z&to=2026-11-04T00:00:00Z", as(COLD_SITE, "COLD-LAB-001"), SITE_COLD_DAY],
    ["Cold analysed period", "/sites/COLD-LAB-001?from=2026-11-03T06:00:00Z&to=2026-11-03T09:30:00Z", as(COLD_SITE, "COLD-LAB-001"), SITE_COLD_PERIOD],
    ["EV whole day", "/sites/EV-LAB-001/ev?from=2026-11-03T00:00:00Z&to=2026-11-04T00:00:00Z", as(EV_SITE, "EV-LAB-001"), SITE_EV_DAY],
    [
      "Kisiwa Findings, story nights",
      "/sites/KISIWA-001/findings?from=2026-10-25T00:00:00Z&to=2026-11-05T00:00:00Z",
      as(HYBRID_MINI_GRID_SITE, "KISIWA-001"),
      SITE_KISIWA_FINDINGS,
    ],
    [
      "Kisiwa Service, story hour",
      "/sites/KISIWA-001/performance/service?from=2026-10-31T09:00:00Z&to=2026-10-31T10:00:00Z",
      as(HYBRID_MINI_GRID_SITE, "KISIWA-001"),
      SITE_KISIWA_SERVICE,
    ],
  ])("%s requests exactly what it did before SR-2b", async (_label, path, site, expected) => {
    expect(await siteRequestsAt(path, site)).toEqual(expected);
  });
});

describe("SR-2 the demo's API requests are byte-identical", () => {
  // The strings are main's (66a38d849) requests for these story-link addresses, recorded before SR-2 changed a page.
  const W = "from=2026-10-25T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z";
  it.each([
    ["/portfolio?from=2026-10-25T00:00:00Z&to=2026-11-02T00:00:00Z", [`/api/estate/portfolio?${W}&limit=50`, `/api/estate/outcome-summary?${W}`]],
    ["/findings?from=2026-10-25T00:00:00Z&to=2026-11-02T00:00:00Z", [`/api/estate/findings?${W}`, `/api/estate/scope?${W}`, `/api/estate/outcome-summary?${W}`]],
    ["/maintenance?from=2026-10-04T00:00:00Z&to=2026-11-04T00:00:00Z", ["/api/work/maintenance?from=2026-10-04T00%3A00%3A00Z&to=2026-11-04T00%3A00%3A00Z&limit=5"]],
  ])("%s requests exactly what it did before SR-2", async (path, expected) => {
    const got = await requestsAt(path);
    for (const url of expected) expect(got).toContain(url);
    // Nothing else on the estate or Work APIs: no second read for a reshaped range.
    expect(got.filter((u) => u.startsWith("/api/estate/") || u.startsWith("/api/work/")).sort()).toEqual([...expected].sort());
  });
});
