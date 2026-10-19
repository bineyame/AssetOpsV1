import { cleanup, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  ColdAssessmentClient,
  ColdBackupRead,
  ColdEnvelope,
  ColdFindingDetailRead,
  ColdFindingItem,
  ColdFindingsRead,
  ColdRead,
  ColdTemperatureRead,
} from "../coldAssessmentClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

/*
 * W2-03 commit 5 (`.agent/W2-03-build-spec.md` "Commit 5 - exact v69 slots"): a COLDCHAIN Site's
 * Performance/Temperature, Performance/Backup and cold Finding detail routes render `temperature`,
 * `coldbackup`, `cold-finding` and `cold-finding-excursion` in the exact v69 panel structure (titles from
 * `docs/architecture/v69-rendered-panels.json` at test time) in the stocked, empty (UNKNOWN) and refused
 * states. Fixture values follow the accepted backup-failed replay shape, never the mock's illustrations.
 */

afterEach(cleanup);

const FROM = "2026-10-06T19:00:00.000000Z";
const TO = "2026-10-06T20:05:00.000000Z";
const KNOWN = "2026-10-06T20:06:00.000000Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const EXC_FINDING = id(901);
const START_FINDING = id(902);

function envelope(state = "CURRENT", over: Partial<ColdEnvelope> = {}): ColdEnvelope {
  return {
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN },
    currentness: {
      state,
      watermark: { decided_at: KNOWN, assessment_revision_ids: [id(50)] },
      latest_relevant_evidence_at: "2026-10-06T20:00:00.000000Z",
      pending_since: null,
    },
    source_provenance: { classification: "REGISTERED_SIMULATION", source_ids: ["cold-backup-failed"], evidence_ids: [id(100)], basis_sha256: "a".repeat(64) },
    limitations: [],
    ...over,
  };
}

const at = (minute: number) => {
  const d = new Date(Date.UTC(2026, 9, 6, 19, minute));
  return d.toISOString().replace(".000Z", ".000000Z");
};
const VALUES = ["3.1", "3.2", "3.6", "4.2", "4.4", "4.5", "4.6", "4.7", "4.8", "4.8", "4.7", "4.6", "4.6"];

const STOCKED_TEMPERATURE: ColdTemperatureRead = {
  ...envelope(),
  limitations: ["No spoilage, product-loss or failed-part determination is made."],
  state: "OBSERVED_EXCURSION",
  claim_level: "BOUNDED",
  policy: { low_deg_c: "2", high_deg_c: "4", return_hysteresis_deg_c: "0.5", min_excursion_min: 15, probe_asset_id: id(11), room_asset_id: id(10) },
  points: VALUES.map((value, i) => ({ at: at(i * 5), value, quality: "GOOD", evidence_id: id(100 + i) })),
  coverage: { known_points: 13, expected_points: 13, ratio: "1.0000" },
  gaps: [],
  excursions: [
    {
      episode_id: id(70),
      revision_id: id(71),
      direction: "HIGH",
      anchor_time: at(15),
      open: true,
      start_bounds: { earliest: at(10), latest: at(15) },
      end_bounds: { earliest: null, latest: null },
      duration_bounds: { low: "45", high: null },
      degree_minute_bounds: { low: "24.5", high: "31" },
      peak_observed: "4.8",
      claim_level: "BOUNDED",
      exposure_finding: true,
      limitation: null,
    },
  ],
  excluded: [{ evidence_id: id(200), use: "CONTEXT", reason: "DOOR_EVENT", as_of: at(12) }],
};

const step = (kind: string, minute: number | null, outcome: string | null, n: number | null) => ({
  kind,
  at: minute === null ? null : at(minute),
  outcome,
  evidence_id: n === null ? null : id(n),
  evidence_ids: n === null ? [] : [id(n)],
  state: n === null ? "MISSING" : "OBSERVED",
  limitation: n === null ? "No accepted record shows this step." : null,
});

const STOCKED_BACKUP: ColdBackupRead = {
  ...envelope(),
  state: "OBSERVED_FAILURE",
  claim_level: "OBSERVED",
  chains: [
    {
      correlation_id: "start-1",
      episode_id: id(80),
      revision_id: id(81),
      result: "OBSERVED_FAILURE",
      steps: [
        step("GRID", 11, "POWER_LOSS", 300),
        step("START_REQUEST", 11, "START_REQUEST", 301),
        step("START_RESULT", 12, "START_FAILED", 302),
        step("GENERATOR", 12, "FAILED", 303),
        step("TRANSFER", null, null, null),
        step("BUS", null, null, null),
        step("COMPRESSOR", null, null, null),
        step("PROBE", 15, null, 103),
      ],
      missing_steps: ["TRANSFER", "BUS", "COMPRESSOR"],
      claim_level: "OBSERVED",
      start_timeout_min: 2,
      limitation: "Not observed: TRANSFER, BUS, COMPRESSOR.",
    },
  ],
  contradictions: [],
  excluded: [{ evidence_id: id(200), use: "CONTEXT", reason: "DOOR_EVENT", as_of: at(12) }],
};

