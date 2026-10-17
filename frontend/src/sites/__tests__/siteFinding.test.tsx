import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type { SourceProvenance } from "../sourceProvenance";
import {
  createFindingClient,
  type FindingClient,
  type FindingDetailBody,
  type FindingReadResult,
  type RevisionSummary,
} from "../findingClient";
import { SiteFinding } from "../SiteFinding";

const F = "49281b7c-96ac-456d-ab6b-040bb0760444";
const PRIOR = "ce269028-d1c0-41cb-9b11-081b2229da03";
const CANON = "e9f189dd-adec-4868-b322-f5e9244d2198";
const I1 = "d6f4c21f-402f-46cb-b41b-023d36cb8841";
const W1 = "1a81376c-e8ab-41af-bfb1-53e0b1b40edc";

function summary(no: number, transition: string, lifecycle: RevisionSummary["lifecycle"] = "SUPPORTED"): RevisionSummary {
  return {
    id: `rev-${no}`,
    revision_no: no,
    recorded_at: `2026-10-12T08:0${no}:00+00:00`,
    transition,
    lifecycle,
    claim_level: lifecycle === "SUPPORTED" ? "CANDIDATE_AVOIDABLE" : "INDETERMINATE",
    support_changed: transition !== "BASIS_REFRESHED",
    model_version: "dispatch-3.1",
    matcher_version: "finding-episode-2",
    episode: { start: "2026-10-06T08:00:00+00:00", end: "2026-10-06T09:00:00+00:00" },
    candidate_minutes: "45.0000",
    primary_assessment_revision_id: I1,
    window_assessment_revision_ids: [W1],
    interval_assessment_revision_ids: [I1],
    prior_window_assessment_revision_ids: null,
    prior_interval_assessment_revision_ids: null,
    foundation_revision_ids: ["fnd-1"],
    binding_set_revision_ids: ["bnd-1"],
    cited_evidence_count: 2,
  };
}

function body(revisions: RevisionSummary[], selectedNo = revisions.length, patch: Partial<FindingDetailBody> = {}): FindingDetailBody {
  const selected = revisions[selectedNo - 1];
  const latest = revisions[revisions.length - 1];
  const groups: FindingDetailBody["revision_groups"] = [];
  for (const r of revisions) {
    const last = groups[groups.length - 1];
    if (r.transition === "BASIS_REFRESHED" && last?.kind === "BASIS_REFRESHED") {
      last.revision_ids.push(r.id);
      last.count += 1;
      last.last_revision_no = r.revision_no;
    } else {
      groups.push({ kind: r.transition === "BASIS_REFRESHED" ? "BASIS_REFRESHED" : "REVISION", label: r.transition, count: 1,
        revision_ids: [r.id], first_revision_no: r.revision_no, last_revision_no: r.revision_no, support_changed: r.support_changed });
    }
  }
  const supported = selected.lifecycle === "SUPPORTED";
  return {
    site_code: "KOBO-001",
    access_basis: "DEVELOPMENT_TENANT_OPERATOR_CONTEXT: no authenticated human principal exists yet",
    source_gate: { permitted: true, reason: "ok" },
    audit_only: null,
    finding: {
      id: F, finding_key: `gen-support:asset:20261006T080000Z:${F.slice(0, 8)}`, domain: "mini_grid",
      mechanism: "GENERATOR_SUPPORT_CANDIDATE", analytic_id: "dispatch", generator_asset_id: "asset",
      anchor_start: "2026-10-06T08:00:00+00:00", anchor_assessment_revision_id: I1, cohort_sha256: "c".repeat(64),
      matcher_version: "finding-episode-2", opened_at: "2026-10-12T08:01:00+00:00",
      recurs_after_finding_id: null, split_from_finding_id: null,
    },
    selection: { revision_id: selected.id, revision_no: selected.revision_no,
      selected_by: selectedNo === revisions.length ? "LATEST_RECORDED" : "EXACT_REVISION_ID",
      latest_revision_id: latest.id, is_latest: selected === latest, replay: "Exact stored revisions only." },
    revision: {
      ...selected,
      title: "ignored backend title",
      analytic_run_id: "pass-1",
      window_assessment_revision_id: W1,
      minutes: supported ? { candidate: "45.0000", necessary: "15.0000", indeterminate: "0.0000" }
        : { candidate: "0.0000", necessary: "15.0000", indeterminate: "45.0000" },
      claim: {
        statement: "stored statement",
        candidate_spans: supported ? [{ start: "2026-10-06T08:00:00Z", end: "2026-10-06T08:20:00Z", minutes: "20",
          assessment_revision_id: I1, evidence_ids: ["ev-1", "ev-2"] }] : [],
        other_portions: [{ start: "2026-10-06T08:20:00Z", end: "2026-10-06T08:35:00Z", classification: "NECESSARY",
          observed: true, assessment_revision_id: I1 }],
        continuity: [],
      },
      limitations: supported ? [] : ["EVIDENCE_GAP: generator_power missing 08:40-08:45"],
      cited_evidence_sha256: "a".repeat(64),
      input_evidence_sha256: "b".repeat(64),
      assessments: [
        { assessment_revision_id: I1, scope: "INTERVAL", window_start: "2026-10-06T00:00:00+00:00", is_primary: true, analytic_run_id: "pass-1" },
        { assessment_revision_id: W1, scope: "WINDOW", window_start: "2026-10-06T00:00:00+00:00", is_primary: false, analytic_run_id: "pass-1" },
      ],
      runs: [{ id: "pass-1", model_version: "dispatch-3.1", window_start: "2026-10-06T00:00:00+00:00", cohort_sha256: "c".repeat(64) }],
      cited_evidence: [
        { evidence_id: "ev-1", role: "generator_state", source_time: "2026-10-06T08:00:00+00:00", value: "ON", quality: "GOOD",
          batch_id: "batch-1", gateway_id: "gw-1", source_id: "src-1", sequence_epoch: "epoch-1" },
        { evidence_id: "ev-2", role: "feeder_demand", source_time: "2026-10-06T08:05:00+00:00", value: "12.5", unit: "kW",
          quality: "GOOD", batch_id: "batch-1", gateway_id: "gw-1", source_id: "src-2", sequence_epoch: "epoch-1" },
      ],
      off_reports: [],
      previous_revision_id: selectedNo > 1 ? revisions[selectedNo - 2].id : null,
      currentness: selected === latest
        ? { state: "CURRENT", windows: [{ day: "2026-10-06", cited_window_assessment_revision_id: W1, status: "CURRENT",
          status_reasons: [], currently_selected_window_assessment_revision_id: W1, cited_is_current_selection: true }] }
        : { state: "SUPERSEDED_BY_LATER_REVISION", windows: [], latest_revision_id: latest.id },
    },
    state: { lifecycle: latest.lifecycle, latest_transition: latest.transition, projection: "CURRENT",
      claim_is_current: latest.lifecycle === "SUPPORTED", latest_revision_id: latest.id, merged_into_finding_id: null, note: "" },
    relations: { canonical_finding_id: F, merged_into: [], merged_from: [], split_from_finding_id: null, split_parts: [],
      recurs_after_finding_id: null, recurred_by: [], recurrence: { status: "NOT_RECORDED" } },
    revisions,
    revision_page: { total: revisions.length, next_after_revision_no: null },
    revision_groups: groups,
    provenance: { statement: "provenance", cited_evidence_by_source: [], case_annotations: [] },
    watermarks: { finding_recorded_at: selected.recorded_at, analytic_built_at: "2026-10-12T08:00:00+00:00" },
    unavailable: { money: "UNAVAILABLE: no fuel" },
    links: { canonical: `/sites/KOBO-001/findings/${F}`, selected_revision: "", api_selected_revision: "", canonical_finding: "",
      performance: { status: "OPEN", reason: "ok" }, assessment_revisions: {}, windows: {} },
    ...patch,
  };
}

