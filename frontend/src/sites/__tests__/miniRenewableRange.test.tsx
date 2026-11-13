import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { MiniDepthClient, MiniRead, RenewableRangeDay, RenewableRangeRead, RenewableRead } from "../miniDepthClient";
import { MiniRenewableRange } from "../MiniRenewableRange";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";

/*
 * SR-8 page (rev 10 §10.4, D-SR.27/47/48/62/70): the Renewable tab over a shared range reads `renewable-range` once and
 * shows the counted-days line, the average, the per-day bars and the day table in the D-SR.48 words; the one-day page
 * adds the stored figure's line under the headroom card and the D-SR.62 partial label.
 */

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

const link = (day: string) => {
  const lo = new Date(Date.parse(`${day}T00:00:00Z`) - 3 * 3_600_000).toISOString().replace(".000", "");
  const hi = new Date(Date.parse(`${day}T00:00:00Z`) + 21 * 3_600_000).toISOString().replace(".000", "");
  return `/sites/${CODE}/performance/renewable?from=${encodeURIComponent(lo)}&to=${encodeURIComponent(hi)}`;
};

function day(local_day: string, over: Partial<RenewableRangeDay> = {}): RenewableRangeDay {
  return {
    local_day,
    grade: "COMPLETE",
    low_kw: "25",
    high_kw: "31",
    decision: "ELIGIBLE",
    window_hours: 2,
    covered_hours: 12,
    operating_hours: 12,
    state: "COUNTED",
    partial: false,
    link: link(local_day),
    ...over,
  };
}

function rangeRead(): RenewableRangeRead {
  return {
    schema_version: "site-renewable-range-1",
    site: { site_code: CODE, site_name: "Kobo", timezone: TZ },
    window: { from: "2026-11-01T00:00:00.000000Z", to: "2026-11-05T00:00:00.000000Z", known_at: null },
    days: [
      day("2026-11-01"),
      day("2026-11-02", { grade: "PARTIAL", low_kw: "10.5", high_kw: "12", covered_hours: 8, operating_hours: 24, partial: true }),
      day("2026-11-03", { decision: "EXCLUDED", state: "EXCLUDED", low_kw: "50", high_kw: "60" }),
      day("2026-11-04", { grade: "NO_DATA", low_kw: null, high_kw: null, decision: null, window_hours: null, covered_hours: null, operating_hours: null, state: "NO_DATA" }),
    ],
    totals: {
      days_requested: 4,
      days_counted: 2,
      average_low_kw: "17.75",
      average_high_kw: "21.50",
      average_label: "average headroom available in every eligible hour",
      partial: true,
    },
  };
}

const unavailable = { status: "unavailable" as const, message: null };

function renderApp(path: string, range: MiniRead<RenewableRangeRead>[], day?: RenewableRead) {
  const queue = [...range];
  const client: MiniDepthClient = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: vi.fn(() => Promise.resolve(day === undefined ? unavailable : { status: "loaded" as const, value: day })),
    getService: vi.fn(() => Promise.resolve(unavailable)),
    getFuel: vi.fn(() => Promise.resolve(unavailable)),
    getBackup: vi.fn(() => Promise.resolve(unavailable)),
    getRenewableRange: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDepth={client} />
    </MemoryRouter>,
  );
  return client;
}

const text = (selector: string) => document.querySelector(selector)?.textContent ?? null;