function item(findingId: string, kind: string, over: Partial<ColdFindingItem> = {}): ColdFindingItem {
  const excursion = kind === "EXCURSION";
  return {
    finding_id: findingId,
    kind,
    subject_asset_id: excursion ? id(10) : id(12),
    revision_id: id(excursion ? 911 : 912),
    lifecycle: "SUPPORTED",
    claim_level: excursion ? "BOUNDED" : "OBSERVED",
    title: excursion ? "Cold room temperature outside its policy band" : "Backup generator did not start when the grid failed",
    state: excursion ? "OBSERVED_EXCURSION" : "OBSERVED_FAILURE",
    claim: excursion
      ? {
          episode_id: id(70),
          episode_revision_id: id(71),
          kind,
          direction: "HIGH",
          start_bounds: { earliest: at(10), latest: at(15) },
          end_bounds: { earliest: null, latest: null },
          duration_bounds: { low: "45", high: null },
          degree_minute_bounds: { low: "24.5", high: "31" },
          peak_observed: "4.8",
          open: true,
        }
      : { episode_id: id(80), episode_revision_id: id(81), kind, correlation_id: "start-1", result: "OBSERVED_FAILURE", missing_steps: ["TRANSFER", "BUS", "COMPRESSOR"], start_timeout_min: "2" },
    episode_bounds: { start: { earliest: at(10), latest: excursion ? at(15) : at(11) }, end: { earliest: null, latest: null } },
    limitations: excursion ? [] : ["Not observed: TRANSFER, BUS, COMPRESSOR."],
    assessment_revision_id: id(excursion ? 50 : 51),
    evidence_ids: excursion ? [id(103), id(104)] : [id(300), id(301), id(302)],
    split_from_finding_id: null,
    as_of: KNOWN,
    limitation: null,
    ...over,
  };
}

const STOCKED_FINDINGS: ColdFindingsRead = { ...envelope(), items: [item(EXC_FINDING, "EXCURSION"), item(START_FINDING, "START_RESPONSE")], next_cursor: null };

const detailOf = (findingId: string, kind: string): ColdFindingDetailRead => ({
  ...envelope(),
  ...item(findingId, kind),
  basis_sha256: "b".repeat(64),
  episode_id: kind === "EXCURSION" ? id(70) : id(80),
  episode_revision_id: kind === "EXCURSION" ? id(71) : id(81),
  revisions: [{ revision_id: id(kind === "EXCURSION" ? 911 : 912), revision_no: 1, transition: "OPENED", lifecycle: "SUPPORTED", claim_level: "BOUNDED", basis_sha256: "b".repeat(64), created_at: KNOWN, evidence_ids: [id(103)] }],
});

/** A valid window with no selected assessment: 200 UNKNOWN, null values, empty arrays. */
const EMPTY_ENVELOPE = envelope("UNKNOWN", {
  currentness: { state: "UNKNOWN", watermark: { decided_at: KNOWN, assessment_revision_ids: [] }, latest_relevant_evidence_at: null, pending_since: null },
  source_provenance: { classification: null, source_ids: [], evidence_ids: [], basis_sha256: null },
  limitations: ["No selected cold assessment covers this window yet."],
});
const EMPTY_TEMPERATURE: ColdTemperatureRead = { ...EMPTY_ENVELOPE, policy: null, points: [], gaps: [], excursions: [], excluded: [], coverage: { known_points: null, expected_points: null, ratio: null } };
const EMPTY_BACKUP: ColdBackupRead = { ...EMPTY_ENVELOPE, state: null, claim_level: null, chains: [], contradictions: [] };
const EMPTY_FINDINGS: ColdFindingsRead = { ...EMPTY_ENVELOPE, items: [], next_cursor: null };

const FORBIDDEN = { status: "refused", httpStatus: 403, code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: "The source provenance of Site 'COLD-001' may not be disclosed to this caller." } as const;
const NOT_FOUND = { status: "refused", httpStatus: 404, code: "COLD_FINDING_NOT_FOUND", message: "No such cold Finding." } as const;
const DOWN = { status: "refused", httpStatus: 503, code: "COLD_READ_UNAVAILABLE", message: "store down" } as const;

