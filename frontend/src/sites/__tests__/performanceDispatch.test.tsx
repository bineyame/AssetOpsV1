import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { settledScreen } from "../../test/settled";
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
    current_basis: { read_at: "x", accepted_reading_count: 2 },
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
    ["STALE_PROJECTION", "RECOMPUTE_OUTSTANDING: job j1 PENDING", /Out of date/],
    ["FAILED", "RECOMPUTE_FAILED: job j1: RuntimeError", /Reassessment failed/],
    ["PENDING", "RECOMPUTE_OUTSTANDING: job j1 LEASED", /Being assessed/],
    ["UNASSESSED", "NOT_ASSESSED: accepted evidence exists", /Not assessed/],
  ] as const)("shows %s honestly with its reason and keeps any prior result marked", async (status, reason, words) => {
    const stale = status === "STALE_PROJECTION" || status === "FAILED";
    const client = fake({ status: "loaded", value: OPEN }, { status: "loaded", value: window({ status, status_reasons: [reason], stale,
      intervals: stale ? [revision("rev-current", "NECESSARY")] : [] }) }, { "rev-current": detail(revision("rev-current", "NECESSARY")) });
    const { container } = mount(client, "?day=2026-10-02&revision=rev-current");
    await settledScreen();
    expect(container.querySelector(".dispatch-status")?.textContent).toMatch(words);
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
    expect(container.querySelector("[data-older-rule]")?.textContent).toMatch(/dispatch-3; the current rules are dispatch-3.1/);
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
    expect([...container.querySelectorAll("[data-unavailable]")].map((e) => e.getAttribute("data-unavailable")))
      .toEqual(["alternatives", "fuel_and_money", "finding"]);
    expect(container.querySelector("[data-dispatch-gated]")?.textContent).toMatch(/Not yet available/);
    expect(container.querySelector("[data-history-revision='rev-current']")).not.toBeNull();
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
