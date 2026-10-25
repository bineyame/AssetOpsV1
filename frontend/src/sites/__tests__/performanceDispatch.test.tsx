import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { expectStateLineVisible } from "../../test/productPresentation";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { PerformanceDispatch } from "../PerformanceDispatch";
import type {
  AssessmentRevision,
  CutoverState,
  DispatchWindow,
  PerformanceDispatchClient,
  RevisionDetail,
} from "../performanceDispatchClient";
import type { EvidenceRead } from "../siteEvidenceClient";
import type { FindingClient, FindingWindowBody } from "../findingClient";

const EMPTY_SET = {
  report_id: "r1",
  compared_at: "2026-10-11T20:46:38Z",
  model_version: "dispatch-3.1",
  outcome: "PASSED",
  empty_set: true,
  statement: "Empty-set comparison: ... a zero-inventory statement, not claim parity.",
  counts: { MATCH: 0, INTENTIONAL_DELTA: 0, MISSING_SOURCE: 0, UNPROVEN: 0 },
  lineage_breaks: {},
  claims: [],
};
const OPEN: CutoverState = { site_code: "KOBO-001", read: "POSTGRES_DISPATCH_3_1", permitted: true, reason: "ok", comparison: EMPTY_SET };

function revision(id: string, claim: string, model = "dispatch-3.1"): AssessmentRevision {
  return {
    id,
    model_version: model,
    assessment_key: `dispatch:interval:g:${id}`,
    revision_no: 1,
    analytic_run_id: "run-1",
    window_start: "2026-10-02T00:00:00+00:00",
    window_end: "2026-10-03T00:00:00+00:00",
    claim_level: claim,
    basis_sha256: "b",
    created_at: "2026-10-11T00:00:00Z",
    evidence_ids: ["e1", "e2"],
    result: {
      interval: { first_on: "2026-10-02T03:45:00Z", last_on: "2026-10-02T04:15:00Z", lower_minutes: "30", upper_minutes: "60" },
      portions_minutes: { necessary: "15", candidate: "15", indeterminate: "0" },
      segments: [
        { start: "2026-10-02T03:45:00Z", end: "2026-10-02T04:00:00Z", minutes: "15", classification: "NECESSARY",
          reasons: ["reserve 30 %"], evidence_ids: ["e1"], load_kw: "40" },
        { start: "2026-10-02T04:00:00Z", end: "2026-10-02T04:15:00Z", minutes: "15", classification: "CANDIDATE_AVOIDABLE",
          reasons: ["PV covers load"], evidence_ids: ["e2"], margin_kw: "5" },
      ],
      confidence: { level: "LOW", basis: ["open bound"] },
      alternatives: { operator_command: "UNAVAILABLE: no command record" },
    },
  };
}

function window(over: Partial<DispatchWindow> = {}): DispatchWindow {
  return {
    site_code: "KOBO-001",
    model_version: "dispatch-3.1",
    window: { start: "2026-10-02T00:00:00+00:00", end: "2026-10-03T00:00:00+00:00", calendar: "UTC day (dispatch-3.1)" },
    status: "CURRENT",
    status_reasons: [],
    stale: false,
    current_basis: { read_at: "2026-10-11T00:05:00Z", accepted_reading_count: 2 },
    selection: null,
    coverage: { battery_soc: { status: "BOUND", readings: 3, not_good: 0 }, pcs_discharge_capability: { status: "BOUND", readings: 0, not_good: 0 } },
    watermarks: null,
    window_assessment: null,
    limitations: ["MISSING_ROLE: pv_available_power is not bound", "OPEN_BOUND: no OFF evidence"],
    intervals: [revision("rev-current", "CANDIDATE_AVOIDABLE")],
    superseded_keys: [],
    jobs: [],
    unavailable: { alternatives: "UNAVAILABLE: none", fuel_and_money: "UNAVAILABLE: no fuel", finding: "UNAVAILABLE: not a Finding" },
    evidence_count: 2,
    demo_annotations: [],
    ...over,
  };
}

function detail(base: AssessmentRevision, over: Partial<RevisionDetail> = {}): RevisionDetail {
  const item = (id: string, role: string) => ({
    evidence_id: id, envelope_sha256: "s", message_id: `m-${id}`, batch_id: "b1", external_batch_id: null,
    gateway_id: "gw-1", source_id: "src-1", sequence_epoch: "epoch-2", sequence: 7, device_id: "d", signal_id: "s",
    role, asset_id: "a", source_time: "2026-10-02T03:45:00+00:00", interval_start: null, interval_end: null,
    published_at: null, received_at: "r", accepted_at: "2026-10-11T00:00:00Z", quality: "GOOD", value: "31", unit: "%",
    as_accepted: { foundation_revision_id: "f1" },
  });
  return {
    ...base,
    evidence: [item("e1", "battery_soc"), item("e2", "pv_available_power")],
    history: [base],
    selected_by_runs: ["run-1"],
    selected_configuration: { foundation_revision_ids: ["f1"], binding_set_revision_ids: ["bs1"] },
    knowledge_cutoff_label: "label",
    model_note: null,
    demo_annotations: [],
    run: null,
    ...over,
  };
}

