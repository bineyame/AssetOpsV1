/**
 * SR-6b (rev 10 §10.2; D-SR.20, D-SR.49, D-SR.56): mini-grid Health over the date range. The frame mounted at its
 * route with the recorded S7 source-health and battery answers, and a `site-health-range-1` body for a 4-day window.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s7_health_api_contract.json";
import { SiteHealthFrame } from "../../shell/SiteHealthFrames";
import { settledScreen } from "../../test/settled";
import { createHealthRangeClient, type HealthRangeBody } from "../healthRangeClient";
import { statusLine } from "../SiteHealthRange";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { RETRYING_COPY, STILL_UNAVAILABLE_COPY } from "../temporarilyUnavailable";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

interface Served {
  status: number;
  body: unknown;
}
const C = contract as unknown as Record<string, Served>;

const RANGE = "from=2026-10-05T00:00:00Z&to=2026-10-09T00:00:00Z";
const RANGE_API = "from=2026-10-05T00%3A00%3A00Z&to=2026-10-09T00%3A00%3A00Z";
const DAY_API = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z";
const DAYS = ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08"];

const BODY: HealthRangeBody = {
  schema_version: "site-health-range-1",
  site: { site_code: "KOBO-001", site_name: "Kobo", timezone: "Africa/Nairobi" },
  window: { from: "2026-10-05T00:00:00Z", to: "2026-10-09T00:00:00Z", known_at: null, basis: "CURRENT" },
  gateways: [
    {
      gateway_external_id: "G1",
      mode: "LIVE",
      disabled: false,
      cadence_seconds: 300,
      days: [
        { day: DAYS[0], diagnostics: 0, first_received_at: null, last_received_at: null, contact: "NOT_EXPECTED" },
        { day: DAYS[1], diagnostics: 0, first_received_at: null, last_received_at: null, contact: "READINGS_ONLY" },
        { day: DAYS[2], diagnostics: 288, first_received_at: null, last_received_at: null, contact: "IN_CONTACT" },
        { day: DAYS[3], diagnostics: 0, first_received_at: null, last_received_at: null, contact: "AFTER_CUTOFF" },
      ],
    },
  ],
  sources: [
    {
      source_external_id: "S1",
      disabled: false,
      days: [
        { day: DAYS[0], accepted_readings: 0, last_received_at: null, state: "NOT_EXPECTED" },
        { day: DAYS[1], accepted_readings: 288, last_received_at: null, state: "READINGS" },
        { day: DAYS[2], accepted_readings: 0, last_received_at: null, state: "NO_READINGS" },
        { day: DAYS[3], accepted_readings: 0, last_received_at: null, state: "AFTER_CUTOFF" },
      ],
    },
  ],
  days: [
    { day: DAYS[0], state: "NOT_EXPECTED", accepted_readings: null },
    { day: DAYS[1], state: "ANALYSED", accepted_readings: 280 },
    { day: DAYS[2], state: "NO_READINGS", accepted_readings: null },
    { day: DAYS[3], state: "NOT_ANALYSED", accepted_readings: null },
  ],
  summary: {
    days_requested: 4,
    days_with_readings: 1,
    days_without_readings: 1,
    days_not_expected: 1,
    days_after_cutoff: 1,
    gateways_in_contact_all_days: 0,
  },
  links: { day: "/sites/KOBO-001/health?day={day}" },
};

function serve(table: Record<string, Served | Served[]>) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    requests.push(url);
    let hit = table[url];
    if (Array.isArray(hit)) hit = hit.length > 1 ? hit.shift()! : hit[0];
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: url } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return requests;
}

const POINT: Record<string, Served> = {
  "/api/sites/KOBO-001/source-health": C.health_kobo001,
  "/api/sites/KOBO-001/battery": C.battery_entry_kobo001,
};

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;

function mount(path: string, delays: number[] = [0, 0, 0]) {
  const client = createHealthRangeClient(undefined, delays);
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/sites/:siteId/health" element={<SiteHealthFrame detail={detail} sitesPath="/sites" healthRange={client} />} />
      </Routes>
    </MemoryRouter>,
  );
}

const cell = (label: string) => document.body.querySelector(`[aria-label="${label}"]`);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("SR-6b mini-grid Health over the range", () => {
  it("states the readings per day, gateway contact and source readings, then the point-in-time panels", async () => {
    const requests = serve({ ...POINT, [`/api/sites/KOBO-001/health-range?${RANGE_API}`]: { status: 200, body: BODY } });
    mount(`/sites/KOBO-001/health?${RANGE}`);
    await settledScreen();
    expect(requests).toContain(`/api/sites/KOBO-001/health-range?${RANGE_API}`);
    expect(
      screen.getByText("Readings on 1 of 4 days · 1 day with no readings · 1 day before readings began · 1 day not reached yet"),
    ).toBeTruthy();
    expect(screen.getByText("Gateways in contact on every expected day: 0 of 1")).toBeTruthy();
    // Gateway cells: every D-SR.20/49 word, named per gateway and day.
    expect(cell("Gateway G1, 5 Oct: before it was registered")?.textContent).toBe("Before it was registered");
    expect(cell("Gateway G1, 6 Oct: readings received; no status reports")?.textContent).toBe(
      "Readings received; no status reports",
    );
    expect(cell("Gateway G1, 7 Oct: in contact")?.textContent).toBe("In contact");
    expect(cell("Gateway G1, 8 Oct: not reached yet")?.textContent).toBe("Not reached yet");
    // Source cells: "Readings received" counts (D-SR.49 Q3), never under the analysis name.
    expect(cell("Source S1, 6 Oct: 288 readings received")?.textContent).toBe("288");
    expect(cell("Source S1, 7 Oct: no readings")?.textContent).toBe("No readings");
    expect(cell("Source S1, 5 Oct: before readings began")?.textContent).toBe("Before readings began");
    // Day row: the SR-5a state and the dispatch row's count, "Readings used for analysis".
    expect(screen.getByRole("rowheader", { name: "Readings used for analysis" })).toBeTruthy();
    expect(cell("6 Oct: 280 readings used for analysis")?.textContent).toBe("280");
    expect(cell("6 Oct: analysed")).not.toBeNull();
    expect(cell("7 Oct: no readings")?.textContent).toBe("No readings");
    // Each day opens the drill-in, the range kept.
    const link = screen.getAllByRole("link", { name: "6 Oct" })[0];
    const href = new URL(link.getAttribute("href")!, "http://x");
    expect(href.pathname).toBe("/sites/KOBO-001/health");
    expect(href.searchParams.get("day")).toBe("2026-10-06");
    expect(href.searchParams.get("from")).toBe("2026-10-05T00:00:00Z");
    // The point-in-time panels below, renamed (rev 10 §10.2, D-SR.49 Q5).
    expect(screen.getByRole("heading", { name: "Battery (current settings)" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Contact now" })).toBeTruthy();
    expect(screen.getByText(/^Point in time: contact as of now/)).toBeTruthy();
  });

  it("the drill-in reads one day and links back to the whole range", async () => {
    const requests = serve({ ...POINT, [`/api/sites/KOBO-001/health-range?${DAY_API}`]: { status: 200, body: BODY } });
    mount(`/sites/KOBO-001/health?${RANGE}&day=2026-10-06`);
    await settledScreen();
    expect(requests).toContain(`/api/sites/KOBO-001/health-range?${DAY_API}`);
    const back = screen.getByRole("link", { name: "Back to the whole range" });
    const href = new URL(back.getAttribute("href")!, "http://x");
    expect(href.searchParams.get("day")).toBeNull();
    expect(href.searchParams.get("from")).toBe("2026-10-05T00:00:00Z");
    expect(href.searchParams.get("to")).toBe("2026-10-09T00:00:00Z");
    expect(screen.queryAllByRole("link", { name: "6 Oct" })).toHaveLength(0);
  });

  it("503 SITE_HEALTH_RANGE_UNAVAILABLE reads \"Temporarily unavailable. Retrying…\", then the body", async () => {
    const down = { status: 503, body: { detail: { code: "SITE_HEALTH_RANGE_UNAVAILABLE", message: "x" } } };
    serve({ ...POINT, [`/api/sites/KOBO-001/health-range?${RANGE_API}`]: [down, { status: 200, body: BODY }] });
    mount(`/sites/KOBO-001/health?${RANGE}`, [60]);
    expect(await screen.findByText(RETRYING_COPY)).toBeTruthy();
    expect(await screen.findByText(/^Readings on 1 of 4 days/)).toBeTruthy();
  });

  it("after the last retry it reads \"Still unavailable. Refresh to try again.\"", async () => {
    const down = { status: 503, body: { detail: { code: "SITE_HEALTH_RANGE_UNAVAILABLE", message: "x" } } };
    serve({ ...POINT, [`/api/sites/KOBO-001/health-range?${RANGE_API}`]: [down] });
    mount(`/sites/KOBO-001/health?${RANGE}`, [0, 0]);
    expect(await screen.findByText(STILL_UNAVAILABLE_COPY)).toBeTruthy();
  });

  it("another refusal keeps its status and code inside the panel", async () => {
    serve({
      ...POINT,
      [`/api/sites/KOBO-001/health-range?${RANGE_API}`]: { status: 422, body: { detail: { code: "INVALID_WINDOW", message: "x" } } },
    });
    mount(`/sites/KOBO-001/health?${RANGE}`);
    await settledScreen();
    const gap = document.body.querySelector('[data-health-read="refused"][data-health-http="422"]');
    expect(gap).not.toBeNull();
    expect(screen.getByRole("heading", { name: "Contact now" })).toBeTruthy();
  });

  it("without a range in the address the page stays point in time", async () => {
    const requests = serve(POINT);
    mount("/sites/KOBO-001/health");
    await settledScreen();
    expect(requests.some((u) => u.includes("/health-range"))).toBe(false);
    expect(screen.queryByRole("heading", { name: "Contact now" })).toBeNull();
  });

  it("the status line names only the non-zero classes (D-SR.49 Q1)", () => {
    expect(
      statusLine({ ...BODY.summary, days_with_readings: 1, days_without_readings: 3, days_not_expected: 0, days_after_cutoff: 0 }),
    ).toBe("Readings on 1 of 4 days · 3 days with no readings");
  });
});