const ok = <T,>(value: T): ColdRead<T> => ({ status: "loaded", value });

interface Reads {
  temperature: ColdRead<ColdTemperatureRead>;
  backup: ColdRead<ColdBackupRead>;
  findings: ColdRead<ColdFindingsRead>;
  finding: (findingId: string) => ColdRead<ColdFindingDetailRead>;
}

const STOCKED: Reads = {
  temperature: ok(STOCKED_TEMPERATURE),
  backup: ok(STOCKED_BACKUP),
  findings: ok(STOCKED_FINDINGS),
  finding: (f) => ok(detailOf(f, f === EXC_FINDING ? "EXCURSION" : "START_RESPONSE")),
};
const EMPTY: Reads = { ...STOCKED, temperature: ok(EMPTY_TEMPERATURE), backup: ok(EMPTY_BACKUP), findings: ok(EMPTY_FINDINGS) };
const REFUSED: Reads = { temperature: FORBIDDEN, backup: FORBIDDEN, findings: FORBIDDEN, finding: () => NOT_FOUND };

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
  const client: ColdAssessmentClient = {
    getTemperature: vi.fn(() => Promise.resolve(reads.temperature)),
    getBackupChain: vi.fn(() => Promise.resolve(reads.backup)),
    listFindings: vi.fn(() => Promise.resolve(reads.findings)),
    getFinding: vi.fn((_s: string, f: string) => Promise.resolve(reads.finding(f))),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldAssessment={client} />
    </MemoryRouter>,
  );
  return client;
}

const ROUTES = [
  ["temperature", "/sites/COLD-001/performance/temperature"],
  ["coldbackup", "/sites/COLD-001/performance/backup"],
  ["cold-finding", `/sites/COLD-001/findings/${START_FINDING}`],
  ["cold-finding-excursion", `/sites/COLD-001/findings/${EXC_FINDING}`],
] as const;

// W2-03 q3: the mock words are replaced by plain wording, the mock words are gone from these screens.
// The one exemption is the Architect-ruled provenance sentence verbatim (its "run" is on the W1 list); no general exemption.
const MANDATED = new Set<string>(["From a registered test run; not readings from physical equipment."]);
const main = () => document.querySelector("main") as HTMLElement;
const gaps = () => Array.from(document.querySelectorAll("[data-panel-gap]"));

describe("W2-03: cold assessment routes keep the v69 panel structure", () => {
  it.each(ROUTES)("stocked: %s", async (screenId, path) => {
    renderCold(path, STOCKED);
    await settledScreen();
    expect(main().getAttribute("data-cold-view")).toBe(screenId);
    expectV69Panels(screenId);
    expectPlantedPanelRejected(screenId);
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
    expect(document.querySelectorAll(".status-strip")).toHaveLength(1);
    const result = scanProductVocabulary(main(), screenId, { set: "w1" });
    expect(result.scanned).toBeGreaterThan(5);
    expect(describeViolations(result.violations.filter((v) => !MANDATED.has(v.text.trim())))).toBe("");
    for (const panel of Array.from(main().querySelectorAll("section.panel"))) {
      expect(panel.querySelectorAll("details[data-exact-references]").length).toBeLessThanOrEqual(1);
    }
  });

  it.each(ROUTES)("empty window (UNKNOWN 200): %s keeps every slot", async (screenId, path) => {
    renderCold(path, EMPTY);
    await settledScreen();
    expectV69Panels(screenId);
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
    expect(gaps().length).toBeGreaterThan(0);
  });

  it.each([
    ["temperature", ROUTES[0][1], 3],
    ["coldbackup", ROUTES[1][1], 4],
    ["cold-finding", ROUTES[2][1], 3],
  ] as const)("refused: %s keeps every slot with an in-panel gap", async (screenId, path, slots) => {
    renderCold(path, REFUSED);
    await settledScreen();
    expect(document.querySelector("[data-page-refusal]")).not.toBeNull();
    expectV69Panels(screenId);
    expect(gaps()).toHaveLength(slots);
  });

  it("refused companion read: cold-finding-excursion keeps the Temperature slot with its gap", async () => {
    renderCold(ROUTES[3][1], { ...STOCKED, temperature: DOWN });
    await settledScreen();
    expectV69Panels("cold-finding-excursion");
    expect(panelTitled("Temperature").querySelector("[data-panel-gap]")?.textContent).toContain("could not be read");
  });
});

