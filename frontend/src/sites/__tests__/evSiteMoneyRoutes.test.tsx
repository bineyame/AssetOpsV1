import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvEnvelope, EvRead } from "../evAssessmentClient";
import type {
  EvAnalysisItem,
  EvAnalysisRead,
  EvAssumptionsRead,
  EvCapability,
  EvConsequence,
  EvCoverage,
  EvEvidenceRead,
  EvFinancialsRead,
  EvOverviewRead,
  EvSiteClient,
  EvSource,
} from "../evSiteClient";
import { money2 } from "../EvSiteViews";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W2-07 commits 4-5 (`.agent/W2-07-build-spec.md` "Commits 4-5", closure section 4, q5 dry-read, q6): an
 * EV_CHARGING Site's five `/sites/{code}/ev...` routes render `ev`, `ev-evidence`, `ev-evidence-analysis`,
 * `ev-financials` and `ev-assumptions` in the exact v69 panel registry for stocked, empty/unknown, unpriced,
 * pending, historical and refused reads. Fixture values follow the W2-05b replay shapes (EV-LAB-001), never the
 * mock's illustrations.
 */

afterEach(cleanup);

const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:05:00.000000Z";
const KNOWN = "2026-10-06T09:00:00.000000Z";
const Q = `?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;
const RAW_Q = `?from=${FROM}&to=${TO}&known_at=${KNOWN}`;
const id = (n: number) => `0000${String(n).padStart(4, "0")}-0000-4000-8000-${String(n).padStart(12, "0")}`;
const BASIS = "b".repeat(64);
const NO_LINKS = { self: null, evidence: null, analysis: null, finding: null, financials: null };
const links = (own: string) => ({
  self: `/sites/${CODE}/ev${own}${RAW_Q}`,
  evidence: `/sites/${CODE}/ev/evidence${RAW_Q}`,
  analysis: `/sites/${CODE}/ev/evidence/analysis${RAW_Q}`,
  finding: null,
  financials: `/sites/${CODE}/ev/financials${RAW_Q}`,
});

function env(state = "CURRENT"): EvEnvelope {
  return {
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN },
    currentness: { state, as_of: state === "UNKNOWN" ? null : KNOWN, limitation: null },
    source_provenance: { classification: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [], basis_sha256: BASIS },
    limitations: [],
  };
}

const NULL_COV: EvCoverage = { known_seconds: null, expected_seconds: null, ratio: null, unit: null };
const COVERAGE_NULL = "Coverage duration cannot be calculated from the selected records.";
function cap(claim: string, state: string, coverage: EvCoverage = NULL_COV, missing: string[] = [], limitation: string | null = null): EvCapability {
  return { claim, state, required_roles: ["session_event"], missing_roles: missing, coverage, accepted_evidence_ids: [id(100)], as_of: KNOWN, limitation: coverage.unit === null ? (limitation === null ? COVERAGE_NULL : `${limitation} ${COVERAGE_NULL}`) : limitation };
}
const WINDOW_COV: EvCoverage = { known_seconds: 3600, expected_seconds: 3900, ratio: "0.923", unit: "WINDOW_SECONDS" };
const SESSION_COV: EvCoverage = { known_seconds: 1800, expected_seconds: 1800, ratio: "1", unit: "SESSION_SECONDS" };
function caps(gross: EvCoverage = SESSION_COV): EvCapability[] {
  return [
    cap("SESSION_OUTCOME", "SUPPORTED", SESSION_COV),
    cap("SERVICE_STATE", "UNAVAILABLE", NULL_COV, ["connector_status"], "Availability is not assessed."),
    cap("DELIVERED_ENERGY", "SUPPORTED", SESSION_COV),
    cap("FAULT_ASSOCIATION", "UNAVAILABLE", NULL_COV, ["fault_event"], "Cause is not established."),
    cap("SITE_POWER_CONTEXT", "LIMITED", WINDOW_COV),
    cap("POWER_CONSTRAINT", "LIMITED", NULL_COV, ["requested_power", "allocated_limit"]),
    cap("GROSS_TARIFF_SCENARIO", gross.ratio === "1" ? "SUPPORTED" : "LIMITED", gross, [], "Gross scenario only."),
  ];
}

const CONSEQUENCE: EvConsequence = {
  revision_id: id(700), revision_no: 1, state: "ESTIMATED", reason: "ELIGIBLE", quantity_kwh: "30.000",
  tariff_revision_id: id(800), tariff_value: "0.2777", currency: "KES", amount: "8.331000", overlap_group: `ev:${"c".repeat(64)}`,
  recorded_at: KNOWN, tariff_recorded_at: "2026-10-06T07:00:00.000000Z", source_gate: "REGISTERED_SIMULATION",
  session_revision_ids: [id(500)], evidence_ids: [id(301), id(302)], limitation: "Gross scenario; not cash collected.",
};
const GUARD = (reason: string, limitation: string): EvConsequence => ({
  ...CONSEQUENCE, revision_id: null, revision_no: null, state: "WITHHELD", reason, quantity_kwh: null, tariff_revision_id: null,
  tariff_value: null, currency: null, amount: null, overlap_group: null, recorded_at: null, tariff_recorded_at: null,
  source_gate: null, session_revision_ids: [], evidence_ids: [], limitation,
});

interface Opts {
  state?: string;
  consequence?: EvConsequence | null;
  schedule?: "common" | "none" | "outside" | "vary";
  gross?: EvCoverage;
  empty?: boolean;
}

function overview(o: Opts = {}): EvOverviewRead {
  const c = o.consequence === undefined ? CONSEQUENCE : o.consequence;
  const occ = { from: FROM, to: "2026-10-06T16:00:00.000000Z" };
  const sched = o.schedule ?? "common";
  return {
    ...env(o.state),
    status: { state: o.empty ? "UNKNOWN" : "OBSERVED_SESSIONS", claim_level: null, as_of: KNOWN, limitation: o.empty ? "No selected EV session assessment covers this window yet." : null },
    objective: {
      text: "Let depot vehicles charge when scheduled, within the configured Site import limit.",
      configured_service_window: sched === "common" ? occ : null,
      configured_service_windows: sched === "common" ? [occ] : sched === "vary" ? [occ, { from: "2026-10-06T09:00:00.000000Z", to: "2026-10-06T17:00:00.000000Z" }] : [],
      service_schedule_declared: sched !== "none",
      site_import_limit_kw: "80",
      as_of: FROM,
      limitation: "Configuration is not a measured service result.",
    },
    denominator: o.empty
      ? { started: null, completed: null, observed_abort: null, incomplete: null, contradictory: null, orphan: null, confirmed_delivery: null, fault_aborted: null, as_of: null, limitation: "No selected EV session assessment covers this window yet." }
      : { started: 2, completed: 1, observed_abort: 0, incomplete: 1, contradictory: 0, orphan: 0, confirmed_delivery: 1, fault_aborted: 0, as_of: KNOWN, limitation: null },
    energy: o.empty
      ? { supported_kwh: null, complete_kwh: null, partial_kwh: null, unknown_seconds: null, as_of: null, limitation: "No supported session energy." }
      : { supported_kwh: "30.000", complete_kwh: "30.000", partial_kwh: "0.000", unknown_seconds: 0, as_of: KNOWN, limitation: null },
    site_power: o.empty
      ? { observed_peak_kw: null, configured_limit_kw: "80", coverage: NULL_COV, claim_limit: "UNKNOWN", as_of: null, limitation: "No accepted Site import intervals cover this window." }
      : { observed_peak_kw: "60", configured_limit_kw: "80", coverage: WINDOW_COV, claim_limit: "CONTEXT_ONLY", as_of: KNOWN, limitation: null },
    findings: { count: 0, items: [], as_of: KNOWN, limitation: null },
    needs_attention: o.empty
      ? []
      : [
          ...(o.state === "PENDING_RECOMPUTE" ? [{ code: "PENDING", text: "New evidence is being assessed. The previous result may change.", link: null }] : []),
          { code: "INCOMPLETE_SESSION", text: "A session has no accepted end report.", link: links("").analysis },
        ],
    consequence_summary:
      c === null
        ? { state: null, reason: null, quantity_kwh: null, amount: null, currency: null, overlap_group: null, as_of: null, limitation: "No gross tariff scenario assessed." }
        : { state: c.state, reason: c.reason, quantity_kwh: c.quantity_kwh, amount: c.amount, currency: c.currency, overlap_group: c.overlap_group, as_of: c.recorded_at, limitation: c.limitation },
    links: links(""),
  };
}

function source(slot: string, display: string, state: string, by: { id: number; state: string }[], quality = "GOOD", count = 4, roles: string[] = ["session_event"]): EvSource {
  const one = by.length === 1;
  return {
    slot, asset_id: slot === "BILLING" ? null : id(20 + by.length), display_name: display,
    contact: {
      state, checked_at: KNOWN, last_seen_at: one ? "2026-10-06T08:59:00.000000Z" : null, age_seconds: one ? 60 : null,
      diagnostic_id: one ? id(90) : null, diagnostic_received_at: one ? "2026-10-06T08:59:30.000000Z" : null, cadence_seconds: one ? 60 : null,
      by_source: by.map((b) => ({ source_id: id(b.id), state: b.state, last_seen_at: "2026-10-06T08:59:00.000000Z", age_seconds: 60, diagnostic_id: id(90), diagnostic_received_at: "2026-10-06T08:59:30.000000Z", cadence_seconds: 60 })),
    },
    quality: { state: quality, accepted_count: count }, roles, as_of: KNOWN, limitation: count === 0 ? "No accepted report for this role." : null,
  };
}

function evidence(o: Opts = {}): EvEvidenceRead {
  return {
    ...env(o.state),
    capabilities: o.empty ? [] : caps(o.gross),
    sources: [
      source("CONNECTOR_1", "Connector c1", "MIXED", [{ id: 31, state: "RECENT" }, { id: 32, state: "OLD" }, { id: 33, state: "RECENT" }]),
      source("CONNECTOR_2", "Connector c2", "RECENT", [{ id: 34, state: "RECENT" }]),
      source("SITE_METER", "Site meter", "UNKNOWN", [], "NO_FACT", 0, []),
      source("BILLING", "Billing system", "UNKNOWN", [], "NO_FACT", 0, []),
    ],
    next_evidence: o.empty
      ? []
      : [
          { code: "TERMINAL_GAP", text: "Recover the missing session end report", why: "Needed before a session outcome is complete.", link: links("").analysis },
          { code: "BILLING_GAP", text: "Connect billing records", why: "Needed before any amount can be stated as collected.", link: links("").financials },
        ],
    links: links("/evidence"),
  };
}

function item(n: number, over: Partial<EvAnalysisItem> = {}): EvAnalysisItem {
  return {
    evidence_id: id(n), source_label: "Connector c1 · session_event", role: "session_event", record_kind: "EV_SESSION_START",
    value_display: "Session started", unit: null, source_time: `2026-10-06T08:${String(n % 60).padStart(2, "0")}:00.000000Z`,
    sent_at: null, received_at: "2026-10-06T08:59:01.000000Z", quality: "GOOD", use: "SUPPORT", reason: null, session_id: id(500),
    interval_start: null, interval_end: null, note: null, record_target_state: "UNAVAILABLE", links: NO_LINKS, ...over,
  };
}
const UNVERIFIED_ID = id(450);
function analysis(o: Opts = {}): EvAnalysisRead {
  const items = o.empty
    ? []
    : [
        item(101),
        item(102, { record_kind: "EV_SESSION_END", value_display: "Session ended" }),
        item(103, { role: "connector_meter_delta", record_kind: "EV_CONNECTOR_ENERGY", value_display: "1.250", unit: "kWh", interval_start: "2026-10-06T08:05:00.000000Z", interval_end: "2026-10-06T08:10:00.000000Z" }),
        item(104, { role: "site_import", record_kind: "EV_SITE_IMPORT", source_label: "Site meter · site_import", value_display: "60", unit: "kW", interval_start: "2026-10-06T08:00:00.000000Z", interval_end: "2026-10-06T08:15:00.000000Z" }),
        item(450, { use: "EXCLUDED", reason: "SOURCE_UNVERIFIED", note: "Source or binding unverified for this record.", session_id: null }),
      ];
  return {
    ...env(o.state), items, total_count: items.length,
    excluded_records: o.empty ? [] : [{ evidence_id: UNVERIFIED_ID, record_kind: "EV_SESSION_START", reason: "SOURCE_UNVERIFIED" }],
    claim_rules: o.empty ? [] : caps(o.gross).map((c) => ({ claim: c.claim, required_roles: c.required_roles, observed_roles: [], missing_roles: c.missing_roles, coverage: c.coverage, result: c.state, accepted_evidence_ids: c.accepted_evidence_ids, source_class: "REGISTERED_SIMULATION", known_at: KNOWN, limitation: c.limitation })),
    next_cursor: null, links: links("/evidence/analysis"),
  };
}

function financials(o: Opts = {}): EvFinancialsRead {
  const c = o.consequence === undefined ? CONSEQUENCE : o.consequence;
  return {
    ...env(o.state), consequence: c,
    history: o.state === "HISTORICAL" ? [{ ...CONSEQUENCE, revision_id: id(699), label: "Historical scenario", amount: "7.000000" }] : [],
    not_included: ["lost_sales", "collections", "margin", "repair", "warranty"], next_cursor: null, links: links("/financials"),
  };
}

function assumptions(o: Opts = {}): EvAssumptionsRead {
  const tariff = o.consequence === null ? null : { revision_id: id(800), value: "0.2777", currency: "KES", unit: "currency/kWh", basis: "Authored test tariff", valid_from: "2026-10-01T00:00:00.000000Z", valid_to: null, recorded_at: "2026-10-06T07:00:00.000000Z" };
  return {
    ...env(o.state), tariff, tariff_revision_count: tariff === null ? 0 : 1, publication_note: null,
    consequence_tariff: tariff === null ? null : { revision_id: tariff.revision_id, value: tariff.value, currency: tariff.currency, recorded_at: tariff.recorded_at },
    billing_state: "NO_RECORD", missing_keys: tariff === null ? ["ev_gross_tariff_per_kwh"] : [], links: links("/financial-assumptions"),
  };
}

const ok = <T,>(value: T): EvRead<T> => ({ status: "loaded", value });
const refused = (httpStatus: number, code: string): EvRead<never> => ({ status: "refused", httpStatus, code, message: "refused" });

const SITE = {
  site_id: CODE, display_name: "EV lab depot", site_type: "EV_CHARGING", location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Africa/Addis_Ababa", lifecycle_status: "PLANNED", origin: "USER", source: { mode: "SIMULATED" }, template: null, configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

function client(o: Opts = {}, refusal: EvRead<never> | null = null): EvSiteClient {
  const r = <T,>(v: T) => vi.fn(() => Promise.resolve(refusal ?? ok(v)));
  return {
    getOverview: r(overview(o)),
    getEvidence: r(evidence(o)),
    getAnalysis: r(analysis(o)),
    getFinancials: r(financials(o)),
    getAssumptions: r(assumptions(o)),
  };
}

const PATHS = {
  ev: `/sites/${CODE}/ev`,
  "ev-evidence": `/sites/${CODE}/ev/evidence`,
  "ev-evidence-analysis": `/sites/${CODE}/ev/evidence/analysis`,
  "ev-financials": `/sites/${CODE}/ev/financials`,
  "ev-assumptions": `/sites/${CODE}/ev/financial-assumptions`,
} as const;

async function renderAt(path: string, evSite: EvSiteClient) {
  render(
    <MemoryRouter initialEntries={[`${path}${Q}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evSite={evSite} />
    </MemoryRouter>,
  );
  await settledScreen();
}