function fake(cutover: EvidenceRead<CutoverState>, read: EvidenceRead<DispatchWindow>,
  revisions: Record<string, RevisionDetail> = {}): PerformanceDispatchClient & { windows: string[] } {
  const windows: string[] = [];
  return {
    windows,
    getCutover: async () => cutover,
    getWindow: async (_site, day) => {
      windows.push(day);
      return read;
    },
    getRevision: async (_site, id) => (revisions[id] ? { status: "loaded", value: revisions[id] } : { status: "not_found" }),
  };
}

function Where() {
  const at = useLocation();
  return <output data-testid="where">{at.search}</output>;
}

function mount(client: PerformanceDispatchClient, search: string) {
  return render(
    <MemoryRouter initialEntries={[`/sites/KOBO-001/performance/dispatch${search}`]}>
      <Routes>
        <Route path="/sites/:siteId/performance/dispatch" element={<><PerformanceDispatch siteId="KOBO-001" client={client} /><Where /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("durable Performance > Dispatch (S3-01 phase 3b)", () => {
  it("keeps the window read closed while the cutover is closed and shows why with the comparison", async () => {
    const client = fake({ status: "loaded", value: { ...OPEN, permitted: false, read: "CLOSED", reason: "The newest report is EXCEPTIONS",
      comparison: { ...EMPTY_SET, empty_set: false, outcome: "EXCEPTIONS", counts: { MATCH: 0, INTENTIONAL_DELTA: 0, MISSING_SOURCE: 1, UNPROVEN: 0 },
        claims: [{ class: "MISSING_SOURCE", legacy_assessment_id: "a1", missing_message_ids: ["m9"], reason: "not accepted" }] } } },
      { status: "loaded", value: window() });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    expect(container.querySelector("[data-dispatch-cutover='closed']")).not.toBeNull();
    expect(container.querySelector("[data-missing-message-ids]")).toBeNull();
    expect(container.textContent).not.toMatch(/EXCEPTIONS|MISSING_SOURCE|INTENTIONAL_DELTA|m9|lineage|\{"/);
    expect(container.querySelector("[data-closed-plain]")?.textContent).toMatch(/not be shown|not shown/);
    expect(client.windows).toEqual([]);
    expect(container.querySelector("[data-dispatch-status]")).toBeNull();
  });

  it("shows a 503 cutover body as a closed, unreadable check", async () => {
    const client = fake({ status: "loaded", value: { ...OPEN, permitted: false, read: "CLOSED", comparison: null,
      reason: "The Performance read is unavailable: report unreadable", unavailable: { code: "COMPARISON_STORE_UNAVAILABLE", message: "x" } } },
      { status: "loaded", value: window() });
    mount(client, "?day=2026-10-02");
    await settledScreen();
    expect(screen.getByText(/The check could not be read/)).toBeTruthy();
    expect(client.windows).toEqual([]);
  });

  it("reads the selected day, names limitations in plain words and never claims parity for an empty comparison", async () => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    expect(client.windows).toEqual(["2026-10-02"]);
    expect(container.querySelector("[data-dispatch-status='CURRENT']")).not.toBeNull();
    expect(container.querySelector("[data-limitation='MISSING_ROLE']")?.textContent).toMatch(/not set up/);
    expect(container.querySelector("[data-total='avoidable']")?.textContent).toMatch(/15 min/);
    expect(container.querySelector("[data-comparison-empty='true']")?.textContent).toMatch(/This is not a match/);
    expect(container.textContent).not.toMatch(/simulat|SIMULATED|fixture/i);
  });

  it.each([
    ["STALE_PROJECTION", "RECOMPUTE_OUTSTANDING: job j1 PENDING", /This result may miss newer readings/],
    ["FAILED", "RECOMPUTE_FAILED: job j1: RuntimeError", /The latest check could not be completed/],
    ["PENDING", "RECOMPUTE_OUTSTANDING: job j1 LEASED", /Not checked yet/],
    ["UNASSESSED", "NOT_ASSESSED: accepted evidence exists", /We have not checked this period/],
  ] as const)("shows %s honestly with its reason and keeps any prior result marked", async (status, reason, words) => {
    const stale = status === "STALE_PROJECTION" || status === "FAILED";
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ status, status_reasons: [reason], stale,
      intervals: stale ? [revision("rev-current", "NECESSARY")] : [] }) }, { "rev-current": detail(revision("rev-current", "NECESSARY")) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current");
    await settledScreen();
    // W1-UX-03: the shared state labels; the state line keeps its sentence, scope and "as of" outside any closed disclosure.
    const line = container.querySelector(".dispatch-status") as HTMLElement;
    expect(line.textContent).toMatch(words);
    expectStateLineVisible(line);
    expect(line.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(container.querySelector(`[data-status-reason='${reason.split(":")[0]}']`)).not.toBeNull();
    if (stale) {
      expect(container.querySelector("[data-dispatch-stale-selection]")).not.toBeNull();
    } else {
      expect(container.querySelector("[data-total]")).toBeNull();
    }
  });

  it("selects a block, lists its accepted records and keeps the exact IDs in the address", async () => {
    const current = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "rev-current": detail(current) });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    fireEvent.click(container.querySelector("[data-revision-id='rev-current']") as Element);
    await settledScreen();
    fireEvent.click(container.querySelector("[data-block='1']") as Element);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe("?day=2026-10-02&revision=rev-current&block=1");
    expect(container.querySelector("[data-evidence-scope='block']")).not.toBeNull();
    expect([...container.querySelectorAll("[data-evidence-id]")].map((e) => e.getAttribute("data-evidence-id"))).toEqual(["e2"]);
    expect(container.querySelector("[data-configuration-note='same']")).not.toBeNull();
  });

  it("reopens a stored revision that is not the day's current one, labelled, with an older-rule note", async () => {
    const old = revision("rev-old", "CANDIDATE_AVOIDABLE", "dispatch-3");
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, {
      "rev-old": detail(old, { model_note: "OLDER_RULE_RESULT: produced by dispatch-3",
        selected_configuration: { foundation_revision_ids: ["f2"], binding_set_revision_ids: [] } }) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-old");
    await settledScreen();
    expect(container.querySelector("[data-selected-revision='rev-old']")).not.toBeNull();
    expect(container.querySelector("[data-dispatch-pinned]")).not.toBeNull();
    // W1-UX-03: the versions move from the default sentence to labelled exact references in the closed disclosure.
    const older = container.querySelector("[data-older-rule]") as HTMLElement;
    expect(older.querySelector("p")?.textContent).toMatch(/earlier version of the assessment rules/);
    expect(older.querySelector("p")?.textContent).not.toMatch(/dispatch-3/);
    const refs = older.querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(refs.open).toBe(false);
    expect(Array.from(refs.querySelectorAll("code")).map((c) => c.textContent)).toEqual(["dispatch-3", "dispatch-3.1"]);
    expect(container.querySelector("[data-configuration-note='differs']")).not.toBeNull();
  });

  it("names a missing stored revision instead of substituting another", async () => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() });
    const { container } = mount(client, "?day=2026-10-02&revision=gone");
    await settledScreen();
    expect(container.querySelector("[data-dispatch-selected-missing]")?.textContent).toMatch(/No other result/);
  });

  it("keeps demonstration notes apart from the accepted-record provenance", async () => {
    const current = revision("rev-current", "INDETERMINATE");
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, {
      "rev-current": detail(current, { demo_annotations: [{ kind: "DEMO_MANIFEST_FAULT_FIXTURE", case_label: "contradictory reports", matched_evidence_ids: ["e1"] }] }) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current");
    await settledScreen();
    const notes = container.querySelector("[data-demo-annotations='1']");
    expect(notes?.textContent).toMatch(/not records AssetOps accepted/);
    expect(notes?.closest("table")).toBeNull();
    expect(container.querySelector("[data-evidence-id='e1']")?.textContent).not.toMatch(/contradictory/);
  });

  it("keeps the technical comparison on the closed path in the Analysis view only", async () => {
    const closed: CutoverState = { ...OPEN, permitted: false, read: "CLOSED", reason: "The newest report is EXCEPTIONS",
      comparison: { ...EMPTY_SET, empty_set: false, outcome: "EXCEPTIONS", counts: { MATCH: 0, INTENTIONAL_DELTA: 0, MISSING_SOURCE: 1, UNPROVEN: 0 },
        lineage_breaks: { x: 1 }, claims: [{ class: "MISSING_SOURCE", legacy_assessment_id: "a1", missing_message_ids: ["m9"], reason: "not accepted" }] } };
    const { container } = mount(fake({ status: "loaded", value: closed }, { status: "loaded", value: window() }), "?day=2026-10-02&view=analysis");
    await settledScreen();
    expect(container.querySelector("[data-missing-message-ids]")?.textContent).toMatch(/m9.*not a match/);
    expect(screen.getByText(/The newest report is EXCEPTIONS/)).toBeTruthy();
  });

  it("shows the day's demonstration notes on the Overview even when no period can be selected", async () => {
    const notes = [{ kind: "DEMO_MANIFEST_FAULT_FIXTURE", case_label: "out-of-order-fault-fixture", matched_evidence_ids: ["e1", "e2"] }];
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ intervals: [], demo_annotations: notes }) });
    const { container } = mount(client, "?day=2026-10-07");
    await settledScreen();
    const found = container.querySelector("[data-demo-annotations='1']");
    expect(found?.textContent).toMatch(/not records AssetOps accepted/);
    expect(found?.textContent).toMatch(/out-of-order-fault-fixture/);
  });

  it("does not label the battery channel row as a missing reserve setting", async () => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({
      coverage: { battery_reserve: { status: "UNBOUND", readings: 0, not_good: 0 } } }) });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    const row = container.querySelector("[data-coverage-role='battery_reserve']")?.textContent ?? "";
    expect(row).not.toMatch(/^Battery reserve setting/);
    expect(row).toMatch(/site settings/);
  });

  it("W1-F2 compaction: coverage shows three inputs then 'Show all'; the recorded limits list sits in the closed detail row", async () => {
    const item = { status: "BOUND", readings: 4, not_good: 0 };
    const coverage = { generator_state: item, pcs_discharge_capability: item, pv_available_power: item, load_power: item, battery_reserve: item };
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ coverage }) });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    const rows = [...container.querySelectorAll<HTMLTableRowElement>("tr[data-coverage-role]")];
    expect(rows.map((r) => r.hidden)).toEqual([false, false, false, true, true]);
    const toggle = screen.getByRole("button", { name: "Show all 5 inputs" });
    fireEvent.click(toggle);
    expect(rows.map((r) => r.hidden)).toEqual([false, false, false, false, false]);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    // The recorded limits (summarised as one line in panel 1) are in the closed detail disclosure.
    const detail = container.querySelector("details[data-disclosure='dispatch-coverage-detail']") as HTMLDetailsElement;
    expect(detail.open).toBe(false);
    expect(detail.querySelector("[data-limitation='MISSING_ROLE']")).not.toBeNull();
    expect(container.querySelector("[data-dispatch-limitation-summary]")?.closest("details")).toBeNull();
    expect(container.querySelector("[data-coverage-note]")?.closest("details")).toBeNull();
  });

  it("W1-F2 compaction: Analysis shows three constraint blocks then 'Show all'; technical disclosures nest in one closed row", async () => {
    const current = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const seg = current.result.segments[0];
    current.result.segments = [0, 1, 2, 3, 4].map((n) => ({
      ...seg,
      start: `2026-10-02T0${n}:00:00Z`,
      end: `2026-10-02T0${n}:15:00Z`,
    }));
    const client = fake(
      { status: "loaded", value: OPEN },
      { status: "loaded", value: window({ intervals: [current], limitations: ["MISSING_ROLE: x"] }) },
      { "rev-current": detail(current) },
    );
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current&view=analysis");
    await settledScreen();
    const rows = [...container.querySelectorAll<HTMLTableRowElement>("tr[data-constraint-block]")];
    expect(rows.map((r) => r.hidden)).toEqual([false, false, false, true, true]);
    const toggle = screen.getByRole("button", { name: "Show all 5 blocks" });
    fireEvent.click(toggle);
    expect(rows.map((r) => r.hidden)).toEqual([false, false, false, false, false]);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    const technical = container.querySelector("details[data-disclosure='analysis-technical']") as HTMLDetailsElement;
    expect(technical.open).toBe(false);
    for (const name of ["dispatch-stored-record", "window-limitations"]) {
      const inner = technical.querySelector(`details[data-disclosure='${name}']`) as HTMLDetailsElement;
      expect(inner, name).not.toBeNull();
      expect(inner.open, name).toBe(false);
    }
  });

  it("uses plain words for the shortfall constraint and a missing series, and hides model strings", async () => {
    const base = revision("rev-current", "NECESSARY");
    base.result.binding_constraints = ["CAPABILITY_SHORTFALL"];
    base.result.limitations = ["NO_COHORT: nothing"];
    base.result.segments[0].missing = ["not bound in the selected role set (missing role)"];
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ intervals: [base],
      limitations: ["NO_COHORT: nothing"] }) }, { "rev-current": detail(base) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current&block=0");
    await settledScreen();
    const text = container.textContent ?? "";
    expect(text).toMatch(/Demand above what solar and battery could supply/);
    expect(text).not.toMatch(/capability shortfall|Another limitation is recorded/i);
    expect(container.querySelector("[data-limitation='NO_COHORT']")?.textContent).toMatch(/series of records/);
    const block = container.querySelector("[data-selected-block]")?.textContent ?? "";
    expect(block).not.toMatch(/role set|missing role|cohort|Missing:/);
    expect(block).toMatch(/Analysis/);
    expect(container.querySelector("[data-evidence-id='e1']")?.textContent).not.toMatch(/GOOD|T\d\d:\d\d:\d\d/);
    expect(container.querySelector("[data-evidence-id='e1'] details")?.textContent).not.toMatch(/2026-10-11T/);
  });

  it("says plainly when records exist but no series was chosen, and when a binding covers only part of the day", async () => {
    const selection = { cohort_status: "AMBIGUOUS", cohort: { status: "AMBIGUOUS", reason: "two series", members: [] },
      model_version: "dispatch-3.1" } as unknown as DispatchWindow["selection"];
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ intervals: [], selection,
      evidence_count: 0, current_basis: { read_at: "x", accepted_reading_count: 14 }, limitations: ["AMBIGUOUS_COHORT: two"] }) });
    const { container } = mount(client, "?day=2026-10-05");
    await settledScreen();
    const note = container.querySelector("[data-coverage-note]")?.textContent ?? "";
    expect(note).toMatch(/no single series/i);
    expect(note).not.toMatch(/^0 accepted records/);
    expect(container.querySelector("[data-limitation='AMBIGUOUS_COHORT']")).not.toBeNull();
  });

  it("names part-of-the-day for a missing measurement", async () => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    expect(container.querySelector("[data-limitation='MISSING_ROLE']")?.textContent).toMatch(/part of the day/);
  });

  it.each(["STALE_PROJECTION", "FAILED"] as const)("marks the day totals as not current on a %s day", async (status) => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ status, stale: true,
      status_reasons: ["RECOMPUTE_OUTSTANDING: job"] }) });
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    expect(container.querySelector("[data-totals-stale]")?.textContent).toMatch(/not current/);
    expect(container.querySelectorAll("[data-total][data-stale='true']")).toHaveLength(4);
  });

  it("Analysis shows the constraint and coverage portions and types the rest unavailable", async () => {
    const current = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "rev-current": detail(current) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current&view=analysis");
    await settledScreen();
    expect(container.querySelectorAll("[data-constraint-block]")).toHaveLength(2);
    // Review fix M6: the result records alternatives, so the not-available "alternatives" row is suppressed and
    // exactly one "Other explanations" line remains, stating the recorded count.
    expect([...container.querySelectorAll("[data-unavailable]")].map((e) => e.getAttribute("data-unavailable")))
      .toEqual(["fuel_and_money", "finding"]);
    const terms = (c: HTMLElement) => [...c.querySelectorAll("dt")].map((dt) => dt.textContent);
    expect(terms(container).filter((t) => t === "Other explanations")).toHaveLength(1);
    expect(container.textContent).toMatch(/Other explanations\s*1 recorded/);
    expect(container.querySelector("[data-dispatch-gated]")?.textContent).toMatch(/Not yet available/);
    expect(container.querySelector("[data-history-revision='rev-current']")).not.toBeNull();
  });

  it("Analysis without recorded alternatives keeps the not-available row once, and names every unavailable key (M6)", async () => {
    const r = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const bare = { ...r, result: { ...r.result, alternatives: {} } };
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ intervals: [bare],
      unavailable: { alternatives: "UNAVAILABLE: none", grid_import_cost: "UNAVAILABLE: later" } }) }, { "rev-current": detail(bare) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current&view=analysis");
    await settledScreen();
    expect([...container.querySelectorAll("[data-unavailable]")].map((e) => e.getAttribute("data-unavailable")))
      .toEqual(["alternatives", "grid_import_cost"]);
    const terms = [...container.querySelectorAll("dt")].map((dt) => dt.textContent);
    expect(terms.filter((t) => t === "Other explanations")).toHaveLength(1);
    expect(terms).toContain("Grid import cost");
    expect(container.textContent).not.toMatch(/Another result/);
  });
});

