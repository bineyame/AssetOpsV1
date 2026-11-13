/**
 * SR-7a (rev 10 §10.3, rev 10a.2 Q8; D-SR.26, D-SR.45, D-SR.57): the mini-grid Service tab over the date range, and
 * its drill-in to the 12:00 hour and back.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { useLayoutEffect } from "react";
import { MemoryRouter, Route, Routes, useLocation, useParams, useSearchParams } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { settledScreen } from "../../test/settled";
import { MiniBackup, MiniService } from "../MiniPerformance";
import { serviceWindowFromParams, type MiniDepthClient } from "../miniDepthClient";
import { SERVICE_DAY_WORDS, SERVICE_NO_VALUE, SERVICE_RANGE_NOT_APPLICABLE, SERVICE_RANGE_OPEN_A_DAY } from "../MiniServiceRange";
import { BACK_TO_RANGE, OPEN_NOON_HOUR, gapDaysText } from "../SiteRangeParts";
import { RETRYING_COPY } from "../temporarilyUnavailable";
import { createSiteRangeClient, type RangeRead, type ServiceRangeBody, type ServiceRangeDay, type SiteRangeClient } from "../siteRangeClient";

/** D-SR.57: the number of mounted components that declare a span to the date-range bar right now. */
const declarers = vi.hoisted(() => ({ live: 0 }));
vi.mock("../../ui/rangeFocus", async (importActual) => {
  const actual = await importActual<typeof import("../../ui/rangeFocus")>();
  const useCounted = (from: string | null, to: string | null) => {
    useLayoutEffect(() => {
      if (from === null || to === null) return undefined;
      declarers.live += 1;
      return () => {
        declarers.live -= 1;
      };
    }, [from, to]);
    actual.useDeclareRangeSpan(from, to);
  };
  return {
    ...actual,
    useDeclareRangeSpan: useCounted,
    useDeclareRangeFocus: (day: string | null) => useCounted(day, day),
    RangeSpan: ({ from, to }: { from: string | null; to: string | null }) => {
      useCounted(from, to);
      return null;
    },
  };
});

const TZ = "Africa/Nairobi";
const CODE = "KOBO-001";
const RANGE = "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z";
const hourLink = (d: string) => `/sites/${CODE}/performance/service?from=${d}T09%3A00%3A00Z&to=${d}T10%3A00%3A00Z`;

const day = (d: string, state: string, over: Partial<ServiceRangeDay> = {}): ServiceRangeDay => ({
  local_day: d,
  grade: "COMPLETE",
  served_kwh: null,
  unserved_kwh: null,
  demand_kwh: null,
  covered_hours: 24,
  operating_hours: 24,
  state,
  partial: false,
  hour_link: hourLink(d),
  ...over,
});

const BODY: ServiceRangeBody = {
  schema_version: "site-service-range-1",
  site: { site_code: CODE, site_name: "Kobo", timezone: TZ },
  window: { from: "2026-11-02T00:00:00Z", to: "2026-11-09T00:00:00Z", known_at: null },
  days: [
    day("2026-11-02", "SHORTFALL", { served_kwh: "144", unserved_kwh: "12.0", demand_kwh: "156.0" }),
    day("2026-11-03", "SERVED_ALL", { grade: "PARTIAL", served_kwh: "20", unserved_kwh: "0", demand_kwh: "20", covered_hours: 5.5, operating_hours: 8, partial: true }),
    day("2026-11-04", "NO_VALUE"),
    day("2026-11-05", "NO_READINGS", { grade: "NO_DATA", covered_hours: null, operating_hours: null }),
    day("2026-11-06", "STILL_PROCESSING", { grade: "PENDING" }),
    day("2026-11-07", "NOT_ENOUGH_READINGS", { grade: "LOW", served_kwh: null }),
    day("2026-11-08", "NOT_EXPECTED", { grade: "NOT_EXPECTED" }),
  ],
  totals: { served_kwh: "164", unserved_kwh: "12.0", demand_kwh: "176.0", days_counted: 2, days_requested: 7 },
};

function rangeStub(answer: RangeRead<ServiceRangeBody>): SiteRangeClient & { calls: unknown[][] } {
  const calls: unknown[][] = [];
  const no = () => Promise.resolve({ status: "unavailable" as const, code: null });
  return {
    calls,
    getServiceRange: (...args) => {
      calls.push(args);
      return Promise.resolve(answer);
    },
    getBackupRange: no,
    getClaimLimitRange: no,
  };
}

