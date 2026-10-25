import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
import koboDetail from "../../shell/__tests__/kobo-site-detail.json";

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
  noNote?: boolean;
  capList?: EvCapability[];
  reversedFaultIds?: boolean;
}
const PUBLICATION_NOTE = "Tariff published 2026-10-06 09:30 UTC; applied as a scenario to the selected delivery window. Evidence through 2026-10-06 09:00 UTC.";

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
    capabilities: o.empty ? [] : (o.capList ?? caps(o.gross)),
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
    evidence_id: id(n), source_label: "Connector c1 · session", role: "session_event", record_kind: "EV_SESSION_START",
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
        item(102, { source_label: "Connector c2 · session", record_kind: "EV_SESSION_END", value_display: "Session ended" }),
        item(103, { source_label: "Connector c2 · energy", role: "connector_meter_delta", record_kind: "EV_CONNECTOR_ENERGY", value_display: "1.250", unit: "kWh", interval_start: "2026-10-06T08:05:00.000000Z", interval_end: "2026-10-06T08:10:00.000000Z" }),
        item(104, { role: "site_import", record_kind: "EV_SITE_IMPORT", source_label: "Site meter · site import", value_display: "60", unit: "kW", interval_start: "2026-10-06T08:00:00.000000Z", interval_end: "2026-10-06T08:15:00.000000Z" }),
        item(105, { source_label: "Connector c1 · connector status", role: "connector_status", record_kind: "STATE", value_display: "Authorizing" }),
        item(450, { use: "EXCLUDED", reason: "SOURCE_UNVERIFIED", note: "Source or binding unverified for this record.", session_id: null }),
      ];
  return {
    ...env(o.state), items, total_count: items.length,
    excluded_records: o.empty ? [] : [{ evidence_id: UNVERIFIED_ID, record_kind: "EV_SESSION_START", reason: "SOURCE_UNVERIFIED" }],
    claim_rules: o.empty ? [] : (o.capList ?? caps(o.gross)).map((c) => ({ claim: c.claim, required_roles: c.required_roles, observed_roles: [], missing_roles: c.missing_roles, coverage: c.coverage, result: c.state, accepted_evidence_ids: c.accepted_evidence_ids, source_class: "REGISTERED_SIMULATION", known_at: KNOWN, limitation: c.limitation })),
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
  const tariff = o.consequence === null ? null : { revision_id: id(800), value: "0.2777", currency: "KES", unit: "currency/kWh", basis: "AUTHORED_ESTIMATE", valid_from: "2026-10-01T00:00:00.000000Z", valid_to: null, recorded_at: "2026-10-06T09:30:00.000000Z" };
  return {
    ...env(o.state), tariff, tariff_revision_count: tariff === null ? 0 : 1, publication_note: o.noNote === true ? null : PUBLICATION_NOTE,
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
    expect(rows.map((r) => r.querySelectorAll("td")[0].textContent)).toEqual(["Full", "None", "Full", "No interruption"]);
    expect(rows[0].textContent).toContain("1 completed · 0 observed aborts · 1 incomplete");
    expect(rows[1].textContent).toContain("Not assessed");
    expect(rows[2].textContent).toContain("30.000 kWh with complete meter coverage");
    // post-W6 W2-EV R258: with nothing interrupted the Cause row is not a limited claim.
    expect(rows[3].textContent).toContain("No interruption observed in this window");
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
    // post-W6 W2-EV R258: panel 3 lists only recorded requests, never a padded gap row.
    const next = panelTitled("Most useful next evidence");
    expect(next.textContent).toContain("Recover the missing session end report");
    expect(next.textContent).not.toContain("No further evidence request recorded");
    expect(main().querySelector('[data-ev-notice="analysis"] a')?.getAttribute("href")).toBe(`${PATHS["ev-evidence-analysis"]}${RAW_Q}`);
    // Analysis tab: real accepted rows only, closed to three; the claim limit has its two exact blocks.
    cleanup();
    await renderAt(PATHS["ev-evidence-analysis"], client());
    expect(subtabs("Evidence sections").map((t) => [t.text, t.current])).toEqual([["Overview", null], ["Analysis", "page"]]);
    expect(strip()).toContain("6 accepted records");
    const headers = Array.from(panelTitled("Accepted records behind the conclusions").querySelectorAll("thead th")).map((th) => th.textContent);
    expect(headers).toEqual(["Source · reading", "Value", "Measured (EAT)", "Sent (EAT)", "Received (EAT)", "Record"]);
    const first = Array.from(panelTitled("Accepted records behind the conclusions").querySelectorAll("tbody tr")[0].children).map((c) => c.textContent);
    expect(first).toEqual(["Connector c1 · session", "Session started", "11:41:00", "Not recorded", "11:59:01", `REC ${id(101)} · No analysis link`]);
    // Review r1 M3: plain first-cell and value words, never a role code or enum in a visible cell.
    const recordsPanel = panelTitled("Accepted records behind the conclusions");
    const closed = Array.from(recordsPanel.querySelectorAll("tbody tr"));
    expect(closed.map((r) => r.querySelector("th")?.textContent)).toEqual(["Connector c1 · session", "Connector c2 · session", "Connector c2 · energy"]);
    expect(closed.map((r) => r.querySelectorAll("td")[0].textContent)).toEqual(["Session started", "Session ended", "1.250 kWh"]);
    expect(recordsPanel.querySelector(`[data-record-detail="${id(105)}"]`)?.textContent).toContain("Connector c1 · connector status · Authorizing");
    expect(recordsPanel.textContent).not.toMatch(/connector_status|session_event|AUTHORIZING|EV_SESSION_START/);
    const claim = panelTitled("How a claim limit is set");
    expect(claim.querySelector("[data-claim-prose]")?.textContent).toBe(
      "Each capability lists the readings it needs. Missing readings narrow the conclusion to covered periods; gaps are shown.Source reporting is not equipment condition.",
    );
    expect(claim.querySelector('[data-claim-rule="GROSS_TARIFF_SCENARIO"]')?.textContent).toContain("Gross tariff scenario: Full · 1800/1800 session-seconds covered");
  });

  it("claim_details_use_plain_capability_and_chip_words", async () => {
    const all = [
      cap("SESSION_OUTCOME", "SUPPORTED", SESSION_COV),
      cap("SERVICE_STATE", "LIMITED"),
      cap("DELIVERED_ENERGY", "UNAVAILABLE", NULL_COV, ["connector_meter_delta"]),
      cap("FAULT_ASSOCIATION", "CONTRADICTORY"),
      cap("SITE_POWER_CONTEXT", "SUPPORTED", WINDOW_COV),
      cap("POWER_CONSTRAINT", "LIMITED"),
      cap("GROSS_TARIFF_SCENARIO", "UNAVAILABLE"),
    ];
    await renderAt(PATHS["ev-evidence-analysis"], client({ capList: all }));
    const claim = panelTitled("How a claim limit is set");
    const rules = Array.from(claim.querySelectorAll("[data-claim-rule]")).map((r) => (r.firstChild?.textContent ?? "").split(" · ")[0]);
    expect(rules).toEqual([
      "Session outcomes: Full", "Connector availability: Limited", "Delivered energy: None", "Cause of interruption: Contradictory",
      "Site power context: Full", "Site power constraint: Limited", "Gross tariff scenario: None",
    ]);
    expect(claim.textContent).not.toMatch(/SESSION_OUTCOME|SERVICE_STATE|SUPPORTED|UNAVAILABLE|CONTRADICTORY/);
    // Review r1 L2: four rows and four counts; the three other claims never change the chip or the count.
    cleanup();
    await renderAt(PATHS["ev-evidence"], client({ capList: all }));
    expect(panelTitled("What we can conclude now").querySelectorAll("tbody tr")).toHaveLength(4);
    expect(strip()).toContain("Evidence contradictory");
    expect(strip()).toContain("4 capabilities · 1 full · 1 limited · 1 none · 1 contradictory · no single score");
    cleanup();
    const supported = [
      cap("SESSION_OUTCOME", "SUPPORTED", SESSION_COV), cap("SERVICE_STATE", "SUPPORTED", SESSION_COV),
      cap("DELIVERED_ENERGY", "SUPPORTED", SESSION_COV), cap("FAULT_ASSOCIATION", "SUPPORTED", SESSION_COV),
      cap("SITE_POWER_CONTEXT", "UNAVAILABLE"), cap("POWER_CONSTRAINT", "LIMITED"), cap("GROSS_TARIFF_SCENARIO", "LIMITED"),
    ];
    await renderAt(PATHS["ev-evidence"], client({ capList: supported }));
    expect(strip()).toContain("Evidence supported");
    expect(strip()).toContain("4 capabilities · 4 full · 0 limited · 0 none · no single score");
    cleanup();
    await renderAt(PATHS["ev-evidence"], client());
    expect(strip()).toContain("4 capabilities · 2 full · 0 limited · 2 none · no single score");
  });

  it("same_instant_fault_precedes_abort_in_chronology", async () => {
    const same = "2026-10-06T08:16:00.000000Z";
    const reversed = {
      ...analysis(),
      items: [
        item(101),
        item(902, { record_kind: "EV_SESSION_ABORT", value_display: "Session aborted", source_time: same }),
        item(901, { role: "fault_event", record_kind: "EV_CONNECTOR_FAULT", value_display: "Connector fault", source_time: same }),
      ],
      total_count: 3,
    };
    await renderAt(PATHS.ev, { ...client(), getAnalysis: vi.fn(() => Promise.resolve(ok(reversed))) });
    const text = Array.from(panelTitled("What happened on the service day").querySelectorAll(".v69-timeline > li")).map((li) => li.textContent ?? "");
    const fault = text.findIndex((t) => t.includes("Connector fault"));
    const abort = text.findIndex((t) => t.includes("Session aborted"));
    expect(fault).toBeGreaterThanOrEqual(0);
    expect(fault).toBeLessThan(abort);
    // Analysis keeps its served (source_time, evidence_id) order.
    cleanup();
    const served = { ...reversed, items: [reversed.items[0], reversed.items[2], reversed.items[1]] };
    await renderAt(PATHS["ev-evidence-analysis"], { ...client(), getAnalysis: vi.fn(() => Promise.resolve(ok(served))) });
    const rows = Array.from(panelTitled("Accepted records behind the conclusions").querySelectorAll("tbody tr")).map((r) => r.textContent ?? "");
    expect(rows[1]).toContain("Connector fault");
    expect(rows[2]).toContain("Session aborted");
  });

  it("unknown_pending_historical_are_not_current_zero", async () => {
    await renderAt(PATHS.ev, client({ empty: true, state: "UNKNOWN", consequence: null }));
    expectV69Panels("ev");
    expect(strip()).toContain("Evidence unknown");
    const values = Array.from(document.querySelectorAll("[data-ev-card] .v69-metric__value")).map((x) => x.textContent);
    expect(values).toEqual(["Unknown", "Not summarised here", "Unknown", "Not summarised here", "Unknown"]);
    expect(main().querySelector('[data-ev-card="sessions"]')?.textContent).toContain("Session outcomes not assessed");
    expect(panelTitled("Bounded money consequence").textContent).toContain("No gross tariff scenario assessed");
    expect(panelTitled("Needs attention").textContent).toContain("No recorded attention item for this window");
    expect(panelTitled("Next step").textContent).toContain("No recorded next step");
    // post-W6 W2-EV R283: no padding slots; no accepted event says so once.
    expect(panelTitled("What happened on the service day").querySelectorAll(".v69-timeline > li")).toHaveLength(0);
    expect(panelTitled("What happened on the service day").querySelector("[data-ev-day-empty]")).not.toBeNull();
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
      { text: "Scenarios", href: `/sites/${CODE}/ev/financials/scenarios${Q}`, current: null },
    ]);
    expect(strip()).toContain("1 consequence line");
    expect(strip()).toContain("KES");
    const cards = Array.from(document.querySelectorAll("[data-ev-fin-card] .v69-metric__value")).map((x) => x.textContent);
    expect(cards).toEqual(["30.000 kWh", "KES 8.33", "Unknown", "Not recorded"]);
    const bridge = panelTitled("What happened → what it means in money");
    const row = Array.from(bridge.querySelectorAll('[data-bridge-row="scenario"] > *')).map((c) => c.textContent);
    expect(row).toEqual(["30.000 kWh delivered with complete coverage", "30.000 kWh × 0.2777 KES/kWh", "KES 8.33 gross estimate", "Scenario", "Metered with complete coverage", "Energy ↗"]);
    expect(bridge.querySelector('[data-disclosure="ev-site-basis-details"]')?.textContent).toContain("KES 8.331000");
    const assumptionsPanel = panelTitled("Assumptions in use");
    expect(assumptionsPanel.textContent).toContain("0.2777 KES/kWh · Authored estimate");
    expect(assumptionsPanel.textContent).not.toContain("AUTHORED_ESTIMATE");
    // Review r1 M4: both clocks sit in the Assumption details, never as a claim the tariff was known at known_at.
    const finDetails = assumptionsPanel.querySelector('[data-disclosure="ev-site-assumption-details"]') as HTMLElement;
    expect(finDetails.textContent).toContain(PUBLICATION_NOTE);
    expect(finDetails.textContent).toContain("Authored estimate");
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
    // W2-F M5: the displayed withheld scenario row is counted (unpriced context), never a priced revision.
    expect(strip()).toContain("1 consequence line");
    expect(strip()).toContain("Displayed rows include unpriced context");
    expect(main().querySelector('[data-ev-fin-card="gross"] .v69-metric__value')?.textContent).toBe("Withheld");
    expect(main().textContent).not.toContain("8.33");

    // No tariff, no consequence: one explanatory row, never zero.
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ consequence: null }));
    expect(Array.from(panelTitled("What happened → what it means in money").querySelectorAll('[data-bridge-row="none"] > *')).map((c) => c.textContent)).toEqual([
      "No eligible delivered-energy consequence", "Tariff not declared", "No gross tariff scenario assessed", "Not assessed", "Not assessed", "No linked page for this item",
    ]);
    expect(strip()).toContain("Currency not declared");
    expect(main().querySelector('[data-ev-fin-card="gross"] .v69-metric__value')?.textContent).toBe("No gross tariff scenario assessed");

    // Review r1 L1: a stored UNPRICED consequence still says Unpriced; a null-note fixture shows no sentence.
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ noNote: true, consequence: { ...GUARD("TARIFF_MISSING", "No published EV tariff covers the eligible delivery."), state: "UNPRICED" } }));
    expect(main().querySelector('[data-ev-fin-card="gross"] .v69-metric__value')?.textContent).toBe("Unpriced");
    expect(panelTitled("What happened → what it means in money").querySelector('[data-bridge-row="scenario"]')?.textContent).toContain("Unpriced");
    expect(main().querySelector('[data-disclosure="ev-site-assumption-details"]')?.textContent ?? "").not.toContain("Tariff published");

    // Assumptions tab.
    cleanup();
    await renderAt(PATHS["ev-assumptions"], client());
    expectV69Panels("ev-assumptions");
    expect(subtabs("Financials sections").map((t) => [t.text, t.current])).toEqual([["Overview", null], ["Assumptions", "page"], ["Scenarios", null]]);
    const table = panelTitled("Financial assumptions");
    expect(Array.from(table.querySelectorAll("tbody tr")).map((r) => Array.from(r.children).map((c) => c.textContent))).toEqual([
      ["Tariff", "0.2777 KES/kWh · Authored estimate", "Translating metered energy"],
      ["Billing / collections", "No recordMOCK DEVIATION D4 (R421)", "Cash collection not assessed"],
      ["Currency", "KES", "Scenario display currency"],
    ]);
    expect(main().querySelector('[data-ev-notice="assumptions"]')?.textContent).toBe("Changing the tariff re-translates the same metered energy. It does not change what was measured.");
    expect(table.textContent).not.toContain("AUTHORED_ESTIMATE");
    expect((main().querySelector('[data-disclosure="ev-site-assumption-details"]') as HTMLElement).textContent).toContain(PUBLICATION_NOTE);
    expect(main().querySelector("[data-ev-publication-note]")?.textContent).toBe(PUBLICATION_NOTE);
    cleanup();
    await renderAt(PATHS["ev-assumptions"], client({ noNote: true }));
    expect(main().querySelector("[data-ev-publication-note]")).toBeNull();
    expect(main().textContent).not.toContain("Tariff published");
    // Review r1 M2: half even on the absolute value, every discarded digit inspected.
    expect(money2("8.325")).toBe("8.32");
    expect(money2("8.335")).toBe("8.34");
    expect(money2("8.32500001")).toBe("8.33");
    expect(money2("-8.325")).toBe("-8.32");
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
        // W5-03b E6: no EV subtab row carries an unavailable slot; the financial rows link the live Scenarios route.
        const financialRoute = screenId === "ev-financials" || screenId === "ev-assumptions";
        expect(main().querySelectorAll("nav.site-subtabs [data-tab-unavailable]")).toHaveLength(0);
        expect(main().querySelectorAll('nav.site-subtabs [data-ev-subtab="scenarios"]')).toHaveLength(financialRoute ? 1 : 0);
        cleanup();
      }
    }
    // Refusals replace data inside the same frame with the typed copy.
    for (const [status, code, copy] of [
      [401, "UNAUTHENTICATED", "Sign in to view EV evidence."],
      [403, "SITE_SCOPE_FORBIDDEN", "You do not have access to this EV evidence."],
      [404, "SITE_NOT_FOUND", "This EV Site or record was not found."],
      [409, "EV_CURSOR_BASIS_CHANGED", "Selection changed. Reload this view."],
      [422, "EV_WINDOW_INVALID", "The selected window needs both a start and an end, with the start before the end."],
      [422, "EV_WINDOW_TOO_LONG", "The selected window is longer than 31 days."],
      [422, "EV_SOMETHING_ELSE", "The selected window is invalid."],
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
    expect(day.querySelectorAll(".v69-timeline > li")).toHaveLength(3);
    expect(day.textContent).toContain(`Session started · REC ${id(101)}`);
    expect(day.textContent).toContain("End record missing");
    expect(day.textContent).not.toContain("No accepted event");
    expect(day.textContent).not.toContain(id(450).slice(0, 8));
    expect(within(day).getByRole("link", { name: "Review sessions →" }).getAttribute("href")).toBe(`/sites/${CODE}/performance/sessions${Q}`);
    const power = panelTitled("Charging activity and site power");
    expect(power.textContent).toContain("Connector energy");
    expect(power.textContent).toContain("Site import");
    expect(power.textContent).toContain("Configured limit");
    expect(power.textContent).toContain("Power is operating context, not proof of charger condition or cause.");
    // W2-F M8: the built Foundation SLD is a live link (exact proof in `w2f_overview_sld_link_is_real`).
    expect(within(power).getByRole("link", { name: "Single line diagram →" })).toBeTruthy();
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

describe("W3-01 r1 M2: selected versus pending source on the EV Site reads", () => {
  const SEL = { classification: "REGISTERED_SIMULATION", state: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [], basis_sha256: `sha256:${BASIS}`, reasons: [] };
  const PENDING = { ...SEL, classification: "MIXED", state: "MIXED", basis_sha256: null };
  const siblings = (selected: typeof SEL | null) => ({ source_provenance: PENDING, selected_source_provenance: selected, pending_source_provenance: PENDING });
  const withEnv = (extra: Record<string, unknown>): EvSiteClient => {
    const base = client();
    const wrap = <T extends EvEnvelope,>(read: () => Promise<EvRead<T>>) => vi.fn(() => read().then((r) => (r.status === "loaded" ? ok({ ...r.value, ...extra, currentness: { ...r.value.currentness, state: "PENDING_RECOMPUTE" } }) : r)));
    return {
      ...base,
      getOverview: wrap(base.getOverview as never) as never,
      getEvidence: wrap(base.getEvidence as never) as never,
      getAnalysis: wrap(base.getAnalysis as never) as never,
      getFinancials: wrap(base.getFinancials as never) as never,
      getAssumptions: wrap(base.getAssumptions as never) as never,
    };
  };

  it("selected_claim_rules_and_money_lines_ignore_pending_class", async () => {
    await renderAt(PATHS["ev-evidence"], withEnv(siblings(SEL)));
    const details = main().querySelector('[data-disclosure="ev-site-capability-details"]') as HTMLElement;
    expect(details.textContent).toContain("source REGISTERED_SIMULATION");
    expect(details.textContent).not.toContain("source MIXED");
    cleanup();
    await renderAt(PATHS["ev-financials"], withEnv(siblings(SEL)));
    expect(main().textContent).toContain("source REGISTERED_SIMULATION");
    expect(main().textContent).not.toContain("source MIXED");
    cleanup();
    await renderAt(PATHS["ev-assumptions"], withEnv(siblings(SEL)));
    expect(main().textContent).toContain("Generated test data");
    cleanup();
    // no selected assessment: Unknown, and no selected-result badge; the pending class is never a claim result
    await renderAt(PATHS["ev-evidence"], withEnv(siblings(null)));
    const none = main().querySelector('[data-disclosure="ev-site-capability-details"]') as HTMLElement;
    expect(none.textContent).toContain("source Unknown");
    expect(none.textContent).not.toContain("source MIXED");
    cleanup();
    await renderAt(PATHS["ev-assumptions"], withEnv(siblings(null)));
    expect(main().textContent).not.toContain("Generated test data");
  });

  it("current_accepted_record_line_names_pending_class", async () => {
    await renderAt(PATHS["ev-evidence-analysis"], withEnv(siblings(SEL)));
    const row = main().querySelector(`[data-record-detail="${UNVERIFIED_ID}"]`) as HTMLElement;
    expect(row.textContent).toContain("current accepted evidence source MIXED");
    expect(row.textContent).not.toContain("source REGISTERED_SIMULATION");
    const rule = main().querySelector("[data-claim-rule]") as HTMLElement;
    expect(rule.textContent).toContain("source REGISTERED_SIMULATION");
  });
});

/*
 * W2-F unit 3 (`.agent/W2-F-build-spec.md` ledger M8/M9/M10, closure B2, S9, N1): the Overview SLD link, the status and
 * confidence chips, and full timeline record IDs.
 */
describe("W2-F: EV Overview link, status and record IDs", () => {
  const SLD = `/sites/${CODE}/foundation/sld`;
  const CUTOFF_NOTE = "Opens configuration at window end; evidence cutoff is not carried.";
  const SELECTED_TO = "2026-10-06T09:04:00.000000Z";
  const withWindowEnd = (o: EvOverviewRead): EvOverviewRead => ({ ...o, window: { ...o.window, to: SELECTED_TO } });
  const sldLink = () => document.querySelector("[data-ev-sld-link]") as HTMLElement;
  const chips = () => Array.from(document.querySelectorAll(".status-strip .ev-site-chip")).map((c) => c.textContent);

  it("w2f_overview_sld_link_is_real", async () => {
    // Selected: the selected window end, the exact Site code and the cutoff-loss label.
    await renderAt(PATHS.ev, { ...client(), getOverview: vi.fn(() => Promise.resolve(ok(withWindowEnd(overview())))) });
    const link = within(sldLink()).getByRole("link", { name: "Single line diagram →" });
    expect(link.getAttribute("href")).toBe(`${SLD}?at=${encodeURIComponent(SELECTED_TO)}`);
    expect(sldLink().querySelector("[data-ev-sld-cutoff-note]")?.textContent).toBe(CUTOFF_NOTE);
    expect(sldLink().textContent).not.toContain("Not available yet");
    fireEvent.click(link);
    await settledScreen();
    expect(screen.getByRole("link", { name: "Single line diagram", current: "page" }).getAttribute("href")).toContain(`${SLD}?at=`);
    cleanup();
    // Refused: the requested window end.
    await renderAt(PATHS.ev, client({}, refused(503, "EV_SITE_UNAVAILABLE")));
    expect(within(sldLink()).getByRole("link", { name: "Single line diagram →" }).getAttribute("href")).toBe(`${SLD}?at=${encodeURIComponent(TO)}`);
    expect(sldLink().textContent).toContain(CUTOFF_NOTE);
    cleanup();
    // No selected version: the requested window end, not the read's.
    const none = withWindowEnd(overview({ empty: true, state: "UNKNOWN", consequence: null }));
    await renderAt(PATHS.ev, { ...client({ empty: true, state: "UNKNOWN", consequence: null }), getOverview: vi.fn(() => Promise.resolve(ok(none))) });
    expect(within(sldLink()).getByRole("link", { name: "Single line diagram →" }).getAttribute("href")).toBe(`${SLD}?at=${encodeURIComponent(TO)}`);
    cleanup();
    // No requested window end on a refusal: an honest null target, never a current SLD.
    render(
      <MemoryRouter initialEntries={[`${PATHS.ev}?from=${encodeURIComponent(FROM)}`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evSite={client({}, refused(422, "INVALID_WINDOW"))} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(sldLink().querySelector("a")).toBeNull();
    expect(sldLink().textContent).toBe("No linked page for this item");
  });

  it("w2f_overview_status_confidence", async () => {
    const vector = async (o: EvOverviewRead, state = "CURRENT") => {
      cleanup();
      await renderAt(PATHS.ev, { ...client({ state }), getOverview: vi.fn(() => Promise.resolve(ok(o))) });
      return chips().slice(0, 2);
    };
    const base = overview();
    // Interrupted, selected BOUNDED with an observed abort -> Needs attention / Limited.
    const interrupted = { ...base, status: { ...base.status, claim_level: "BOUNDED" }, denominator: { ...base.denominator, observed_abort: 1 } };
    expect(await vector(interrupted)).toEqual(["Needs attention", "Confidence: Limited"]);
    // An observed complete abort -> Needs attention / Bounded.
    expect(await vector({ ...interrupted, status: { ...base.status, claim_level: "OBSERVED" } })).toEqual(["Needs attention", "Confidence: Bounded"]);
    // A selected Finding alone also needs attention.
    expect(await vector({ ...base, status: { ...base.status, claim_level: "OBSERVED" }, findings: { ...base.findings, count: 1 } })).toEqual(["Needs attention", "Confidence: Bounded"]);
    // Complete, nothing aborted -> Sessions observed / Bounded.
    expect(await vector({ ...base, status: { ...base.status, claim_level: "OBSERVED" } })).toEqual(["Sessions observed", "Confidence: Bounded"]);
    expect(await vector({ ...base, status: { ...base.status, state: "NO_SESSIONS_OBSERVED", claim_level: "OBSERVED" } })).toEqual(["No sessions observed", "Confidence: Bounded"]);
    // Contradiction outranks pending and attention.
    const contradictory = { ...interrupted, status: { ...base.status, state: "CONTRADICTORY", claim_level: "CONTRADICTORY" } };
    expect(await vector(contradictory)).toEqual(["Records disagree", "Confidence: Unknown"]);
    // Pending keeps the selected level stored but shows Unknown confidence.
    const pending = { ...overview({ state: "PENDING_RECOMPUTE" }), status: { ...base.status, claim_level: "OBSERVED" }, denominator: { ...base.denominator, observed_abort: 1 } };
    expect(await vector(pending, "PENDING_RECOMPUTE")).toEqual(["Evidence pending", "Confidence: Unknown"]);
    // No selection.
    expect(await vector({ ...overview({ empty: true, state: "UNKNOWN" }), status: { ...base.status, state: "UNKNOWN", claim_level: "OBSERVED" } }, "UNKNOWN")).toEqual(["Unknown", "Confidence: Unknown"]);
    // Source-provenance badges are retained beside the chips.
    expect(strip()).toContain("Generated test data");
    cleanup();
    // Refused.
    await renderAt(PATHS.ev, client({}, refused(503, "EV_SITE_UNAVAILABLE")));
    expect(chips()).toEqual(["Unknown", "Confidence: Unknown"]);
  });

  it("w2f_timeline_analysis_ids_distinct", async () => {
    const a = "00000502-0000-4000-8000-000000000001";
    const b = "00000502-0000-4000-8000-000000000002";
    const read = { ...analysis(), items: [item(101, { evidence_id: a }), item(102, { evidence_id: b, value_display: "Session ended", record_kind: "EV_SESSION_END" })], total_count: 2 };
    await renderAt(PATHS.ev, { ...client(), getAnalysis: vi.fn(() => Promise.resolve(ok(read))) });
    const day = panelTitled("What happened on the service day");
    const labels = Array.from(day.querySelectorAll("code.ev-site-id")).map((c) => ({ text: c.textContent, aria: c.getAttribute("aria-label") }));
    expect(labels).toEqual([
      { text: `REC ${a}`, aria: `Record ${a}` },
      { text: `REC ${b}`, aria: `Record ${b}` },
    ]);
    expect(new Set(labels.map((l) => l.text)).size).toBe(2);
    cleanup();
    // EV Analysis: the same full stored IDs in the Record column.
    await renderAt(PATHS["ev-evidence-analysis"], { ...client(), getAnalysis: vi.fn(() => Promise.resolve(ok(read))) });
    const rows = Array.from(panelTitled("Accepted records behind the conclusions").querySelectorAll("tbody code.ev-site-id"));
    expect(rows.map((c) => ({ text: c.textContent, aria: c.getAttribute("aria-label") }))).toEqual([
      { text: `REC ${a}`, aria: `Record ${a}` },
      { text: `REC ${b}`, aria: `Record ${b}` },
    ]);
  });

  // W2-F M5/N9: the chip counts exactly the displayed bridge rows from the selected responses.
  it("w2f_consequence_chip_equals_bridge_rows", async () => {
    const counted = () => panelTitled("What happened → what it means in money").querySelectorAll('tbody [data-bridge-row]:not([data-bridge-row="none"])');
    const chip = () => document.querySelector("[data-ev-line-count]");
    // Empty: no consequence, no Finding -> 0 rows / 0 lines (the explanatory `none` row is not a consequence line).
    await renderAt(PATHS["ev-financials"], client({ consequence: null }));
    expect(counted()).toHaveLength(0);
    expect(chip()?.textContent).toBe("0 consequence lines");
    expect(document.querySelector('[data-bridge-row="none"]')).not.toBeNull();
    cleanup();
    // EV interrupted: the scenario plus the interruption and repair context rows -> 3 / 3.
    const interrupted = { ...overview(), findings: { ...overview().findings, count: 1 } };
    await renderAt(PATHS["ev-financials"], { ...client(), getOverview: vi.fn(() => Promise.resolve(ok(interrupted))) });
    expect(Array.from(counted()).map((r) => r.getAttribute("data-bridge-row"))).toEqual(["scenario", "interruption", "repair"]);
    expect(chip()?.getAttribute("data-ev-line-count")).toBe(String(counted().length));
    expect(chip()?.textContent).toBe("3 consequence lines");
    expect(strip()).toContain("Displayed rows include unpriced context");
    cleanup();
    // Refused: no count is claimed at all, never a zero.
    await renderAt(PATHS["ev-financials"], client({}, refused(503, "EV_SITE_UNAVAILABLE")));
    expect(chip()).toBeNull();
    expect(main().textContent).not.toMatch(/\d+ consequence lines?/);
  });

  // W5-03b E6 (replaces W2-F M12): the mock's Scenarios entry on both financial screens is a live link to the route.
  it("w503b_ev_scenarios_tab_live", async () => {
    for (const key of ["ev-financials", "ev-assumptions"] as const) {
      await renderAt(PATHS[key], client());
      const nav = document.querySelector('nav[aria-label="Financials sections"]') as HTMLElement;
      expect(Array.from(nav.querySelectorAll("li")).map((li) => li.textContent)).toEqual(["Overview", "Assumptions", "Scenarios"]);
      expect(nav.querySelector("[data-tab-unavailable]")).toBeNull();
      const live = nav.querySelector('[data-ev-subtab="scenarios"]') as HTMLAnchorElement;
      expect(live.getAttribute("href")).toBe(`/sites/${CODE}/ev/financials/scenarios${Q}`);
      expect(live.hasAttribute("aria-current")).toBe(false);
      expect(nav.querySelectorAll("a")).toHaveLength(3);
      expect(nav.querySelector('[aria-current="page"]')?.textContent).toBe(key === "ev-financials" ? "Overview" : "Assumptions");
      cleanup();
    }
  });

  // W2-F S10/M11: one missing-basis renderer for the Evidence table and its request details.
  it("w2f_limited_rows_name_missing_basis", async () => {
    const SERVICE_NO_ROLE = cap("SERVICE_STATE", "LIMITED", NULL_COV, [], null);
    const FAULT_NO_ROLE = cap("FAULT_ASSOCIATION", "LIMITED", NULL_COV, [], "Cause is not established.");
    const ENERGY_GAP = cap("DELIVERED_ENERGY", "LIMITED", WINDOW_COV, [], null);
    const SESSIONS_DISAGREE = cap("SESSION_OUTCOME", "CONTRADICTORY", SESSION_COV, ["session_event"]);
    const capList = [SESSIONS_DISAGREE, SERVICE_NO_ROLE, ENERGY_GAP, FAULT_NO_ROLE, cap("GROSS_TARIFF_SCENARIO", "SUPPORTED", SESSION_COV)];
    await renderAt(PATHS["ev-evidence"], client({ capList }));
    const cell = (key: string) => document.querySelector(`[data-ev-missing-basis="${key}"]`)?.textContent;
    expect(cell("sessions")).toBe("Accepted records disagree");
    expect(cell("availability")).toBe("Connector status coverage not assessed");
    // Limited, no missing role, no limitation: the exact selected coverage, no invented one-hour gap.
    expect(cell("energy")).toBe("3600/3900 s of selected window covered");
    expect(cell("cause")).toBe("Charger diagnostics and vehicle request not recorded");
    expect(main().textContent).not.toContain("No required role missing");
    expect(main().textContent).not.toMatch(/one hour|1 h gap/i);
    const details = Array.from(document.querySelectorAll("[data-ev-request-basis]")).map((li) => [li.getAttribute("data-ev-request-basis"), li.textContent?.split(" · ")[0]]);
    expect(details).toEqual([
      ["SESSION_OUTCOME", "Accepted records disagree"],
      ["SERVICE_STATE", "Connector status coverage not assessed"],
      ["DELIVERED_ENERGY", "3600/3900 s of selected window covered"],
      ["FAULT_ASSOCIATION", "Charger diagnostics and vehicle request not recorded"],
    ]);
    cleanup();
    // Limited with missing roles names the roles; Full with no limitation is the only `Nothing required`.
    await renderAt(PATHS["ev-evidence"], client({ capList: [cap("SESSION_OUTCOME", "SUPPORTED", SESSION_COV), cap("SERVICE_STATE", "LIMITED", NULL_COV, ["connector_status"], "Availability is not assessed.")] }));
    expect(cell("sessions")).toBe("Nothing required for this claim");
    expect(cell("availability")).not.toBe("Connector status coverage not assessed");
    expect(cell("availability")).not.toContain("Nothing required");
    expect(cell("energy")).toBe("Not assessed");
  });
});

describe("post-W6 W2-EV (Q14/Q23): EV Site main tabs and the bare Site home", () => {
  const tabHrefs = () =>
    Object.fromEntries(Array.from(document.querySelectorAll('nav[aria-label="Site sections"] a')).map((a) => [a.textContent ?? "", a.getAttribute("href")]));

  it("every EV Site screen's main tabs open EV pages at the loaded read's window", async () => {
    for (const path of Object.values(PATHS)) {
      await renderAt(path, client());
      await waitFor(() => expect(tabHrefs().Overview, path).toBe(`/sites/${CODE}/ev${Q}`));
      const tabs = tabHrefs();
      expect(tabs.Evidence, path).toBe(`/sites/${CODE}/ev/evidence${Q}`);
      expect(tabs.Financials, path).toBe(`/sites/${CODE}/ev/financials${Q}`);
      expect(tabs.Foundation, path).toBe(`/sites/${CODE}/foundation${Q}`);
      cleanup();
    }
  });

  it("a refused read carries no window on the main tabs", async () => {
    for (const path of Object.values(PATHS)) {
      await renderAt(path, client({}, refused(503, "EV_READ_UNAVAILABLE")));
      const tabs = tabHrefs();
      expect(tabs.Overview, path).toBe(`/sites/${CODE}/ev`);
      expect(Object.values(tabs).some((h) => (h ?? "").includes("?")), path).toBe(false);
      cleanup();
    }
  });

  it("bare /sites/:id opens the EV Overview for an EV Site, keeping the query", async () => {
    const evSite = client();
    render(
      <MemoryRouter initialEntries={[`/sites/${CODE}${RAW_Q}`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evSite={evSite} />
      </MemoryRouter>,
    );
    await waitFor(() => expect(main().getAttribute("data-ev-site-view")).toBe("ev"));
    await settledScreen();
    expect(evSite.getOverview).toHaveBeenCalledWith(CODE, { from: FROM, to: TO, known_at: KNOWN });
  });

  it("bare /sites/:id keeps the mini Overview for a MINIGRID Site", async () => {
    const mini = { ...(koboDetail as unknown as SiteDetailReadModel), site_id: "MINI-001" } as SiteDetailReadModel;
    const miniDetail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: mini }) };
    const evSite = client();
    render(
      <MemoryRouter initialEntries={["/sites/MINI-001"]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={miniDetail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evSite={evSite} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Kalangala mini-grid");
    expect(main().getAttribute("data-ev-site-view")).toBeNull();
    expect(evSite.getOverview).not.toHaveBeenCalled();
    expect(tabHrefs().Overview).toBe("/sites/MINI-001");
  });
});

describe("post-W6 W2-EV U3: EV Site refusals, chronology, money links, cards, evidence and timezone", () => {
  const WINDOW_INVALID = "The selected window needs both a start and an end, with the start before the end.";
  const TOO_LONG = "The selected window is longer than 31 days.";
  const gaps = () => Array.from(main().querySelectorAll("[data-panel-gap]")).map((g) => g.textContent ?? "");
  const withAnalysis = (items: EvAnalysisItem[]): EvSiteClient => {
    const c = client();
    c.getAnalysis = vi.fn(() => Promise.resolve(ok({ ...analysis(), items, total_count: items.length, next_cursor: null })));
    return c;
  };

  it("R284: a window refusal keeps the strip and tile labels, one in-panel sentence and a technical disclosure", async () => {
    for (const [code, copy] of [["EV_WINDOW_INVALID", WINDOW_INVALID], ["EV_WINDOW_TOO_LONG", TOO_LONG]] as const) {
      await renderAt(PATHS.ev, client({}, refused(422, code)));
      expectV69Panels("ev");
      expect(strip()).toContain("Window cannot be read");
      expect(Array.from(main().querySelectorAll("[data-ev-refused-card]")).map((c) => c.getAttribute("data-ev-refused-card"))).toEqual([
        "Session service", "Availability", "Site power", "Charger condition", "Evidence",
      ]);
      expect(Array.from(main().querySelectorAll("[data-ev-refused-card] .v69-metric__value")).every((v) => v.textContent === "Not assessed")).toBe(true);
      expect(gaps().filter((g) => g === copy)).toHaveLength(1);
      expect(main().querySelector('[data-disclosure="ev-refusal-detail"]')?.textContent).toContain(code);
      expect(main().querySelector("[data-ev-window-requested]")).toBeNull();
      expect(main().querySelector("[data-page-refusal]")).toBeNull();
      cleanup();
    }
    for (const path of [PATHS["ev-evidence"], PATHS["ev-evidence-analysis"], PATHS["ev-financials"], PATHS["ev-assumptions"]]) {
      await renderAt(path, client({}, refused(422, "EV_WINDOW_TOO_LONG")));
      expect(strip(), path).toContain("Window cannot be read");
      expect(gaps().filter((g) => g === TOO_LONG), path).toHaveLength(1);
      cleanup();
    }
    await renderAt(PATHS["ev-financials"], client({}, refused(422, "EV_WINDOW_INVALID")));
    expect(main().querySelectorAll("[data-ev-refused-card]")).toHaveLength(4);
  });

  it("R284: a non-window refusal keeps its own wording and the requested-window line, never a window title", async () => {
    await renderAt(PATHS.ev, client({}, refused(403, "SITE_SCOPE_FORBIDDEN")));
    expect(strip()).not.toContain("Window cannot be read");
    expect(main().querySelector("[data-ev-window-requested]")?.textContent).toContain("6 Oct 08:00");
    expect(gaps().filter((g) => g === "You do not have access to this EV evidence.")).toHaveLength(1);
    expect(main().querySelectorAll("[data-ev-refused-card]")).toHaveLength(5);
  });

  it("R283 (Q10): the chronology shows only accepted events: none, one and eight", async () => {
    await renderAt(PATHS.ev, withAnalysis([]));
    let day = panelTitled("What happened on the service day");
    // The stocked overview has an incomplete session, so its end gap is the only entry; no padding slot.
    expect(Array.from(day.querySelectorAll(".v69-timeline > li")).map((li) => li.textContent ?? "").filter((t) => !t.includes("End record missing"))).toEqual([]);
    expect(day.textContent).not.toContain("No accepted event ·");
    cleanup();
    await renderAt(PATHS.ev, withAnalysis([item(101)]));
    day = panelTitled("What happened on the service day");
    expect(day.querySelectorAll(".v69-timeline > li").length).toBeLessThanOrEqual(2);
    expect(day.textContent).not.toContain("No accepted event");
    cleanup();
    await renderAt(PATHS.ev, withAnalysis(Array.from({ length: 8 }, (_, k) => item(110 + k))));
    day = panelTitled("What happened on the service day");
    expect(Array.from(day.querySelectorAll(".v69-timeline > li")).filter((li) => (li.textContent ?? "").includes("REC "))).toHaveLength(8);
  });

  it("R285 (Q12) and R286 fix, D4 R421 (Q13): Energy source link only when estimated; billing chips follow the wire", async () => {
    await renderAt(PATHS["ev-financials"], client());
    const source = main().querySelector('[data-ev-bridge-source="scenario"]') as HTMLElement;
    expect(source.textContent).toBe("Energy ↗");
    expect(source.getAttribute("href")).toBe(`/sites/${CODE}/performance/energy${Q}`);
    expect(panelTitled("Assumptions in use").querySelector(".ev-site-chip")).not.toBeNull();
    cleanup();
    await renderAt(PATHS["ev-financials"], client({ consequence: { ...GUARD("TARIFF_MISSING", "No published EV tariff covers the eligible delivery."), state: "UNPRICED" } }));
    expect(main().querySelector('a[data-ev-bridge-source="scenario"]')).toBeNull();
    cleanup();
    for (const [state, word] of [["NO_RECORD", "No record"], ["NOT_CONNECTED", "Not connected"]] as const) {
      const c = client();
      c.getAssumptions = vi.fn(() => Promise.resolve(ok({ ...assumptions(), billing_state: state })));
      await renderAt(PATHS["ev-assumptions"], c);
      const cell = main().querySelector('[data-assumption-row="billing"] td') as HTMLElement;
      expect(cell.querySelector(".ev-site-chip")?.textContent).toBe(word);
      expect(main().querySelectorAll('[data-mock-deviation="R421"]')).toHaveLength(1);
      expect(main().querySelector('[data-mock-deviation="R421"]')?.textContent?.trim()).toBe("MOCK DEVIATION D4 (R421)");
      cleanup();
    }
  });

  it("R254 (Q15): every Overview card has a plain label and View detail at the window", async () => {
    await renderAt(PATHS.ev, client());
    const card = (k: string) => main().querySelector(`[data-ev-card="${k}"]`) as HTMLElement;
    const expected: [string, string, string][] = [
      ["sessions", "Session service", `/sites/${CODE}/performance/sessions${Q}`],
      ["availability", "Availability", `/sites/${CODE}/performance/availability${Q}`],
      ["power", "Site power", `/sites/${CODE}/performance/energy${Q}`],
      ["charger", "Charger condition", `/sites/${CODE}/health${Q}`],
      ["evidence", "Evidence", `/sites/${CODE}/ev/evidence${Q}`],
    ];
    for (const [k, label, href] of expected) {
      expect(card(k).querySelector(".v69-metric__label")?.textContent, k).toBe(label);
      expect(card(k).querySelector(".v69-metric__label a"), k).toBeNull();
      expect(within(card(k)).getByRole("link", { name: "View detail →" }).getAttribute("href"), k).toBe(href);
    }
    expect(card("availability").textContent).toContain("Not summarised here");
    expect(card("charger").textContent).toContain("Charger condition is listed under Health");
  });

  it("R258 (Q15): Portfolio evidence, Review energy, Review work and only recorded next-evidence rows", async () => {
    await renderAt(PATHS["ev-evidence"], client());
    expect(within(document.querySelector(".status-strip") as HTMLElement).getByRole("link", { name: "Portfolio evidence" }).getAttribute("href")).toBe("/evidence");
    const conclude = panelTitled("What we can conclude now");
    expect(within(conclude).getByRole("link", { name: "Review energy →" }).getAttribute("href")).toBe(`/sites/${CODE}/performance/energy${Q}`);
    expect(within(conclude).getByRole("link", { name: "Review work →" }).getAttribute("href")).toBe(`/sites/${CODE}/work${Q}`);
    expect(conclude.querySelector('[data-link-unavailable="Work"]')).toBeNull();
    expect(panelTitled("Most useful next evidence").textContent).not.toContain("No further evidence request recorded");
    cleanup();
    await renderAt(PATHS["ev-evidence"], client({ empty: true, state: "UNKNOWN", consequence: null }));
    expect(panelTitled("Most useful next evidence").textContent?.match(/No further evidence request recorded/g) ?? []).toHaveLength(1);
  });

  it("R259 (Q15): Analysis times use the Site timezone with exact UTC in title; midnight crossing and UTC fallback", async () => {
    const recordsPanel = () => panelTitled("Accepted records behind the conclusions");
    const rows = (): string[][] => Array.from(recordsPanel().querySelectorAll("tbody tr")).map((r) => Array.from(r.querySelectorAll("td")).map((td) => td.textContent ?? ""));
    const heads = () => Array.from(recordsPanel().querySelectorAll("thead th")).map((h) => h.textContent);
    const late = item(120, { source_time: "2026-10-06T20:30:00.000000Z", sent_at: "2026-10-06T20:30:05.000000Z", received_at: "2026-10-06T21:15:00.000000Z" });
    await renderAt(PATHS["ev-evidence-analysis"], withAnalysis([late]));
    expect(heads()).toEqual(["Source · reading", "Value", "Measured (EAT)", "Sent (EAT)", "Received (EAT)", "Record"]);
    // 20:30 UTC is 23:30 EAT; 21:15 UTC is 00:15 on the next local day, so it carries its date.
    expect(rows()[0].slice(1, 4)).toEqual(["23:30:00", "23:30:05", "7 Oct 00:15:00"]);
    expect((recordsPanel().querySelectorAll("tbody tr td")[3] as HTMLElement).getAttribute("title")).toBe("2026-10-06T21:15:00.000Z UTC");
    cleanup();
    const utcSite = { ...SITE, timezone: null } as unknown as SiteDetailReadModel;
    const utcDetail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: utcSite }) };
    render(
      <MemoryRouter initialEntries={[`${PATHS["ev-evidence-analysis"]}${Q}`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={utcDetail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evSite={withAnalysis([late])} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(heads()).toEqual(["Source · reading", "Value", "Measured (UTC; Site time zone unavailable)", "Sent (UTC; Site time zone unavailable)", "Received (UTC; Site time zone unavailable)", "Record"]);
    expect(rows()[0].slice(1, 4)).toEqual(["20:30:00", "20:30:05", "21:15:00"]);
  });
});