describe("Dispatch day Finding links (S4-01 phase 3)", () => {
  function findingsFake(state: string, findings: FindingWindowBody["findings"]): FindingClient & { days: string[] } {
    const days: string[] = [];
    return {
      days,
      getFinding: async () => ({ status: "not_found", message: null }),
      getFindingEvidence: async () => ({ status: "not_found", message: null }),
      getFindingHistory: async () => ({ status: "not_found", message: null }),
      getFindingWindow: async (_site, day) => {
        days.push(day);
        return { status: "loaded", value: { day, state, note: "", assessment_status: "CURRENT", findings } };
      },
    };
  }

  function mountWith(findings: FindingClient) {
    return render(
      <MemoryRouter initialEntries={["/sites/KOBO-001/performance/dispatch?day=2026-10-02"]}>
        <Routes>
          <Route
            path="/sites/:siteId/performance/dispatch"
            element={<PerformanceDispatch siteId="KOBO-001" client={fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() })}
              findings={findings} findingHref={(id) => `/sites/KOBO-001/findings/${id}`} />}
          />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("links each recorded Finding over the day and hides one joined into another", async () => {
    const findings = findingsFake("FINDINGS_RECORDED", [
      { finding_id: "f-1", lifecycle: "SUPPORTED", episode_start: "2026-10-02T05:15:00+00:00", episode_end: "2026-10-02T09:15:00+00:00", cites_current_window_selection: true },
      { finding_id: "f-2", lifecycle: "MERGED", episode_start: "2026-10-02T10:00:00+00:00", episode_end: "2026-10-02T10:30:00+00:00", cites_current_window_selection: true },
    ]);
    const { container } = mountWith(findings);
    await settledScreen();
    const link = await screen.findByRole("link", { name: /Open: 05:15–09:15 UTC/ });
    expect(link.getAttribute("href")).toBe("/sites/KOBO-001/findings/f-1");
    expect(findings.days).toEqual(["2026-10-02"]);
    expect(container.querySelector("[data-dispatch-finding='f-2']")).toBeNull();
  });

  it.each([
    ["NO_FINDING", /fully assessed and has no Finding/],
    ["NOT_DETERMINABLE", /not a no-Finding result/],
    ["FINDING_MATCH_PENDING", /not yet been compared/],
  ])("names a %s day without a Finding link", async (state, words) => {
    const { container } = mountWith(findingsFake(state, []));
    await settledScreen();
    await screen.findByText(words);
    expect(container.querySelector(`[data-day-findings='${state}']`)).not.toBeNull();
    expect(container.querySelector("[data-dispatch-finding]")).toBeNull();
  });
});