describe("W2-03: temperature", () => {
  it("draws every selected point, the policy band and the excursion bounds", async () => {
    renderCold(ROUTES[0][1], STOCKED);
    await settledScreen();
    expect(document.querySelectorAll("[data-cold-point]")).toHaveLength(13);
    expect(document.querySelector(".cold-chart__band")).not.toBeNull();
    const context = panelTitled("Excursion context").textContent ?? "";
    expect(context).toContain("Began 19:10–19:15");
    expect(context).toContain("still outside policy at 20:05");
    expect(context).toContain("4.8 °C");
    expect(context).toContain("Door record 19:12");
    expect(document.querySelector('[data-cold-card="duration"]')?.textContent).toContain("At least 45 min");
    expect(document.querySelector('[data-cold-card="exposure"]')?.textContent).toContain("24.5–31");
    expect(panelTitled("How each limit is set").textContent).toContain("No spoilage");
  });

  it("links the excursion Finding only when it is persisted", async () => {
    renderCold(ROUTES[0][1], STOCKED);
    await settledScreen();
    const link = panelTitled("Excursion context").querySelector(`[data-finding-link="${EXC_FINDING}"]`);
    expect(link?.getAttribute("href")).toBe(`/sites/COLD-001/findings/${EXC_FINDING}`);
    cleanup();
    renderCold(ROUTES[0][1], { ...STOCKED, findings: ok({ ...STOCKED_FINDINGS, items: [] }) });
    await settledScreen();
    expect(document.querySelector("[data-finding-link]")).toBeNull();
    expect(panelTitled("Excursion context").textContent).toContain("No Finding is recorded for this excursion");
  });

  it("shows a probe gap and breaks the line across it", async () => {
    const points = STOCKED_TEMPERATURE.points.filter((_, i) => i < 3 || i > 8);
    renderCold(ROUTES[0][1], {
      ...STOCKED,
      temperature: ok({
        ...STOCKED_TEMPERATURE,
        state: "UNKNOWN",
        points,
        excursions: [],
        coverage: { known_points: 7, expected_points: 13, ratio: "0.5385" },
        gaps: [{ start: at(15), end: at(45), reason: "MISSING_PROBE", expected_points: 7, received_points: 0 }],
      }),
    });
    await settledScreen();
    expectV69Panels("temperature");
    expect(document.querySelectorAll("[data-cold-point]")).toHaveLength(7);
    expect(document.querySelectorAll(".cold-chart__line")).toHaveLength(2);
    expect(document.querySelector("[data-cold-gap]")?.textContent).toContain("No usable reading 19:15–19:45");
    expect(panelTitled("How each limit is set").textContent).toContain("7 of 13 expected");
  });

  it("keeps the selected window in the subtab and Finding addresses", async () => {
    const client = renderCold(`${ROUTES[0][1]}?from=${FROM}&to=${TO}`, STOCKED);
    await settledScreen();
    expect(client.getTemperature).toHaveBeenCalledWith("COLD-001", { from: FROM, to: TO, known_at: null });
    expect(document.querySelector('[data-performance-subtab="backup"]')?.getAttribute("href")).toContain(`from=${encodeURIComponent(FROM)}`);
  });
});

