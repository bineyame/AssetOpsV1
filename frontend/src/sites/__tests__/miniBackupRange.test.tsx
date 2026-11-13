/**
 * SR-11 (rev 10b.1 / 10b.3; D-SR.51, D-SR.57, D-SR.58, D-SR.60, D-SR.70-72): the mini-grid Backup tab over the date
 * range, and its drill-in to the 12:00 hour and back.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { useLayoutEffect } from "react";
import { MemoryRouter, Route, Routes, useLocation, useSearchParams } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { settledScreen } from "../../test/settled";
import { MiniBackup } from "../MiniPerformance";
import { serviceWindowFromParams, type MiniDepthClient } from "../miniDepthClient";
import { BACKUP_DAY_WORDS, BACKUP_NO_READINGS_DAY, BACKUP_RANGE_NOT_APPLICABLE, BACKUP_STILL_PREPARED, rangeSequences } from "../MiniBackupRange";
import { BACK_TO_RANGE, OPEN_NOON_HOUR } from "../SiteRangeParts";
import { RETRYING_COPY } from "../temporarilyUnavailable";
import { createSiteRangeClient, type BackupRangeBody, type BackupRangeDay, type RangeRead, type SiteRangeClient } from "../siteRangeClient";

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
const CODE = "KISIWA-001";
const RANGE = "from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z";
const hourLink = (d: string) => `/sites/${CODE}/performance/backup?from=${d}T09%3A00%3A00Z&to=${d}T10%3A00%3A00Z`;

const seq = (chain_id: string, outage_start: string, result: string, seconds: number | null, target: number | null = 120) => ({
  chain_id,
  outage_start,
  result,
  service_outcome: result === "PASS" ? "RECOVERED" : result === "FAIL" ? "MISSED_TARGET" : "UNKNOWN",
  critical_recovery: { seconds, target_seconds: target },
});

const stored = (d: string, state: string, over: Partial<BackupRangeDay> = {}): BackupRangeDay => ({
  local_day: d,
  stored: true,
  hours_expected: 24,
  hours_assessed: 24,
  hours_pending: 0,
  hours_missing: 0,
  status_counts: { SUPPORTED: 24, LIMITED: 0, UNKNOWN: 0 },
  limitations: [],
  sequences: [],
  sequence_counts: { PASS: 0, FAIL: 0, INCOMPLETE: 0 },
  start_success_count: null,
  slowest_recovery: null,
  state,
  partial: false,
  hour_link: hourLink(d),
  ...over,
});

const absent = (d: string, state: string, isStored = false): BackupRangeDay => ({
  ...stored(d, state),
  stored: isStored,
  hours_expected: null,
  hours_assessed: null,
  hours_pending: null,
  hours_missing: null,
  status_counts: null,
  limitations: null,
  sequences: null,
  sequence_counts: null,
  start_success_count: null,
  slowest_recovery: null,
});

// cX crosses local midnight: on 2 and 3 Nov's rows, counted once in the totals (D-SR.51.4, server-side).
const CX = seq("cX", "2026-11-02T20:50:00Z", "PASS", 90);
const BODY: BackupRangeBody = {
  schema_version: "site-backup-range-1",
  site: { site_code: CODE, site_name: "Kisiwa", timezone: TZ },
  window: { from: "2026-11-02T00:00:00Z", to: "2026-11-09T00:00:00Z", known_at: null },
  days: [
    stored("2026-11-02", "SEQUENCE_FAILED", {
      sequences: [seq("c1", "2026-11-02T08:00:00Z", "FAIL", 300, 150), CX],
      sequence_counts: { PASS: 1, FAIL: 1, INCOMPLETE: 0 },
      start_success_count: 1,
      slowest_recovery: { seconds: 300, target_seconds: 150 },
    }),
    stored("2026-11-03", "SEQUENCES_PASSED", {
      sequences: [CX],
      sequence_counts: { PASS: 1, FAIL: 0, INCOMPLETE: 0 },
      start_success_count: null,
      slowest_recovery: { seconds: 90, target_seconds: 120 },
      partial: true,
      hours_assessed: 20,
      hours_missing: 4,
    }),
    stored("2026-11-04", "NO_SEQUENCE"),
    absent("2026-11-05", "STILL_PROCESSING"),
    absent("2026-11-06", "NO_DATA", true),
    absent("2026-11-07", "NO_DATA"),
    stored("2026-11-08", "SEQUENCE_INCOMPLETE", {
      sequences: [seq("c3", "2026-11-08T06:00:00Z", "INCOMPLETE", null)],
      sequence_counts: { PASS: 0, FAIL: 0, INCOMPLETE: 1 },
    }),
  ],
  totals: {
    days_counted: 4,
    days_requested: 7,
    partial: true,
    sequence_counts: { PASS: 1, FAIL: 1, INCOMPLETE: 1 },
    start_success_count: 1,
  },
};

function rangeStub(answer: RangeRead<BackupRangeBody>): SiteRangeClient & { calls: unknown[][] } {
  const calls: unknown[][] = [];
  const no = () => Promise.resolve({ status: "unavailable" as const, code: null });
  return {
    calls,
    getServiceRange: no,
    getBackupRange: (...args) => {
      calls.push(args);
      return Promise.resolve(answer);
    },
    getClaimLimitRange: no,
  };
}

function hourClient(): MiniDepthClient {
  const no = () => Promise.resolve({ status: "unavailable" as const, message: null });
  return { getCapabilities: vi.fn(no), getRenewable: vi.fn(no), getService: vi.fn(no), getFuel: vi.fn(no), getBackup: vi.fn(no) };
}

function Tab({ client, rangeClient }: { client: MiniDepthClient; rangeClient: SiteRangeClient }) {
  const [params] = useSearchParams();
  return (
    <MiniBackup
      client={client}
      siteCode={CODE}
      timeZone={TZ}
      window={serviceWindowFromParams(params, TZ)}
      pageHref={(search) => `/sites/${CODE}/performance/backup${search}`}
      rangeClient={rangeClient}
    />
  );
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
          path="/sites/:code/performance/backup"
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

const rows = (attr: string) =>
  Array.from(document.querySelectorAll(`[${attr}]`), (tr) => Array.from(tr.querySelectorAll("th, td"), (c) => c.textContent));

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("SR-11 Backup over the range", () => {
  it("one range read; counted days show starts and the slowest recovery; unknown days span in words, never zero", async () => {
    const ranges = rangeStub({ status: "loaded", value: BODY });
    const client = mount(`/sites/${CODE}/performance/backup?${RANGE}`, ranges);
    await settledScreen();
    expect(ranges.calls).toEqual([[CODE, { from: "2026-11-02T00:00:00Z", to: "2026-11-09T00:00:00Z", known_at: null }, expect.any(Function)]]);
    expect(client.getBackup).not.toHaveBeenCalled();
    expect(rows("data-backup-range-day")).toEqual([
      ["2 Nov", "2 backup starts: 1 passed, 1 failed, 0 incomplete", "Slowest recovery 5 min (target 2.5 min)", BACKUP_DAY_WORDS.SEQUENCE_FAILED, OPEN_NOON_HOUR],
      ["3 Nov", "1 backup start: 1 passed, 0 failed, 0 incomplete", "Slowest recovery 1.5 min (target 2 min)", `${BACKUP_DAY_WORDS.SEQUENCES_PASSED} · Partial day: 20 of 24 hours assessed`, OPEN_NOON_HOUR],
      ["4 Nov", "0 backup starts: 0 passed, 0 failed, 0 incomplete", "No timed recovery", "No backup start recorded", OPEN_NOON_HOUR],
      ["5 Nov", BACKUP_STILL_PREPARED, OPEN_NOON_HOUR],
      ["6 Nov", BACKUP_NO_READINGS_DAY, OPEN_NOON_HOUR],
      ["7 Nov", BACKUP_NO_READINGS_DAY, OPEN_NOON_HOUR],
      ["8 Nov", "1 backup start: 0 passed, 0 failed, 1 incomplete", "No timed recovery", BACKUP_DAY_WORDS.SEQUENCE_INCOMPLETE, OPEN_NOON_HOUR],
    ]);
    expect(BACKUP_NO_READINGS_DAY).toBe("No readings this day");
    // Totals are the server's (cX once); the gap days are grouped by reason (D-E5.45, D-SR.70 words).
    expect(document.querySelector("[data-backup-range-summary]")?.textContent).toBe(
      "3 backup starts: 1 passed, 1 failed, 1 incomplete, for 4 of 7 days analysed · 5 Nov: still being prepared · 6, 7 Nov: no readings",
    );
    expect(document.querySelector("[data-backup-range-starts]")?.textContent).toBe("Start successes: 1");
    // Never an outage count (q3 ruling 8).
    expect(document.body.textContent).not.toMatch(/outage/i);
  });

  it("Sequences in this range: each sequence once (cX crosses midnight), in start order, with outcome, recovery and result", async () => {
    mount(`/sites/${CODE}/performance/backup?${RANGE}`, rangeStub({ status: "loaded", value: BODY }));
    await settledScreen();
    expect(rangeSequences(BODY).map((s) => s.chain_id)).toEqual(["c1", "cX", "c3"]);
    expect(rows("data-backup-range-sequence")).toEqual([
      ["2 Nov 11:00", "Missed recovery target", "5 min (target 2.5 min)", "Fail"],
      ["2 Nov 23:50", "Recovered", "1.5 min (target 2 min)", "Pass"],
      ["8 Nov 09:00", "Unknown", "–", "Incomplete"],
    ]);
  });

  it("no counted day: the status line says so and the sequences table is empty in words", async () => {
    const body: BackupRangeBody = {
      ...BODY,
      days: [absent("2026-11-02", "NO_DATA"), absent("2026-11-03", "NOT_EXPECTED")],
      totals: { days_counted: 0, days_requested: 2, partial: true, sequence_counts: { PASS: 0, FAIL: 0, INCOMPLETE: 0 }, start_success_count: null },
    };
    mount(`/sites/${CODE}/performance/backup?${RANGE}`, rangeStub({ status: "loaded", value: body }));
    await settledScreen();
    expect(document.querySelector("[data-backup-range-summary]")?.textContent).toBe(
      "No day in this range has assessed backup starts · 2 Nov: no readings · 3 Nov: before readings began",
    );
    expect(document.querySelector("[data-backup-range-starts]")).toBeNull();
    expect(screen.getByText("No backup start sequence was assessed in this range")).toBeTruthy();
  });

  it("D-SR.57: the range view declares nothing; the hour view declares once; Back returns to the range", async () => {
    const ranges = rangeStub({ status: "loaded", value: BODY });
    const client = mount(`/sites/${CODE}/performance/backup?${RANGE}`, ranges);
    await settledScreen();
    expect(declarers.live).toBe(0);
    fireEvent.click(screen.getAllByRole("link", { name: OPEN_NOON_HOUR })[3]);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(hourLink("2026-11-05"));
    expect(client.getBackup).toHaveBeenCalledWith(CODE, { from: "2026-11-05T09:00:00Z", to: "2026-11-05T10:00:00Z", known_at: null });
    expect(declarers.live).toBe(1);
    const back = screen.getByRole("link", { name: BACK_TO_RANGE });
    expect(back.getAttribute("href")).toBe(`/sites/${CODE}/performance/backup?${RANGE}`);
    fireEvent.click(back);
    await settledScreen();
    expect(document.querySelector('[data-mini-range="backup"]')).not.toBeNull();
    expect(declarers.live).toBe(0);
  });

  it("503 SITE_BACKUP_RANGE_UNAVAILABLE shows Retrying… while it waits to retry", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const urls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        urls.push(String(input));
        return Promise.resolve(new Response(JSON.stringify({ detail: { code: "SITE_BACKUP_RANGE_UNAVAILABLE" } }), { status: 503 }));
      }),
    );
    mount(`/sites/${CODE}/performance/backup?${RANGE}`, createSiteRangeClient("/api/sites", [10_000]));
    expect(await screen.findByText(RETRYING_COPY)).toBeTruthy();
    expect(urls).toEqual([`/api/sites/${CODE}/backup-range?${RANGE}`]);
    vi.useRealTimers();
  });

  it("BACKUP_RANGE_NOT_APPLICABLE is named in words", async () => {
    mount(`/sites/${CODE}/performance/backup?${RANGE}`, rangeStub({ status: "refused", httpStatus: 404, code: "BACKUP_RANGE_NOT_APPLICABLE", message: "x" }));
    await settledScreen();
    expect(screen.getByText(BACKUP_RANGE_NOT_APPLICABLE)).toBeTruthy();
    expect(document.body.textContent).not.toContain("BACKUP_RANGE_NOT_APPLICABLE");
  });
});