describe("W1-UX-03: dispatch and analysis presentation", () => {
  /** The rendered screen without the test's location probe (it prints the raw address). */
  function reading(container: HTMLElement): HTMLElement {
    const copy = container.cloneNode(true) as HTMLElement;
    copy.querySelectorAll("[data-testid='where']").forEach((n) => n.remove());
    return copy;
  }

  /** The default reading: everything outside closed disclosures. */
  function defaultText(container: HTMLElement): string {
    const copy = reading(container);
    copy.querySelectorAll("details:not([open])").forEach((d) => d.querySelectorAll(":scope > :not(summary)").forEach((n) => n.remove()));
    return copy.textContent ?? "";
  }

  it("leads with why the generator operated, a selectable block strip, the state line and the exact selection; W1 vocabulary", async () => {
    const current = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "rev-current": detail(current) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current&block=1");
    await settledScreen();
    // W1-F2: no answer card; the v69 dispatch panels, with the state line in the statusbar above them.
    expectV69Panels("dispatch", { interval: "04:00–04:15 UTC" }, container.querySelector("[data-dispatch-root]") as HTMLElement);
    expect(container.querySelector("[data-headline-card]")).toBeNull();
    const card = container.querySelector(".durable-dispatch__body") as HTMLElement;
    const blocks = panelTitled("Sources and 15-minute blocks", container);
    expect(card.querySelector("[data-dispatch-headline]")?.textContent).toBe(
      "The generator operated for 30 min to 1 h: 15 min possibly avoidable, 15 min needed and 0 min that cannot be determined.",
    );
    expect(expectStateLineVisible(card)).toBe("Using the latest checked readings");
    const strip = card.querySelector("[data-period-strip='dispatch-day-blocks']") as HTMLElement;
    const links = Array.from(strip.querySelectorAll<HTMLAnchorElement>("a[data-period-strip-segment]"));
    expect(links.map((a) => a.dataset.periodStripSegment)).toEqual(["necessary", "avoidable"]);
    const chosen = links.find((a) => a.getAttribute("aria-current") === "true") as HTMLAnchorElement;
    expect(chosen.getAttribute("href")).toContain("revision=rev-current");
    expect(chosen.getAttribute("href")).toContain("block=1");
    expect(chosen.getAttribute("aria-label")).toBe("04:00 to 04:15 UTC: Possibly avoidable");
    // Review fix H1: the period chips and the selectable block tiles are in panel 1 under the strip, and
    // panel 2 leads with the selected block's own outcome; the period facts follow under a period label.
    expect(blocks.querySelector("[data-revision-id='rev-current']")).not.toBeNull();
    expect(blocks.querySelector("[data-block='1'][aria-pressed='true']")?.textContent).toBe("Avoidable04:00");
    const selectedPanel = panelTitled("Selected block · 04:00–04:15 UTC", container);
    expect(selectedPanel.querySelector("[data-block], [data-revision-id]")).toBeNull();
    const firstBadge = selectedPanel.querySelector("[data-claim-level]") as HTMLElement;
    expect(firstBadge.closest("[data-selected-block]")).not.toBeNull();
    expect(firstBadge.textContent).toBe("Possibly avoidable");
    expect(selectedPanel.querySelector(".dispatch-block-detail__lead")?.textContent).toMatch(/above the demand in this block/);
    expect(selectedPanel.querySelector("[data-dispatch-period-label]")?.textContent).toMatch(/^The period this block is in: \d\d:\d\d to/);
    expect(card.querySelector("[data-dispatch-analysis-link]")?.getAttribute("href")).toContain("view=analysis");
    // The rule versions are labelled exact references in the closed disclosure, never default prose.
    expect(defaultText(container)).not.toMatch(/dispatch-3\.1|model version/);
    const disclosure = scanDisclosureVocabulary(blocks, "dispatch disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(describeViolations(disclosure.violations)).toBe("");
    const w1 = scanProductVocabulary(reading(container), "dispatch overview (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(describeViolations(w1.violations)).toBe("");
  });

  it("an unstated portion is 'not known', never counted as zero", async () => {
    const r = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const partial = { ...r, result: { ...r.result, portions_minutes: { necessary: "15", candidate: "15" } } };
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ intervals: [partial] }) }, {});
    const { container } = mount(client, "?day=2026-10-02");
    await settledScreen();
    expect(container.querySelector("[data-total='unknown']")?.textContent).toMatch(/not known/);
    expect(container.querySelector("[data-total='unknown']")?.textContent).not.toMatch(/0 min/);
    expect(container.querySelector("[data-dispatch-headline]")?.textContent).toMatch(/not known that cannot be determined/);
  });

  it("an undetermined block draws as its own hatched outcome; late input keeps the earlier result marked not current", async () => {
    const r = revision("rev-current", "INDETERMINATE");
    const undetermined = { ...r, result: { ...r.result, segments: r.result.segments.map((s) => ({ ...s, classification: "INDETERMINATE", missing: ["pcs_discharge_capability"] })) } };
    const client = fake({ status: "loaded", value: OPEN }, {
      status: "loaded",
      value: window({ status: "STALE_PROJECTION", stale: true, status_reasons: ["RECOMPUTE_OUTSTANDING: job j1 PENDING"], intervals: [undetermined] }),
    }, { "rev-current": detail(undetermined) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current");
    await settledScreen();
    const card = container.querySelector(".durable-dispatch__body") as HTMLElement;
    expect(card.querySelector("[data-dispatch-headline]")?.textContent).toMatch(/^From an earlier result that is not current: /);
    expectStateLineVisible(card);
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    const segments = Array.from(card.querySelectorAll("[data-period-strip-segment]")).map((a) => a.getAttribute("data-period-strip-segment"));
    expect(segments).toEqual(["undetermined", "undetermined"]);
    expect(card.querySelector("[data-period-strip-row='blocks']")?.textContent).toMatch(/0 needed, 0 possibly avoidable, 2 cannot be determined/);
  });

  it("Analysis: accepted readings, then the rule, then a bounded conclusion for the exact selection; W1 vocabulary", async () => {
    const current = revision("rev-current", "CANDIDATE_AVOIDABLE");
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "rev-current": detail(current) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current&block=1&view=analysis");
    await settledScreen();
    const story = container.querySelector("[data-dispatch-story='block']") as HTMLElement;
    expect(Array.from(story.querySelectorAll("[data-dispatch-story-step]")).map((s) => s.getAttribute("data-dispatch-story-step"))).toEqual([
      "readings",
      "rule",
      "conclusion",
    ]);
    expect(story.querySelector("[data-dispatch-story-conclusion]")?.textContent).toBe("Possibly avoidable, for the block 04:00 to 04:15 UTC.");
    expect(story.textContent).toMatch(/2 accepted readings used/);
    expect(story.textContent).toMatch(/says nothing about fuel, savings or money/);
    expectStateLineVisible(container.querySelector(".dispatch-status") as HTMLElement);
    expect(defaultText(container).match(/.{0,60}(dispatch-3\.1|run-1|CURRENT\b).{0,40}/g) ?? []).toEqual([]);
    const w1 = scanProductVocabulary(reading(container), "dispatch analysis (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    // Known deviation (review packet): the legacy fuel/money missing-capability sentence is pinned verbatim by the
    // missing-claim baseline until G-04 renders it through MissingClaim; its word "claim" is the only W1 hit allowed,
    // and only in that one element.
    const gated = container.querySelector("[data-dispatch-gated]")?.textContent ?? "";
    const others = w1.violations.filter((v) => !(v.phrase === "claim" && gated.includes(v.text.trim().slice(0, 60))));
    expect(describeViolations(others)).toBe("");
    expect(w1.violations.length - others.length).toBeLessThanOrEqual(1);
  });

  it("Analysis frames a stored version outside the day's current set as not current, also via the versions panel (fix round 1, F1)", async () => {
    const old = revision("rev-old", "CANDIDATE_AVOIDABLE", "dispatch-3");
    const current = { ...revision("rev-current", "CANDIDATE_AVOIDABLE"), revision_no: 2 };
    const history = [old, current];
    const revisions = {
      "rev-old": detail(old, { history, model_note: "OLDER_RULE_RESULT: produced by dispatch-3" }),
      "rev-current": detail(current, { history }),
    };
    const assertStored = (container: HTMLElement) => {
      const conclusion = container.querySelector("[data-dispatch-story-conclusion]")?.textContent;
      expect(conclusion).toBe("Possibly avoidable, for the period 03:45 to 04:15 UTC, from a stored version that is not the current result.");
      expect(container.querySelector("[data-dispatch-pinned]")?.textContent).toMatch(/stored result that is not the current one for 2026-10-02/);
      const line = container.querySelector(".dispatch-status") as HTMLElement;
      expect(line.getAttribute("data-dispatch-shown")).toBe("stored-not-current");
      expect(expectStateLineVisible(line)).not.toBe("Using the latest checked readings");
      expect(line.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
      expect(line.textContent).not.toMatch(/latest checked readings/);
    };

    // Directly by address, on a CURRENT day.
    const direct = mount(fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, revisions), "?day=2026-10-02&revision=rev-old&view=analysis");
    await settledScreen();
    assertStored(direct.container);
    direct.unmount();

    // Through every non-current link in the visible "Versions of this period" panel.
    const viaPanel = mount(fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, revisions), "?day=2026-10-02&revision=rev-current&view=analysis");
    await settledScreen();
    expect(viaPanel.container.querySelector("[data-dispatch-story-conclusion]")?.textContent).toBe("Possibly avoidable, for the period 03:45 to 04:15 UTC.");
    expect(viaPanel.container.querySelector("[data-dispatch-pinned]")).toBeNull();
    const links = Array.from(viaPanel.container.querySelectorAll("[data-history-revision] a"));
    expect(links.map((a) => a.closest("[data-history-revision]")?.getAttribute("data-history-revision"))).toEqual(["rev-old", "rev-current"]);
    fireEvent.click(links[0]);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toContain("revision=rev-old");
    await waitFor(() => expect(viaPanel.container.querySelector("[data-dispatch-pinned]")).not.toBeNull());
    assertStored(viaPanel.container);
  });

  it("Analysis without a selected period concludes nothing", async () => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, {});
    const { container } = mount(client, "?day=2026-10-02&view=analysis");
    await settledScreen();
    expect(container.querySelector("[data-dispatch-story='none']")?.textContent).toMatch(/nothing is concluded here/);
  });
});

