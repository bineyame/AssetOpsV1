import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { FuelRangeDay, FuelRangeRead, FuelRead, MiniDepthClient, MiniRead } from "../miniDepthClient";
import { MiniFuelRange, MiniFuelRangePage } from "../MiniFuelRange";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";

/*
 * SR-10c (rev 10b.2, D-SR.32/51/57/70-72): the Fuel tab over a shared range reads `fuel-range` once and shows the
 * modelled-days line, the per-day modelled band, the day table and "Residual: not available"; a day's 12:00 hour opens
 * the hour page with "Back to the whole range". D-SR.57: in the hour view the FocusPicker is the only declarer, and
 * the range view declares nothing.
 */

// Every range declaration a page makes, recorded around the real hooks (behaviour unchanged).
const declared = vi.hoisted(() => [] as Array<[string, string | null, string | null]>);
vi.mock("../../ui/rangeFocus", async (importOriginal) => {
  const real = await importOriginal<typeof import("../../ui/rangeFocus")>();
  return {
    ...real,
    RangeSpan: (props: { from: string | null; to: string | null }) => {
      declared.push(["span", props.from, props.to]);
      return real.RangeSpan(props);
    },
    useDeclareRangeFocus: (day: string | null) => {
      declared.push(["focus", day, day]);
      real.useDeclareRangeFocus(day);
    },
  };
});

beforeEach(() => {
  declared.length = 0;
});
afterEach(cleanup);

const CODE = "KOBO-001";
const TZ = "Africa/Addis_Ababa";
const SITE = {
  site_id: CODE,
  display_name: "Kobo",
  site_type: "MINIGRID",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: TZ,
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };
const CAPS = [
  { id: "service", display_name: "Service" },
  { id: "fuel", display_name: "Fuel" },
  { id: "renewable", display_name: "Renewable" },
  { id: "backup", display_name: "Backup" },
];

/** `[local 12:00, +1 h)` of a Site-local date at UTC+3, as the server's `hour_link`. */
const hourLink = (day: string) =>
  `/sites/${CODE}/performance/fuel?from=${encodeURIComponent(`${day}T09:00:00Z`)}&to=${encodeURIComponent(`${day}T10:00:00Z`)}`;

function day(local_day: string, over: Partial<FuelRangeDay> = {}): FuelRangeDay {
  return {
    local_day,
    stored: true,
    hours_expected: 24,
    hours_assessed: 24,
    hours_pending: 0,
    hours_missing: 0,
    status_counts: { SUPPORTED: 24, LIMITED: 0, UNKNOWN: 0 },
    limitations: [],
    expected_use_l: { low: 10, high: 12 },
    hours_with_use: 6,
    state: "ASSESSED",
    partial: false,
    hour_link: hourLink(local_day),
    ...over,
  };
}

const NULLS = {
  hours_expected: null,
  hours_assessed: null,
  hours_pending: null,
  hours_missing: null,
  status_counts: null,
  limitations: null,
  expected_use_l: null,
  hours_with_use: null,
};

function rangeRead(): FuelRangeRead {
  return {
    schema_version: "site-fuel-range-1",
    site: { site_code: CODE, site_name: "Kobo", timezone: TZ },
    window: { from: "2026-11-01T00:00:00.000000Z", to: "2026-11-05T00:00:00.000000Z", known_at: null },
    days: [
      day("2026-11-01"),
      day("2026-11-02", { hours_assessed: 20, hours_missing: 4, expected_use_l: { low: 8, high: 9.5 }, partial: true }),
      day("2026-11-03", { ...NULLS, stored: false, state: "STILL_PROCESSING" }),
      day("2026-11-04", { ...NULLS, stored: true, state: "NO_DATA" }),
    ],
    totals: { days_counted: 2, days_requested: 4, partial: true, expected_use_l: { low: 18, high: 21.5 } },
  };
}

const unavailable = { status: "unavailable" as const, message: null };

function hourRead(): FuelRead {
  return {
    schema_version: "w4-02.mini.v1",
    domain: "fuel",
    site: { code: CODE, timezone: TZ },
    window: { from: "2026-11-01T09:00:00Z", to: "2026-11-01T10:00:00Z", known_at: null, bounds: "[from,to)" },
    currentness: { state: "CURRENT", job_state: "SETTLED", windows: [] },
    source_provenance: null,
    status: "LIMITED",
    coverage: null,
    cards: null,
    rows: [],
    limitations: [],
    basis: null,
    links: { dispatch: null, evidence: null, financials: null, actions: null },
  } as FuelRead;
}

function renderApp(path: string, range: MiniRead<FuelRangeRead> = { status: "loaded", value: rangeRead() }) {
  const client: MiniDepthClient = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: vi.fn(() => Promise.resolve(unavailable)),
    getService: vi.fn(() => Promise.resolve(unavailable)),
    getFuel: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: hourRead() })),
    getBackup: vi.fn(() => Promise.resolve(unavailable)),
    getFuelRange: vi.fn(() => Promise.resolve(range)),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDepth={client} />
    </MemoryRouter>,
  );
  return client;
}

const RANGE = `/sites/${CODE}/performance/fuel?from=2026-11-01T00:00:00Z&to=2026-11-05T00:00:00Z&known_at=2026-11-06T00:00:00Z`;
const text = (selector: string) => document.querySelector(selector)?.textContent ?? null;
const row = (d: string) => document.querySelector(`[data-mini-range-day="${d}"]`) as HTMLElement;
/** Declarations with a day: what the date-range bar was told. */
const madeDeclarations = () => declared.filter(([, from, to]) => from !== null && to !== null);