describe("W2-03: backup chain", () => {
  it("renders the ordered steps with observed and missing links", async () => {
    renderCold(ROUTES[1][1], STOCKED);
    await settledScreen();
    const steps = Array.from(panelTitled("Evidence by causal step").querySelectorAll("[data-cold-step]")).map((r) => r.getAttribute("data-cold-step"));
    expect(steps).toEqual(["GRID", "START_REQUEST", "START_RESULT", "GENERATOR", "TRANSFER", "BUS", "COMPRESSOR", "PROBE", "TEMPERATURE"]);
    expect(panelTitled("Reconstructed event chain").querySelectorAll("[data-timeline-event]")).toHaveLength(8);
    expect(panelTitled("What the chain shows").textContent).toContain("Not recorded: transfer to backup, backup bus, compressor.");
    expect(panelTitled("Backup event chains").querySelectorAll("th")).toHaveLength(8);
    expect(panelTitled("Backup event chains").querySelectorAll("[data-cold-chain-row]")).toHaveLength(1);
    expect(panelTitled("Evidence by causal step").querySelector(`[data-evidence-link="${id(300)}"]`)).not.toBeNull();
    expect(main().querySelector('a[href*="incident"]')).toBeNull();
    // Review M1: a failed chain (no compressor running record) never says "after recovery".
    expect(panelTitled("Evidence by causal step").textContent).not.toContain("after recovery");
    expect(panelTitled("Evidence by causal step").querySelector('[data-cold-step="PROBE"]')?.textContent).toContain("after the compressor record");
    // q3 deviation 18: the cold column labels, all eight in order.
    const heads = Array.from(panelTitled("Backup event chains").querySelectorAll("th")).map((h) => h.textContent);
    expect(heads).toEqual(["When", "Grid", "Start requested", "Generator", "Power to compressor", "Compressor response", "Outcome for service", "Result"]);
    // Review L3: no run-on, and L4: the failed-start chip is the danger tone.
    expect(panelTitled("Backup event chains").textContent).not.toMatch(/policy At least/);
    expect(panelTitled("Backup event chains").querySelector("[data-cold-result='OBSERVED_FAILURE']")?.className).toContain("cold-result--danger");
  });

  it("says the probe reading came after recovery only when the compressor shows cooling running", async () => {
    const base = STOCKED_BACKUP.chains[0];
    const steps = base.steps.map((s) => (s.kind === "COMPRESSOR" ? { ...s, state: "OBSERVED", outcome: "RUNNING", at: s.at ?? base.steps[7].at, evidence_id: id(305) } : s));
    renderCold(ROUTES[1][1], { ...STOCKED, backup: ok({ ...STOCKED_BACKUP, chains: [{ ...base, steps: steps as typeof base.steps, missing_steps: [] }] }) });
    await settledScreen();
    expect(panelTitled("Evidence by causal step").querySelector('[data-cold-step="PROBE"]')?.textContent).toContain("after recovery");
  });

  it("states contradictory start results without a failure", async () => {
    const chain = { ...STOCKED_BACKUP.chains[0], result: "CONTRADICTORY", claim_level: "CONTRADICTORY" };
    renderCold(ROUTES[1][1], {
      ...STOCKED,
      backup: ok({ ...STOCKED_BACKUP, chains: [chain], contradictions: [{ correlation_id: "start-1", evidence_ids: [id(302), id(304)], reason: "CONTRADICTORY", limitation: null }] }),
    });
    await settledScreen();
    expect(panelTitled("What the chain shows").textContent).toContain("no start failure is claimed");
  });
});

describe("W2-03 q3: unavailable entries, wording and provenance", () => {
  const row = (label: string) => document.querySelector(`nav[aria-label="${label}"]`) as HTMLElement;
  const entries = (nav: HTMLElement) => Array.from(nav.querySelectorAll("li")).map((li) => li.textContent?.trim());

  it.each([
    ["Performance sections", ROUTES[0][1], ["Temperature", "Cooling · Not available yet", "Backup"], "Cooling"],
    ["Performance sections", ROUTES[1][1], ["Temperature", "Cooling · Not available yet", "Backup"], "Cooling"],
    ["Finding sections", ROUTES[2][1], ["Overview", "Recommendation · Not available yet"], "Recommendation"],
    ["Finding sections", ROUTES[3][1], ["Overview", "Recommendation · Not available yet"], "Recommendation"],
  ] as const)("%s on %s keep order and render the unbuilt entry as text only", async (aria, path, order, unbuilt) => {
    renderCold(path, STOCKED);
    await settledScreen();
    const nav = row(aria);
    expect(entries(nav)).toEqual(order);
    const li = nav.querySelector(`[data-tab-unavailable="${unbuilt}"]`) as HTMLElement;
    expect(li.getAttribute("aria-label")).toBe(`${unbuilt}, Not available yet`);
    expect(li.querySelector("a, button, [tabindex], [role], [disabled], [aria-disabled]")).toBeNull();
    expect(li.getAttribute("tabindex")).toBeNull();
    expect(nav.querySelectorAll("a")).toHaveLength(aria === "Performance sections" ? 2 : 0);
    expect(nav.querySelector('[aria-current="page"]')).not.toBeNull();
    expect(main().querySelector('a[href*="cooling"], a[href*="recommendation"]')).toBeNull();
  });

  it("uses the approved panel title and keeps the mock title out", async () => {
    renderCold(ROUTES[0][1], STOCKED);
    await settledScreen();
    expect(panelTitled("How each limit is set")).not.toBeNull();
    expect(main().textContent).not.toContain("Claim boundary");
  });

  it("labels the simulated source as generated test data with the adjacent sentence", async () => {
    renderCold(ROUTES[0][1], STOCKED);
    await settledScreen();
    const source = main().querySelector("[data-cold-source]") as HTMLElement;
    expect(source.textContent).toBe("Generated test data");
    expect(source.nextElementSibling?.textContent).toBe("From a registered test run; not readings from physical equipment.");
    expect(main().textContent).not.toContain("Registered simulation");
  });
});

