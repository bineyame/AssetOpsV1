/**
 * SR-5b (architect rev 9 §9.4 "Frontend (vitest)"): the mini-grid range Overview and the SiteOverview switch. Whole
 * App in a memory router with the Kobo fixture; the range read is stubbed per case; every other read is the real
 * client against a stubbed fetch.
 */
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import {
  createRangeOverviewClient,
  type RangeDay,
  type RangeOverviewClient,
  type RangeOverviewRead,
  type SiteRangeOverviewBody,
} from "../rangeOverviewClient";
import {
  BEFORE_READINGS,
  CHECKED_NOTHING,
  RANGE_NO_READINGS,
  rangeDayWords,
  rangeStatusLine,
} from "../SiteRangeOverview";
import { BACK_TO_RANGE } from "../SiteOverview";
import { RETRYING_COPY, STILL_UNAVAILABLE_COPY } from "../temporarilyUnavailable";

const SITE = { ...HYBRID_MINI_GRID_SITE, site_id: "KOBO-001" } as SiteDetailReadModel;
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) } as SiteDetailClient;
const RANGE = "from=2026-11-03T00:00:00Z&to=2026-11-10T00:00:00Z"; // 3-9 Nov
const FROM = "2026-11-03T00:00:00Z";
const TO = "2026-11-10T00:00:00Z";

const day = (d: string, state: RangeDay["state"], over: Partial<RangeDay> = {}): RangeDay => ({
  day: d,
  state,
  finding_count: state === "FINDINGS" ? 2 : state === "CLEAR" ? 0 : null,
  retired_finding_count: state === "FINDINGS" || state === "CLEAR" ? 0 : null,
  money: null,
  money_state: state === "FINDINGS" || state === "CLEAR" ? "NO_ELIGIBLE_LINES" : "WITHHELD",
  accepted_readings: null,
  ...over,
});

const DAYS: RangeDay[] = [
  day("2026-11-03", "NOT_EXPECTED"),
  day("2026-11-04", "NO_READINGS"),
  day("2026-11-05", "FINDINGS", { money: { low: "12.5", high: "14", currency: "USD" }, money_state: "SUMMED" }),
  day("2026-11-06", "CLEAR"),
  day("2026-11-07", "CLEAR", { retired_finding_count: 1 }),
  day("2026-11-08", "READINGS_CONFLICT"),
  day("2026-11-09", "STILL_PROCESSING"),
];

function body(over: Partial<SiteRangeOverviewBody> = {}): SiteRangeOverviewBody {
  return {
    schema_version: "site-range-overview-1",
    site: { site_code: "KOBO-001", site_name: "Kobo", site_type: "MINIGRID", timezone: "Africa/Kampala" },
    window: { from: FROM, to: TO, known_at: "2026-11-10T12:00:00Z", basis: "CURRENT" },
    status: "PARTIAL",
    coverage: {
      state: "PARTIAL",
      days: {
        requested: 7,
        checked: 3,
        gaps: [
          { day: "2026-11-04", state: "UNASSESSED", reason: "NO_READINGS" },
          { day: "2026-11-08", state: "UNASSESSED", reason: "READINGS_CONFLICT" },
        ],
      },
    },
    money: {
      card: { key: "OPERATING_COST", state: "SITE_OWNED", display_value: "$12.50–$14.00", currency: "USD", detail: "Kobo fuel", basis_text: "", tone: "amber" },
      partial: {
        site_id: "s",
        site_code: "KOBO-001",
        site_name: "Kobo",
        state: "SUMMED",
        amount: { low: "12.5", high: "14", currency: "USD" },
        line_count: 1,
        analysed_days: 3,
        requested_days: 7,
        gaps: [
          { day: "2026-11-04", state: "UNASSESSED", reason: "NO_READINGS" },
          { day: "2026-11-08", state: "UNASSESSED", reason: "READINGS_CONFLICT" },
        ],
      },
      quantity: { low: "10", high: "12", unit: "L" },
    },
    findings: { count: 2, confirmed: 1, not_confirmed: 1, awaiting_verification: 0 },
    actions: { open: 1, awaiting_verification: 0, verified_resolution_count: 0 },
    dispatch: { days_requested: 7, days_analysed: 3, days_with_findings: 1, days_with_retired_findings: 1, accepted_readings: null },
    days: DAYS,
    links: { findings: "/sites/KOBO-001/findings", day: "/sites/KOBO-001?day={day}" },
    ...over,
  };
}