function hourClient(): MiniDepthClient {
  const no = () => Promise.resolve({ status: "unavailable" as const, message: null });
  return { getCapabilities: vi.fn(no), getRenewable: vi.fn(no), getService: vi.fn(no), getFuel: vi.fn(no), getBackup: vi.fn(no) };
}

function Tab({ client, rangeClient }: { client: MiniDepthClient; rangeClient: SiteRangeClient }) {
  const [params] = useSearchParams();
  const { tab } = useParams();
  const props = {
    client,
    siteCode: CODE,
    timeZone: TZ,
    window: serviceWindowFromParams(params, TZ),
    pageHref: (search: string) => `/sites/${CODE}/performance/${tab}${search}`,
    rangeClient,
  };
  return tab === "backup" ? <MiniBackup {...props} /> : <MiniService {...props} />;
}

function Where() {
  const at = useLocation();
  return <output data-testid="where">{`${at.pathname}${at.search}`}</output>;
}

function mount(path: string, rangeClient: SiteRangeClient, client: MiniDepthClient = hourClient()) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/sites/:code/performance/:tab"
          element={
            <>
              <Tab client={client} rangeClient={rangeClient} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
  return client;
}

const rows = () =>
  Array.from(document.querySelectorAll("[data-service-range-day]"), (tr) => Array.from(tr.querySelectorAll("th, td"), (c) => c.textContent));

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("SR-7a Service over the range", () => {
  it("one range read with the address window; counted days show served and not served; every other day spans in words", async () => {
    const ranges = rangeStub({ status: "loaded", value: BODY });
    const client = mount(`/sites/${CODE}/performance/service?${RANGE}`, ranges);
    await settledScreen();
    expect(ranges.calls).toEqual([[CODE, { from: "2026-11-02T00:00:00Z", to: "2026-11-09T00:00:00Z", known_at: null }, expect.any(Function)]]);
    expect(client.getService).not.toHaveBeenCalled();
    expect(rows()).toEqual([
      ["2 Nov", "144 kWh", "12 kWh", "24 h of 24 h", SERVICE_DAY_WORDS.SHORTFALL, OPEN_NOON_HOUR],
      ["3 Nov", "20 kWh", "0 kWh", "5.5 h of 8 h", `${SERVICE_DAY_WORDS.SERVED_ALL} · Partial day: 5.5 h of 8 h covered`, OPEN_NOON_HOUR],
      ["4 Nov", SERVICE_NO_VALUE, OPEN_NOON_HOUR],
      ["5 Nov", "No readings received for this day", OPEN_NOON_HOUR],
      ["6 Nov", "Still being prepared", OPEN_NOON_HOUR],
      ["7 Nov", "Not enough readings received to analyse this day", OPEN_NOON_HOUR],
      ["8 Nov", "Before this Site's readings began", OPEN_NOON_HOUR],
    ]);
    // D-SR.26 words; D-E5.45 label with more than 3 gap days; D-SR.45 J2 the partial day is flagged.
    expect(SERVICE_NO_VALUE).toBe("No critical-load figure for this day");
    expect(document.querySelector("[data-service-range-summary]")?.textContent).toBe(
      "164 kWh critical load served, 12 kWh not served, for 2 of 7 days analysed · 5 days without a usable result",
    );
    expect(document.querySelector("[data-service-partial-days]")?.textContent).toBe("1 day was only partly covered");
    expect(screen.getByText(SERVICE_RANGE_OPEN_A_DAY)).toBeTruthy();
    // No zero is invented for an uncounted day, and no all-load or interruption figure over the range.
    expect(document.querySelector('[data-service-range-day="2026-11-05"]')?.textContent).not.toContain("0 kWh");
    expect(document.body.textContent).not.toMatch(/interruptions seen|delivered load \d/i);
  });

  it("D-SR.57: the range view declares nothing; the hour view declares once (its FocusPicker)", async () => {
    mount(`/sites/${CODE}/performance/service?${RANGE}`, rangeStub({ status: "loaded", value: BODY }));
    await settledScreen();
    expect(declarers.live).toBe(0);
    fireEvent.click(screen.getAllByRole("link", { name: OPEN_NOON_HOUR })[0]);
    await settledScreen();
    expect(document.querySelector("[data-mini-period]")).not.toBeNull();
    expect(declarers.live).toBe(1);
  });

  it("Open the 12:00 hour opens the hour page; Back to the whole range returns to the range it came from", async () => {
    const ranges = rangeStub({ status: "loaded", value: BODY });
    const client = mount(`/sites/${CODE}/performance/service?${RANGE}`, ranges);
    await settledScreen();
    fireEvent.click(screen.getAllByRole("link", { name: OPEN_NOON_HOUR })[0]);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(hourLink("2026-11-02"));
    expect(client.getService).toHaveBeenCalledWith(CODE, { from: "2026-11-02T09:00:00Z", to: "2026-11-02T10:00:00Z", known_at: null });
    const back = screen.getByRole("link", { name: BACK_TO_RANGE });
    expect(back.getAttribute("href")).toBe(`/sites/${CODE}/performance/service?${RANGE}`);
    fireEvent.click(back);
    await settledScreen();
    expect(document.querySelector('[data-mini-range="service"]')).not.toBeNull();
    expect(ranges.calls).toHaveLength(2);
  });

  it("a story hour reached directly goes back to its own day", async () => {
    mount(hourLink("2026-11-02"), rangeStub({ status: "loaded", value: BODY }));
    await settledScreen();
    expect(screen.getByRole("link", { name: BACK_TO_RANGE }).getAttribute("href")).toBe(
      `/sites/${CODE}/performance/service?from=2026-11-02T00%3A00%3A00Z&to=2026-11-03T00%3A00%3A00Z`,
    );
  });

  it("a day= link keeps the hour page and goes back to the range without day", async () => {
    const ranges = rangeStub({ status: "loaded", value: BODY });
    mount(`/sites/${CODE}/performance/service?${RANGE}&day=2026-11-04`, ranges);
    await settledScreen();
    expect(ranges.calls).toEqual([]);
    expect(screen.getByRole("link", { name: BACK_TO_RANGE }).getAttribute("href")).toBe(`/sites/${CODE}/performance/service?${RANGE}`);
  });

  it("503 SITE_SERVICE_RANGE_UNAVAILABLE shows Retrying… while it waits to retry", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const urls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        urls.push(String(input));
        return Promise.resolve(new Response(JSON.stringify({ detail: { code: "SITE_SERVICE_RANGE_UNAVAILABLE" } }), { status: 503 }));
      }),
    );
    mount(`/sites/${CODE}/performance/service?${RANGE}`, createSiteRangeClient("/api/sites", [10_000]));
    expect(await screen.findByText(RETRYING_COPY)).toBeTruthy();
    expect(urls).toEqual([`/api/sites/${CODE}/service-range?${RANGE}`]);
    vi.useRealTimers();
  });

  it("SERVICE_RANGE_NOT_APPLICABLE is named in words", async () => {
    mount(`/sites/${CODE}/performance/service?${RANGE}`, rangeStub({ status: "refused", httpStatus: 404, code: "SERVICE_RANGE_NOT_APPLICABLE", message: "x" }));
    await settledScreen();
    expect(screen.getByText(SERVICE_RANGE_NOT_APPLICABLE)).toBeTruthy();
    expect(document.body.textContent).not.toContain("SERVICE_RANGE_NOT_APPLICABLE");
  });
});

describe("the D-E5.45 day-gap label", () => {
  it("groups days by reason in first-day order; more than 3 gap days are counted", () => {
    expect(gapDaysText([])).toBe("");
    expect(
      gapDaysText([
        { day: "2026-11-03", reason: "no readings" },
        { day: "2026-11-04", reason: "no readings" },
        { day: "2026-11-06", reason: "still being prepared" },
      ]),
    ).toBe(" · 3, 4 Nov: no readings · 6 Nov: still being prepared");
    expect(gapDaysText([{ day: "2026-10-31", reason: "no readings" }, { day: "2026-11-01", reason: "no readings" }])).toBe(" · 31 Oct, 1 Nov: no readings");
    expect(gapDaysText(["1", "2", "3", "4"].map((d) => ({ day: `2026-11-0${d}`, reason: "no readings" })))).toBe(" · 4 days without a usable result");
  });
});