describe("W2-03: cold Finding detail", () => {
  it("routes by kind and shows the next-step gap", async () => {
    renderCold(ROUTES[2][1], STOCKED);
    await settledScreen();
    expect(panelTitled("Recommended next step").textContent).toContain("No recorded next step");
    expect(panelTitled("Operational context").querySelectorAll("[data-timeline-event]")).toHaveLength(8);
    // Retro correction 14: the assessment is labelled text with the unavailable gap, never a link.
    const analysis = panelTitled("Operational context").querySelector(`[data-analysis-unavailable="${id(51)}"]`);
    expect(analysis?.textContent).toContain("Analysis view not available for this cold record");
    expect(analysis?.closest("a")).toBeNull();
    expect(panelTitled("Operational context").querySelector('a[href*="assessment="]')).toBeNull();
    expect(panelTitled("Bounded conclusion").textContent).toContain("Transfer to backup".toLowerCase());
    cleanup();
    renderCold(ROUTES[3][1], STOCKED);
    await settledScreen();
    expect(panelTitled("Bounded conclusion").textContent).toContain("above 4 °C for at least 45 minutes");
    expect(panelTitled("Temperature").querySelectorAll("[data-cold-point]")).toHaveLength(13);
    expect(panelTitled("Recommended next step").querySelector(`[data-finding-link="${START_FINDING}"]`)).not.toBeNull();
  });
});