function fake(result: FindingReadResult<FindingDetailBody> | ((revisionId: string | null) => FindingReadResult<FindingDetailBody>)) {
  const asked: (string | null)[] = [];
  const client: FindingClient & { asked: (string | null)[] } = {
    asked,
    getFinding: async (_site, _id, revisionId) => {
      asked.push(revisionId);
      return typeof result === "function" ? result(revisionId) : result;
    },
    getFindingWindow: async () => ({ status: "not_found", message: null }),
    getFindingEvidence: async () => ({ status: "not_found", message: null }),
    getFindingHistory: async () => ({ status: "not_found", message: null }),
  };
  return client;
}

function Where() {
  const at = useLocation();
  return <output data-testid="where">{at.pathname + at.search}</output>;
}

function mount(client: FindingClient, search = "", id = F, withRecommendation = true) {
  return render(
    <MemoryRouter initialEntries={[`/sites/KOBO-001/findings/${id}${search}`]}>
      <Routes>
        <Route
          path="/sites/:siteId/findings/:findingId"
          element={
            <>
              <main>
              <SiteFinding
                siteId="KOBO-001"
                findingId={id}
                client={client}
                links={{
                  finding: (fid, rid) => `/sites/KOBO-001/findings/${fid}${rid ? `?revision_id=${rid}` : ""}`,
                  dispatch: (day, rid) => `/sites/KOBO-001/performance/dispatch?day=${day}${rid ? `&revision=${rid}` : ""}`,
                  evidence: "/sites/KOBO-001/evidence",
                  findingEvidence: (rid) => `/sites/KOBO-001/findings/${id}/evidence${rid ? `?revision_id=${rid}` : ""}`,
                  history: (rid) => `/sites/KOBO-001/findings/${id}/history${rid ? `?revision_id=${rid}` : ""}`,
                  ...(withRecommendation
                    ? { recommendation: (rid: string | null) => `/sites/KOBO-001/findings/${id}/recommendation${rid ? `?revision_id=${rid}` : ""}` }
                    : {}),
                }}
              />
              </main>
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

const where = () => screen.getByTestId("where").textContent ?? "";
/** W1-F3: the one concise claim line of panel 1 (formerly the answer card's h2). */
const claim = () => document.querySelector("[data-finding-claim]")?.textContent ?? "";
const happened = () => panelTitled("What happened");


/** S4-05b: a stored source provenance block for the selected version. */
function stored(state: "AUTHORED_DEMONSTRATION" | "MIXED"): SourceProvenance {
  return {
    tenant_id: "t1", site_id: "s1", finding_revision_id: "rev-x", consequence_revision_id: null,
    cited_accepted_evidence_ids: ["ev-1", "ev-2"], power_accepted_evidence_ids: null, state,
    reasons: state === "MIXED" ? [{ code: "BOUND_AND_UNBOUND", accepted_evidence_ids: ["ev-2"] }] : [],
    accepted_evidence_ids: ["ev-1", "ev-2"], problematic_accepted_evidence_ids: state === "MIXED" ? ["ev-2"] : [],
    publication_ids: ["pub-1"], source_classes: ["AUTHORED_DEMONSTRATION"],
    fixtures: [{ fixture_id: "assetops.s4-power-demo-cases", fixture_version: "1" }], runs: [], evidence: [],
  };
}

describe("Site Finding detail (S4-01 phase 3)", () => {
  it("offers no recommendation link, and says so, when the frame gives none (phase-1 review L5)", async () => {
    const { container } = mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }), "", F, false);
    await settledScreen();
    const none = panelTitled("What to do next").querySelector("[data-finding-recommendation-link='none']");
    expect(none?.textContent).toMatch(/^No recorded next action\. Nothing here asks you to change how the generator is operated\.$/);
    expect(container.querySelector("[data-finding-recommendation-link] a")).toBeNull();
    expectV69Panels("finding");
  });

  it("shows what happened, its limits and where to look, in plain words, with the Dispatch drill-down", async () => {
    const client = fake({ status: "loaded", value: body([summary(1, "OPENED")]) });
    const { container } = mount(client);
    await settledScreen();
    expect(client.asked).toEqual([null]);
    expectV69Panels("finding");
    expect(container.querySelector("[data-finding-card='CANDIDATE_AVOIDABLE']")?.textContent).toMatch(/45 min/);
    expect(container.querySelector("[data-finding-card='NECESSARY']")?.textContent).toMatch(/15 min/);
    expect(container.querySelector("[data-finding-card='MONEY'] .v69-metric__value")?.textContent).toBe("Not available");
    expect(container.querySelector("[data-finding-card='MONEY']")?.textContent).toMatch(/No fuel or money estimate is made on this page/);
    // W1-UX-02: the shared currentness words replace "Up to date".
    expect(container.querySelector("[data-chip='currentness']")?.textContent).toBe("Using the latest checked readings");
    // S6-01b: "What to do next" links to the Recommendation view at the exact version read.
    const next = panelTitled("What to do next").querySelector("[data-finding-recommendation-link] a");
    expect(next?.getAttribute("href")).toContain(`/sites/KOBO-001/findings/${F}/recommendation?revision_id=`);
    const day = container.querySelector("[data-finding-dispatch-day='2026-10-06']");
    expect(day?.getAttribute("href")).toBe(`/sites/KOBO-001/performance/dispatch?day=2026-10-06&revision=${I1}`);
    // W1-F3: the record list moved to the Finding's Evidence view; the count and its exact link stay here.
    const evidence = container.querySelector("[data-attention-item='evidence']");
    expect(evidence?.textContent).toMatch(/2 accepted records support the counted blocks/);
    expect(evidence?.querySelector("[data-finding-evidence-link]")?.getAttribute("href")).toBe(`/sites/KOBO-001/findings/${F}/evidence?revision_id=rev-1`);
    expect(container.querySelector("[data-evidence-id]")).toBeNull();
    const { violations, scanned } = scanProductVocabulary(container, "finding overview");
    expect(scanned).toBeGreaterThan(20);
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("selects a block from the keyboard, keeps it in the address and links that block's Dispatch day", async () => {
    const { container } = mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }));
    await settledScreen();
    const block = screen.getByRole("button", { name: /Possibly avoidable, 08:00–08:20 UTC/ });
    block.focus();
    expect(document.activeElement).toBe(block);
    fireEvent.click(block);
    expect(block.getAttribute("aria-pressed")).toBe("true");
    expect(where()).toMatch(/portion=0/);
    const detail = container.querySelector("[data-finding-portion-detail]");
    expect(detail?.textContent).toMatch(/2 accepted records/);
    expect(detail?.querySelector("a")?.getAttribute("href")).toContain(`revision=${I1}`);
  });

  it("reopens an exact earlier version from the address and leads with that it was replaced", async () => {
    const revs = [summary(1, "OPENED"), summary(2, "SUPPORT_CHANGED")];
    const client = fake((rid) => ({ status: "loaded", value: body(revs, rid === "rev-1" ? 1 : 2) }));
    const { container } = mount(client, "?revision_id=rev-1");
    await settledScreen();
    expect(client.asked).toEqual(["rev-1"]);
    expect(claim()).toBe("Earlier version 1 of 2");
    expect(container.querySelector("[data-chip='currentness']")?.textContent).toBe("Earlier version, kept for the record");
    // W1-F3: the version list lives on History (siteFindingHistory.test "marks the selected and the latest version");
    // the History link keeps the exact earlier version selected.
    expect(container.querySelector("[data-finding-history-link]")?.getAttribute("href")).toBe(`/sites/KOBO-001/findings/${F}/history?revision_id=rev-1`);
    fireEvent.click(screen.getByRole("link", { name: "Open the latest version" }));
    await settledScreen();
    expect(client.asked).toEqual(["rev-1", null]);
    expect(where()).toBe(`/sites/KOBO-001/findings/${F}`);
  });

  it("W1-F3: lists no versions on the Overview; History carries them, each exact version selectable", async () => {
    const revs = [summary(1, "OPENED"), summary(2, "BASIS_REFRESHED"), summary(3, "BASIS_REFRESHED")];
    const { container } = mount(fake({ status: "loaded", value: body(revs) }));
    await settledScreen();
    // The grouped, individually selectable versions are asserted on History
    // (siteFindingHistory.test "keeps assessment updates with an unchanged amount individually selectable").
    expect(container.querySelector("[data-finding-version]")).toBeNull();
    expect(container.querySelector("[data-version-group]")).toBeNull();
    expect(container.querySelector("[data-chip='version']")?.textContent).toMatch(/3/);
    expect(container.querySelector("[data-finding-history-link]")?.getAttribute("href")).toBe(`/sites/KOBO-001/findings/${F}/history?revision_id=rev-3`);
    expect(container.textContent).not.toMatch(/new issue/i);
    expectV69Panels("finding");
  });

  it("an unconfirmed version after a closed review does not read as a new active issue", async () => {
    const revs = [summary(1, "OPENED"), summary(2, "NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED"), summary(3, "UNCONFIRMED", "UNCONFIRMED")];
    const { container } = mount(fake({ status: "loaded", value: body(revs) }));
    await settledScreen();
    expect(claim()).toBe("Not confirmed: cannot decide whether any time was possibly avoidable");
    expect(container.querySelector("[data-finding-after-closure]")?.textContent).toMatch(/already been closed.*not a new issue/);
    expect(container.querySelector("[data-finding-card='CANDIDATE_AVOIDABLE']")?.textContent).toMatch(/0 min/);
    expect(container.querySelector("[data-limitation='EVIDENCE_GAP']")).not.toBeNull();
  });

  it("a no-longer-supported version says it is not a repair or a saving", async () => {
    const revs = [summary(1, "OPENED"), summary(2, "NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED")];
    const { container } = mount(fake({ status: "loaded", value: body(revs) }));
    await settledScreen();
    expect(container.querySelector("[data-finding-lifecycle-sentence]")?.textContent).toMatch(/does not mean the generator was repaired or that money was saved/);
    expect(container.querySelector("[data-finding-sentence]")?.textContent).toMatch(/counts no possibly avoidable time/);
  });

  it("C7: a pinned version under closed assessments leads with the record-only state, not a current result", async () => {
    const value = body([summary(1, "OPENED")], 1, {
      source_gate: { permitted: false, reason: "The newest comparison report is EXCEPTIONS" },
      audit_only: { non_current: true, reason: "closed", statement: "Audit material only" },
    });
    value.revision.currentness = { state: "SOURCE_CLOSED", windows: [] };
    value.links.performance = { status: "CLOSED", reason: "closed" };
    const { container } = mount(fake({ status: "loaded", value }), "?revision_id=rev-1");
    await settledScreen();
    // W1-F3: the lead is panel 1's claim line; its state line carries the record-only state.
    const lead = happened();
    expect(lead.querySelector("[data-finding-claim]")?.textContent).toBe("Record only: this site's assessments are not released");
    expect(lead?.querySelector("[data-finding-audit-only]")).not.toBeNull();
    expect(expectStateLineVisible(lead)).toBe("For the record only");
    expect(container.querySelector("[data-chip='currentness']")?.textContent).toBe("For the record only");
    expect(container.textContent).not.toMatch(/Up to date/);
    expect(container.textContent).not.toMatch(/Using the latest checked readings/);
    expect(container.querySelector("[data-finding-dispatch-closed]")).not.toBeNull();
    expect(container.querySelector("[data-finding-dispatch-day]")).toBeNull();
  });

  it("a recurrence link to an earlier Finding does not say that Finding is still open", async () => {
    const value = body([summary(1, "OPENED")]);
    value.relations.recurs_after_finding_id = PRIOR;
    value.relations.recurrence = { status: "LINKED", prior_finding_id: PRIOR };
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    const item = container.querySelector("[data-finding-recurrence='LINKED']");
    expect(item?.textContent).toMatch(/does not say the earlier Finding is still open/);
    expect(item?.querySelector("a")?.getAttribute("href")).toBe(`/sites/KOBO-001/findings/${PRIOR}`);
    expect(container.querySelector(`[data-finding-related='${PRIOR}']`)).not.toBeNull();
  });

  it.each([
    ["NO_EARLIER_FINDING", false],
    ["SEPARATION_NOT_ASSESSED", true],
  ])("a recurrence not established for %s is named only when an earlier Finding exists", async (reason, shown) => {
    const value = body([summary(1, "OPENED")]);
    value.relations.recurrence = { status: "NOT_ESTABLISHED", reason };
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    expect(container.querySelector("[data-finding-recurrence='NOT_ESTABLISHED']") !== null).toBe(shown);
  });

  it("a merged Finding leads with the Finding that carries the review", async () => {
    const value = body([summary(1, "OPENED"), summary(2, "MERGED_INTO", "MERGED")]);
    value.state.merged_into_finding_id = CANON;
    value.relations.merged_into = [{ superseded_finding_id: F, canonical_finding_id: CANON, finding_revision_id: "rev-2", created_at: "x" }];
    value.relations.canonical_finding_id = CANON;
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    expect(claim()).toBe("Joined into an earlier Finding");
    expect(container.querySelector(`[data-finding-merged='${CANON}'] a`)?.getAttribute("href")).toBe(`/sites/KOBO-001/findings/${CANON}`);
  });

  it.each([
    ["STALE", "This result may miss newer readings"],
    ["FINDING_MATCH_PENDING", "Being compared with a newer assessment"],
    ["FAILED", "The latest check could not be completed"],
    ["PENDING", "Not checked yet"],
  ])("shows a %s latest version as %s, keeping the recorded version visible", async (state, label) => {
    const value = body([summary(1, "OPENED")]);
    value.revision.currentness = { state, windows: [] };
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    expect(container.querySelector("[data-chip='currentness']")?.textContent).toBe(label);
    expect(container.querySelector(`[data-finding-currentness='${state}']`)?.textContent).toMatch(/last recorded version|not current/);
    expect(container.querySelector("[data-finding-card='CANDIDATE_AVOIDABLE']")).not.toBeNull();
    // W1-F3: the state line in What happened says the shown version is not current, outside the closed disclosure.
    const card = happened();
    expect(expectStateLineVisible(card)).toBe(label);
    expect(card.querySelector(".product-status__sentence")?.textContent).toMatch(/last recorded version|not current/);
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
  });

  it.each([
    ["not_found", /no such Finding/],
    ["unauthenticated", /Sign in/],
    ["forbidden", /no access/],
    ["closed", /not released for use yet.*no 'no Finding'/],
    ["unavailable", /could not be read/],
  ] as const)("names a %s read without showing a Finding", async (status, words) => {
    const result = (status === "closed" ? { status, message: "gate", note: null } : { status, message: null }) as FindingReadResult<FindingDetailBody>;
    const { container } = mount(fake(result));
    await settledScreen();
    expect(container.querySelector(`[data-finding-read='${status}']`)?.textContent).toMatch(words);
    expect(container.querySelector("[data-finding-card]")).toBeNull();
    expectV69Panels("finding");
  });

  it("keeps stored codes and full identifiers in Analysis, with plain labels", async () => {
    const { container } = mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }), "?view=analysis");
    await settledScreen();
    expect(container.querySelector("[data-finding-technical]")).not.toBeNull();
    expect(container.textContent).toContain(I1);
    expect(container.textContent).toContain("finding-episode-2");
    expect(container.querySelector("[data-tech-evidence-id='ev-1']")).not.toBeNull();
    const { violations } = scanProductVocabulary(container, "finding analysis");
    expect(violations, describeViolations(violations)).toEqual([]);
  });
});