let urls: string[] = [];
let calls: { code: string; from: string; to: string; known_at?: string | null }[] = [];

beforeEach(() => {
  urls = [];
  calls = [];
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
  vi.useRealTimers();
});

function stubClient(read: RangeOverviewRead | ((onRetrying?: () => void | boolean) => Promise<RangeOverviewRead>)): RangeOverviewClient {
  return {
    getRangeOverview: (code, query, onRetrying) => {
      calls.push({ code, ...query });
      return typeof read === "function" ? read(onRetrying) : Promise.resolve(read);
    },
  };
}

async function open(path: string, rangeOverview: RangeOverviewClient) {
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDetail={DETAIL} rangeOverview={rangeOverview} />
    </MemoryRouter>,
  );
  await settledScreen();
  return view;
}

const query = (href: string | null) => new URL(href ?? "", "http://x").searchParams;

describe("SR-5b the range view", () => {
  it("a range without a day reads range-overview with the range and no one-day board", async () => {
    await open(`/sites/KOBO-001?${RANGE}`, stubClient({ status: "loaded", value: body() }));
    expect(calls).toEqual([{ code: "KOBO-001", from: FROM, to: TO, known_at: null }]);
    expect(urls.filter((u) => u.includes("/overview?") || u.includes("/outcome-board"))).toEqual([]);
    expect(urls).toContain(`/api/sites/KOBO-001/finding-index?domain=mini-grid-dispatch&from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&limit=5`);
    // The bar keeps "All pages": the range view declares nothing.
    const tag = screen.getByRole("button", { name: /^Date range for every page:/ }).querySelector(".shared-range__tag");
    expect(tag?.textContent).toBe("All pages");
  });

  it("shows the status line, the four tiles and the partial money label", async () => {
    await open(`/sites/KOBO-001?${RANGE}`, stubClient({ status: "loaded", value: body() }));
    expect(document.querySelector("[data-range-status-line]")?.textContent).toBe(
      "Incomplete days · 3 of 7 days analysed · 4 Nov: no readings · 8 Nov: conflicting readings",
    );
    const tile = (name: string) => document.querySelector(`[data-range-tile="${name}"]`) as HTMLElement;
    expect(within(tile("money")).getByText("$12.50–$14.00")).toBeTruthy();
    expect(tile("money").textContent).toContain(
      "$12.50–$14.00 for 3 of 7 days analysed · 4 Nov: no readings · 8 Nov: conflicting readings · 10–12 L at stake",
    );
    expect(tile("findings").textContent).toContain("Confirmed 1 · Not yet confirmed 1");
    expect(tile("actions").textContent).toContain("Awaiting verification 0");
    expect(tile("days").textContent).toContain("3 of 7");
    expect(tile("days").textContent).toContain("1 day with a finding no longer supported");
  });

  it("words every day state, links each day keeping the range, and labels each strip cell", async () => {
    await open(`/sites/KOBO-001?${RANGE}`, stubClient({ status: "loaded", value: body() }));
    const words = Array.from(document.querySelectorAll("[data-range-day-words]")).map((n) => n.textContent);
    expect(words).toEqual([
      BEFORE_READINGS,
      "No readings received for this day",
      "2 findings",
      CHECKED_NOTHING,
      "Checked: no current findings · 1 finding no longer supported",
      "Readings for this day conflict (duplicate or overlapping reports), so it can't be analysed",
      "Still processing",
    ]);
    const open5 = document.querySelector('[data-range-open-day="2026-11-05"]');
    expect(open5?.textContent).toBe("Open day");
    const href = open5?.getAttribute("href") ?? "";
    expect(href.startsWith("/sites/KOBO-001?")).toBe(true);
    expect(query(href).get("day")).toBe("2026-11-05");
    expect(query(href).get("from")).toBe(FROM);
    expect(query(href).get("to")).toBe(TO);
    expect(document.querySelector('[data-range-day-money="SUMMED"]')?.textContent).toBe("$12.50–$14.00");
    const cells = Array.from(document.querySelectorAll("[data-range-strip-day]"));
    expect(cells).toHaveLength(7);
    expect(cells[2].getAttribute("aria-label")).toBe("5 Nov: 2 findings");
    expect(cells[0].getAttribute("aria-label")).toBe(`3 Nov: ${BEFORE_READINGS}`);
    expect(query(cells[2].getAttribute("href")).get("day")).toBe("2026-11-05");
    expect(cells[2].tagName).toBe("A"); // keyboard focusable
  });

  it("D-SR.56: a NOT_EXPECTED day with readings shows the server note", () => {
    expect(rangeDayWords(day("2026-11-03", "NOT_EXPECTED", { note: "Readings began late this day · not counted" }))).toBe(
      "Readings began late this day · not counted",
    );
    expect(rangeDayWords(day("2026-11-03", "NOT_EXPECTED"))).toBe(BEFORE_READINGS);
    expect(rangeDayWords(day("2026-11-03", "NOT_ANALYSED"))).toBe("Not analysed yet");
    expect(rangeDayWords(day("2026-11-03", "NOT_ENOUGH_READINGS"))).toBe("Not enough readings received to analyse this day");
    expect(rangeDayWords(day("2026-11-03", "FINDINGS", { finding_count: 1, retired_finding_count: 2 }))).toBe(
      "1 finding · 2 findings no longer supported",
    );
  });

  it("no readings in the whole range: the status line says so, the tiles show –, the days are still listed", async () => {
    const empty = body({ days: DAYS.map((d) => day(d.day, "NO_READINGS")), status: "PARTIAL" });
    expect(rangeStatusLine(empty)).toBe(RANGE_NO_READINGS);
    await open(`/sites/KOBO-001?${RANGE}`, stubClient({ status: "loaded", value: empty }));
    expect(document.querySelector("[data-range-status-line]")?.textContent).toBe(RANGE_NO_READINGS);
    for (const name of ["money", "findings", "actions", "days"]) {
      expect(document.querySelector(`[data-range-tile="${name}"] .v69-metric__value`)?.textContent).toBe("–");
    }
    expect(document.querySelectorAll("[data-range-day]")).toHaveLength(7);
  });

  it("503 unavailable reads as \"Temporarily unavailable. Retrying…\", never as data", async () => {
    await open(
      `/sites/KOBO-001?${RANGE}`,
      stubClient((onRetrying) => {
        onRetrying?.();
        return new Promise<RangeOverviewRead>(() => undefined);
      }),
    );
    expect(await screen.findByText(RETRYING_COPY)).toBeTruthy();
    expect(document.querySelector("[data-range-tiles]")).toBeNull();
  });

  it("after the retries the page says it is still unavailable", async () => {
    await open(`/sites/KOBO-001?${RANGE}`, stubClient({ status: "refused", httpStatus: 503, code: "TEMPORARILY_UNAVAILABLE" }));
    expect(screen.getByText(STILL_UNAVAILABLE_COPY)).toBeTruthy();
    expect(document.querySelector("[data-range-tiles]")).toBeNull();
  });

  it("a 404 keeps the one-day page (a Site the range read does not know)", async () => {
    await open(`/sites/KOBO-001?${RANGE}`, stubClient({ status: "refused", httpStatus: 404, code: "SITE_NOT_FOUND" }));
    expect(urls).toContain("/api/sites/KOBO-001/overview?date=2026-11-09");
  });
});