/* D-2026-10-19-w2-03-followup: closed-panel compaction and W2-03 chip tones. */
describe("W2-03 follow-up: closed panels keep the primary form, one disclosure holds the detail", () => {
  const disclosureOf = (panel: HTMLElement) => {
    const found = panel.querySelectorAll("details[data-exact-references]");
    expect(found).toHaveLength(1);
    const details = found[0] as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.querySelector("summary")?.textContent).toBe("How this was worked out");
    details.open = true;
    return details;
  };
  const outside = (panel: HTMLElement, selector: string) => {
    const el = panel.querySelector(selector);
    expect(el).not.toBeNull();
    expect(el?.closest("details")).toBeNull();
    return el as HTMLElement;
  };
  const closedText = (panel: HTMLElement) =>
    Array.from(panel.querySelectorAll(".panel__body > *"))
      .filter((n) => !n.matches("details"))
      .map((n) => n.textContent)
      .join(" ");
  const withGap = { ...STOCKED_TEMPERATURE, gaps: [{ start: at(15), end: at(30), reason: "MISSING_PROBE", expected_points: 4, received_points: 0 }] };

  it.each([
    ["excursion", STOCKED_TEMPERATURE, "support a bounded temperature excursion above policy. Product quality or spoilage conclusions need product identity, an exposure policy and further evidence."],
    ["within policy", { ...STOCKED_TEMPERATURE, state: "NO_EXCURSION_OBSERVED", excursions: [] }, "stay within policy for this window. This says nothing about product condition."],
    ["unknown", { ...STOCKED_TEMPERATURE, state: "UNKNOWN", excursions: [] }, "do not support a temperature conclusion for this window."],
  ] as const)("temperature claim panel (%s): sentence closed, facts and limits in the disclosure", async (_name, read, sentence) => {
    renderCold(ROUTES[0][1], { ...STOCKED, temperature: ok(read as ColdTemperatureRead) });
    await settledScreen();
    const panel = panelTitled("How each limit is set");
    expect(outside(panel, ".prose").textContent).toContain(sentence);
    expect(closedText(panel)).not.toContain("usable");
    expect(closedText(panel)).not.toContain("No spoilage");
    const details = disclosureOf(panel);
    expect(details.getAttribute("data-disclosure")).toBe("cold-claim-references");
    expect(details.querySelector("[data-cold-claim-facts]")?.textContent).toMatch(/set aside/);
    expect(details.querySelector("[data-cold-claim-facts]")?.textContent).toContain("13 of 13 expected readings usable");
    expect(details.querySelector("[data-cold-source]")?.textContent).toBe("Generated test data");
    expect(details.querySelector("[data-cold-limitations]")?.textContent).toContain("No spoilage");
    expect(details.querySelector("[data-cold-source-sentence]")?.textContent).toBe("From a registered test run; not readings from physical equipment.");
    expect(details.textContent).toContain("Records not used");
  });

  it("temperature claim panel states 'no records set aside' inside the disclosure when empty", async () => {
    renderCold(ROUTES[0][1], { ...STOCKED, temperature: ok({ ...STOCKED_TEMPERATURE, excluded: [] }) });
    await settledScreen();
    const details = disclosureOf(panelTitled("How each limit is set"));
    expect(details.querySelector("[data-cold-claim-facts]")?.textContent).toContain("no records set aside");
  });

  it("start Finding: full chain and missing-step line closed, versions and evidence in the disclosure", async () => {
    renderCold(ROUTES[2][1], STOCKED);
    await settledScreen();
    const panel = panelTitled("Operational context");
    expect(panel.querySelectorAll("[data-timeline-event]")).toHaveLength(8);
    for (const e of Array.from(panel.querySelectorAll("[data-timeline-event]"))) expect(e.closest("details")).toBeNull();
    expect(outside(panel, ".cold-operational-missing").textContent).toMatch(/^Missing steps: .+, .+, .+$/);
    expect(closedText(panel)).not.toContain("Versions");
    expect(closedText(panel)).not.toContain("Accepted records");
    const details = disclosureOf(panel);
    expect(details.getAttribute("data-disclosure")).toBe("cold-finding-references");
    expect(details.textContent).toContain("Versions");
    expect(details.querySelectorAll("[data-evidence-link]").length).toBeGreaterThan(0);
    expect(details.querySelector(`[data-analysis-unavailable="${id(51)}"]`)?.textContent).toContain("Analysis view not available for this cold record");
    expect(details.querySelector("a[href*='assessment=']")).toBeNull();
    const next = panelTitled("Recommended next step");
    expect(next.querySelector("details")).toBeNull();
    expect(next.textContent).toContain("No recorded next step. No Action or Recommendation record is linked to this Finding.");
    expect(next.textContent).toContain("Open the Backup view →");
    expect(panel.closest(".panel-pair")?.classList.contains("cold-finding-pair")).toBe(true);
  });

  it("start Finding: missing line reads 'None' when nothing is missing and survives an unreadable chain", async () => {
    const none = (f: string) => {
      const d = detailOf(f, "START_RESPONSE");
      return ok({ ...d, claim: { ...d.claim, missing_steps: [] } });
    };
    renderCold(ROUTES[2][1], { ...STOCKED, finding: none });
    await settledScreen();
    expect(panelTitled("Operational context").querySelector(".cold-operational-missing")?.textContent).toBe("Missing steps: None");
    cleanup();
    renderCold(ROUTES[2][1], { ...STOCKED, backup: DOWN });
    await settledScreen();
    const panel = panelTitled("Operational context");
    expect(panel.querySelectorAll("[data-timeline-event]")).toHaveLength(0);
    expect(panel.querySelector("[data-panel-gap]")).not.toBeNull();
    expect(panel.querySelector(".cold-operational-missing")?.textContent).toMatch(/^Missing steps: .+/);
  });

  it("excursion Finding: chart and gap notes closed, peak/exposure/evidence in the disclosure, next step unchanged", async () => {
    renderCold(ROUTES[3][1], { ...STOCKED, temperature: ok(withGap as ColdTemperatureRead) });
    await settledScreen();
    const panel = panelTitled("Temperature");
    expect(panel.querySelectorAll("[data-cold-point]")).toHaveLength(13);
    for (const p of Array.from(panel.querySelectorAll("[data-cold-point]"))) expect(p.closest("details")).toBeNull();
    outside(panel, "[data-cold-gap]");
    expect(closedText(panel)).not.toContain("Peak observed");
    expect(closedText(panel)).not.toContain("Exposure size");
    const details = disclosureOf(panel);
    expect(details.getAttribute("data-disclosure")).toBe("cold-finding-references");
    expect(details.textContent).toContain("Peak observed");
    expect(details.textContent).toContain("Exposure size");
    expect(details.textContent).toContain("24.5");
    expect(details.querySelectorAll("[data-evidence-link]").length).toBeGreaterThan(0);
    const next = panelTitled("Recommended next step");
    expect(next.querySelector("details")).toBeNull();
    expect(next.textContent).toContain("No recorded next step. No Action or Recommendation record is linked to this Finding.");
    expect(next.textContent).toContain("Open the Temperature view →");
    expect(next.querySelector(`[data-finding-link="${START_FINDING}"]`)).not.toBeNull();
    expect(panel.closest(".panel-pair")?.classList.contains("cold-finding-pair")).toBe(true);
  });

  it("excursion Finding: no related link without a selected start Finding; unreadable chart keeps its gap", async () => {
    renderCold(ROUTES[3][1], { ...STOCKED, findings: ok({ ...STOCKED_FINDINGS, items: STOCKED_FINDINGS.items.filter((f) => f.kind !== "START_RESPONSE") }), temperature: DOWN });
    await settledScreen();
    expect(panelTitled("Recommended next step").querySelector("[data-finding-link]")).toBeNull();
    expect(panelTitled("Temperature").querySelector("[data-panel-gap]")).not.toBeNull();
    expect(panelTitled("Temperature").querySelectorAll("details[data-exact-references]")).toHaveLength(1);
  });

  it("pending and refused states keep the single disclosure rule and their gaps", async () => {
    renderCold(ROUTES[0][1], { ...STOCKED, temperature: ok({ ...STOCKED_TEMPERATURE, currentness: { ...STOCKED_TEMPERATURE.currentness, state: "PENDING_RECOMPUTE", pending_since: KNOWN } }) });
    await settledScreen();
    expect(panelTitled("How each limit is set").querySelectorAll("details[data-exact-references]")).toHaveLength(1);
    cleanup();
    renderCold(ROUTES[0][1], REFUSED);
    await settledScreen();
    expect(panelTitled("How each limit is set").querySelector("[data-panel-gap]")).not.toBeNull();
  });
});