describe("Site Finding detail (S4-01 phase 3 fix round 3)", () => {
  const unconfirmed = (patch: (b: FindingDetailBody) => void) => {
    const value = body([summary(1, "OPENED"), summary(2, "UNCONFIRMED", "UNCONFIRMED")]);
    value.revision.limitations = [];
    patch(value);
    return value;
  };

  const RUNTIME_RAW = "possibly within the configured minimum runtime (120 min from the first ON report); Candidate withheld, no policy Necessary claimed";
  const RUNTIME_SENTENCE = "No records are missing. It could not decide because the generator may still have been inside its 120-minute minimum operating time after starting.";
  const settingCause = (b: FindingDetailBody) => {
    b.revision.limitations = ["OPEN_BOUND: interval end not observed"];
    b.revision.indeterminate_reasons = [{ assessment_revision_id: I1, start: null, end: null, kind: "MODELLING",
      plain: ["the generator may still have been inside its 120-minute minimum operating time after starting"],
      missing: [RUNTIME_RAW],
      reasons: ["PV available plus PCS discharge capability covers load with 10 % headroom", "reserve 20.0 % (Foundation revision e41a0085)"] }];
    b.revision.indeterminate_cause = { kind: "MODELLING", sentence: RUNTIME_SENTENCE };
  };
  const gapCause = (b: FindingDetailBody) => {
    b.revision.limitations = [];
    b.revision.indeterminate_reasons = [{ assessment_revision_id: I1, start: null, end: null, kind: "RECORD_GAP", plain: [],
      missing: ["PV available power: no accepted reading"], reasons: [] }];
    b.revision.indeterminate_cause = { kind: "RECORD_GAP", sentence: "Some records it needs are missing or conflict over part of the period." };
  };

  it("R1: Not confirmed names only the real cause in one plain sentence, on an earlier version too; raw words stay in Analysis", async () => {
    for (const latest of [true, false]) {
      const value = unconfirmed((b) => { settingCause(b); b.selection.is_latest = latest; });
      const { container, unmount } = mount(fake({ status: "loaded", value }));
      await settledScreen();
      const lead = container.querySelector("[data-finding-lifecycle-sentence]")?.textContent ?? "";
      expect(lead).toContain(RUNTIME_SENTENCE);
      expect(lead).not.toMatch(/PV|PCS|Candidate|Necessary|reserve|headroom|settings now in force|Foundation revision/);
      expect(lead).not.toMatch(/records it needs are missing/);
      expect(container.textContent).not.toMatch(/configured minimum runtime/);
      const { violations } = scanProductVocabulary(container, "finding not confirmed");
      expect(violations, describeViolations(violations)).toEqual([]);
      expect(container.querySelector("[data-finding-card='INDETERMINATE']")?.textContent).not.toMatch(/missing/);
      expect(container.querySelector("[data-finding-sentence]")?.textContent).toMatch(/cannot decide whether any of that time was possibly avoidable/);
      unmount();
    }
    const value = unconfirmed(settingCause);
    const { container } = mount(fake({ status: "loaded", value }), "?view=analysis");
    await settledScreen();
    expect(container.querySelector("[data-tech-undecided]")?.textContent).toContain(RUNTIME_RAW);
  });

  it("R2/C8: a record-gap cause from the read says records are missing, and the limits do not say none were found", async () => {
    const value = unconfirmed(gapCause);
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    expect(container.querySelector("[data-finding-lifecycle-sentence]")?.textContent).toMatch(/records it needs are missing or conflict/);
    expect(container.querySelector("[data-finding-limitations='none']")).toBeNull();
    expect(container.querySelector("[data-finding-record-gap]")?.textContent).toMatch(/missing or conflict/);
  });

  it("R2: an OPEN_BOUND limitation alone does not read as missing records", async () => {
    const value = unconfirmed(settingCause);
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    expect(container.querySelector("[data-finding-lifecycle-sentence]")?.textContent).not.toMatch(/missing or conflict/);
    expect(container.querySelector("[data-finding-record-gap]")).toBeNull();
  });

  it("B2: a bridged stop is not described as the generator staying on throughout", async () => {
    const value = body([summary(1, "OPENED")]);
    value.revision.claim.continuity = [{ bridged_by: ["x"], stops: [{ off_after: "2026-10-06T08:50:00Z", off_before: "2026-10-06T08:55:00Z" }] } as never];
    const { container } = mount(fake({ status: "loaded", value }));
    await settledScreen();
    const sentence = container.querySelector("[data-finding-sentence]")?.textContent ?? "";
    expect(sentence).toMatch(/ran between .* one short stop/);
    expect(sentence).not.toMatch(/stayed on/);
  });

  it("C2/C3/C4: counts wording, out-of-date heading, and the earlier-version lead is not duplicated", async () => {
    const stale = body([summary(1, "OPENED")]);
    stale.revision.currentness = { ...stale.revision.currentness, state: "STALE" };
    const a = mount(fake({ status: "loaded", value: stale }));
    await settledScreen();
    expect(claim()).toBe("Open in the last recorded version: 45 min of generator time possibly avoidable");
    a.unmount();

    const none = unconfirmed(() => {});
    const b = mount(fake({ status: "loaded", value: none }));
    await settledScreen();
    expect(b.container.textContent).toMatch(/accepted records are cited by this version/);
    expect(b.container.textContent).not.toMatch(/support the counted blocks/);
    b.unmount();

    const revs = [summary(1, "OPENED"), summary(2, "UNCONFIRMED", "UNCONFIRMED")];
    const client = fake((rid) => ({ status: "loaded", value: body(revs, rid === "rev-1" ? 1 : 2) }));
    const c = mount(client, "?revision_id=rev-1");
    await settledScreen();
    expect((c.container.textContent?.match(/A later version replaces/g) ?? []).length).toBe(1);
  });
});