describe("SR-5b the drill-in", () => {
  it("day= reads the one-day board and links back to the whole range", async () => {
    await open(`/sites/KOBO-001?${RANGE}&day=2026-11-05`, stubClient({ status: "loaded", value: body() }));
    expect(calls).toEqual([]);
    expect(urls).toContain("/api/sites/KOBO-001/overview?date=2026-11-05");
    const back = screen.getByRole("link", { name: `← ${BACK_TO_RANGE}` });
    const href = back.getAttribute("href") ?? "";
    expect(href.split("?")[0]).toBe("/sites/KOBO-001");
    expect(query(href).get("day")).toBeNull();
    expect(query(href).get("from")).toBe(FROM);
    expect(query(href).get("to")).toBe(TO);
  });
});

describe("SR-5b the range client", () => {
  it("retries a 503 SITE_RANGE_OVERVIEW_UNAVAILABLE and reports it as temporarily unavailable", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: { code: "SITE_RANGE_OVERVIEW_UNAVAILABLE" } }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const retries: number[] = [];
    const pending = createRangeOverviewClient().getRangeOverview("KOBO-001", { from: FROM, to: TO }, () => {
      retries.push(1);
    });
    await vi.runAllTimersAsync();
    expect(await pending).toEqual({ status: "refused", httpStatus: 503, code: "TEMPORARILY_UNAVAILABLE" });
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(retries).toHaveLength(3);
    expect(fetchMock.mock.calls[0]).toEqual([
      `/api/sites/KOBO-001/range-overview?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`,
      { headers: { Accept: "application/json" } },
    ]);
  });
});
