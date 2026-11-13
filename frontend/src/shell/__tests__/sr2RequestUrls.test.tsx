/**
 * SR-2 (demo-critical): moving pages onto the shared range must not change any API request for the same range or
 * day, so the demo's pre-built responses (`tools/demo_combined.py` `prebuilt_routes`, which derives each request from
 * the `story_links` web link with `URLSearchParams` encoding) and the demo-script links keep matching. Each case opens
 * a story-link address in the whole App with the real clients and records the URLs the page fetches.
 */
import { render, screen } from "@testing-library/react";
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
import { summary } from "./s5WindowFixtures";
import { MINI_HOUR_OR_DAY, MINI_INVALID_WINDOW, MINI_RENEWABLE_DAYS, MINI_REVERSED_WINDOW } from "../../sites/MiniPerformance";
import { localDaysWindow } from "../../sites/miniDepthClient";
import { presetRange, rangeParams } from "../../ui/sharedRange";

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
// SR-10k: the Kisiwa Fuel tab's nights list reads the date range (rev 10b.4). The hour read is SR-4's (D-SR.59):
// one Site-local hour of the range's last day, as on Service.
const SITE_KISIWA_FUEL_RANGE = [
  "/api/sites/KISIWA-001/fuel-balance/nights?from=2026-10-25T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z",
  "/api/sites/KISIWA-001/performance/mini/capabilities",
  "/api/sites/KISIWA-001/performance/mini/fuel?from=2026-10-31T09%3A00%3A00.000Z&to=2026-10-31T10%3A00%3A00.000Z",
];
const SITE_KISIWA_SERVICE = [
  "/api/sites/KISIWA-001/performance/mini/capabilities",
  "/api/sites/KISIWA-001/performance/mini/service?from=2026-10-31T09%3A00%3A00Z&to=2026-10-31T10%3A00%3A00Z",
];
// Old `date=` Renewable/Service links (Site-local day of the UTC day; KISIWA fixture zone UTC+3) and the Kobo board
// with its overview answered: recorded on the pre-change sources (miniDepthClient at 2e291ecc1; SiteOverview and
// SiteWindowOverview at bfb2376f5), restored after.
const SITE_KISIWA_SERVICE_DATE = [
  "/api/sites/KISIWA-001/performance/mini/capabilities",
  "/api/sites/KISIWA-001/performance/mini/service?from=2026-10-31T09%3A00%3A00.000Z&to=2026-10-31T10%3A00%3A00.000Z",
];
const SITE_KISIWA_RENEWABLE_DATE = [
  "/api/sites/KISIWA-001/performance/mini/capabilities",
  "/api/sites/KISIWA-001/performance/mini/renewable?from=2026-10-30T21%3A00%3A00.000Z&to=2026-10-31T21%3A00%3A00.000Z",
];
const SITE_KOBO_BOARD = [
  "/api/sites/KOBO-001/outcome-board?date=2026-11-03&finding_id=11111111-1111-4111-8111-111111111111&finding_revision_id=22222222-2222-4222-8222-222222222222",
  "/api/sites/KOBO-001/overview?date=2026-11-03",
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

describe("SR-2b old date= links on Renewable and Service read the same day as day=", () => {
  // The legacy `date=` and the new `day=` must request exactly the same window; `date=` strings recorded on the sources
  // before this change (main's miniDepthClient read `date` only).
  it.each([
    ["service", SITE_KISIWA_SERVICE_DATE],
    ["renewable", SITE_KISIWA_RENEWABLE_DATE],
  ])("%s: date= and day= request the same window, unchanged from before", async (page, expected) => {
    const site = as(HYBRID_MINI_GRID_SITE, "KISIWA-001");
    const legacy = await siteRequestsAt(`/sites/KISIWA-001/performance/${page}?date=2026-10-31`, site);
    urls = [];
    const current = await siteRequestsAt(`/sites/KISIWA-001/performance/${page}?day=2026-10-31`, site);
    expect(legacy).toEqual(expected);
    expect(current).toEqual(expected);
  });
});

describe("SR-4b Kobo/Kisiwa with a range and no day read the range's last day, never today", () => {
  const RANGED = "from=2026-11-02T00:00:00Z&to=2026-11-09T00:00:00Z"; // 2-8 Nov
  // Dispatch (`windows/<range.to>`) sits behind the analytics and cutover reads; its pin is in performanceDispatch.test.
  it.each([
    ["Kobo board", "/sites/KOBO-001", "KOBO-001", ["/api/sites/KOBO-001/overview?date=2026-11-08"]],
    ["Kisiwa board", "/sites/KISIWA-001", "KISIWA-001", ["/api/sites/KISIWA-001/overview?date=2026-11-08"]],
  ])("%s", async (_label, path, code, expected) => {
    const got = await siteRequestsAt(`${path}?${RANGED}`, as(HYBRID_MINI_GRID_SITE, code));
    expect(got.filter((u) => u.includes("/overview"))).toEqual(expected);
  });
});

describe("SR-2b the Kobo board's outcome-board request is byte-identical", () => {
  // The overview read answers (s5 window fixture for the served day) so the board reaches its outcome-board read.
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        urls.push(url);
        const day = /\/overview\?date=(\d{4}-\d{2}-\d{2})/.exec(url)?.[1];
        if (day) return Promise.resolve(new Response(JSON.stringify(summary(day)), { status: 200, headers: { "Content-Type": "application/json" } }));
        return Promise.resolve(new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } }));
      }),
    );
  });
  it.each([
    ["old date= link", "/sites/KOBO-001?date=2026-11-03"],
    ["day= link", "/sites/KOBO-001?day=2026-11-03"],
    ["day= inside a shared range", "/sites/KOBO-001?from=2026-11-01T00:00:00Z&to=2026-11-04T00:00:00Z&day=2026-11-03"],
  ])("%s", async (_label, path) => {
    const got = await siteRequestsAt(path, as(HYBRID_MINI_GRID_SITE, "KOBO-001"));
    expect(got.filter((u) => u.includes("/overview") || u.includes("/outcome-board"))).toEqual(SITE_KOBO_BOARD);
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

describe("SR-10k the Kisiwa Fuel tab reads the range's fuel-check nights", () => {
  it("a 7-day range sends its instants on the nights request", async () => {
    const path = "/sites/KISIWA-001/performance/fuel?from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z";
    expect(await siteRequestsAt(path, as(HYBRID_MINI_GRID_SITE, "KISIWA-001"))).toEqual(SITE_KISIWA_FUEL_RANGE);
  });
});

describe("SR-6b mini-grid Health with a range reads health-range over the range's instants", () => {
  it("the range page and its one-day drill-in", async () => {
    const range = "from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z";
    // Sorted: the point-in-time battery and source-health reads stay, beside the one range read.
    expect(await siteRequestsAt(`/sites/KOBO-001/health?${range}`, as(HYBRID_MINI_GRID_SITE, "KOBO-001"))).toEqual([
      "/api/sites/KOBO-001/battery",
      "/api/sites/KOBO-001/health-range?from=2026-10-25T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z",
      "/api/sites/KOBO-001/source-health",
    ]);
    urls = [];
    expect(await siteRequestsAt(`/sites/KOBO-001/health?${range}&day=2026-10-28`, as(HYBRID_MINI_GRID_SITE, "KOBO-001"))).toEqual([
      "/api/sites/KOBO-001/battery",
      "/api/sites/KOBO-001/health-range?from=2026-10-28T00%3A00%3A00Z&to=2026-10-29T00%3A00%3A00Z",
      "/api/sites/KOBO-001/source-health",
    ]);
  });
});

describe("SR-4 H-1 (D-SR.59) Kobo Renewable and Service under \"Yesterday\" send Site-local bounds and show no refusal", () => {
  // The stub refuses (INVALID_WINDOW, like `hour_windows`) every mini read except the pinned Site-local window, so a
  // client that sends the raw UTC day gets the refusal on screen and a different URL.
  const site = as(HYBRID_MINI_GRID_SITE, "KOBO-001");
  const tz = site.timezone as string;
  const yesterday = presetRange("yesterday");
  const address = rangeParams({ ...yesterday, known_at: null }).toString();
  const mini = (page: string, w: { from: string; to: string }) =>
    `/api/sites/KOBO-001/performance/mini/${page}?${new URLSearchParams(w).toString()}`;
  it.each([
    ["renewable", mini("renewable", localDaysWindow(tz, yesterday.from, 1))],
  ])("%s", async (page, expected) => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        urls.push(url);
        if (url.includes(`/performance/mini/${page}?`) && url !== expected) {
          return Promise.resolve(new Response(JSON.stringify({ detail: { code: "INVALID_WINDOW" } }), { status: 422, headers: { "Content-Type": "application/json" } }));
        }
        return Promise.resolve(new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } }));
      }),
    );
    const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site }) };
    const view = render(
      <MemoryRouter initialEntries={[`/sites/KOBO-001/performance/${page}?${address}`]}>
        <App flags={featureFlagsWith(false)} siteDetail={detail} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(urls.filter((u) => u.includes(`/performance/mini/${page}?`))).toEqual([expected]);
    for (const copy of [MINI_RENEWABLE_DAYS, MINI_HOUR_OR_DAY, MINI_INVALID_WINDOW, MINI_REVERSED_WINDOW]) {
      expect(screen.queryByText(copy)).toBeNull();
    }
    view.unmount();
  });
});