/**
 * W1-F2 (D-2026-10-17-mockup-layout-spec): the v69 `dispatch` and `analysis` panel structure in every variant.
 * A page-level refusal keeps the same panel slots with the gap inside each.
 */
describe("W1-F2: v69 dispatch and analysis panel structure", () => {
  const root = (container: HTMLElement) => container.querySelector("[data-dispatch-root]") as HTMLElement;
  const stocked = () => {
    const current = revision("rev-current", "CANDIDATE_AVOIDABLE");
    return fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "rev-current": detail(current) });
  };

  it.each([
    ["stocked, block selected", "?day=2026-10-02&revision=rev-current&block=1", "04:00–04:15 UTC"],
    ["stocked, period selected", "?day=2026-10-02&revision=rev-current", "03:45–04:15 UTC"],
    ["stocked, nothing selected", "?day=2026-10-02", "No block selected"],
  ])("dispatch, %s", async (_name, search, interval) => {
    const { container } = mount(stocked(), search);
    await settledScreen();
    expectV69Panels("dispatch", { interval }, root(container));
  });

  it("dispatch and analysis on an empty day keep their panels with the gap inside", async () => {
    const empty = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ intervals: [] }) });
    const { container, unmount } = mount(empty, "?day=2026-10-02");
    await settledScreen();
    expectV69Panels("dispatch", { interval: "No block selected" }, root(container));
    expect(panelTitled("Selected block · No block selected", root(container)).textContent).toContain("No period selected");
    unmount();
    const analysis = mount(empty, "?day=2026-10-02&view=analysis");
    await settledScreen();
    expectV69Panels("analysis", {}, root(analysis.container));
    expect(panelTitled("Constraint comparison", root(analysis.container)).textContent).toContain("Select a period");
  });

  it("analysis, stocked: three panels, no fuel calculation claimed", async () => {
    const { container } = mount(stocked(), "?day=2026-10-02&revision=rev-current&block=1&view=analysis");
    await settledScreen();
    expectV69Panels("analysis", {}, root(container));
    expect(panelTitled("Bounded fuel calculation", root(container)).querySelector("[data-dispatch-gated]")).not.toBeNull();
  });

  it.each([
    ["cutover unreadable", { status: "unavailable", message: "store down" } as EvidenceRead<CutoverState>, { status: "loaded", value: window() } as EvidenceRead<DispatchWindow>, "cutover-unreadable"],
    ["cutover closed", { status: "loaded", value: { ...OPEN, permitted: false, reason: "not compared" } } as EvidenceRead<CutoverState>, { status: "loaded", value: window() } as EvidenceRead<DispatchWindow>, "closed"],
    ["window not found", { status: "loaded", value: OPEN } as EvidenceRead<CutoverState>, { status: "not_found" } as EvidenceRead<DispatchWindow>, "window-unreadable"],
  ])("refused (%s): the refusal precedes the same panels, each stating the gap", async (_name, cutover, read, name) => {
    for (const view of ["", "&view=analysis"]) {
      const { container, unmount } = mount(fake(cutover, read), `?day=2026-10-02${view}`);
      await settledScreen();
      expect(container.querySelector(`[data-page-refusal="${name}"]`)).not.toBeNull();
      if (view === "") {
        expectV69Panels("dispatch", { interval: "No block selected" }, root(container));
      } else {
        expectV69Panels("analysis", {}, root(container));
      }
      expect(container.querySelectorAll(`[data-dispatch-gap="${name}"]`)).toHaveLength(3);
      unmount();
    }
  });
});