const main = () => document.querySelector("main") as HTMLElement;
const strip = () => (document.querySelector(".status-strip") as HTMLElement | null)?.textContent ?? "";
const subtabs = (label: string) =>
  Array.from(document.querySelectorAll(`nav[aria-label="${label}"] li`)).map((li) => ({
    text: li.textContent,
    href: li.querySelector("a")?.getAttribute("href") ?? null,
    current: li.querySelector("a")?.getAttribute("aria-current") ?? null,
  }));

describe("W2-07 EV Site routes", () => {
  it("analysis_source_unverified_shows_full_id_and_sentence", async () => {
    await renderAt(PATHS["ev-evidence-analysis"], client());
    expectV69Panels("ev-evidence-analysis");
    const records = panelTitled("Accepted records behind the conclusions");
    // Closed table: first three real accepted rows only, ordered as served; the excluded row is not invented as a session.
    expect(records.querySelectorAll("tbody tr")).toHaveLength(3);
    expect(within(records).getAllByText(/No analysis link/)).toHaveLength(3);
    const details = records.querySelector('[data-disclosure="ev-site-record-details"]') as HTMLElement;
    const row = details.querySelector(`[data-record-detail="${UNVERIFIED_ID}"]`) as HTMLElement;
    expect(row.textContent).toContain(UNVERIFIED_ID);
    expect(row.textContent).toContain("Source or binding unverified for this record.");
    expect(row.textContent).toContain("use EXCLUDED · SOURCE_UNVERIFIED");
    expect(row.textContent).toContain("Analysis view not available for this EV record");
    expect(row.querySelector("a")).toBeNull();
    expect(details.querySelector("[data-ev-record-selection]")?.textContent).toBe(`Site ${CODE} · ${FROM} to ${TO} · known at ${KNOWN}`);
    // The sentence is per record, never a panel banner.
    expect(records.querySelector("[data-panel-gap]")).toBeNull();
    expect(strip()).not.toContain("Source or binding unverified");
    expect(main().querySelectorAll("[data-ev-record-note]")).toHaveLength(1);
  });

  it("ev_evidence_tabs_and_record_limit", async () => {
    await renderAt(PATHS["ev-evidence"], client());
    expectV69Panels("ev-evidence");
    expect(subtabs("Evidence sections")).toEqual([
      { text: "Overview", href: `${PATHS["ev-evidence"]}${Q}`, current: "page" },
      { text: "Analysis", href: `${PATHS["ev-evidence-analysis"]}${Q}`, current: null },
    ]);
    const conclude = panelTitled("What we can conclude now");
    const rows = Array.from(conclude.querySelectorAll("tbody tr"));
    expect(rows.map((r) => r.querySelector("th")?.textContent)).toEqual(["Session outcomes", "Connector availability", "Delivered energy", "Cause of interruption"]);
    expect(rows.map((r) => r.querySelectorAll("td")[0].textContent)).toEqual(["Full", "None", "Full", "None"]);
    expect(rows[0].textContent).toContain("1 completed · 0 observed aborts · 1 incomplete");
    expect(rows[1].textContent).toContain("Not assessed");
    expect(rows[2].textContent).toContain("30.000 kWh with complete meter coverage");
    expect(rows[3].textContent).toContain("Cause not established");
    expect(rows[1].textContent).toContain("Connector status reports");
    // q6 R3: null coverage shows the exact limitation, and both units keep their own words.
    const capDetails = conclude.querySelector('[data-disclosure="ev-site-capability-details"]') as HTMLElement;
    expect(capDetails.querySelector('[data-capability-detail="SESSION_OUTCOME"]')?.textContent).toContain("1800/1800 session-seconds covered");
    expect(capDetails.querySelector('[data-capability-detail="SITE_POWER_CONTEXT"]')?.textContent).toContain("3600/3900 s of selected window covered");
    expect(capDetails.querySelector('[data-capability-detail="POWER_CONSTRAINT"]')?.textContent).toContain(COVERAGE_NULL);
    expect(capDetails.textContent).not.toMatch(/\b0\/0\b|%/);
    // q6 R2: Mixed contact chip, detail, and the footer from checked_at.
    const sources = panelTitled("Data sources · data quality, not equipment condition");
    const srcRows = Array.from(sources.querySelectorAll("tbody tr"));
    expect(srcRows.map((r) => r.querySelector("th")?.firstChild?.textContent)).toEqual(["Connector 1", "Connector 2", "Site meter", "Billing system"]);
    expect(srcRows.map((r) => r.querySelectorAll("td")[0].textContent)).toEqual(["Mixed", "Recent", "Unknown", "Unknown"]);
    expect(srcRows.map((r) => r.querySelectorAll("td")[1].textContent)).toEqual(["Good", "Good", "No fact", "No fact"]);
    expect(srcRows.map((r) => r.querySelectorAll("td")[2].textContent)).toEqual(["Sessions and status", "Sessions and status", "No accepted report for this role", "No payment feed"]);
    expect(srcRows.map((r) => r.querySelectorAll("td")[3].textContent)).toEqual(["Sessions", "Sessions", "Site power", "Collections not assessed"]);
    expect(srcRows[0].querySelector(".ev-tone--amber")?.textContent).toBe("Mixed");
    expect(sources.querySelector("[data-ev-contact-checked]")?.textContent).toBe("Contact checked at 6 Oct 09:00 UTC");
    const c1 = sources.querySelector('[data-source-detail="CONNECTOR_1"]') as HTMLElement;
    expect(c1.textContent).toContain("Source contacts differ");
    expect(c1.querySelectorAll("[data-source-contact]")).toHaveLength(3);
    expect((sources.querySelector('[data-source-detail="SITE_METER"]') as HTMLElement).textContent).toContain("No source-specific record");
    expect(sources.textContent).not.toMatch(/healthy|faulty/i);
    // Panel 3 keeps three rows; an unfilled row is a named gap.
    const next = panelTitled("Most useful next evidence");
    expect(next.textContent).toContain("Recover the missing session end report");
    expect(next.textContent).toContain("No further evidence request recorded");
    expect(main().querySelector('[data-ev-notice="analysis"] a')?.getAttribute("href")).toBe(`${PATHS["ev-evidence-analysis"]}${RAW_Q}`);
    // Analysis tab: real accepted rows only, closed to three; the claim limit has its two exact blocks.
    cleanup();
    await renderAt(PATHS["ev-evidence-analysis"], client());
    expect(subtabs("Evidence sections").map((t) => [t.text, t.current])).toEqual([["Overview", null], ["Analysis", "page"]]);
    expect(strip()).toContain("5 accepted records");
    const headers = Array.from(panelTitled("Accepted records behind the conclusions").querySelectorAll("thead th")).map((th) => th.textContent);
    expect(headers).toEqual(["Source · reading", "Value", "Measured (EAT)", "Sent (UTC)", "Received (UTC)", "Record"]);
    const first = Array.from(panelTitled("Accepted records behind the conclusions").querySelectorAll("tbody tr")[0].children).map((c) => c.textContent);
    expect(first).toEqual(["Connector c1 · session_event", "Session started", "11:41:00", "Not recorded", "08:59:01", `Record ${id(101).slice(0, 8)} · No analysis link`]);
    const claim = panelTitled("How a claim limit is set");
    expect(claim.querySelector("[data-claim-prose]")?.textContent).toBe(
      "Each capability lists the readings it needs. Missing readings narrow the conclusion to covered periods; gaps are shown.Source reporting is not equipment condition.",
    );
    expect(claim.querySelector('[data-claim-rule="GROSS_TARIFF_SCENARIO"]')?.textContent).toContain("Gross tariff scenario: Full · 1800/1800 session-seconds covered");
  });

  it("unknown_pending_historical_are_not_current_zero", async () => {
    await renderAt(PATHS.ev, client({ empty: true, state: "UNKNOWN", consequence: null }));
    expectV69Panels("ev");
    expect(strip()).toContain("Evidence unknown");
    const values = Array.from(document.querySelectorAll("[data-ev-card] .v69-metric__value")).map((x) => x.textContent);
    expect(values).toEqual(["Unknown", "Not assessed", "Unknown", "Not assessed", "Unknown"]);
    expect(main().querySelector('[data-ev-card="sessions"]')?.textContent).toContain("Session outcomes not assessed");
    expect(panelTitled("Bounded money consequence").textContent).toContain("No gross tariff scenario assessed");
    expect(panelTitled("Needs attention").textContent).toContain("No recorded attention item for this window");
    expect(panelTitled("Next step").textContent).toContain("No recorded next step");
    expect(panelTitled("What happened on the service day").querySelectorAll(".v69-timeline > li")).toHaveLength(7);
    expect(main().textContent).not.toMatch(/\b0 completed|KES 0|\$0|0\.00/);

    cleanup();
    await renderAt(PATHS.ev, client({ state: "PENDING_RECOMPUTE", consequence: GUARD("PENDING_RECOMPUTE", "New evidence is being assessed. The previous result may change.") }));
    expectV69Panels("ev");
    expect(strip()).toContain("New evidence is being assessed");
    expect(panelTitled("Bounded money consequence").querySelector("[data-ev-money]")?.textContent).toBe("Withheld");
    expect(panelTitled("Needs attention").textContent).toContain("New evidence pending");
    expect(main().textContent).not.toContain("KES 8.33");

    cleanup();
    await renderAt(PATHS.ev, client({ state: "HISTORICAL", consequence: GUARD("HISTORICAL_CURRENT_CLAIM", "Historical scenario") }));
    expectV69Panels("ev");
    expect(strip()).toContain("Historical selection · 6 Oct 09:00 UTC");
    const money = panelTitled("Bounded money consequence");
    expect(money.querySelector("[data-ev-money]")?.textContent).toBe("Withheld");
    expect(money.textContent).toContain("Historical scenario");
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ state: "HISTORICAL", consequence: GUARD("HISTORICAL_CURRENT_CLAIM", "Historical scenario") }));
    expect(main().querySelector('[data-ev-fin-card="gross"] .v69-metric__value')?.textContent).toBe("Withheld");
    const history = main().querySelector(`[data-ev-history="${id(699)}"]`) as HTMLElement;
    expect(history.textContent).toContain("Historical scenario · revision 1 · KES 7.000000");
  });

  it("financial_tabs_and_price_gate", async () => {
    await renderAt(PATHS["ev-financials"], client());
    expectV69Panels("ev-financials");
    expect(subtabs("Financials sections")).toEqual([
      { text: "Overview", href: `${PATHS["ev-financials"]}${Q}`, current: "page" },
      { text: "Assumptions", href: `${PATHS["ev-assumptions"]}${Q}`, current: null },
    ]);
    expect(strip()).toContain("1 consequence line");
    expect(strip()).toContain("KES");
    const cards = Array.from(document.querySelectorAll("[data-ev-fin-card] .v69-metric__value")).map((x) => x.textContent);
    expect(cards).toEqual(["30.000 kWh", "KES 8.33", "Unknown", "Not recorded"]);
    const bridge = panelTitled("What happened → what it means in money");
    const row = Array.from(bridge.querySelectorAll('[data-bridge-row="scenario"] > *')).map((c) => c.textContent);
    expect(row).toEqual(["30.000 kWh delivered with complete coverage", "30.000 kWh × 0.2777 KES/kWh", "KES 8.33 gross estimate", "Scenario", "Metered with complete coverage", "Sessions ↗"]);
    expect(bridge.querySelector('[data-disclosure="ev-site-basis-details"]')?.textContent).toContain("KES 8.331000");
    const assumptionsPanel = panelTitled("Assumptions in use");
    expect(assumptionsPanel.textContent).toContain("0.2777 KES/kWh · Authored test tariff");
    expect(assumptionsPanel.textContent).toContain("No record");
    expect(within(assumptionsPanel).getByRole("link", { name: "Review assumptions" }).getAttribute("href")).toBe(`${PATHS["ev-assumptions"]}${Q}`);
    expect(panelTitled("Not included").querySelector(".prose")?.textContent).toBe("Lost sales, collections, margin, repair and warranty are not included in this gross tariff scenario.");

    // q6 R3: no complete gross coverage -> no `Metered with complete coverage`.
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ gross: NULL_COV }));
    const limited = panelTitled("What happened → what it means in money");
    expect(limited.textContent).not.toContain("Metered with complete coverage");
    expect(limited.textContent).toContain(`Gross scenario only. ${COVERAGE_NULL}`);

    // Pending: no current amount anywhere.
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ state: "PENDING_RECOMPUTE", consequence: GUARD("PENDING_RECOMPUTE", "New evidence is being assessed. The previous result may change.") }));
    expectV69Panels("ev-financials");
    expect(strip()).toContain("0 consequence lines");
    expect(main().querySelector('[data-ev-fin-card="gross"] .v69-metric__value')?.textContent).toBe("Withheld");
    expect(main().textContent).not.toContain("8.33");

    // No tariff, no consequence: one explanatory row, never zero.
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ consequence: null }));
    expect(Array.from(panelTitled("What happened → what it means in money").querySelectorAll('[data-bridge-row="none"] > *')).map((c) => c.textContent)).toEqual([
      "No eligible delivered-energy consequence", "Tariff not declared", "Unpriced", "Not assessed", "Not assessed", "No linked page for this item",
    ]);
    expect(strip()).toContain("Currency not declared");

    // Assumptions tab.
    cleanup();
    await renderAt(PATHS["ev-assumptions"], client());
    expectV69Panels("ev-assumptions");
    expect(subtabs("Financials sections").map((t) => [t.text, t.current])).toEqual([["Overview", null], ["Assumptions", "page"]]);
    const table = panelTitled("Financial assumptions");
    expect(Array.from(table.querySelectorAll("tbody tr")).map((r) => Array.from(r.children).map((c) => c.textContent))).toEqual([
      ["Tariff", "0.2777 KES/kWh · Authored test tariff", "Translating metered energy"],
      ["Billing / collections", "No record", "Cash collection not assessed"],
      ["Currency", "KES", "Scenario display currency"],
    ]);
    expect(main().querySelector('[data-ev-notice="assumptions"]')?.textContent).toBe("Changing the tariff re-translates the same metered energy. It does not change what was measured.");
    expect(money2("8.335")).toBe("8.34");
    expect(money2("8.331000")).toBe("8.33");
  });

  it("all_five_routes_keep_mock_panels_and_truthful_tabs", async () => {
    for (const [screenId, path] of Object.entries(PATHS)) {
      for (const [label, evSite] of [
        ["stocked", client()],
        ["empty", client({ empty: true, state: "UNKNOWN", consequence: null })],
        ["unpriced", client({ consequence: { ...GUARD("TARIFF_MISSING", "No published EV tariff covers the eligible delivery."), state: "UNPRICED" } })],
        ["refused", client({}, refused(503, "EV_READ_UNAVAILABLE"))],
      ] as const) {
        await renderAt(path, evSite);
        try {
          expectV69Panels(screenId);
        } catch (error) {
          throw new Error(`${screenId} ${label}: ${String(error)}`);
        }
        // +0 unavailable tabs: the route-local rows hold only live links.
        expect(main().querySelectorAll("nav.site-subtabs [data-tab-unavailable]")).toHaveLength(0);
        cleanup();
      }
    }
    // Refusals replace data inside the same frame with the typed copy.
    for (const [status, code, copy] of [
      [401, "UNAUTHENTICATED", "Sign in to view EV evidence."],
      [403, "SITE_SCOPE_FORBIDDEN", "You do not have access to this EV evidence."],
      [404, "SITE_NOT_FOUND", "This EV Site or record was not found."],
      [409, "EV_CURSOR_BASIS_CHANGED", "Selection changed. Reload this view."],
      [422, "EV_WINDOW_INVALID", "Choose a valid UTC start and end, up to 31 days."],
      [503, "EV_READ_UNAVAILABLE", "EV evidence is temporarily unavailable. Retry."],
    ] as const) {
      await renderAt(PATHS["ev-evidence"], client({}, refused(status, code)));
      expectV69Panels("ev-evidence");
      expect(panelTitled("What we can conclude now").textContent).toContain(copy);
      cleanup();
    }
    // q6 R1: the three objective labels plus the declared common hours.
    for (const [schedule, text] of [
      ["none", "Service window not declared"],
      ["outside", "No configured service hours overlap this selection"],
      ["vary", "Configured service hours vary by connector"],
      ["common", "Configured service hours 08:00–16:00 UTC"],
    ] as const) {
      await renderAt(PATHS.ev, client({ schedule }));
      expect(main().querySelector("[data-ev-objective]")?.textContent).toContain(text);
      cleanup();
    }
    // Stocked overview: chronology, chart legend, attention mapping, money and the static Recommendation entry.
    await renderAt(PATHS.ev, client());
    expectPlantedPanelRejected("ev");
    const day = panelTitled("What happened on the service day");
    expect(day.querySelectorAll(".v69-timeline > li")).toHaveLength(7);
    expect(day.textContent).toContain(`Session started · Record ${id(101).slice(0, 8)}`);
    expect(day.textContent).toContain("End record missing");
    expect(day.textContent).toContain("No accepted event");
    expect(day.textContent).not.toContain(id(450).slice(0, 8));
    expect(within(day).getByRole("link", { name: "Review sessions →" }).getAttribute("href")).toBe(`/sites/${CODE}/performance/sessions${Q}`);
    const power = panelTitled("Charging activity and site power");
    expect(power.textContent).toContain("Connector energy");
    expect(power.textContent).toContain("Site import");
    expect(power.textContent).toContain("Configured limit");
    expect(power.textContent).toContain("Power is operating context, not proof of charger condition or cause.");
    expect(power.textContent).toContain("Open single line diagram · Not available yet");
    expect(main().querySelector('[data-ev-card="power"]')?.textContent).toContain("60 kW observed peak3600/3900 s of selected window covered");
    expect(main().textContent).not.toMatch(/Healthy/);
    expect(panelTitled("Needs attention").textContent).toContain("End record missing");
    const money = panelTitled("Bounded money consequence");
    expect(money.querySelector("[data-ev-money]")?.textContent).toBe("KES 8.33 gross tariff estimate");
    expect(money.textContent).toContain("Gross tariff estimate for 30.000 kWh delivered with complete coverage. Not cash collected.");
    expect(within(money).getByRole("link", { name: "Open financial bridge →" }).getAttribute("href")).toBe(`${PATHS["ev-financials"]}${RAW_Q}`);
    const next = panelTitled("Next step");
    expect(next.textContent).toContain("Recover the missing session end report");
    const rec = next.querySelector('[data-link-unavailable="Review recommendation"]') as HTMLElement;
    expect(rec.getAttribute("aria-label")).toBe("Review recommendation, Not available yet");
    expect(rec.querySelector("a, button")).toBeNull();
    expect(strip()).toContain("Evidence limited");
    expect(strip()).toContain("Generated test data");
    fireEvent.click(within(main()).getByRole("link", { name: "Inspect evidence" }));
    await settledScreen();
    expectV69Panels("ev-evidence");
    expect(screen.getByRole("link", { name: "Analysis" }).getAttribute("href")).toBe(`${PATHS["ev-evidence-analysis"]}${Q}`);
  });
});