describe("W2-03 follow-up: M5 chip tones on the selected state and result badge only", () => {
  const badgeIn = (scope: Element, text: string) => {
    const b = Array.from(scope.querySelectorAll(".badge")).find((e) => e.textContent?.trim() === text);
    expect(b, text).toBeDefined();
    return b as HTMLElement;
  };
  const strip = (label: string) => document.querySelector(`[aria-label="${label}"]`) as HTMLElement;
  const GREEN = "cold-temperature-tone--green";
  const AMBER = "cold-temperature-tone--amber";

  it.each([
    ["NO_EXCURSION_OBSERVED", "Within policy", GREEN],
    ["OBSERVED_EXCURSION", "Outside policy", AMBER],
    ["CONTRADICTORY", "Readings disagree", AMBER],
    ["UNKNOWN", "Not assessed", null],
  ] as const)("temperature state %s reads %s", async (state, word, tone) => {
    renderCold(ROUTES[0][1], { ...STOCKED, temperature: ok({ ...STOCKED_TEMPERATURE, state }) });
    await settledScreen();
    const bar = strip("Temperature state");
    const chip = badgeIn(bar, word);
    expect(chip.classList.contains(GREEN)).toBe(tone === GREEN);
    expect(chip.classList.contains(AMBER)).toBe(tone === AMBER);
    if (tone === null) expect(chip.classList.contains("badge--neutral")).toBe(true);
    const coverage = Array.from(bar.querySelectorAll(".badge")).find((e) => e.textContent?.startsWith("Coverage")) as HTMLElement;
    expect(coverage.className).not.toMatch(/cold-temperature-tone/);
  });

  it.each([
    ["OBSERVED_SUCCESS", "Started", "green"],
    ["OBSERVED_FAILURE", "Start failed", "danger"],
    ["CONTRADICTORY", "Results disagree", "warning"],
    ["UNKNOWN", "Not established", "neutral"],
  ] as const)("backup result %s reads %s in the status bar and the chain table", async (result, word, tone) => {
    const chain = { ...STOCKED_BACKUP.chains[0], result };
    renderCold(ROUTES[1][1], { ...STOCKED, backup: ok({ ...STOCKED_BACKUP, chains: [chain] }) });
    await settledScreen();
    const bar = strip("Backup chain state");
    const table = panelTitled("Backup event chains");
    for (const scope of [bar, table]) {
      const wrapper = scope.querySelector(".cold-result") as HTMLElement;
      const chip = badgeIn(wrapper, word);
      expect(chip.classList.contains(GREEN)).toBe(tone === "green");
      expect(chip.classList.contains(AMBER)).toBe(false);
      expect(wrapper.className).toContain(tone === "green" ? "cold-result--neutral" : `cold-result--${tone}`);
    }
    const evidence = Array.from(bar.querySelectorAll(".badge")).find((e) => e.textContent?.startsWith("Evidence:")) as HTMLElement;
    expect(evidence.className).not.toMatch(/cold-temperature-tone/);
    expect(evidence.closest(".cold-result")).toBeNull();
  });
});