describe("SR-10c: Fuel over the whole range", () => {
  it("a shared range reads the fuel range once over its UTC-midnight window, never the hour read, and declares nothing", async () => {
    const client = renderApp(RANGE);
    await settledScreen();
    await screen.findByText("Days in the range");
    expect(client.getFuelRange).toHaveBeenCalledTimes(1);
    expect(client.getFuelRange).toHaveBeenCalledWith(CODE, {
      from: "2026-11-01T00:00:00Z",
      to: "2026-11-05T00:00:00Z",
      known_at: "2026-11-06T00:00:00Z",
    });
    expect(client.getFuel).not.toHaveBeenCalled();
    expect(madeDeclarations()).toEqual([]);
    expect(document.querySelector(".shared-range__tag")?.textContent).toMatch(/^All pages/);
  });

  it("modelled-days line, per-day band, hours, states, spanned rows, residual never summed and the 12:00 hour link", async () => {
    renderApp(RANGE);
    await settledScreen();
    await screen.findByText("Days in the range");
    expect(text("[data-mini-range-line]")).toBe("Fuel use modelled on 2 of 4 days · 3 Nov: still being prepared · 4 Nov: no readings");
    expect(document.querySelector("[data-mini-range-partial]")).not.toBeNull();
    expect(document.querySelector('[data-mock-deviation="R727"]')).not.toBeNull();
    expect(row("2026-11-01").textContent).toContain("10–12 L");
    expect(row("2026-11-01").textContent).toContain("24 of 24 hours assessed");
    expect(row("2026-11-02").textContent).toContain("Assessed · Partial: 4 hours missing");
    // D-SR.51 (3) / D-SR.70: absent and no-readings rows span their words, never "0 of 0 hours".
    expect(row("2026-11-03").querySelector("[data-mini-range-span]")?.textContent).toBe("Still being prepared");
    expect(row("2026-11-04").querySelector("[data-mini-range-span]")?.textContent).toBe("No readings this day");
    expect(document.body.textContent).not.toContain("0 of 0");
    expect(text("[data-mini-range-residual-note]")).toBe("Residual: not available");
    const bars = Array.from(document.querySelectorAll("[data-value-bar-key]")).map((b) => b.getAttribute("data-value-bar-key"));
    expect(bars).toEqual(["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"]);
    const href = row("2026-11-01").querySelector("a")?.getAttribute("href") ?? "";
    expect(href.startsWith(hourLink("2026-11-01"))).toBe(true);
    expect(new URLSearchParams(href.split("?")[1]).get("known_at")).toBe("2026-11-06T00:00:00Z");
  });

  it("the 12:00 hour opens the hour page with Back to the whole range; there the FocusPicker is the only declarer (D-SR.57)", async () => {
    const client = renderApp(RANGE);
    await settledScreen();
    await screen.findByText("Days in the range");
    fireEvent.click(row("2026-11-01").querySelector("a") as HTMLElement);
    await settledScreen();
    const back = await screen.findByRole("link", { name: "Back to the whole range" });
    expect(back.getAttribute("href")).toBe(RANGE);
    expect(client.getFuel).toHaveBeenCalledWith(CODE, {
      from: "2026-11-01T09:00:00Z",
      to: "2026-11-01T10:00:00Z",
      known_at: "2026-11-06T00:00:00Z",
    });
    expect(new Set(madeDeclarations().map(([kind]) => kind))).toEqual(new Set(["focus"]));
    expect(madeDeclarations().every(([, d]) => d === "2026-11-01")).toBe(true);
  });

  it("an hour address opened directly has no way back to a range it never came from", async () => {
    renderApp(`/sites/${CODE}/performance/fuel?from=2026-11-01T09:00:00Z&to=2026-11-01T10:00:00Z`);
    await settledScreen();
    expect(document.querySelector("[data-mini-back-to-range]")).toBeNull();
  });

  it("D-SR.76 Q3/L3: a partial day with no missing hours reads the too-few-readings words; Still unavailable after the retries", async () => {
    const read = rangeRead();
    read.days[1] = { ...read.days[1], hours_missing: 0, partial: true };
    render(
      <MemoryRouter>
        <MiniFuelRangePage read={read} />
      </MemoryRouter>,
    );
    expect(row("2026-11-02").textContent).toContain("Partial: some hours have too few readings");
    cleanup();
    const refused = { status: "refused", httpStatus: 503, code: "SITE_FUEL_RANGE_UNAVAILABLE", message: null };
    const client = { getFuelRange: vi.fn().mockResolvedValue(refused) } as unknown as MiniDepthClient;
    render(
      <MemoryRouter>
        <MiniFuelRange client={client} siteCode={CODE} window={{ from: "a", to: "b", known_at: null }} retryDelays={[0, 0]} />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Still unavailable. Refresh to try again.")).toBeTruthy();
  });

  it("503 SITE_FUEL_RANGE_UNAVAILABLE reads Temporarily unavailable. Retrying…, never as data", async () => {
    const getFuelRange = vi
      .fn()
      .mockResolvedValueOnce({ status: "refused", httpStatus: 503, code: "SITE_FUEL_RANGE_UNAVAILABLE", message: "x" })
      .mockResolvedValueOnce({ status: "loaded", value: rangeRead() });
    render(
      <MemoryRouter>
        <MiniFuelRange client={{ getFuelRange } as unknown as MiniDepthClient} siteCode={CODE} window={{ from: "a", to: "b", known_at: null }} retryDelays={[30]} />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Temporarily unavailable. Retrying…")).toBeTruthy();
    expect(document.querySelector("[data-mini-range-day]")).toBeNull();
    await screen.findByText("Days in the range");
    expect(getFuelRange).toHaveBeenCalledTimes(2);
  });
});