describe("Finding client status mapping", () => {
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    [401, { detail: { code: "UNAUTHENTICATED", message: "Sign in" } }, "unauthenticated"],
    [403, { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "No access" } }, "forbidden"],
    [404, { detail: "No such Finding or revision for this Site." }, "not_found"],
    [409, { detail: { code: "PERFORMANCE_CUTOVER_CLOSED", message: "closed", note: "n" } }, "closed"],
    [503, { detail: { code: "FINDING_STORE_UNAVAILABLE", message: "down" } }, "unavailable"],
  ])("maps HTTP %s to a named state and passes the exact revision", async (code, payload, status) => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", async (path: string) => {
      calls.push(path);
      return new Response(JSON.stringify(payload), { status: code });
    });
    const read = await createFindingClient("/api/sites").getFinding("KOBO-001", F, "rev 1");
    expect(read.status).toBe(status);
    expect(calls).toEqual([`/api/sites/KOBO-001/findings/${F}?revision_id=rev%201`]);
  });
});

describe("Site Finding detail: LR-01 series limit end", () => {
  it("states a SERIES_LIMIT end in plain words, and nothing for other ends", async () => {
    const base = body([summary(1, "OPENED")]);
    const limited = {
      ...base,
      revision: {
        ...base.revision,
        claim: { ...base.revision.claim, end_reason: "SERIES_LIMIT" as const },
        limitations: ["GENERATOR_SERIES_AMBIGUOUS: generator_power 2026-10-06T09:05:00Z..2026-10-06T10:00:00Z"],
      },
    };
    const view = mount(fake({ status: "loaded", value: limited }));
    await settledScreen();
    const item = document.querySelector("[data-finding-end-reason='SERIES_LIMIT']") as HTMLElement;
    expect(item).toHaveTextContent("could not be put in a proven time order");
    expect(item).toHaveTextContent("09:00");
    expect(document.querySelector("[data-limitation='GENERATOR_SERIES_AMBIGUOUS']")).toHaveTextContent(
      "could not be put in one proven time order",
    );
    view.unmount();
    mount(fake({ status: "loaded", value: base }));
    await settledScreen();
    expect(document.querySelector("[data-finding-end-reason]")).toBeNull();
  });

  it("names the selected version's stored source, and an unrecorded source as not confirmed (S4-05b)", async () => {
    const { container } = mount(fake({ status: "loaded", value: body([summary(1, "OPENED")], 1, { source_provenance: stored("AUTHORED_DEMONSTRATION") }) }));
    await settledScreen();
    expect(container.querySelector("[data-source-provenance-subject='finding']")).toHaveAttribute("data-source-provenance", "AUTHORED_DEMONSTRATION");
    expect(container.querySelector("[data-source-provenance]")).toHaveTextContent("Prepared example data.");
    const plain = mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }));
    await settledScreen();
    expect(plain.container.querySelector("[data-source-provenance]")).toHaveTextContent("Source unverified.");
  });
});