describe("post-W6 W1-a Q6 / R178: a whole-window assessment named as the selected revision", () => {
  const whole = (over: Partial<RevisionDetail> = {}): RevisionDetail =>
    ({
      ...detail(revision("win-1", "CANDIDATE_AVOIDABLE")),
      assessment_key: "dispatch:window:g:2026-10-02",
      scope: "WINDOW",
      result: { portions_minutes: { necessary: "15", candidate: "15", indeterminate: "0" } },
      ...over,
    }) as unknown as RevisionDetail;

  it("refuses a window-shaped revision with the ruled copy and a link to the bare day, without throwing", async () => {
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "win-1": whole() });
    const { container } = mount(client, "?day=2026-10-02&revision=win-1&block=1");
    await settledScreen();
    await waitFor(() => expect(container.querySelector("[data-dispatch-refused='not-interval']")).not.toBeNull());
    const refusal = container.querySelector("[data-page-refusal='not-interval']") as HTMLElement;
    expect(refusal.querySelector(".page-refusal__title")?.textContent).toBe("This assessment cannot be shown as 15-minute blocks");
    expect(refusal.textContent).toContain(
      "The address names a whole-window assessment, not a 15-minute interval result for this day. Open the day without a selected revision.",
    );
    const open = refusal.querySelector("[data-dispatch-open-day]") as HTMLAnchorElement;
    expect(open.textContent).toBe("Open this day");
    expect(open.getAttribute("href")).toBe("/sites/KOBO-001/performance/dispatch?day=2026-10-02");
    expect(container.querySelector("[data-selected-revision]")).toBeNull();
  });

  it("refuses a known WINDOW scope even when it carries interval-shaped fields", async () => {
    const shaped = { ...detail(revision("win-2", "NECESSARY")), scope: "WINDOW" } as RevisionDetail;
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "win-2": shaped });
    const { container } = mount(client, "?day=2026-10-02&revision=win-2&block=0");
    await settledScreen();
    await waitFor(() => expect(container.querySelector("[data-dispatch-refused='not-interval']")).not.toBeNull());
  });

  it("keeps a valid interval revision from another day as the labelled stored-other-day notice, with an unknown scope", async () => {
    const other = { ...revision("rev-other", "CANDIDATE_AVOIDABLE"), window_start: "2026-09-30T00:00:00+00:00", scope: "SOMETHING_NEW" };
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window() }, { "rev-other": detail(other) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-other&block=1");
    await settledScreen();
    await waitFor(() => expect(container.querySelector("[data-selected-revision='rev-other']")).not.toBeNull());
    expect(container.querySelector("[data-dispatch-refused='not-interval']")).toBeNull();
    expect(container.querySelector("[data-dispatch-pinned]")).not.toBeNull();
  });
});
