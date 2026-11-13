/**
 * SR-5e (architect rev 9 §9.4, D-SR.10): every Site route, per Site type, against `RANGE_MATRIX`. Whole App with the
 * SR-4a Site fixtures (Kobo for `mini`, the cold and EV labs); every read but the Site detail answers 503, and the
 * test records each request the page makes, with the range 3–9 Nov in the address.
 *
 * - R: every Site data request (excluding the reads in NOT_DATA) carries `from`/`to` equal to the range's instants
 *   (or is `range-overview` with them); only the row's `knownUnranged` reads may lack them. The bar says "All pages".
 * - D: with `day=` inside the range, the bar names that day ("Showing 5 Nov of the range"); without one, the bar never
 *   claims the range is unused.
 * - N: the bar declares "Range not used · …"; a record page that declares only once its record loads (the fixture
 *   refuses it) at least never names a span.
 * - A Site route in `App.tsx` with no matrix row fails, and so does a row whose route is not in `App.tsx`.
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
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";
import { RANGE_MATRIX, type MatrixSite, type RangeMatrixEntry } from "../../ui/rangeMatrix";
import * as ROUTES from "../operatorSiteRoutes";

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();

const FROM = "2026-11-03T00:00:00Z";
const TO = "2026-11-10T00:00:00Z";
const RANGE = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;

const CODE: Record<MatrixSite, string> = { mini: "KOBO-001", cold: "COLD-LAB-001", ev: "EV-LAB-001" };
const as = (site: SiteDetailReadModel, code: string): SiteDetailReadModel => ({ ...site, site_id: code }) as SiteDetailReadModel;
const SITES: Record<string, SiteDetailReadModel> = {
  "KOBO-001": as(HYBRID_MINI_GRID_SITE, "KOBO-001"),
  "COLD-LAB-001": as(COLD_SITE as SiteDetailReadModel, "COLD-LAB-001"),
  "EV-LAB-001": as(EV_SITE as SiteDetailReadModel, "EV-LAB-001"),
};
const DETAIL = {
  getSite: (code: string) => Promise.resolve(SITES[code] ? { status: "loaded", site: SITES[code] } : { status: "not_found" }),
} as SiteDetailClient;
const DIRECTORY = { listSites: () => Promise.resolve({ status: "loaded", sites: Object.values(SITES) }) } as SiteDirectoryClient;

/** Reads that are not range data: the analytics declaration, the mini capability list and the Dispatch cutover. */
const NOT_DATA = [/\/analytics$/, /\/performance\/mini\/capabilities$/, /\/cutover$/, /lineage/];

let urls: string[] = [];

beforeEach(() => {
  urls = [];
  window.sessionStorage.clear();
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

async function open(entry: RangeMatrixEntry, extra = "") {
  urls = [];
  const view = render(
    <MemoryRouter initialEntries={[`/sites/${CODE[entry.site]}${entry.path}?${RANGE}${extra}`]}>
      <App flags={featureFlagsWith(false)} siteDetail={DETAIL} siteDirectory={DIRECTORY} />
    </MemoryRouter>,
  );
  await settledScreen();
  const tag = document.querySelector(".shared-range__tag");
  const result = {
    text: tag?.textContent ?? null,
    focus: tag?.getAttribute("data-shared-range-focus") ?? null,
    requests: [...new Set(urls)].filter((u) => u.startsWith(`/api/sites/${CODE[entry.site]}/`)),
  };
  view.unmount();
  return result;
}

/** A Site data request that does not carry the range's own `from`/`to`. */
function unranged(url: string): boolean {
  const [path, query = ""] = url.split("?", 2);
  if (NOT_DATA.some((re) => re.test(path))) return false;
  const q = new URLSearchParams(query);
  return q.get("from") !== FROM || q.get("to") !== TO;
}

const label = (e: RangeMatrixEntry) => `${e.site} ${e.path || "/"} (${e.class})`;

describe("SR-5e every Site route is classified", () => {
  it("each Site route in App.tsx has a matrix row, and each row's route is in App.tsx", () => {
    const app = NODE_FS.readFileSync(`${CWD}/src/App.tsx`, "utf8");
    const used = new Set(app.match(/\b[A-Z_]+_ROUTE_PATH\b/g) ?? []);
    const routes = new Set(
      Object.entries(ROUTES)
        .filter(([name, value]) => used.has(name) && typeof value === "string" && value.startsWith("/sites/:siteId"))
        .map(([, value]) => value as string),
    );
    expect(routes.size).toBeGreaterThan(30); // the set is not empty
    const classified = new Set(RANGE_MATRIX.map((e) => e.route));
    expect([...routes].filter((r) => !classified.has(r)), "Site routes with no RANGE_MATRIX row").toEqual([]);
    expect([...classified].filter((r) => !routes.has(r)), "RANGE_MATRIX rows for routes App.tsx does not mount").toEqual([]);
  });
});

describe("SR-5e R rows: every data read carries the range, and the bar says All pages", () => {
  it.each(RANGE_MATRIX.filter((e) => e.class === "R").map((e) => [label(e), e] as const))("%s", async (_l, entry) => {
    const got = await open(entry);
    expect(got.focus, "the bar declares nothing").toBeNull();
    expect(got.text).toBe("All pages");
    const allowed = (entry.knownUnranged ?? []).map((g) => g.read);
    const bad = got.requests.filter(unranged).filter((u) => !allowed.some((read) => u.split("?", 1)[0].endsWith(read)));
    expect(bad, "data reads without the range").toEqual([]);
    // A known gap that is no longer read unranged must leave the list.
    for (const read of allowed) expect(got.requests.filter(unranged).some((u) => u.split("?", 1)[0].endsWith(read)), `${read} still unranged`).toBe(true);
  });
});

describe("SR-5e D rows: a day inside the range is named in the bar", () => {
  it.each(RANGE_MATRIX.filter((e) => e.class === "D").map((e) => [label(e), e] as const))("%s", async (_l, entry) => {
    const day = await open(entry, "&day=2026-11-05");
    if (entry.blockedBy !== undefined) {
      expect(day.requests.some((u) => u.split("?", 1)[0].endsWith(entry.blockedBy as string))).toBe(true);
      expect(day.focus).not.toBe("now");
      return;
    }
    expect(day.focus).not.toBeNull();
    expect(day.focus).not.toBe("now");
    expect(day.text).toMatch(/^Showing .* of the range$/);
    const bare = await open(entry);
    expect(bare.focus).not.toBe("now");
  });
});

describe("SR-5e N rows: the bar says the range is not used", () => {
  it.each(RANGE_MATRIX.filter((e) => e.class === "N").map((e) => [label(e), e] as const))("%s", async (_l, entry) => {
    const got = await open(entry);
    if (entry.declaresOnLoad || entry.forwards) {
      expect(got.text ?? "").not.toMatch(/^Showing /);
      return;
    }
    expect(got.focus).toBe("now");
    expect(got.text).toMatch(/^Range not used · /);
  });
});
