// @vitest-environment jsdom
/**
 * CH-9b3 (CH9b3-R Q2/Q3/Q5-Q7): the mill verdict page at `/sites/{code}/domain-actions/{id}/verification`: loading,
 * each refusal, and each state (VERIFIED, INEFFECTIVE, INCONCLUSIVE LATER_SHORT / BASELINE_ZERO, NOT_JUDGED, NO_PLAN).
 */
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteMillVerificationFrame } from "../../shell/SiteAnalyticsFrames";
import { siteMillVerificationHref } from "../../shell/operatorSiteRoutes";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import {
  createMillVerificationClient,
  millVerificationPath,
  MILL_UNEXPECTED,
  MILL_UNREACHABLE,
  type MillVerification,
  type MillVerificationClient,
  type MillVerificationResult,
} from "../millVerificationClient";
import { MILL_LOADING, MILL_NOT_FOUND } from "../SiteMillVerification";

const SITE = "KOBO-001";
const ACTION = "5a1c2a7e-0d4b-4c3e-9a51-1b2c3d4e5f61";
const KOBO = {
  site_id: SITE,
  display_name: "Kobo Mini-grid",
  site_type: "MINIGRID",
  timezone: "Africa/Nairobi",
  lifecycle_status: "OPERATING",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail = { getSite: async () => ({ status: "loaded", site: KOBO }) } as unknown as SiteDetailClient;

const VERIFIED: MillVerification = {
  action_id: ACTION,
  action_code: "ACT-000002",
  title: "Run the mill at midday",
  state: "VERIFIED",
  reasons: ["TARGET_MET"],
  sentence: "Midday use rose by at least the declared 10% on fully checked days",
  line: "Midday use before and after the change: 10.00 → 11.50 kWh a day on 3 fully checked days each",
  not_judged_text: null,
  outcome: { outcome_id: "o1", outcome: "VERIFIED", recorded_at: "2026-10-25T09:00:00+00:00" },
  plan: { effective_day: "2026-10-20", baseline_days: ["2026-10-17", "2026-10-18", "2026-10-19"], later_days: ["2026-10-21", "2026-10-22", "2026-10-23"] },
  metrics: [
    { metric_key: "midday_productive_kwh", label: "Midday use", unit: "kWh a day", before: "10.00", after: "11.50", threshold: "11.00", days_before: 3, days_after: 3, state: "PASS" },
  ],
};

function client(result: MillVerificationResult | Promise<MillVerificationResult>): MillVerificationClient {
  return { read: vi.fn(async () => result) };
}

function renderAt(c: MillVerificationClient) {
  return render(
    <MemoryRouter initialEntries={[siteMillVerificationHref(SITE, ACTION)]}>
      <Routes>
        <Route path="/sites/:siteId/domain-actions/:actionId/verification" element={<SiteMillVerificationFrame detail={detail} sitesPath="/sites" client={c} />} />
      </Routes>
    </MemoryRouter>,
  );
}

const main = () => screen.getByRole("main");

/** The settled page carries no forbidden client word (Q8: the stored title is exempt as user-owned). */
function clean() {
  const scan = scanProductVocabulary(main(), "mill-verdict", { set: "w1" });
  expect(scan.scanned).toBeGreaterThan(5);
  expect(scan.violations, describeViolations(scan.violations)).toEqual([]);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("mill verdict page", () => {
  it("reads once at its own address and shows the loading line until the read settles", async () => {
    let resolve: (r: MillVerificationResult) => void = () => {};
    const c = client(new Promise<MillVerificationResult>((r) => (resolve = r)));
    renderAt(c);
    expect(await screen.findByText(MILL_LOADING)).toBeTruthy();
    resolve({ status: "loaded", body: VERIFIED });
    await settledScreen();
    expect(c.read).toHaveBeenCalledWith(SITE, ACTION);
    expect(screen.queryByText(MILL_LOADING)).toBeNull();
  });

  it("VERIFIED: the headline, the SCOPE-1 sentence, the R7 line and the one-row table", async () => {
    renderAt(client({ status: "loaded", body: VERIFIED }));
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("ACT-002 · Run the mill at midday");
    expect(main().querySelector("[data-mill-state]")?.textContent).toBe("Target met");
    expect(screen.getByText(VERIFIED.sentence as string)).toBeTruthy();
    expect(screen.getByText(VERIFIED.line as string)).toBeTruthy();
    const rows = main().querySelectorAll("tbody tr");
    expect(rows).toHaveLength(1);
    expect([...rows[0].querySelectorAll("th, td")].map((c) => c.textContent)).toEqual([
      "Midday use",
      "10.00 kWh a day",
      "11.50 kWh a day",
      "3 of 3, 3 of 3",
      "At least 10% above before: 11.00 kWh a day",
    ]);
    expect(main().querySelector('[data-mock-deviation="R700"]')).not.toBeNull();
    expect(main().textContent).not.toMatch(/cost check|trial hour/i);
    const scan = scanProductVocabulary(main(), "mill-verdict", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(5);
    expect(scan.violations, describeViolations(scan.violations)).toEqual([]);
  });

  it("INEFFECTIVE TARGET_MISS reads 'Target not met' with the before/after line", async () => {
    const body = { ...VERIFIED, state: "INEFFECTIVE" as const, reasons: ["TARGET_MISS"], sentence: null,
      line: "Midday use before and after the change: 10.00 → 10.50 kWh a day on 3 fully checked days each",
      metrics: [{ ...VERIFIED.metrics[0], after: "10.50", state: "FAIL" }] };
    renderAt(client({ status: "loaded", body }));
    await settledScreen();
    expect(main().querySelector("[data-mill-state]")?.textContent).toBe("Target not met");
    expect(screen.getByText(body.line)).toBeTruthy();
    expect(main().querySelector('[data-mill-metric="FAIL"]')).not.toBeNull();
  });

  it("INCONCLUSIVE LATER_SHORT and BASELINE_ZERO read 'Could not conclude' with their own line", async () => {
    const later = "Only 2 of 3 fully checked days after the change in the 14 days allowed, so no verdict is given";
    renderAt(client({ status: "loaded", body: { ...VERIFIED, state: "INCONCLUSIVE", reasons: ["LATER_SHORT"], sentence: null, line: later,
      metrics: [{ ...VERIFIED.metrics[0], after: null, days_after: 2, state: "UNKNOWN" }] } }));
    await settledScreen();
    expect(main().querySelector("[data-mill-state]")?.textContent).toBe("Could not conclude");
    expect(screen.getByText(later)).toBeTruthy();
    clean();
    expect(screen.getByText("Too few fully checked days")).toBeTruthy();
    cleanup();
    const zero = "No midday use was measured before the change, so a 10% rise cannot be measured";
    renderAt(client({ status: "loaded", body: { ...VERIFIED, state: "INCONCLUSIVE", reasons: ["BASELINE_ZERO"], sentence: zero } }));
    await settledScreen();
    expect(main().querySelector("[data-mill-state]")?.textContent).toBe("Could not conclude");
    expect(screen.getByText(zero)).toBeTruthy();
    clean();
  });

  it("NOT_JUDGED shows the server's not-judged text and no verdict; NO_PLAN says no plan yet", async () => {
    const text = "Not judged yet: only 1 of 3 fully checked days after the change";
    renderAt(client({ status: "loaded", body: { ...VERIFIED, state: "NOT_JUDGED", reasons: [], sentence: null, line: null, not_judged_text: text, outcome: null,
      metrics: [{ ...VERIFIED.metrics[0], after: null, days_after: 1, state: "UNKNOWN" }] } }));
    await settledScreen();
    expect(main().querySelector("[data-mill-state]")?.textContent).toBe("Not judged yet");
    expect(screen.getByText(text)).toBeTruthy();
    expect(main().textContent).not.toContain("Target met");
    clean();
    cleanup();
    renderAt(client({ status: "loaded", body: { ...VERIFIED, state: "NO_PLAN", reasons: [], sentence: null, line: null, outcome: null, plan: null, metrics: [] } }));
    await settledScreen();
    expect(main().querySelector("[data-mill-state]")?.textContent).toBe("No verification plan yet");
    expect(main().querySelector("table")).toBeNull();
  });

  it("a 404 says the Action was not found and an error shows its sentence, never a verdict", async () => {
    renderAt(client({ status: "not_found" }));
    await settledScreen();
    expect(screen.getByRole("alert").textContent).toBe(MILL_NOT_FOUND);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Action");
    cleanup();
    renderAt(client({ status: "error", message: MILL_UNREACHABLE }));
    await settledScreen();
    expect(screen.getByRole("alert").textContent).toBe(MILL_UNREACHABLE);
    expect(main().querySelector("[data-mill-state]")).toBeNull();
  });
});

describe("mill verdict client", () => {
  it("reads the one GET and names every refusal", async () => {
    expect(millVerificationPath("/api/sites", SITE, ACTION)).toBe(`/api/sites/${SITE}/domain-work/actions/${ACTION}/verification`);
    const respond = (status: number, body: unknown) => vi.fn(async () => new Response(JSON.stringify(body), { status }));
    vi.stubGlobal("fetch", respond(200, VERIFIED));
    expect(await createMillVerificationClient().read(SITE, ACTION)).toEqual({ status: "loaded", body: VERIFIED });
    vi.stubGlobal("fetch", respond(404, { detail: {} }));
    expect((await createMillVerificationClient().read(SITE, ACTION)).status).toBe("not_found");
    vi.stubGlobal("fetch", respond(200, { ...VERIFIED, state: "MAYBE" }));
    expect(await createMillVerificationClient().read(SITE, ACTION)).toEqual({ status: "error", message: MILL_UNEXPECTED });
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("offline"); }));
    expect(await createMillVerificationClient().read(SITE, ACTION)).toEqual({ status: "error", message: MILL_UNREACHABLE });
  });
});
