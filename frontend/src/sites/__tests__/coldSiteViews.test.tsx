import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { ColdAssessmentClient, ColdEnvelope, ColdRead, ColdTemperatureRead } from "../coldAssessmentClient";
import type {
  ColdAnalysisRead,
  ColdAssumptionsRead,
  ColdEvidenceRead,
  ColdFinancialsRead,
  ColdOverviewRead,
  ColdSiteClient,
} from "../coldSiteClient";
import { coldUiHref, COLD_SITE_UNAVAILABLE, NO_COLD_ASSESSMENT, SOURCE_FORBIDDEN, eatTime } from "../coldSiteViews";
import { coldSiteRoutes } from "../../shell/coldSiteRoutes";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

/*
 * W2-04 commit 4: the five cold Site routes (`.agent/W2-04-build-spec.md` "v69 panel contract and UI" and the
 * "Commit-4 copy ledger") keep their exact v69 panels in the stocked, empty (200 UNKNOWN), refused (403) and
 * unavailable (503) states, with the ledger's in-panel copy; a planted panel is rejected on every route.
 */

afterEach(cleanup);

const FROM = "2026-10-06T16:00:00.000000Z";
const TO = "2026-10-06T17:05:00.000000Z";
const KNOWN = "2026-10-06T17:06:00.000000Z";
const Q = `?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const API = "/api/sites/COLD-001/cold";
const EXC_FINDING = id(901);
const START_FINDING = id(902);
const HEX = "a".repeat(64);

function envelope(state = "CURRENT", selected = true): ColdEnvelope {
  return {
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN },
    currentness: {
      state,
      watermark: { decided_at: KNOWN, assessment_revision_ids: selected ? [id(51), id(52)] : [] },
      latest_relevant_evidence_at: selected ? TO : null,
      pending_since: null,
    },
    source_provenance: { classification: selected ? "REGISTERED_SIMULATION" : null, source_ids: [], evidence_ids: selected ? [id(11)] : [], basis_sha256: selected ? HEX : null },
    limitations: [],
  };
}
const dated = { as_of: KNOWN, limitation: null };
// W2-F 1a backend claim limitations (cold_site_reads.py COOLING_LIMITATION / PRODUCT_LIMITATION), verbatim.
const COOLING_LIMITATION = "Ordered compressor running after the interruption and a later in-band chamber reading are not established by this assessment.";
const PRODUCT_LIMITATION = "Product identity, stock value and a reviewed response rule are not declared.";

const STOCKED_OVERVIEW: ColdOverviewRead = {
  ...envelope(),
  status: { state: "OBSERVED_EXCURSION", claim_level: "BOUNDED", ...dated },
  objective: { text: "Keep the chamber between 2–4°C through power, cooling and operating disturbances.", policy_low_deg_c: "2", policy_high_deg_c: "4", room_asset_id: id(3), ...dated },
  temperature_summary: { latest_deg_c: "4.6", latest_at: TO, coverage: { known_points: 13, expected_points: 13, ratio: "1" }, episode_count: 1, claim_level: "BOUNDED", ...dated },
  backup_summary: { attempts: 1, observed_success: 0, observed_failure: 1, unknown: 0, latest_chain_id: "corr-1", ...dated },
  causal_strip: [
    { step: "GRID", state: "OBSERVED", at: "2026-10-06T16:11:00Z", evidence_id: id(11), ...dated },
    { step: "START_RESULT", state: "OBSERVED", at: "2026-10-06T16:11:10Z", evidence_id: id(12), ...dated },
    { step: "TRANSFER", state: "MISSING", at: null, evidence_id: null, ...dated },
  ],
  findings: { count: 2, items: [{ finding_id: EXC_FINDING, revision_id: id(911), title: "Chamber above policy", claim_level: "BOUNDED", link: `${API}/findings/${EXC_FINDING}${Q}` }], ...dated },
  needs_attention: [
    { code: "COLD_START_FAILURE", text: "Automatic generator start failed in the accepted record", link: `${API}/findings/${START_FINDING}${Q}`, ...dated },
    { code: "COLD_TRANSFER_UNKNOWN", text: "Transfer-switch position was not observed", link: `${API}/backup-chain${Q}`, ...dated },
  ],
  cooling: { state: "LIMITED", text: "Cooling recovery is not established by the selected start chain.", ...dated },
  maintenance: { state: "NOT_RECORDED", text: "No maintenance work record is available for this window", record_id: null, link: null, as_of: KNOWN, limitation: "No accepted maintenance work record is in the W2-04 read contract." },
  consequence_summary: { state: "UNPRICED", quantity: { low: "50", high: null, unit: "degC_min" }, amount: { low: null, high: null, currency: null }, overlap_group: "g1", ...dated },
  links: {
    temperature: `${API}/temperature${Q}`,
    backup: `${API}/backup-chain${Q}`,
    findings: `${API}/findings${Q}`,
    evidence: `${API}/evidence${Q}`,
    analysis: `${API}/evidence/analysis${Q}`,
    financials: `${API}/financials${Q}`,
  },
};

const cap = (claim: string, state: string, required: string[], missing: string[] = []) => ({
  claim,
  state,
  required_roles: required,
  missing_roles: missing,
  coverage: { known_points: 13, expected_points: 13, ratio: "1" },
  ...dated,
});
const source = (n: number, role: string, contact: string, count: number) => ({
  id: id(n),
  role,
  contact,
  contact_at: contact === "RECENT" ? TO : null,
  fact_age: count > 0 ? 60 : null,
  accepted_count: count,
  last_accepted_at: count > 0 ? "2026-10-06T17:04:00Z" : null,
  quality: { good_count: count, other_count: 0 },
  as_of: KNOWN,
  limitation: contact === "UNKNOWN" ? "No gateway diagnostic was available by the window end and evidence cutoff." : null,
});
const STOCKED_EVIDENCE: ColdEvidenceRead = {
  ...envelope(),
  capabilities: [
    cap("TEMPERATURE_POINT", "SUPPORTED", ["chamber_temperature"]),
    cap("EXCURSION_BOUNDS", "SUPPORTED", ["chamber_temperature", "cold_policy_low", "cold_policy_high"]),
    cap("BACKUP_START_RESULT", "SUPPORTED", ["backup_start_event"]),
    cap("TRANSFER_POSITION", "UNAVAILABLE", ["transfer_result"], ["transfer_result"]),
    { ...cap("COOLING_RESPONSE", "LIMITED", ["compressor_state", "chamber_temperature"], ["compressor_state"]), limitation: COOLING_LIMITATION },
    { ...cap("PRODUCT_EXPOSURE", "UNAVAILABLE", ["chamber_temperature", "cold_policy_low", "cold_policy_high"]), limitation: PRODUCT_LIMITATION },
  ],
  sources: [source(21, "chamber_temperature", "RECENT", 13), source(22, "backup_start_event", "UNKNOWN", 2), source(23, "grid_power_event", "NEVER", 1)],
  links: { analysis: `${API}/evidence/analysis${Q}`, foundation: `${API}/foundation?at=${encodeURIComponent(TO)}`, temperature: `${API}/temperature${Q}`, backup: `${API}/backup-chain${Q}` },
  selected_excursion_present: true,
};

const STOCKED_ANALYSIS: ColdAnalysisRead = {
  ...envelope(),
  accepted_records: {
    items: [
      {
        evidence_id: id(11),
        kind: "MEASUREMENT",
        source_time: "2026-10-06T16:19:00Z",
        received_at: "2026-10-06T16:19:02Z",
        quality: "GOOD",
        role: "chamber_temperature",
        exclusion: null,
        source_id: id(21),
        envelope_sha256: HEX,
        assessment_revision_id: id(51),
        value_display: "4.6",
        unit: "degC",
        sent_at: null,
        record_target_state: "UNAVAILABLE",
        link: null,
        as_of: "2026-10-06T16:19:02Z",
        limitation: "Analysis view not available for this cold record",
      },
    ],
    next_cursor: null,
    total_count: 1,
  },
  claim_rules: [
    {
      rule_id: "cold-excursion/1",
      requirement: "Accepted chamber readings, the selected temperature policy and enough coverage to bound an excursion.",
      observed_roles: ["chamber_temperature", "cold_policy_low", "cold_policy_high"],
      missing_roles: [],
      coverage: { known_points: 13, expected_points: 13, ratio: "1" },
      result: "OBSERVED_EXCURSION",
      ...dated,
    },
  ],
  links: { evidence: `${API}/evidence${Q}`, findings: `${API}/findings${Q}` },
};

const STOCKED_FINANCIALS: ColdFinancialsRead = {
  ...envelope(),
  consequences: [
    {
      id: id(71),
      kind: "PRODUCT_EXPOSURE",
      state: "UNPRICED",
      quantity_bounds: { low: "50", high: null },
      quantity_unit: "degC_min",
      amount_bounds: { low: null, high: null },
      currency: null,
      reason: "Thermal exposure is recorded, but no approved product valuation is available.",
      overlap_group: "g1",
      exact_basis: {
        finding_revision_id: id(911),
        episode_revision_id: id(61),
        assessment_revision_id: id(51),
        evidence_ids: [id(11)],
        source_gate_sha256: HEX,
        assumption_revision_ids: [],
        consequence_basis_sha256: HEX,
      },
      as_of: KNOWN,
      limitation: "The excursion has no recorded end, so its total exposure has no upper bound.",
    },
  ],
  not_included: [
    { code: "STOCK_VALUE_UNDECLARED", text: "Stock quantity and unit value have not been declared for this chamber.", ...dated },
    { code: "SPOILAGE_UNPROVED", text: "Chamber temperature alone does not establish spoilage or stock loss.", ...dated },
  ],
  links: { assumptions: `${API}/financial-assumptions${Q}`, findings: `${API}/findings${Q}`, evidence: `${API}/evidence${Q}` },
};

const assumptions = (selected: boolean): ColdAssumptionsRead => ({
  ...envelope(selected ? "CURRENT" : "UNKNOWN", selected),
  items: [],
  missing_keys: ["cold_stock_quantity", "cold_stock_unit_value", "cold_exposure_rule"],
  publication_state: "NOT_SUPPORTED_IN_W2",
  currency_state: "UNDECLARED",
  links: { financials: `${API}/financials${Q}` },
});

const EMPTY_ENV = envelope("UNKNOWN", false);
const EMPTY_OVERVIEW: ColdOverviewRead = {
  ...STOCKED_OVERVIEW,
  ...EMPTY_ENV,
  status: { state: "UNKNOWN", claim_level: null, ...dated },
  objective: { text: "Chamber temperature objective not declared for this window", policy_low_deg_c: null, policy_high_deg_c: null, room_asset_id: null, ...dated },
  temperature_summary: { latest_deg_c: null, latest_at: null, coverage: { known_points: null, expected_points: null, ratio: null }, episode_count: 0, claim_level: null, ...dated },
  backup_summary: { attempts: 0, observed_success: 0, observed_failure: 0, unknown: 0, latest_chain_id: null, ...dated },
  causal_strip: [],
  findings: { count: 0, items: [], ...dated },
  needs_attention: [],
  cooling: { state: "UNAVAILABLE", text: "Cooling response was not assessed", ...dated },
  consequence_summary: { state: "UNKNOWN", quantity: { low: null, high: null, unit: null }, amount: { low: null, high: null, currency: null }, overlap_group: null, ...dated },
};
const EMPTY_EVIDENCE: ColdEvidenceRead = { ...STOCKED_EVIDENCE, ...EMPTY_ENV, capabilities: [], sources: [], selected_excursion_present: false };
const EMPTY_ANALYSIS: ColdAnalysisRead = { ...STOCKED_ANALYSIS, ...EMPTY_ENV, accepted_records: { items: [], next_cursor: null, total_count: 0 }, claim_rules: [] };
const EMPTY_FINANCIALS: ColdFinancialsRead = { ...STOCKED_FINANCIALS, ...EMPTY_ENV, consequences: [], not_included: [] };

const point = (minute: number, v: string) => ({ at: `2026-10-06T16:${String(minute).padStart(2, "0")}:00Z`, value: v, quality: "GOOD", evidence_id: id(100 + minute) });
const TEMPERATURE = (selected: boolean): ColdTemperatureRead => ({
  ...envelope(selected ? "CURRENT" : "UNKNOWN", selected),
  policy: selected ? { low_deg_c: "2", high_deg_c: "4", return_hysteresis_deg_c: "0.5", min_excursion_min: 10, probe_asset_id: id(4), room_asset_id: id(3) } : null,
  points: selected ? [point(0, "3.1"), point(5, "3.6"), point(10, "4.4"), point(15, "4.6")] : [],
  coverage: selected ? { known_points: 4, expected_points: 4, ratio: "1" } : { known_points: null, expected_points: null, ratio: null },
  gaps: [],
  excursions: [],
  excluded: [],
});

const ok = <T,>(v: T): ColdRead<T> => ({ status: "loaded", value: v });
const FORBIDDEN = { status: "refused", httpStatus: 403, code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: "Not for this caller." } as const;
const DOWN = { status: "refused", httpStatus: 503, code: "COLD_READ_UNAVAILABLE", message: "store down" } as const;

interface Reads {
  overview: ColdRead<ColdOverviewRead>;
  evidence: ColdRead<ColdEvidenceRead>;
  analysis: ColdRead<ColdAnalysisRead>;
  financials: ColdRead<ColdFinancialsRead>;
  assumptions: ColdRead<ColdAssumptionsRead>;
  temperature: ColdRead<ColdTemperatureRead>;
}
const STOCKED: Reads = {
  overview: ok(STOCKED_OVERVIEW),
  evidence: ok(STOCKED_EVIDENCE),
  analysis: ok(STOCKED_ANALYSIS),
  financials: ok(STOCKED_FINANCIALS),
  assumptions: ok(assumptions(true)),
  temperature: ok(TEMPERATURE(true)),
};
const EMPTY: Reads = {
  overview: ok(EMPTY_OVERVIEW),
  evidence: ok(EMPTY_EVIDENCE),
  analysis: ok(EMPTY_ANALYSIS),
  financials: ok(EMPTY_FINANCIALS),
  assumptions: ok(assumptions(false)),
  temperature: ok(TEMPERATURE(false)),
};
const all = (r: ColdRead<never>): Reads => ({ overview: r, evidence: r, analysis: r, financials: r, assumptions: r, temperature: r });

const SITE = {
  site_id: "COLD-001",
  display_name: "Kobo vaccine cold store",
  site_type: "COLDCHAIN",
  location: { country: "Ethiopia", locality: "Kobo" },
  timezone: "Africa/Addis_Ababa",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

function renderCold(path: string, reads: Reads) {
  const coldSite: ColdSiteClient = {
    getOverview: vi.fn(() => Promise.resolve(reads.overview)),
    getEvidence: vi.fn(() => Promise.resolve(reads.evidence)),
    getAnalysis: vi.fn(() => Promise.resolve(reads.analysis)),
    getFinancials: vi.fn(() => Promise.resolve(reads.financials)),
    getAssumptions: vi.fn(() => Promise.resolve(reads.assumptions)),
  };
  const coldAssessment: ColdAssessmentClient = {
    getTemperature: vi.fn(() => Promise.resolve(reads.temperature)),
    getBackupChain: vi.fn(() => Promise.resolve(DOWN)),
    listFindings: vi.fn(() =>
      Promise.resolve(
        reads.financials.status === "loaded" && reads.financials.value.consequences.length > 0
          ? ok({
              ...envelope(),
              items: [
                { finding_id: EXC_FINDING, kind: "EXCURSION", revision_id: id(911), title: "Chamber above policy", claim_level: "BOUNDED" },
                { finding_id: START_FINDING, kind: "START_RESPONSE", revision_id: id(912), title: "Automatic start failed", claim_level: "OBSERVED" },
              ],
              next_cursor: null,
            } as never)
          : ok({ ...EMPTY_ENV, items: [], next_cursor: null } as never),
      ),
    ),
    getFinding: vi.fn(() => Promise.resolve(DOWN)),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldSite={coldSite} coldAssessment={coldAssessment} />
    </MemoryRouter>,
  );
  return { coldSite, coldAssessment };
}

const ROUTES = [
  ["cold", `/sites/COLD-001${Q}`],
  ["cold-evidence", `/sites/COLD-001/evidence${Q}`],
  ["cold-evidence-analysis", `/sites/COLD-001/evidence${Q}&view=analysis`],
  ["cold-financials", `/sites/COLD-001/financials${Q}`],
  ["cold-assumptions", `/sites/COLD-001/financials/assumptions${Q}`],
] as const;
const PANELS: Record<string, string[]> = {
  cold: ["What happened · power → cooling → product conditions", "Chamber temperature", "Needs attention", "Bounded money consequence", "Next step"],
  "cold-evidence": ["What we can conclude now", "Data sources · data quality, not equipment condition", "Most useful next evidence"],
  "cold-evidence-analysis": ["Accepted records behind the conclusions", "How a claim limit is set"],
  "cold-financials": ["What happened → what it means in money", "Assumptions in use", "Not included"],
  "cold-assumptions": ["Financial assumptions"],
};
// The binding copy ledger (spec "Commit-4 copy ledger" and its copy-source closure) fixes these "claim" sentences
// verbatim; "claim" is on the W1 list, so exactly these ledger strings are exempt and nothing else.
const LEDGER_CLAIM = new RegExp(
  "^(" +
    [
      "Selected records support this claim for the covered window\.",
      "Selected records support only part of this claim\.",
      "This claim is not established from the selected records\.",
      "Nothing required for this claim",
      "Coverage or claim basis incomplete",
      "Claim effect not assessed",
      "Claim limit not assessed",
      "Record-level detail and claim limits are on",
      "How a claim limit is set",
      // Run-7 ruled copy for the closed claim panel and its one disclosure.
      "Each claim needs accepted readings and enough coverage for the selected window\.",
      "Claim details",
    ].join("|") +
    ")",
);
const main = () => document.querySelector("main") as HTMLElement;
const text = (el: Element) => (el.textContent ?? "").replace(/\s+/g, " ");

describe("W2-04: cold Site routes keep the v69 panel structure", () => {
  it.each(ROUTES)("stocked: %s", async (screenId, path) => {
    renderCold(path, STOCKED);
    await settledScreen();
    expect(main().getAttribute("data-cold-view")).toBe(screenId);
    expectV69Panels(screenId);
    expectPlantedPanelRejected(screenId);
    // Run-7: cold-assumptions has the mock's one panel and notice and no status strip.
    expect(document.querySelectorAll(".status-strip")).toHaveLength(screenId === "cold-assumptions" ? 0 : 1);
    for (const panel of Array.from(main().querySelectorAll("section.panel"))) {
      expect(panel.querySelectorAll("details").length).toBeLessThanOrEqual(1);
    }
    const result = scanProductVocabulary(main(), screenId, { set: "w1" });
    expect(result.scanned).toBeGreaterThan(3);
    expect(describeViolations(result.violations.filter((v) => !LEDGER_CLAIM.test(v.text.trim())))).toBe("");
    // No raw enum or backend code reaches the screen.
    expect(text(main())).not.toMatch(/\b[A-Z]{2,}_[A-Z_]{2,}\b/);
  });

  it.each(ROUTES)("empty window (UNKNOWN 200): %s keeps every slot with the ledger's empty copy", async (screenId, path) => {
    renderCold(path, EMPTY);
    await settledScreen();
    expectV69Panels(screenId);
    const body = text(main());
    if (screenId === "cold") {
      for (const t of PANELS.cold.slice(0, 3)) expect(text(panelTitled(t))).toContain(NO_COLD_ASSESSMENT);
      expect(text(panelTitled("Next step"))).toContain("No recorded next step");
      expect(text(panelTitled("Bounded money consequence"))).toContain("No product exposure consequence assessed");
    } else if (screenId === "cold-evidence") {
      for (const t of PANELS["cold-evidence"]) expect(text(panelTitled(t))).toContain(NO_COLD_ASSESSMENT);
    } else if (screenId === "cold-evidence-analysis") {
      expect(text(panelTitled("Accepted records behind the conclusions"))).toContain("No accepted records for this window");
      expect(text(panelTitled("How a claim limit is set"))).toContain("Claim limit not assessed");
    } else {
      expect(body).toContain("No assumption in use");
      expect(body).toContain("Cold stock and exposure assumptions have not been declared");
    }
    expect(body).not.toMatch(/\bUSD\b|\$|Healthy|Online/);
  });

  it.each(ROUTES)("refused source disclosure (403): %s keeps every panel with the statement and no IDs", async (screenId, path) => {
    renderCold(path, all(FORBIDDEN as never));
    await settledScreen();
    expectV69Panels(screenId);
    const affected = screenId === "cold-financials" ? ["What happened → what it means in money", "Assumptions in use", "Not included"] : PANELS[screenId];
    for (const t of affected) expect(text(panelTitled(t))).toContain(SOURCE_FORBIDDEN);
    expect(text(main())).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-/);
  });

  it.each(ROUTES)("unavailable (503): %s keeps every panel with the statement and one retry", async (screenId, path) => {
    const { coldSite } = renderCold(path, all(DOWN as never));
    await settledScreen();
    expectV69Panels(screenId);
    for (const t of PANELS[screenId]) expect(text(panelTitled(t))).toContain(COLD_SITE_UNAVAILABLE);
    const retries = screen.getAllByRole("button", { name: "Retry" });
    expect(retries.length).toBeGreaterThanOrEqual(1);
    const calls = Object.values(coldSite).reduce((n, f) => n + (f as ReturnType<typeof vi.fn>).mock.calls.length, 0);
    fireEvent.click(retries[0]);
    await settledScreen();
    expect(Object.values(coldSite).reduce((n, f) => n + (f as ReturnType<typeof vi.fn>).mock.calls.length, 0)).toBeGreaterThan(calls);
  });
});

describe("W2-04: Run-7 date bar", () => {
  it.each(ROUTES)("stocked: %s shows the selected window and cutoff in the date-bar slot, never in the status strip", async (_screenId, path) => {
    renderCold(path, STOCKED);
    await settledScreen();
    const bars = document.querySelectorAll("[data-cold-date-bar]");
    expect(bars).toHaveLength(1);
    expect(text(bars[0])).toContain("Selected window 6 Oct 2026 16:00–17:05 UTC");
    expect(text(bars[0])).toContain("Selected evidence through 6 Oct 17:06 UTC");
    for (const strip of Array.from(document.querySelectorAll(".status-strip"))) {
      expect(text(strip)).not.toContain("Selected evidence through");
      expect(text(strip)).not.toContain("16:00–17:05");
    }
    // The date bar sits before panel 1 and after the tab rows.
    const firstPanel = document.querySelector("main section.panel")!;
    expect(bars[0].compareDocumentPosition(firstPanel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    for (const nav of Array.from(document.querySelectorAll("main nav"))) {
      expect(nav.compareDocumentPosition(bars[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
  });

  it("cold-assumptions gets no status strip", async () => {
    renderCold(ROUTES[4][1], STOCKED);
    await settledScreen();
    expect(document.querySelector(".status-strip")).toBeNull();
  });
});

describe("W2-04: Run-7 Evidence status chip", () => {
  const withCaps = (states: Record<string, string>): Reads => ({
    ...STOCKED,
    evidence: ok({ ...STOCKED_EVIDENCE, capabilities: STOCKED_EVIDENCE.capabilities.map((c) => ({ ...c, state: states[c.claim] ?? "SUPPORTED" })) }),
  });
  it.each([
    ["three Full rows and one Limited row (excursion replay)", { TRANSFER_POSITION: "UNAVAILABLE" }, "Evidence limited", "3 full · 1 limited · 0 none", "Limited"],
    ["any Contradictory row wins over Limited", { TRANSFER_POSITION: "UNAVAILABLE", COOLING_RESPONSE: "CONTRADICTORY" }, "Evidence contradictory", "2 full · 1 limited · 0 none · 1 contradictory", "Contradictory"],
    ["a None row without Limited is unknown", { COOLING_RESPONSE: "UNAVAILABLE" }, "Evidence unknown", "3 full · 0 limited · 1 none", "Unknown"],
    ["all four rows Full", {}, "Evidence supported", "4 full · 0 limited · 0 none", "Supported"],
  ])("%s", async (_name, states, chip, counts, card) => {
    renderCold(ROUTES[1][1], withCaps(states));
    await settledScreen();
    const strip = text(document.querySelector(".status-strip")!);
    expect(strip).toContain(chip);
    expect(strip).toContain(`4 capabilities · ${counts} · no single score`);
    cleanup();
    renderCold(ROUTES[0][1], withCaps(states));
    await settledScreen();
    expect(text(document.querySelector('[data-cold-card="evidence"]')!)).toContain(card);
  });
});

describe("W2-04: cold Overview", () => {
  it("renders the ledger's strip, five cards and the selected panels with window-preserving links", async () => {
    renderCold(ROUTES[0][1], STOCKED);
    await settledScreen();
    const strip = text(document.querySelector(".status-strip")!);
    expect(strip).toContain("Degraded");
    expect(strip).toContain("Confidence: Bounded");
    expect(strip).toContain("Potential product exposure");
    expect(strip).not.toContain("Selected evidence through");
    expect(document.querySelector("[data-cold-objective]")?.textContent).toBe(STOCKED_OVERVIEW.objective.text);
    expect(Array.from(document.querySelectorAll("[data-cold-card]")).map((c) => c.getAttribute("data-cold-card"))).toEqual([
      "temperature",
      "backup",
      "cooling",
      "maintenance",
      "evidence",
    ]);
    expect(text(document.querySelector('[data-cold-card="cooling"]')!)).toContain("Recovery comparison not assessed");
    expect(text(document.querySelector('[data-cold-card="cooling"]')!)).not.toContain("Not available yet");
    expect(text(document.querySelector('[data-cold-card="maintenance"]')!)).toContain("Not recorded");
    const happened = panelTitled(PANELS.cold[0]);
    expect(happened.querySelectorAll("[data-timeline-event]")).toHaveLength(3);
    expect(text(happened)).toContain("No accepted transfer to backup report for this chain");
    expect(text(happened)).toContain("No incident recorded");
    const attention = panelTitled("Needs attention");
    expect(Array.from(attention.querySelectorAll("[data-attention-item]")).map((n) => n.getAttribute("data-attention-item"))).toEqual([
      "COLD_START_FAILURE",
      "COLD_TRANSFER_UNKNOWN",
    ]);
    expect(attention.querySelector('[data-attention-link="COLD_START_FAILURE"]')?.getAttribute("href")).toBe(`/sites/COLD-001/findings/${EXC_FINDING.replace("901", "902")}${Q}`);
    expect(attention.querySelector('[data-attention-link="COLD_TRANSFER_UNKNOWN"]')?.getAttribute("href")).toBe(`/sites/COLD-001/performance/backup${Q}`);
    expect(text(panelTitled("Bounded money consequence"))).toContain("Not priced");
    expect(text(panelTitled("Next step"))).toContain("Automatic generator start failed in the accepted record");
    // Run-7 link and card copy.
    expect(panelTitled("Next step").querySelector("h3")?.textContent).toBe("Automatic generator start failed in the accepted record");
    expect(panelTitled("Next step").querySelector("a")?.textContent).toBe("Open Finding →");
    expect(attention.querySelector('[data-attention-link="COLD_START_FAILURE"]')?.textContent).toBe("Open Finding →");
    expect(attention.querySelector('[data-attention-link="COLD_TRANSFER_UNKNOWN"]')?.textContent).toBe("Performance › Backup →");
    expect(text(document.querySelector('[data-cold-card="temperature"]')!)).toContain("1 excursion · latest 4.6 °C · policy 2–4 °C · coverage 13 / 13 readings");
    expect(text(document.querySelector('[data-cold-card="backup"]')!)).toContain("1 start attempt · 0 started · 1 failed");
    expect(Array.from(happened.querySelectorAll("[data-timeline-event]")).map((e) => text(e))[0]).toContain("16:11 UTC");
    expect(panelTitled("Chamber temperature").querySelectorAll("[data-cold-point]").length).toBe(4);
  });

  it("a null attention destination is noninteractive 'No linked page for this item'; Next step takes the first real destination", async () => {
    const o: ColdOverviewRead = {
      ...STOCKED_OVERVIEW,
      needs_attention: [{ ...STOCKED_OVERVIEW.needs_attention[0], link: null }, STOCKED_OVERVIEW.needs_attention[1]],
      temperature_summary: { ...STOCKED_OVERVIEW.temperature_summary, coverage: { known_points: 13, expected_points: null, ratio: null } },
      backup_summary: { ...STOCKED_OVERVIEW.backup_summary, as_of: null },
    };
    renderCold(ROUTES[0][1], { ...STOCKED, overview: ok(o) });
    await settledScreen();
    const noop = panelTitled("Needs attention").querySelector('[data-attention-link="COLD_START_FAILURE"]')!;
    expect(noop.tagName).toBe("SPAN");
    expect(noop.textContent).toBe("No linked page for this item");
    expect(panelTitled("Next step").querySelector("h3")?.textContent).toBe("Transfer-switch position was not observed");
    expect(panelTitled("Next step").querySelector("a")?.textContent).toBe("Performance › Backup →");
    const temp = text(document.querySelector('[data-cold-card="temperature"]')!);
    expect(temp).not.toContain("coverage");
    expect(temp).not.toContain("?");
    expect(text(document.querySelector('[data-cold-card="backup"]')!)).toContain("Backup result not observed");
  });

  it("pending: withholds the money consequence and states the waiting evidence", async () => {
    const pending: ColdOverviewRead = {
      ...STOCKED_OVERVIEW,
      currentness: { ...STOCKED_OVERVIEW.currentness, state: "PENDING_RECOMPUTE" },
      needs_attention: [{ code: "COLD_RECOMPUTE_PENDING", text: "New evidence is waiting to be assessed", link: `${API}/evidence${Q}`, as_of: KNOWN, limitation: "New evidence is waiting to be assessed" }],
      consequence_summary: { ...STOCKED_OVERVIEW.consequence_summary, state: "WITHHELD", limitation: "New evidence is waiting to be assessed" },
    };
    renderCold(ROUTES[0][1], { ...STOCKED, overview: ok(pending) });
    await settledScreen();
    expect(text(document.querySelector(".status-strip")!)).toContain("New evidence is waiting to be assessed");
    const money = text(panelTitled("Bounded money consequence"));
    expect(money).toContain("Money consequence withheld");
    expect(money).not.toContain("Not priced");
    expect(panelTitled("Next step").querySelector("a")?.getAttribute("href")).toBe(`/sites/COLD-001/evidence${Q}`);
    expect(panelTitled("Next step").querySelector("a")?.textContent).toBe("Evidence →");
  });
});

describe("W2-04: cold Evidence, Analysis, Financials and Assumptions", () => {
  it("evidence: four capability rows, six source rows, next evidence and the Foundation link at window end", async () => {
    renderCold(ROUTES[1][1], STOCKED);
    await settledScreen();
    expect(text(document.querySelector(".status-strip")!)).toContain("Evidence limited");
    expect(text(document.querySelector(".status-strip")!)).toContain("4 capabilities · 1 full · 2 limited · 1 none · no single score");
    expect(screen.getByRole("link", { name: "Configuration at window end" }).getAttribute("href")).toBe(`/sites/COLD-001/foundation?at=${encodeURIComponent(TO)}`);
    const rows = Array.from(panelTitled("What we can conclude now").querySelectorAll("[data-capability-row]"));
    expect(rows.map((r) => r.querySelector("th")?.textContent)).toEqual(["Temperature compliance", "Backup response", "Cooling recovery", "Product exposure"]);
    expect(text(rows[0])).toContain("Full");
    expect(text(rows[0])).toContain("Nothing required for this claim");
    expect(text(rows[1])).toContain("Transfer position");
    expect(text(rows[3])).toContain("Thermal exposure does not prove product loss.");
    const sources = Array.from(panelTitled("Data sources · data quality, not equipment condition").querySelectorAll("[data-source-row]"));
    expect(sources.map((r) => r.getAttribute("data-source-row"))).toEqual(["Chamber probe", "Inverter-charger + battery", "Generator controller", "Compressor meter", "Transfer switch", "Loading / door log"]);
    expect(Array.from(sources[0].querySelectorAll("td")).slice(0, 2).map((c) => text(c))).toEqual(["Recent", "Good"]);
    expect(Array.from(panelTitled("Data sources · data quality, not equipment condition").querySelectorAll("thead th")).map((c) => text(c))).toEqual(["Source", "Contact at window end", "Accepted quality", "What it provides", "Affects"]);
    expect(text(sources[2])).toContain("Unknown");
    // Run-7: the Q-R5 limitation moves from the closed cell into the row's Source details.
    expect(text(sources[2])).not.toContain("No gateway diagnostic was available");
    expect(text(sources[4])).toContain("No source-specific record");
    // Run-7 source placement: the inverter/battery row states no declared source; grid reports only in its details.
    expect(Array.from(sources[1].querySelectorAll("th, td")).map((c) => text(c))).toEqual(["Inverter-charger + battery", "Not declared", "No fact", "No inverter or battery feed", "Claim effect not assessed"]);
    expect(text(Array.from(document.querySelectorAll("[data-source-detail]")).find((g) => g.getAttribute("data-source-detail") === "Inverter-charger + battery")!)).toContain("No inverter or battery source declared");
    // Run-8 closed What / Affects labels by mock row (the full mapping stays in Source details).
    const closedCells = sources.map((r) => Array.from(r.querySelectorAll("td")).slice(2).map((c) => text(c)));
    expect(closedCells).toEqual([
      ["Chamber temperature", "Temperature"],
      ["No inverter or battery feed", "Claim effect not assessed"],
      ["Start result", "Backup"],
      ["No accepted report for this role", "Cooling"],
      ["No accepted report for this role", "Backup"],
      ["No accepted report for this role", "Temperature · cooling"],
    ]);
    const sourcesPanel = panelTitled("Data sources · data quality, not equipment condition");
    expect(sourcesPanel.querySelectorAll("[data-cold-contact-checked]")).toHaveLength(1);
    expect(text(sourcesPanel).match(/Contact checked at window end/g)).toHaveLength(1);
    const details = sourcesPanel.querySelectorAll("details");
    expect(details).toHaveLength(1);
    expect((details[0] as HTMLDetailsElement).open).toBe(false);
    expect(details[0].querySelector("summary")?.textContent).toBe("Source details");
    // Matched by attribute value (jsdom selector parsing mishandles "+" inside the quoted value).
    const group = (label: string) => text(Array.from(sourcesPanel.querySelectorAll("[data-source-detail]")).find((g) => g.getAttribute("data-source-detail") === label)!);
    expect(group("Inverter-charger + battery")).toContain("Other power-path reports");
    expect(group("Inverter-charger + battery")).toContain("Grid meter · Grid power loss and restoration");
    expect(group("Inverter-charger + battery")).toContain(id(23));
    expect(group("Generator controller")).toContain("No gateway diagnostic was available by the window end and evidence cutoff.");
    expect(group("Chamber probe")).toContain("Last accepted fact 6 Oct 17:04 UTC · 60 s old");
    expect(group("Chamber probe")).toContain("Other temperature context");
    expect(group("Transfer switch")).toContain("No source-specific record");
    expect(text(sourcesPanel)).not.toContain("How this was worked out");
    const next = panelTitled("Most useful next evidence");
    expect(text(next)).toContain("Record Transfer position");
    expect(text(next)).toContain("Declare stock identity and value");
    expect(text(main())).not.toMatch(/Online|Offline|Raise action/);
  });

  it("evidence: disagreeing channels in one row get Mixed chips; ambient and manual reports stay out of the chamber row", async () => {
    const generatorState = { ...source(24, "generator_state", "RECENT", 3), quality: { good_count: 0, other_count: 3 } };
    const ambient = { ...source(25, "ambient_temperature", "NEVER", 0) };
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok({ ...STOCKED_EVIDENCE, sources: [...STOCKED_EVIDENCE.sources, generatorState, ambient] }) });
    await settledScreen();
    const sourcesPanel = panelTitled("Data sources · data quality, not equipment condition");
    const row = (label: string) => sourcesPanel.querySelector(`[data-source-row="${label}"]`)!;
    expect(Array.from(row("Generator controller").querySelectorAll("td")).slice(0, 2).map((c) => text(c))).toEqual(["Mixed", "Mixed"]);
    expect(Array.from(row("Chamber probe").querySelectorAll("td")).slice(0, 2).map((c) => text(c))).toEqual(["Recent", "Good"]);
    // R1: a bound role with zero accepted facts never shows a role label as if a report had been accepted.
    expect(text(row("Loading / door log"))).not.toContain("Door/loading context");
    const chamber = text(sourcesPanel.querySelector('[data-source-detail="Chamber probe"]')!);
    expect(chamber).toContain("Ambient probe");
    expect(chamber).toContain("Configured source, no accepted report");
  });

  it("analysis: the accepted record keeps its labelled ID and no guessed record link (retro correction 14)", async () => {
    renderCold(ROUTES[2][1], STOCKED);
    await settledScreen();
    const row = panelTitled("Accepted records behind the conclusions").querySelector(`[data-accepted-record="${id(11)}"]`)!;
    expect(text(row)).toContain("4.6 degC");
    expect(text(row)).toContain(eatTime("2026-10-06T16:19:00Z")!);
    expect(text(row)).toContain(`Record ${id(11)}`);
    expect(text(row)).toContain("No analysis link");
    expect(text(row)).not.toContain("Analysis view not available for this cold record");
    expect(row.querySelector("code")?.getAttribute("aria-label")).toBe(id(11));
    const detail = text(panelTitled("Accepted records behind the conclusions").querySelector(`[data-record-detail="${id(11)}"]`)!);
    expect(detail).toContain(id(11));
    expect(detail).toContain("Target: Unavailable");
    expect(detail).toContain("Analysis view not available for this cold record");
    expect(row.querySelector("a")).toBeNull();
    expect(text(panelTitled("How a claim limit is set"))).toContain("Accepted chamber readings, the selected temperature policy and enough coverage to bound an excursion.");
    const claim = panelTitled("How a claim limit is set");
    expect(text(claim.querySelector("[data-claim-record-pointer]")!)).toBe("Accepted record IDs for this assessment are in Record details.");
    expect(text(claim)).not.toContain("Listed by exact ID");
  });

  it("W3-01 r1 M2: record and claim-rule source follow the selected block, never the pending alias", async () => {
    const sel = { classification: "REGISTERED_SIMULATION", source_ids: [], evidence_ids: [id(11)], basis_sha256: HEX };
    const pend = { classification: "MIXED", source_ids: [], evidence_ids: [id(11), id(12)], basis_sha256: null };
    const withSiblings = (selected: typeof sel | null) => ({ ...STOCKED_ANALYSIS, source_provenance: pend, selected_source_provenance: selected, pending_source_provenance: pend }) as ColdAnalysisRead;
    renderCold(ROUTES[2][1], { ...STOCKED, analysis: ok(withSiblings(sel)) });
    await settledScreen();
    const records = panelTitled("Accepted records behind the conclusions");
    expect(text(records.querySelector(`[data-record-detail="${id(11)}"]`)!)).toContain("Generated test data");
    expect(text(records.querySelector(`[data-record-detail="${id(11)}"]`)!)).not.toContain("Mixed");
    expect(text(panelTitled("How a claim limit is set"))).not.toContain("Mixed");
    cleanup();
    renderCold(ROUTES[2][1], { ...STOCKED, analysis: ok(withSiblings(null)) });
    await settledScreen();
    expect(text(panelTitled("Accepted records behind the conclusions").querySelector(`[data-record-detail="${id(11)}"]`)!)).toContain("Source classification unknown");
  });

  it("analysis: first three records, 'Show all {total}' from the full count, then only 'Show more'; closed Record and Claim details", async () => {
    const base = STOCKED_ANALYSIS.accepted_records.items[0];
    const items = [11, 12, 13, 14, 15].map((n, i) => ({ ...base, evidence_id: id(n), source_time: `2026-10-06T16:${19 + i}:00Z`, sent_at: "2026-10-06T16:19:01Z" }));
    const analysis = { ...STOCKED_ANALYSIS, accepted_records: { items, next_cursor: "c1", total_count: 12 } };
    renderCold(ROUTES[2][1], { ...STOCKED, analysis: ok(analysis) });
    await settledScreen();
    const records = panelTitled("Accepted records behind the conclusions");
    const visible = () => Array.from(records.querySelectorAll<HTMLElement>("[data-accepted-record]")).filter((r) => !r.hidden);
    expect(visible()).toHaveLength(3);
    // Run-7 time copy: Sent (UTC) and Received (UTC) headers over bare clock values; only Measured (EAT) is East Africa Time.
    const cells = visible()[0].querySelectorAll("td");
    expect(cells[1].textContent).toBe(eatTime("2026-10-06T16:19:00Z"));
    expect(cells[2].textContent).toBe("16:19:01");
    expect(cells[3].textContent).toBe("16:19:02");
    expect(Array.from(records.querySelectorAll("thead th")).map((h) => h.textContent)).toEqual(["Source · reading", "Value", "Measured (EAT)", "Sent (UTC)", "Received (UTC)", "Record"]);
    expect(records.querySelector("[data-cold-more]")).toBeNull();
    const details = records.querySelectorAll("details");
    expect(details).toHaveLength(1);
    expect((details[0] as HTMLDetailsElement).open).toBe(false);
    expect(details[0].querySelector("summary")?.textContent).toBe("Record details");
    expect(Array.from(details[0].querySelectorAll("[data-record-detail]")).map((d) => d.getAttribute("data-record-detail"))).toEqual([id(11), id(12), id(13)]);
    expect(text(details[0])).toContain(`Assessment: ${id(51)}`);
    fireEvent.click(screen.getByRole("button", { name: "Show all 12 accepted records" }));
    expect(visible()).toHaveLength(5);
    expect(records.querySelector("[data-cold-all-records]")).toBeNull();
    expect(Array.from(records.querySelectorAll("button")).map((b) => b.textContent)).toEqual(["Show more accepted records"]);
    expect(records.querySelectorAll("[data-record-detail]")).toHaveLength(5);
    const limit = panelTitled("How a claim limit is set");
    const prose = Array.from(limit.querySelectorAll("[data-claim-prose] p")).map((x) => x.textContent);
    expect(prose).toEqual([
      "Each claim needs accepted readings and enough coverage for the selected window. A missing or conflicting input limits what can be concluded.",
      "Source reporting describes data availability, not equipment condition.",
    ]);
    const claim = limit.querySelectorAll("details");
    expect(claim).toHaveLength(1);
    expect((claim[0] as HTMLDetailsElement).open).toBe(false);
    expect(claim[0].querySelector("summary")?.textContent).toBe("Claim details");
    expect(text(claim[0].querySelector('[data-claim-rule="cold-excursion/1"]')!)).toContain("cold-excursion/1 · Observed excursion");
  });

  it("analysis: no selected assessment says 'Claim limit not assessed' instead of the two sentences", async () => {
    renderCold(ROUTES[2][1], EMPTY);
    await settledScreen();
    const limit = text(panelTitled("How a claim limit is set"));
    expect(limit).toContain("Claim limit not assessed");
    expect(limit).not.toContain("Each claim needs accepted readings");
  });

  it("Run-9: tone classes on mapped cold chips only, and no raw unit token or null sentinel in closed cells", async () => {
    renderCold(ROUTES[1][1], STOCKED);
    await settledScreen();
    const sourceRow = (label: string) => Array.from(document.querySelectorAll("[data-source-row]")).find((r) => r.getAttribute("data-source-row") === label)!;
    const rowChips = (label: string) => Array.from(sourceRow(label).querySelectorAll(".badge")).map((b) => [text(b), b.className]);
    expect(rowChips("Chamber probe")).toEqual([
      ["Recent", "badge badge--neutral cold-tone--green"],
      ["Good", "badge badge--neutral cold-tone--green"],
    ]);
    expect(rowChips("Generator controller")[0]).toEqual(["Unknown", "badge badge--neutral"]);
    expect(rowChips("Compressor meter")).toEqual([["No fact", "badge badge--neutral"]]);
    expect(rowChips("Inverter-charger + battery")[0]).toEqual(["Not declared", "badge badge--neutral cold-tone--amber"]);
    const strip = document.querySelector(".status-strip .badge")!;
    expect([text(strip), strip.className]).toEqual(["Evidence limited", "badge badge--neutral cold-tone--amber"]);
    const caps = Array.from(document.querySelectorAll("[data-capability-row]")).map((r) => [text(r.querySelector(".badge")!), r.querySelector(".badge")!.className]);
    expect(caps).toContainEqual(["Full", "badge badge--neutral cold-tone--green"]);
    expect(caps).toContainEqual(["Limited", "badge badge--neutral cold-tone--amber"]);
    cleanup();
    const states = (state: string) => STOCKED_EVIDENCE.capabilities.map((c) => ({ ...c, state }));
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok({ ...STOCKED_EVIDENCE, capabilities: states("UNAVAILABLE") }) });
    await settledScreen();
    expect(Array.from(document.querySelectorAll("[data-capability-row] .badge")).map((b) => [text(b), b.className])).toContainEqual(["None", "badge badge--neutral"]);
    const unknown = document.querySelector(".status-strip .badge")!;
    expect([text(unknown), unknown.className]).toEqual(["Evidence unknown", "badge badge--neutral"]);
    cleanup();
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok({ ...STOCKED_EVIDENCE, capabilities: states("CONTRADICTORY") }) });
    await settledScreen();
    const red = document.querySelector(".status-strip .badge")!;
    expect([text(red), red.className]).toEqual(["Evidence contradictory", "badge badge--neutral cold-tone--red"]);
  });

  it("Run-9 L2: an accepted non-primary role names itself in closed What", async () => {
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok({ ...STOCKED_EVIDENCE, sources: [source(21, "generator_state", "RECENT", 2)] }) });
    await settledScreen();
    const row = Array.from(document.querySelectorAll("[data-source-row]")).find((r) => r.getAttribute("data-source-row") === "Generator controller")!;
    expect(text(row.querySelectorAll("td")[2])).toBe("Generator state");
  });

  it("Run-9: financial quantity phrase covers both bounds, lower-only and no lower bound; the null link has ruled copy", async () => {
    const withBounds = (low: string | null, high: string | null, revision = id(911)) => ({
      ...STOCKED_FINANCIALS,
      consequences: [{ ...STOCKED_FINANCIALS.consequences[0], quantity_bounds: { low, high }, exact_basis: { ...STOCKED_FINANCIALS.consequences[0].exact_basis, finding_revision_id: revision } }],
    });
    const cases: [string | null, string | null, string][] = [
      ["10", "50", "Consequence basis: 10–50 °C·min"],
      ["50", null, "Consequence basis: at least 50 °C·min; upper bound not established"],
      [null, null, "Consequence basis: Not assessed"],
    ];
    for (const [low, high, phrase] of cases) {
      renderCold(ROUTES[3][1], { ...STOCKED, financials: ok(withBounds(low, high)) });
      await settledScreen();
      const bridge = panelTitled("What happened → what it means in money");
      expect(text(bridge.querySelector("[data-consequence-row=\"PRODUCT_EXPOSURE\"] th")!)).toBe(`Chamber thermal exposure · ${phrase}`);
      expect(text(bridge.querySelector("details")!)).toContain(phrase);
      expect(text(main())).not.toMatch(/degC_min|Unknown bound/);
      cleanup();
    }
    renderCold(ROUTES[3][1], { ...STOCKED, financials: ok(withBounds("10", "50", id(999))) });
    await settledScreen();
    const row = panelTitled("What happened → what it means in money").querySelector("[data-consequence-row=\"PRODUCT_EXPOSURE\"]")!;
    const cell = row.querySelectorAll("td")[4];
    expect(text(cell)).toBe("No linked page for this item");
    expect(cell.querySelector("a")).toBeNull();
    expect(text(main())).not.toContain("Finding link not available");
  });

  it("financials: one exposure row with its exact basis, the backup gap row and no price", async () => {
    renderCold(ROUTES[3][1], STOCKED);
    await settledScreen();
    expect(text(document.querySelector(".status-strip")!)).toContain("1 consequence line");
    const bridge = panelTitled("What happened → what it means in money");
    expect(text(bridge)).toContain("Chamber thermal exposure · Consequence basis: at least 50 °C·min; upper bound not established");
    expect(text(bridge)).toContain("Observed backup start failure");
    // Run-7: one closed 'Basis details' disclosure holds the exact basis; closed cells carry no reason or ID.
    const basis = bridge.querySelectorAll("details");
    expect(basis).toHaveLength(1);
    expect((basis[0] as HTMLDetailsElement).open).toBe(false);
    expect(basis[0].querySelector("summary")?.textContent).toBe("Basis details");
    expect(basis[0].textContent).toContain(id(911));
    expect(basis[0].textContent).toContain("The excursion has no recorded end, so its total exposure has no upper bound.");
    expect(text(basis[0])).toContain("No stored consequence or exact cost basis for this row.");
    const table = bridge.querySelector("table")!;
    expect(text(table)).not.toContain("The excursion has no recorded end");
    expect(text(table)).not.toContain(id(911));
    expect(text(panelTitled("Assumptions in use"))).toContain("Not declared");
    expect(screen.getByRole("link", { name: "Review assumptions" }).getAttribute("href")).toBe(`/sites/COLD-001/financials/assumptions${Q}`);
    expect(text(panelTitled("Not included"))).toContain("Chamber temperature alone does not establish spoilage or stock loss.");
    expect(text(main())).not.toMatch(/\bUSD\b|\$/);
  });

  it("assumptions: three read-only rows, no edit control and no assumption publish", async () => {
    renderCold(ROUTES[4][1], STOCKED);
    await settledScreen();
    const rows = Array.from(panelTitled("Financial assumptions").querySelectorAll("[data-assumption-row]"));
    expect(rows.map((r) => text(r))).toEqual([
      "Stock value in chamberNot declaredPricing product exposure",
      "Product exposure ruleNot declaredTranslating thermal exposure",
      "CurrencyNot declaredDisplaying a priced consequence",
    ]);
    expect(main().querySelector("form, input, select, textarea")).toBeNull();
  });

  it("assumptions: the pending sentence sits on the date bar's second line and no status strip is added", async () => {
    const pending = { ...assumptions(true), currentness: { ...assumptions(true).currentness, state: "PENDING_RECOMPUTE" } } as ColdAssumptionsRead;
    renderCold(ROUTES[4][1], { ...STOCKED, assumptions: ok(pending) });
    await settledScreen();
    const cutoff = main().querySelector(".site-date-bar__cutoff")!;
    expect(text(cutoff)).toMatch(/^Selected evidence through .+ · New evidence is waiting to be assessed$/);
    expect(main().querySelector(".status-strip")).toBeNull();
  });
});

describe("W2-04: link mapping and retro correction 17", () => {
  it("maps each selected API link to its UI route with the exact selection", () => {
    const routes = coldSiteRoutes("COLD-001");
    expect(coldUiHref(`${API}/evidence/analysis${Q}`, routes)).toBe(`/sites/COLD-001/evidence${Q}&view=analysis`);
    expect(coldUiHref(`${API}/financial-assumptions${Q}`, routes)).toBe(`/sites/COLD-001/financials/assumptions${Q}`);
    expect(coldUiHref(`${API}/foundation?at=x`, routes)).toBe("/sites/COLD-001/foundation?at=x");
    expect(coldUiHref(`${API}/unknown`, routes)).toBeNull();
    expect(coldUiHref(null, routes)).toBeNull();
  });

  it("the cold Performance context row reads exactly 'Loading / batch' with 'Not established'", async () => {
    renderCold(`/sites/COLD-001/performance/temperature${Q}`, STOCKED);
    await settledScreen();
    const row = document.querySelector('[data-key-value="loading"]')!;
    expect(row.querySelector("dt")?.textContent).toBe("Loading / batch");
    expect(row.querySelector("dd")?.textContent).toBe("Not established");
  });
});

describe("W2-F 1b: one honest cooling and product rule across the cold screens", () => {
  const capRow = (key: string) => panelTitled("What we can conclude now").querySelector(`[data-capability-row="${key}"]`) as HTMLElement;
  const cells = (key: string) => Array.from(capRow(key).querySelectorAll("th, td")).map((c) => text(c));

  // H1/S1/S2: Evidence's columns, Overview's cooling card and money basis, all from the same selected reads.
  it("w2f_recovery_and_exposure_copy", async () => {
    renderCold(ROUTES[1][1], STOCKED);
    await settledScreen();
    expect(cells("cooling")).toEqual([
      "Cooling recovery",
      "Limited",
      "Selected records support only part of this claim.",
      `Compressor state · ${COOLING_LIMITATION}`,
      "Review evidence",
    ]);
    expect(cells("exposure")).toEqual([
      "Product exposure",
      "None",
      "This claim is not established from the selected records. Thermal exposure does not prove product loss.",
      `${PRODUCT_LIMITATION} · Required basis: Product identity; stock quantity and unit value; currency; reviewed product response rule`,
      "Review financials",
    ]);
    for (const key of ["cooling", "exposure"]) expect(text(capRow(key))).not.toMatch(/Nothing required for this claim|Full/);
    cleanup();
    // An apparent first-step completion still stays Limited; a contradictory chain never reads as complete.
    const evidenceWith = (state: string, limitation: string | null): ColdEvidenceRead => ({
      ...STOCKED_EVIDENCE,
      capabilities: STOCKED_EVIDENCE.capabilities.map((c) => (c.claim === "COOLING_RESPONSE" ? { ...c, state, missing_roles: [], limitation } : c)),
    });
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok(evidenceWith("LIMITED", COOLING_LIMITATION)) });
    await settledScreen();
    expect(cells("cooling").slice(1, 4)).toEqual(["Limited", "Selected records support only part of this claim.", COOLING_LIMITATION]);
    cleanup();
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok(evidenceWith("CONTRADICTORY", null)) });
    await settledScreen();
    expect(cells("cooling").slice(1, 4)).toEqual(["Contradictory", "Selected records contradict one another.", "Coverage or claim basis incomplete"]);
    cleanup();
    renderCold(ROUTES[0][1], STOCKED);
    await settledScreen();
    const cooling = text(document.querySelector('[data-cold-card="cooling"]')!);
    expect(cooling).toContain("Limited");
    expect(cooling).toContain("Cooling recovery is not established by the selected start chain. · Recovery comparison not assessed");
    expect(cooling).not.toMatch(/Supported|Cooling resumed/);
    expect(text(document.querySelector("[data-cold-money-basis]")!)).toBe("Consequence basis: at least 50 °C·min; upper bound not established");
  });

  // S5: the stock prompt follows the selected excursion flag, not the product capability chip (None here).
  it("w2f_stock_prompt_follows_selected_excursion", async () => {
    const pendingPrior: ColdEvidenceRead = { ...STOCKED_EVIDENCE, currentness: { ...STOCKED_EVIDENCE.currentness, state: "PENDING_RECOMPUTE" } };
    const cases: [ColdEvidenceRead, boolean][] = [
      [STOCKED_EVIDENCE, true],
      [pendingPrior, true],
      [{ ...STOCKED_EVIDENCE, selected_excursion_present: false }, false],
    ];
    for (const [evidence, shown] of cases) {
      renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok(evidence) });
      await settledScreen();
      expect(cells("exposure")[1]).toBe("None");
      const next = text(panelTitled("Most useful next evidence"));
      if (shown) expect(next).toContain("Declare stock identity and value");
      else expect(next).not.toContain("Declare stock identity and value");
      cleanup();
    }
    // With no missing role: a selected excursion keeps the prompt; without one the panel says nothing is identified.
    const noGaps = (present: boolean): ColdEvidenceRead => ({
      ...STOCKED_EVIDENCE,
      capabilities: STOCKED_EVIDENCE.capabilities.map((c) => ({ ...c, missing_roles: [] })),
      selected_excursion_present: present,
    });
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok(noGaps(true)) });
    await settledScreen();
    expect(text(panelTitled("Most useful next evidence"))).toContain("Declare stock identity and value");
    expect(text(panelTitled("Most useful next evidence"))).not.toContain("Next evidence not identified");
    cleanup();
    renderCold(ROUTES[1][1], { ...STOCKED, evidence: ok(noGaps(false)) });
    await settledScreen();
    expect(text(panelTitled("Most useful next evidence"))).toContain("Next evidence not identified");
  });

  // S7/S8: Financials names the thermal claim and its consequence basis; Evidence keeps Product exposure at None.
  it("w2f_consequence_bound_is_labelled", async () => {
    renderCold(ROUTES[3][1], STOCKED);
    await settledScreen();
    const card = text(document.querySelector('[data-cold-card="exposure"]')!);
    expect(card).toContain("Chamber thermal exposure");
    expect(card).toContain("Consequence basis: at least 50 °C·min; upper bound not established");
    expect(card).not.toContain("Observed excursion estimate");
    const bridge = panelTitled("What happened → what it means in money");
    expect(text(bridge)).not.toContain("Product exposure");
    const note = text(bridge.querySelector("[data-cold-thermal-basis-note]")!);
    expect(note).toContain("Thermal exposure does not establish product damage or loss.");
    expect(note).toContain("The consequence bound may be wider than the observed excursion estimate.");
    expect(text(bridge.querySelector("details")!)).toContain(id(911));
    cleanup();
    renderCold(ROUTES[1][1], STOCKED);
    await settledScreen();
    expect(cells("exposure").slice(0, 2)).toEqual(["Product exposure", "None"]);
  });

  // M7/N6: one projection, three rows in mock order on both screens; never a multiplied value.
  it("w2f_assumption_rows_match", async () => {
    const base = assumptions(true);
    const declared: ColdAssumptionsRead = {
      ...base,
      currentness: { ...base.currentness, state: "HISTORICAL" },
      items: [
        { key: "cold_stock_quantity", revision_id: id(601), value: "120", unit: "kg", currency: null, valid_from: FROM, valid_to: null, recorded_at: KNOWN, source: "operator", ...dated },
        { key: "cold_stock_unit_value", revision_id: id(602), value: "4.50", unit: null, currency: "ETB", valid_from: FROM, valid_to: null, recorded_at: KNOWN, source: "operator", ...dated },
        { key: "cold_exposure_rule", revision_id: id(603), value: "Discard above 8 °C for 2 h", unit: null, currency: null, valid_from: FROM, valid_to: null, recorded_at: KNOWN, source: "operator", ...dated },
      ],
      missing_keys: [],
      currency_state: "DECLARED",
    };
    const partial: ColdAssumptionsRead = { ...declared, items: declared.items.slice(1), missing_keys: ["cold_stock_quantity"] };
    const expected: [ColdAssumptionsRead, string[]][] = [
      [base, ["Not declared", "Not declared", "Not declared"]],
      [declared, ["120 kg × 4.50 ETB", "Discard above 8 °C for 2 h", "ETB"]],
      [partial, ["Not declared", "Discard above 8 °C for 2 h", "ETB"]],
    ];
    for (const [read, values] of expected) {
      renderCold(ROUTES[4][1], { ...STOCKED, assumptions: ok(read) });
      await settledScreen();
      const rows = Array.from(panelTitled("Financial assumptions").querySelectorAll("[data-assumption-row]"));
      expect(rows.map((r) => text(r.querySelector("th")!))).toEqual(["Stock value in chamber", "Product exposure rule", "Currency"]);
      expect(rows.map((r) => text(r.querySelectorAll("td")[0]))).toEqual(values);
      cleanup();
      renderCold(ROUTES[3][1], { ...STOCKED, assumptions: ok(read) });
      await settledScreen();
      const inUse = panelTitled("Assumptions in use");
      expect(Array.from(inUse.querySelectorAll("dt")).map((d) => text(d))).toEqual(["Stock value in chamber", "Product exposure rule", "Currency"]);
      expect(Array.from(inUse.querySelectorAll("dd")).map((d) => text(d))).toEqual(values);
      expect(text(main())).not.toContain("540");
      cleanup();
    }
    renderCold(ROUTES[3][1], { ...STOCKED, assumptions: DOWN as ColdRead<ColdAssumptionsRead> });
    await settledScreen();
    expect(panelTitled("Assumptions in use").querySelectorAll("dt")).toHaveLength(0);
    expect(panelTitled("Assumptions in use").querySelector("[data-panel-gap]")).not.toBeNull();
  });
});