/** W1-UX-02: a state whose read records no time: explicit checks instead of `expectStateLineVisible`. */
function expectUntimedStateLine(card: Element): string {
  const status = card.querySelector("[data-product-status]");
  expect(status, "a shared state line is rendered").not.toBeNull();
  for (const selector of ["[data-product-status-label]", ".product-status__sentence", "[data-product-status-scope]", "[data-product-status-as-of]"]) {
    const el = status!.querySelector(selector);
    expect(el, selector).not.toBeNull();
    expect((el!.textContent ?? "").trim().length, `${selector} has text`).toBeGreaterThan(0);
    expect(visibleOutsideClosedDisclosure(el!), `${selector} is outside any closed disclosure`).toBe(true);
  }
  expect(status!.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
  return status!.querySelector("[data-product-status-label]")?.textContent ?? "";
}

describe("W1-UX-02 / W1-F3: Site Finding conclusion and state line", () => {
  // W1-F3: the Overview's answer card became panel 1 "What happened"; the Analysis view keeps the card.
  const card = () => document.querySelector("[data-headline-card='finding']") as HTMLElement;
  const main = () => document.querySelector("main") as HTMLElement;

  it("W1-F3: the Overview leads with the defensible conclusion in What happened, then the limits, next step and labelled exact references; W1 vocabulary on <main>", async () => {
    mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }));
    await settledScreen();
    expectV69Panels("finding");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    const answer = happened();
    expect(answer.querySelector("[data-finding-claim]")?.textContent).toBe("Open: 45 min of generator time possibly avoidable");
    expect(expectStateLineVisible(answer)).toBe("Using the latest checked readings");
    expect(answer.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 12 Oct 2026, 08:01 UTC");
    // The period covered stays visible in panel 1's scope (state line) and subtitle.
    expect(answer.querySelector("[data-product-status-scope]")?.textContent).toMatch(/Version 1 of 1 · 2026-10-06 08:00–09:00 UTC/);
    expect(answer.textContent).toMatch(/Period covered · 2026-10-06 08:00–09:00 UTC · 1 h/);
    // The consequence is not worked out on this page: a muted word, never an amount.
    const money = document.querySelector("[data-finding-card='MONEY']") as HTMLElement;
    expect(money.className).toMatch(/v69-metric--muted/);
    expect(money.className).toMatch(/v69-metric--word/);
    expect(main().textContent).not.toMatch(/\$|USD|saved|savings/);
    const limits = panelTitled("What limits this conclusion");
    expect(limits.querySelector("[data-finding-could-change]")?.textContent).toMatch(/What could change it/);
    expect(limits.querySelector("[data-finding-lifecycle-sentence]")).not.toBeNull();
    expect(limits.querySelector("[data-finding-bounded]")?.textContent).toMatch(/not proof of wasted fuel/);
    const look = panelTitled("Where to look next");
    expect(look.querySelector("[data-finding-destination='analysis']")?.getAttribute("href")).toBe("/sites/KOBO-001/findings/" + F + "?view=analysis");
    // Exact references are last, closed, individually labelled; the finding reference is not in the default reading.
    const refs = look.querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(refs.open).toBe(false);
    expect(look.lastElementChild?.contains(refs) || look.lastElementChild === refs).toBe(true);
    expect(Array.from(refs.querySelectorAll("dt")).map((dt) => dt.textContent)).toEqual([
      "Finding reference", "Shown version reference", "Latest version reference", "Recorded state code", "Up-to-date check code", "Change code",
    ]);
    expect(refs.querySelector("code")?.textContent).toBe(F);
    const w1 = scanProductVocabulary(main(), "finding overview (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(40);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const disclosure = scanDisclosureVocabulary(look, "finding exact references");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(5);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
  });

  it("W1-UX-02: the Analysis view keeps the card and the W1 vocabulary; an earlier version keeps its exact selector", async () => {
    const revs = [summary(1, "OPENED"), summary(2, "SUPPORT_CHANGED")];
    mount(fake((rid) => ({ status: "loaded", value: body(revs, rid === "rev-1" ? 1 : 2) })), "?revision_id=rev-1&view=analysis");
    await settledScreen();
    expect(document.querySelector("[data-finding-technical]")).not.toBeNull();
    const answer = card();
    // Historical: the plain "as of" of the shown version stays visible beside the answer.
    expect(expectStateLineVisible(answer)).toBe("Earlier version, kept for the record");
    expect(answer.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 12 Oct 2026, 08:01 UTC");
    expect(answer.querySelector("[data-finding-destination='overview']")?.getAttribute("href")).toBe(`/sites/KOBO-001/findings/${F}?revision_id=rev-1`);
    const steps = Array.from(answer.querySelectorAll("[data-step-strip] li")).map((li) => li.querySelector(".step-strip__label")?.textContent);
    expect(steps).toEqual(["Conclusion", "Cause", "Consequence", "Next useful step"]);
    expect(answer.querySelectorAll("[data-step-strip] li")[2].getAttribute("data-step")).toBe("not-known");
    const w1 = scanProductVocabulary(main(), "finding analysis (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(40);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it.each([
    ["STALE", "This result may miss newer readings"],
    ["PENDING", "Not checked yet"],
    ["PENDING_REASSESSMENT", "New readings call for another assessment"],
    ["FINDING_MATCH_PENDING", "Being compared with a newer assessment"],
    ["FAILED", "The latest check could not be completed"],
    ["NOT_ASSESSED", "We have not checked this period"],
    ["SOMETHING_NEW", "We cannot judge this yet"],
  ])("W1-UX-02: a %s latest version keeps a non-positive state line visible with the disclosure closed", async (state, label) => {
    const value = body([summary(1, "OPENED")]);
    value.revision.currentness = { state, windows: [] };
    mount(fake({ status: "loaded", value }));
    await settledScreen();
    const answer = happened();
    expect(expectStateLineVisible(answer)).toBe(label);
    expect(answer.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(answer.querySelector("[data-finding-claim]")?.textContent).toMatch(/^Open in the last recorded version: /);
    // The raw code stays in the labelled exact detail only.
    expect(answer.querySelector("[data-finding-state]")?.textContent).not.toContain(state);
    expect(document.querySelector("[data-finding-statusbar]")?.textContent).not.toContain(state);
    const w1 = scanProductVocabulary(main(), `finding ${state} (W1)`, { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("W1-UX-02: limited (not confirmed with a record gap), merged, record-only and unknown-source versions keep their state line visible", async () => {
    const limited = body([summary(1, "OPENED"), summary(2, "UNCONFIRMED", "UNCONFIRMED")]);
    limited.revision.indeterminate_cause = { kind: "RECORD_GAP", sentence: "Some records it needs are missing or conflict over part of the period." };
    const a = mount(fake({ status: "loaded", value: limited }));
    await settledScreen();
    expectStateLineVisible(happened());
    // W1-F3: the causal strip's "problem" cause is the record-gap limit, named in What limits this conclusion.
    const limits = panelTitled("What limits this conclusion");
    expect(limits.querySelector("[data-finding-record-gap]")?.textContent).toMatch(/missing or conflict/);
    expect(limits.querySelector("[data-finding-could-change]")?.textContent).toMatch(/fill the missing part/);
    a.unmount();

    const merged = body([summary(1, "OPENED"), summary(2, "MERGED_INTO", "MERGED")]);
    merged.state.merged_into_finding_id = CANON;
    const b = mount(fake({ status: "loaded", value: merged }));
    await settledScreen();
    expect(expectStateLineVisible(happened())).toBe("Joined into an earlier Finding");
    b.unmount();

    const closed = body([summary(1, "OPENED")], 1, { audit_only: { non_current: true, reason: "closed", statement: "Audit material only" } });
    closed.revision.currentness = { state: "SOURCE_CLOSED", windows: [] };
    const c = mount(fake({ status: "loaded", value: closed }), "?revision_id=rev-1");
    await settledScreen();
    expect(expectStateLineVisible(happened())).toBe("For the record only");
    c.unmount();

    // S4-05: an unrecorded source is named beside the state line, never as a positive source.
    mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }));
    await settledScreen();
    expectStateLineVisible(happened());
    const source = happened().querySelector("[data-source-provenance]") as HTMLElement;
    expect(source).toHaveTextContent("Source unverified.");
    expect(visibleOutsideClosedDisclosure(source)).toBe(true);
  });

  it.each([
    ["not_found", "This record was not found"],
    ["forbidden", "This cannot be shown to you"],
    ["unauthenticated", "This cannot be shown to you"],
    ["closed", "Not released for use yet"],
    ["unavailable", "This could not be read right now"],
  ] as const)("W1-F3: a %s read shows the page refusal with a plain state line, the four panels with in-panel gaps and no Finding", async (status, label) => {
    const result = (status === "closed" ? { status, message: null, note: null } : { status, message: null }) as FindingReadResult<FindingDetailBody>;
    mount(fake(result));
    await settledScreen();
    const refusal = document.querySelector(`[data-page-refusal='${status}']`) as HTMLElement;
    expect(expectUntimedStateLine(refusal)).toBe(label);
    expect(refusal.querySelector(`[data-finding-read='${status}']`)).not.toBeNull();
    expect(document.querySelector("[data-finding-card]")).toBeNull();
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expectV69Panels("finding");
    for (const title of ["What happened", "What limits this conclusion", "What to do next", "Where to look next"]) {
      expect(panelTitled(title).querySelector("[data-finding-panel-gap]")?.textContent).toMatch(/nothing is shown here, and this is not a result that no Finding exists/);
    }
    const w1 = scanProductVocabulary(main(), `finding ${status} (W1)`, { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });
});

describe("W1-F3: finding renders exactly the v69 panels", () => {
  const order = () =>
    Array.from(document.querySelectorAll("main [data-finding-statusbar], main h2, main .v69-cards")).map((el) =>
      el.matches("[data-finding-statusbar]") ? "statusbar" : el.matches(".v69-cards") ? "metrics" : el.textContent,
    );

  it("stocked: statusbar, What happened, four metric cards, the limits / next pair, Where to look next", async () => {
    mount(fake({ status: "loaded", value: body([summary(1, "OPENED")]) }));
    await settledScreen();
    expectV69Panels("finding");
    expect(order()).toEqual(["statusbar", "What happened", "metrics", "What limits this conclusion", "What to do next", "Where to look next"]);
    expect(Array.from(document.querySelectorAll("[data-finding-card]")).map((c) => c.getAttribute("data-finding-card"))).toEqual([
      "CANDIDATE_AVOIDABLE", "NECESSARY", "INDETERMINATE", "MONEY",
    ]);
    const pair = document.querySelector(".panel-pair") as HTMLElement;
    expect(Array.from(pair.querySelectorAll("h2")).map((h) => h.textContent)).toEqual(["What limits this conclusion", "What to do next"]);
    expect(Array.from(document.querySelectorAll("[data-attention-item]")).map((i) => i.getAttribute("data-attention-item"))).toEqual([
      "analysis", "evidence", "history", "dispatch", "related",
    ]);
    expect(happened().querySelector("[data-finding-claim]")?.tagName).toBe("P");
  });

  it("unconfirmed, no blocks and no records: the same four panels with honest empty lines", async () => {
    const value = body([summary(1, "OPENED"), summary(2, "UNCONFIRMED", "UNCONFIRMED")]);
    value.revision.claim.other_portions = [];
    value.revision.cited_evidence = [];
    mount(fake({ status: "loaded", value }));
    await settledScreen();
    expectV69Panels("finding");
    expect(happened().querySelector("[data-finding-no-blocks]")?.textContent).toBe("No block is counted in this version.");
    expect(document.querySelector("[data-attention-item='evidence']")?.textContent).toMatch(/0 accepted records are cited by this version/);
    expect(document.querySelector("[data-attention-item='related']")?.textContent).toMatch(/None recorded\./);
  });

  it("an earlier, record-only version: the same four panels; the Analysis view is outside this guard", async () => {
    const value = body([summary(1, "OPENED"), summary(2, "SUPPORT_CHANGED")], 1, {
      audit_only: { non_current: true, reason: "closed", statement: "Audit material only" },
    });
    value.links.performance = { status: "CLOSED", reason: "closed" };
    mount(fake({ status: "loaded", value }), "?revision_id=rev-1");
    await settledScreen();
    expectV69Panels("finding");
    expect(panelTitled("Where to look next").querySelector("[data-finding-dispatch-closed]")).not.toBeNull();
  });
});
