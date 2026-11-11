// @vitest-environment jsdom
/**
 * DIESEL-K6b (DIESEL-1-R3m §9m.4): the fuel verdict page at `/sites/{code}/domain-actions/{id}/fuel-verification`:
 * loading, not found, error, and each state (VERIFIED, INEFFECTIVE, INCONCLUSIVE, NOT_JUDGED, NO_PLAN) from fixture
 * wires; the fixed H1 line in every state; no money text; the origin and case links; FUEL_VERDICT routing.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteFuelVerificationFrame } from "../../shell/SiteAnalyticsFrames";
import { routeFor, siteFuelVerificationHref } from "../../shell/operatorSiteRoutes";
import { refOfHref } from "../../test/linkRefs";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { LinkedMemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import {
  createFuelVerificationClient,
  fuelVerificationPath,
  FUEL_UNEXPECTED,
  parseFuelVerification,
  type FuelState,
  type FuelVerification,
  type FuelVerificationClient,
  type FuelVerificationResult,
} from "../fuelVerificationClient";
import { FUEL_LOADING, FUEL_MOCK_DEVIATIONS, FUEL_NOT_FOUND } from "../SiteFuelResidualVerification";

const SITE = "KISIWA-001";
const ACTION = "7f1e0a52-4444-4a1e-9e7d-000000000007";
const FINDING = "7f1e0a52-3333-4a1e-9e7d-000000000005";
const REVISION = "7f1e0a52-3333-4a1e-9e7d-000000000006";
const CASE = "7f1e0a52-5555-4a1e-9e7d-000000000008";
const FIXED =
  "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented.";
const KISIWA = {
  site_id: SITE,
  display_name: "Kisiwa Mini-grid",
  site_type: "MINIGRID",
  timezone: "Africa/Dar_es_Salaam",
  lifecycle_status: "OPERATING",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail = { getSite: async () => ({ status: "loaded", site: KISIWA }) } as unknown as SiteDetailClient;

// The server's strings, copied from `fuel_verification.py` with the demo nights.
const HEADLINE: Record<FuelState, string> = {
  VERIFIED: "Fuel stayed accounted for",
  INEFFECTIVE: "Target not met",
  INCONCLUSIVE: "Could not conclude",
  NOT_JUDGED: "Not judged yet",
  NO_PLAN: "No verification plan yet",
};
const BASELINE_ROW = {
  role: "BASELINE" as const,
  label: "The night of the finding",
  range_text: "45.0 to 60.0 L",
  sensor_text: "Readings all night",
  result_text: "Unexplained fuel found",
  passes: null,
  window_id: "w0",
  revision: 1,
};
const later = (day: string, i: number, result = "Within the margin", passes = true, sensor = "Readings all night") => ({
  role: "LATER" as const,
  label: `${day} (6 pm to noon)`,
  range_text: "-5.0 to 10.0 L",
  sensor_text: sensor,
  result_text: result,
  passes,
  window_id: `w${i}`,
  revision: 1,
});

function wire(state: FuelState, over: Partial<FuelVerification> = {}): FuelVerification {
  const n = state === "NO_PLAN" ? 0 : state === "INCONCLUSIVE" || state === "NOT_JUDGED" ? 2 : 3;
  return {
    action_id: ACTION,
    action_code: "ACT-000003",
    title: "Seal the tank cap and sign the dip log",
    owner_label: "Site lead",
    rule_id: "fuel-residual-within-band-1",
    state,
    headline: HEADLINE[state],
    sentence: null,
    not_judged_text: null,
    fixed_line: FIXED,
    criterion_text: "3 nights with complete readings after the change within the stated margin, with the tank sensor sending readings all night",
    rule_text:
      "Rule fixed before the check: the first 3 nights with complete readings after the change must each stay within the stated margin, with the tank sensor sending readings all night.",
    cards: [
      { label: "Nights with complete readings after the change", value: `${n} of 3`, note: "Chosen by data quality, never by result" },
      { label: "Fuel accounted for", value: n === 0 ? "Not judged yet" : `${n} of ${n} nights`, note: "Within the stated margin" },
      { label: "Tank sensor", value: n === 0 ? "Not judged yet" : `Readings all night on ${n} of ${n} nights`, note: "A gap is more than 60 minutes without a reading" },
      { label: "Final outcome", value: HEADLINE[state], note: "Decided by the rule fixed before the check" },
    ],
    origin: {
      finding_id: FINDING,
      revision_id: REVISION,
      title: "Unexplained fuel overnight",
      night_text: "20 Oct (6 pm to noon)",
      ref: { kind: "FUEL_FINDING", site: SITE, id: FINDING, revision: REVISION },
      href: `/sites/${SITE}/fuel-findings/${FINDING}?revision_id=${REVISION}`,
    },
    nights: [BASELINE_ROW, ...["22 Oct", "23 Oct", "24 Oct"].slice(0, n).map((d, i) => later(d, i + 1))],
    activity:
      state === "NO_PLAN"
        ? null
        : {
            case_code: "WR-000004",
            case_ref: { kind: "CASE", site: SITE, id: CASE },
            case_href: `/maintenance/requests/${CASE}`,
            completed_text: "21 Oct 15:05",
            site_visit_text: "Sealed the cap and signed the dip log",
            note: "Completed work is evidence of activity, not resolution.",
          },
    effective_from: state === "NO_PLAN" ? null : "2026-10-21T12:05:00+00:00",
    plan: state === "NO_PLAN" ? null : { plan_id: "p1", later_candidates: { from: "2026-10-21", to: "2026-11-03" } },
    outcome: ["VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"].includes(state)
      ? { outcome_id: "o1", outcome: state, reasons: ["TARGET_MET"], recorded_at: "2026-10-25T09:00:00+00:00", source_class: "REGISTERED_SIMULATION" }
      : null,
    value: null,
    cost_check: null,
    ...over,
  };
}

const STATES: Record<FuelState, FuelVerification> = {
  VERIFIED: wire("VERIFIED", {
    sentence:
      "On 3 nights with complete readings after the change, the fuel in the tank matched the generator's modelled use and the recorded deliveries within the stated margin, and the tank sensor sent readings all night.",
  }),
  INEFFECTIVE: wire("INEFFECTIVE", {
    sentence: "On the night of 23 Oct, after the change, the tank sensor did not send readings all night.",
    nights: [BASELINE_ROW, later("22 Oct", 1), later("23 Oct", 2, "Sensor gap", false, "No readings for 90 min"), later("24 Oct", 3)],
  }),
  INCONCLUSIVE: wire("INCONCLUSIVE", {
    sentence: "Only 2 of 3 nights with complete readings after the change in the 14 nights allowed, so no verdict is given",
  }),
  NOT_JUDGED: wire("NOT_JUDGED", { not_judged_text: "Not judged yet: only 2 of 3 nights with complete readings after the change" }),
  NO_PLAN: wire("NO_PLAN"),
};

function client(result: FuelVerificationResult | Promise<FuelVerificationResult>): FuelVerificationClient {
  return { read: vi.fn(async () => result) };
}

function renderAt(c: FuelVerificationClient) {
  return render(
    <LinkedMemoryRouter initialEntries={[siteFuelVerificationHref(SITE, ACTION)]}>
      <Routes>
        <Route path="/sites/:siteId/domain-actions/:actionId/fuel-verification" element={<SiteFuelVerificationFrame detail={detail} sitesPath="/sites" client={c} />} />
      </Routes>
    </LinkedMemoryRouter>,
  );
}

const main = () => screen.getByRole("main");

/** The settled screen, then the fuel read's own settled body: the page (`data-fuel-state`) or its alert. */
async function loadedPage() {
  await settledScreen();
  await waitFor(() => expect(document.querySelector("[data-fuel-state], [role='alert']")).not.toBeNull());
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("fuel verdict page", () => {
  it("reads once at its own address and shows the loading line until the read settles", async () => {
    let resolve: (r: FuelVerificationResult) => void = () => {};
    const c = client(new Promise<FuelVerificationResult>((r) => (resolve = r)));
    renderAt(c);
    expect(await screen.findByText(FUEL_LOADING)).toBeTruthy();
    resolve({ status: "loaded", body: STATES.VERIFIED });
    await loadedPage();
    expect(c.read).toHaveBeenCalledWith(SITE, ACTION);
    expect(screen.queryByText(FUEL_LOADING)).toBeNull();
  });

  it("not found state", async () => {
    renderAt(client({ status: "not_found" }));
    await loadedPage();
    expect((await screen.findByRole("alert")).textContent).toBe(FUEL_NOT_FOUND);
    expect(FUEL_NOT_FOUND).toBe("No such Action for this site.");
  });

  it("error state shows the server's message", async () => {
    renderAt(client({ status: "error", message: "Only an Action raised from an unexplained-fuel Finding has a fuel verification plan." }));
    await loadedPage();
    expect((await screen.findByRole("alert")).textContent).toBe(
      "Only an Action raised from an unexplained-fuel Finding has a fuel verification plan.",
    );
  });

  it.each(Object.keys(STATES) as FuelState[])("%s renders its headline, cards and the fixed H1 line, with no money text", async (state) => {
    const body = STATES[state];
    renderAt(client({ status: "loaded", body }));
    await loadedPage();
    const root = main();
    expect(root.querySelector("[data-fuel-state]")?.getAttribute("data-fuel-state")).toBe(state);
    expect(root.querySelector(".v69-statusbar")?.textContent).toContain(`ACT-003 · ${HEADLINE[state]}`);
    expect(root.querySelector("[data-fuel-fixed-line]")?.textContent).toBe(FIXED);
    expect([...root.querySelectorAll("[data-fuel-card] .v69-metric__value")].map((c) => c.textContent)).toEqual(body.cards.map((c) => c.value));
    const line = body.sentence ?? body.not_judged_text;
    if (line !== null) expect(root.querySelector("[data-fuel-line]")?.textContent).toBe(line);
    else expect(root.querySelector("[data-fuel-line]")).toBeNull();
    const rows = root.querySelectorAll("tbody tr");
    expect(rows).toHaveLength(body.nights.length);
    expect([...rows[0].querySelectorAll("th, td")].map((c) => c.textContent)).toEqual([
      "The night of the finding",
      "Before the change",
      "45.0 to 60.0 L",
      "Readings all night",
      "Unexplained fuel found",
    ]);
    const text = root.textContent ?? "";
    expect(text).not.toMatch(/\$|\bprice\b|\b(USD|TZS|KES|EUR)\b/i);
    expect(text).toContain(FUEL_MOCK_DEVIATIONS);
    const scan = scanProductVocabulary(root, "fuel-verdict", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(5);
    expect(scan.violations, describeViolations(scan.violations)).toEqual([]);
  });

  it("INEFFECTIVE names the failing night's sensor gap in the table", async () => {
    renderAt(client({ status: "loaded", body: STATES.INEFFECTIVE }));
    await loadedPage();
    const failing = main().querySelector('[data-fuel-pass="false"]');
    expect([...(failing?.querySelectorAll("th, td") ?? [])].map((c) => c.textContent)).toEqual([
      "23 Oct (6 pm to noon)",
      "Target",
      "-5.0 to 10.0 L",
      "No readings for 90 min",
      "Sensor gap",
    ]);
  });

  it("links the source to the fuel Finding page and the request to its case page", async () => {
    renderAt(client({ status: "loaded", body: STATES.VERIFIED }));
    await loadedPage();
    const source = screen.getByRole("link", { name: "Unexplained fuel overnight" });
    expect(source.getAttribute("href")).toBe(routeFor({ kind: "FUEL_FINDING", site: SITE, id: FINDING, revision: REVISION }));
    expect(source.getAttribute("href")).toBe(STATES.VERIFIED.origin.href);
    const request = screen.getByRole("link", { name: "WR-000004" });
    expect(request.getAttribute("href")).toBe(routeFor({ kind: "CASE", site: SITE, id: CASE }));
    expect(screen.getByText("Completed work is evidence of activity, not resolution.")).toBeTruthy();
  });
});

describe("FUEL_VERDICT ref and the client", () => {
  it("routes a FUEL_VERDICT ref to the verdict page and round-trips through linkRefs", () => {
    const href = routeFor({ kind: "FUEL_VERDICT", site: SITE, id: ACTION });
    expect(href).toBe(`/sites/${SITE}/domain-actions/${ACTION}/fuel-verification`);
    expect(href).toBe(siteFuelVerificationHref(SITE, ACTION));
    expect(refOfHref(href as string)).toEqual({ kind: "FUEL_VERDICT", site: SITE, id: ACTION });
    const finding = `/sites/${SITE}/fuel-findings/${FINDING}?revision_id=${REVISION}`;
    expect(refOfHref(finding)).toEqual({ kind: "FUEL_FINDING", site: SITE, id: FINDING, revision: REVISION });
  });

  it("parses the wire and refuses a value or a cost check (H2)", () => {
    expect(parseFuelVerification(STATES.VERIFIED)?.state).toBe("VERIFIED");
    expect(parseFuelVerification({ ...STATES.VERIFIED, value: { text: "x" } })).toBeNull();
    expect(parseFuelVerification({ ...STATES.VERIFIED, cost_check: {} })).toBeNull();
    expect(parseFuelVerification({ ...STATES.VERIFIED, state: "PENDING" })).toBeNull();
  });

  it("reads the API path and maps 404, a refusal message and a bad shape", async () => {
    expect(fuelVerificationPath("/api/sites", SITE, ACTION)).toBe(`/api/sites/${SITE}/domain-work/actions/${ACTION}/fuel-verification`);
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const c = createFuelVerificationClient("/api/sites");
    fetchMock.mockResolvedValueOnce(new Response("{}", { status: 404 }));
    expect(await c.read(SITE, ACTION)).toEqual({ status: "not_found" });
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ detail: { code: "X", message: "The fuel checks cannot be read." } }), { status: 503 }));
    expect(await c.read(SITE, ACTION)).toEqual({ status: "error", message: "The fuel checks cannot be read." });
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ nope: 1 }), { status: 200 }));
    expect(await c.read(SITE, ACTION)).toEqual({ status: "error", message: FUEL_UNEXPECTED });
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(STATES.NOT_JUDGED), { status: 200 }));
    expect(((await c.read(SITE, ACTION)) as { body: FuelVerification }).body.not_judged_text).toBe(STATES.NOT_JUDGED.not_judged_text);
  });
});