describe("SR-7 / SR-11: Service and Backup over a range send one range read with the range's instants", () => {
  // Rev 10 §10.3 / 10b.3: a range without an hour reads `service-range` / `backup-range` (was SR-4 H-1's Service hour
  // under "Yesterday"); Site Evidence's claim-limit section with no day reads `claim-limit-range`. No hour read is sent.
  const site = as(HYBRID_MINI_GRID_SITE, "KOBO-001");
  const yesterday = presetRange("yesterday");
  const Y = rangeParams({ ...yesterday, known_at: null }).toString();
  const W = "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z";
  const K = "known_at=2026-11-09T06%3A00%3A00Z";
  it.each([
    ["Service, Yesterday", `/sites/KOBO-001/performance/service?${Y}`, `/api/sites/KOBO-001/service-range?${Y}`],
    ["Service, 7 days at a cutoff", `/sites/KOBO-001/performance/service?${W}&${K}`, `/api/sites/KOBO-001/service-range?${W}&${K}`],
    ["Backup, 7 days", `/sites/KOBO-001/performance/backup?${W}`, `/api/sites/KOBO-001/backup-range?${W}`],
    ["Backup, Kisiwa 7 days", `/sites/KISIWA-001/performance/backup?${W}`, `/api/sites/KISIWA-001/backup-range?${W}`],
  ])("%s", async (_label, path, expected) => {
    const code = path.split("/")[2];
    const got = await siteRequestsAt(path, code === "KOBO-001" ? site : as(HYBRID_MINI_GRID_SITE, code));
    expect(got.filter((u) => u.includes("-range?"))).toEqual([expected]);
    expect(got.filter((u) => /\/performance\/mini\/(service|backup)\?/.test(u))).toEqual([]);
  });
});