describe("SR-8 page: Renewable over the whole range", () => {
  it("a shared range reads the range route once over its UTC-midnight window, with known_at, and never the one-day read", async () => {
    const client = renderApp(
      `/sites/${CODE}/performance/renewable?from=2026-11-01T00:00:00Z&to=2026-11-05T00:00:00Z&known_at=2026-11-06T00:00:00Z`,
      [{ status: "loaded", value: rangeRead() }],
    );
    await settledScreen();
    await screen.findByText("Days in the range");
    expect(client.getRenewableRange).toHaveBeenCalledTimes(1);
    expect(client.getRenewableRange).toHaveBeenCalledWith(CODE, {
      from: "2026-11-01T00:00:00Z",
      to: "2026-11-05T00:00:00Z",
      known_at: "2026-11-06T00:00:00Z",
    });
    expect(client.getRenewable).not.toHaveBeenCalled();
  });

  it("D-SR.48 words: per-day band, the average over counted days, the counted-days line, states and the day link", async () => {
    renderApp(`/sites/${CODE}/performance/renewable?from=2026-11-01T00:00:00Z&to=2026-11-05T00:00:00Z&known_at=2026-11-06T00:00:00Z`, [
      { status: "loaded", value: rangeRead() },
    ]);
    await settledScreen();
    await screen.findByText("Days in the range");
    expect(screen.getByRole("columnheader", { name: "Headroom available in every eligible hour" })).toBeTruthy();
    expect(text("[data-mini-range-average] .v69-metric__label")).toBe("Average headroom available in every eligible hour");
    expect(text("[data-mini-range-average] .v69-metric__value")).toBe("17.75–21.5 kW");
    expect(text("[data-mini-range-line]")).toBe("Headroom counted on 2 of 4 days · 3 Nov: excluded · 4 Nov: no readings");
    expect(document.querySelector("[data-mini-range-partial]")).not.toBeNull();
    expect(document.querySelector('[data-mock-deviation="R726"]')).not.toBeNull();
    const row = (d: string) => document.querySelector(`[data-mini-range-day="${d}"]`) as HTMLElement;
    expect(row("2026-11-01").querySelector("[data-mini-range-band]")?.textContent).toBe("25–31 kW");
    expect(row("2026-11-02").textContent).toContain("Counted · Partial: 16 hours missing");
    expect(row("2026-11-02").textContent).toContain("8 of 24 operating hours covered");
    expect(row("2026-11-03").textContent).toContain("Excluded");
    expect(row("2026-11-03").querySelector("[data-mini-range-band]")?.textContent).toBe("50–60 kW");
    expect(row("2026-11-04").textContent).toContain("No readings this day");
    expect(row("2026-11-04").querySelector("[data-mini-range-band]")?.textContent).toBe("—");
    // The day opens the existing one-day page at the range's cutoff (D-SR.57 L3).
    const href = row("2026-11-01").querySelector("a")?.getAttribute("href") ?? "";
    expect(href.startsWith(link("2026-11-01"))).toBe(true);
    expect(new URLSearchParams(href.split("?")[1]).get("known_at")).toBe("2026-11-06T00:00:00Z");
    // The per-day bars: one per day, the band as text, no figure on a NO_DATA day.
    const bars = Array.from(document.querySelectorAll("[data-value-bar-key]")).map((b) => b.getAttribute("data-value-bar-key"));
    expect(bars).toEqual(["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"]);
    // The range view declares no span of its own (SR-4b's "last 5 days" is gone).
    expect(document.body.textContent).not.toContain("of the range");
  });

  it("503 SITE_RENEWABLE_RANGE_UNAVAILABLE reads Temporarily unavailable. Retrying… and then the range, never as data", async () => {
    const getRenewableRange = vi
      .fn()
      .mockResolvedValueOnce({ status: "refused", httpStatus: 503, code: "SITE_RENEWABLE_RANGE_UNAVAILABLE", message: "x" })
      .mockResolvedValueOnce({ status: "loaded", value: rangeRead() });
    const client = { getRenewableRange } as unknown as MiniDepthClient;
    render(
      <MemoryRouter>
        <MiniRenewableRange client={client} siteCode={CODE} window={{ from: "a", to: "b", known_at: null }} retryDelays={[30]} />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Temporarily unavailable. Retrying…")).toBeTruthy();
    expect(document.querySelector("[data-mini-range-day]")).toBeNull();
    await screen.findByText("Days in the range");
    expect(getRenewableRange).toHaveBeenCalledTimes(2);
  });

  it("after the last retry it says Still unavailable. Refresh to try again.", async () => {
    const refused = { status: "refused", httpStatus: 503, code: "SITE_RENEWABLE_RANGE_UNAVAILABLE", message: null };
    const client = { getRenewableRange: vi.fn().mockResolvedValue(refused) } as unknown as MiniDepthClient;
    render(
      <MemoryRouter>
        <MiniRenewableRange client={client} siteCode={CODE} window={{ from: "a", to: "b", known_at: null }} retryDelays={[0, 0]} />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Still unavailable. Refresh to try again.")).toBeTruthy();
    expect(client.getRenewableRange).toHaveBeenCalledTimes(3);
  });
});

function dayRead(over: { all?: { low: number; high: number } | null; missing?: number }): RenewableRead {
  return {
    schema_version: "w4-02.mini.v1",
    domain: "renewable",
    site: { code: CODE, timezone: TZ },
    window: { from: "2026-10-26T21:00:00Z", to: "2026-10-27T21:00:00Z", known_at: null, bounds: "[from,to)" },
    currentness: { state: "CURRENT", job_state: "SETTLED", windows: [] },
    source_provenance: null,
    selected_source_provenance: null,
    pending_source_provenance: null,
    status: "SUPPORTED",
    coverage: null,
    cards: {
      capability_kw: { low: 41, high: 43 },
      used_kw: { low: 10, high: 12 },
      headroom_kw: { low: 25, high: 33 },
      all_hours_headroom_kw: over.all === undefined ? { low: 25, high: 31 } : over.all,
      eligible_days: 1,
      assessed_days: 1,
    },
    rows: [],
    limitations: [],
    basis: null,
    links: { dispatch: null, evidence: null, financials: null, actions: null },
    missing_hours: over.missing,
  } as RenewableRead;
}

describe("SR-8 page: the one-day Renewable page (D-SR.48, D-SR.62)", () => {
  const STORY_DAY = `/sites/${CODE}/performance/renewable?from=2026-10-26T21:00:00Z&to=2026-10-27T21:00:00Z`;

  it("adds the stored figure under the headroom card in the range words; the card's envelope is the range across eligible hours", async () => {
    const client = renderApp(STORY_DAY, [unavailable], dayRead({ missing: 16 }));
    await settledScreen();
    await screen.findByText("Headroom available in every eligible hour: 25–31 kW");
    expect(client.getRenewableRange).not.toHaveBeenCalled();
    expect(text("[data-mini-headroom-range-label]")).toBe("Range across eligible hours, after retained margin and service checks");
    expect(text("[data-mini-partial-hours]")).toBe("Partial: 16 hours missing");
  });

  it("no partial label without missing hours, and Unknown when the figure is null", async () => {
    renderApp(STORY_DAY, [unavailable], dayRead({ all: null, missing: 0 }));
    await settledScreen();
    await screen.findByText("Headroom available in every eligible hour: Unknown");
    expect(document.querySelector("[data-mini-partial-hours]")).toBeNull();
  });
});
