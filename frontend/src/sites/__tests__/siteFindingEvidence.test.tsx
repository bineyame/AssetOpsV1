/**
 * S4-03 phase 2: the Finding Evidence child view, its section links in the
 * Finding frame, and the old assessment-keyed page's Evidence tab resolving to
 * the same read.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteFindingFrame } from "../../shell/SiteAnalyticsFrames";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type { SourceProvenance } from "../sourceProvenance";
import {
  createFindingClient,
  type EvidenceRecord,
  type FindingClient,
  type FindingEvidenceBody,
  type FindingReadResult,
  type FindingWindowBody,
} from "../findingClient";
import { LINK_DISPLAY_OVERRIDES, LINK_DISPLAY_WORDS, LINK_WORDS, LegacyFindingEvidence, SiteFindingEvidence } from "../SiteFindingEvidence";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

const SITE = HYBRID_MINI_GRID_SITE.site_id;
const F = "49281b7c-96ac-456d-ab6b-040bb0760444";
const R1 = "rev-1";
const R2 = "rev-2";
const IA = "d6f4c21f-402f-46cb-b41b-023d36cb8841";
const WA = "1a81376c-e8ab-41af-bfb1-53e0b1b40edc";

function record(n: number, patch: Partial<EvidenceRecord> = {}): EvidenceRecord {
  const id = `e${String(n).padStart(3, "0")}-0000-4000-8000-000000000000`;
  return {
    evidence_id: id,
    resolved: true,
    lineage_status: "RESOLVED",
    broken_links: [],
    role: "GENERATOR_POWER",
    value: "12.5",
    unit: "kW",
    quality: "GOOD",
    source_time: `2026-10-09T10:${String(n % 60).padStart(2, "0")}:00+00:00`,
    interval: { start: null, end: null },
    received_at: "2026-10-09T11:00:00+00:00",
    accepted_at: "2026-10-09T11:00:01+00:00",
    disposition: "ACCEPTED",
    source: {
      gateway_id: "gw-0001-aaaa",
      source_id: "src-0001-bbbb",
      sequence_epoch: "s4-gateway-epoch-1",
      sequence: n,
      device_id: "GEN-1",
      signal_id: "output_kw",
      asset_id: "GEN-1",
      source_mode: "SIMULATED",
    },
    batch: { batch_id: "batch-uuid", external_batch_id: "batch-0001", resolved: true },
    message_id: `msg-${n}`,
    envelope: { sha256: "ab".repeat(32), digest_verified: true },
    accepted_as: {
      foundation_revision_id: "fr-1",
      foundation_version: 3,
      foundation_resolved: true,
      binding_set_revision_id: "bs-1",
      binding_set_version: 2,
      binding_set_resolved: true,
      binding_revision_id: "b-1",
      binding_resolved: true,
      conversion_kind: "IDENTITY",
      configuration_outdated: false,
    },
    used_by: { assessment_revision_ids: [IA], run_ids: ["run-1"] },
    ...patch,
  };
}

function body(patch: Partial<FindingEvidenceBody> = {}, records: EvidenceRecord[] = [record(1), record(2), record(3)]): FindingEvidenceBody {
  const total = patch.page?.total ?? records.length;
  return {
    site_code: SITE,
    source_gate: { permitted: true, reason: "OPEN" },
    audit_only: null,
    finding: {
      id: F,
      finding_key: "k",
      domain: "generator",
      mechanism: "m",
      analytic_id: "a",
      generator_asset_id: "GEN-1",
      anchor_start: "2026-10-09T10:00:00+00:00",
      anchor_assessment_revision_id: IA,
      cohort_sha256: "c",
      matcher_version: "1",
      opened_at: "2026-10-09T12:00:00+00:00",
      recurs_after_finding_id: null,
      split_from_finding_id: null,
    },
    selection: {
      revision_id: R2,
      revision_no: 2,
      selected_by: "LATEST_RECORDED",
      latest_revision_id: R2,
      is_latest: true,
      replay: "Exact stored revisions only.",
    },
    revision: {
      id: R2,
      revision_no: 2,
      recorded_at: "2026-10-09T12:00:00+00:00",
      transition: "EVIDENCE_APPENDED",
      lifecycle: "SUPPORTED",
      claim_level: "CANDIDATE_AVOIDABLE",
      support_changed: true,
      model_version: "dispatch-3.1",
      matcher_version: "1",
      episode: { start: "2026-10-09T10:00:00+00:00", end: "2026-10-09T11:00:00+00:00" },
      candidate_minutes: "45",
      primary_assessment_revision_id: IA,
      window_assessment_revision_ids: [WA],
      interval_assessment_revision_ids: [IA],
      prior_window_assessment_revision_ids: null,
      prior_interval_assessment_revision_ids: null,
      foundation_revision_ids: ["fr-1"],
      binding_set_revision_ids: ["bs-1"],
      cited_evidence_count: total,
      minutes: { candidate: "45", necessary: "10", indeterminate: "5" },
      analytic_run_id: "run-1",
      window_assessment_revision_id: WA,
      cited_evidence_sha256: "d1",
      input_evidence_sha256: "d2",
      limitations: [],
    },
    counts: {
      cited_total: total,
      cited_resolved: total,
      cited_unresolved: 0,
      cited_with_broken_lineage: 0,
      input_distinct_total: 263,
      input_by_run: [{ analytic_run_id: "run-1", input_evidence_count: 263, input_sha256: "x" }],
      statement: "Membership is the selected revision's cited accepted evidence.",
    },
    lineage: {
      status: "COMPLETE",
      cited_set_digest: { status: "VERIFIED", recorded: "d1", recomputed: "d1" },
      set_breaks: [],
      broken_records: [],
      statement: "Every cited ID is checked.",
      words: {
        ACCEPTED_EVIDENCE: "the cited ID has no accepted evidence row in this Site",
        ENVELOPE_DIGEST: "the stored envelope text does not hash to the recorded envelope digest",
        CITED_SET_DIGEST: "the cited set does not hash to the revision's recorded cited_evidence_sha256",
        ANALYTIC_RUN: "a cited assessment's analytic run does not resolve",
      },
    },
    assessments: [
      {
        assessment_revision_id: IA,
        scope: "INTERVAL",
        is_primary: true,
        assessment_key: "k",
        assessment_revision_no: 1,
        claim_level: "CANDIDATE_AVOIDABLE",
        window: { start: "2026-10-09T10:00:00+00:00", end: "2026-10-09T11:00:00+00:00" },
        model_version: "dispatch-3.1",
        analytic_run_id: "run-1",
        run_resolved: true,
        cohort: { status: "COMPLETE", sha256: "c" },
        basis: {
          foundation_revision_ids: ["fr-1"],
          binding_set_revision_ids: ["bs-1"],
          configuration_sha256: "cfg",
          control_basis: "recorded only inside the run's configuration digest",
        },
        cited_records: total,
      },
    ],
    records,
    page: { offset: 0, limit: 50, total, returned: records.length, next_offset: null },
    provenance: {
      statement: "Central evidence carries no marker.",
      cited_evidence_by_source: [
        { gateway_id: "gw-0001-aaaa", source_id: "src-0001-bbbb", sequence_epoch: "s4-gateway-epoch-1", source_mode: "SIMULATED", count: total },
      ],
      cited_evidence_by_role: [
        { role: "generator_state", count: total - 1, source_ids: ["src-0001-bbbb"] },
        { role: "battery_soc", count: 1, source_ids: ["src-0001-bbbb", "src-0002-cccc"] },
      ],
      case_annotations: [],
    },
    currentness: null,
    links: {
      canonical: `/sites/${SITE}/findings/${F}`,
      evidence: `/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}`,
      performance: { status: "OPEN" },
      records: Object.fromEntries(records.filter((r) => r.resolved).map((r) => [r.evidence_id, `/api/sites/${SITE}/evidence/records/${r.evidence_id}`])),
      assessment_revisions: { [IA]: `/api/sites/${SITE}/performance/dispatch/revisions/${IA}` },
    },
    ...patch,
  };
}

type Asked = { revisionId: string | null; offset: number; limit: number };

function fake(result: FindingReadResult<FindingEvidenceBody> | ((asked: Asked) => FindingReadResult<FindingEvidenceBody>)) {
  const asked: Asked[] = [];
  const client: FindingClient & { asked: Asked[] } = {
    asked,
    getFinding: async () => ({ status: "not_found", message: null }),
    getFindingWindow: async () => ({ status: "not_found", message: null }),
    getFindingEvidence: async (_site, _id, revisionId, offset, limit) => {
      const a = { revisionId, offset, limit };
      asked.push(a);
      return typeof result === "function" ? result(a) : result;
    },
    getFindingHistory: async () => ({ status: "not_found", message: null }),
  };
  return client;
}

function Where() {
  const at = useLocation();
  return <output data-testid="where">{at.pathname + at.search}</output>;
}
const where = () => screen.getByTestId("where").textContent ?? "";

const LINKS = {
  evidence: (rev: string | null) => `/sites/${SITE}/findings/${F}/evidence${rev ? `?revision_id=${rev}` : ""}`,
  finding: (id: string, rev?: string | null) => `/sites/${SITE}/findings/${id}${rev ? `?revision_id=${rev}` : ""}`,
  dispatch: (day: string, rev?: string | null) => `/sites/${SITE}/performance/dispatch?day=${day}${rev ? `&revision=${rev}` : ""}`,
  record: (id: string) => `/sites/${SITE}/evidence?view=analysis&record=${id}`,
};

async function mount(client: FindingClient, search = "") {
  const view = render(
    <MemoryRouter initialEntries={[`/sites/${SITE}/findings/${F}/evidence${search}`]}>
      <Routes>
        <Route
          path="/sites/:siteId/findings/:findingId/evidence"
          element={
            <>
              <main>
                <SiteFindingEvidence siteId={SITE} findingId={F} client={client} links={LINKS} />
              </main>
              <Where />
            </>
          }
        />
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
  return view;
}

const q = (selector: string) => document.querySelector(selector);

/** W1-UX-02: the notes of a state line after its state label and sentence, in order. */
function statusNotes(note: Element): Element[] {
  return Array.from(note.parentElement?.children ?? []).filter(
    (el) => !el.matches(".product-status__label, .product-status__sentence"),
  );
}


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

describe("Finding Evidence child view (S4-03 phase 2)", () => {
  it("labels an omitted version as the latest at read time and separates cited from input records", async () => {
    const client = fake({ status: "loaded", value: body() });
    const { container } = await mount(client);
    expect(client.asked).toEqual([{ revisionId: null, offset: 0, limit: 50 }]);
    expect(q("[data-evidence-latest-at-read]")).toHaveTextContent("Latest version at the time of reading (version 2)");
    expect(q("[data-evidence-pin]")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}`);
    expect(q("[data-evidence-cited-total]")).toHaveTextContent("3");
    expect(q("[data-evidence-input-total]")).toHaveTextContent("263");
    expect(q("[data-evidence-lineage-complete]")).not.toBeNull();
    expect(document.querySelectorAll("tr[data-evidence-id]")).toHaveLength(3);
    expect(q("[data-evidence-page-range]")).toHaveTextContent("Records 1–3 of 3");
    expect(q("[data-evidence-page='end']")).not.toBeNull();
    expect(q(`[data-evidence-dispatch-link='${IA}']`)).toHaveAttribute(
      "href",
      `/sites/${SITE}/performance/dispatch?day=2026-10-09&revision=${IA}`,
    );
    expect(q("[data-evidence-source='s4-gateway-epoch-1']")).toHaveTextContent("Demonstration data");
    expect(q("[data-evidence-source='s4-gateway-epoch-1']")).not.toHaveTextContent("SIMULATED");
    expect(q("[data-source-mode='SIMULATED']")).not.toBeNull();
    const { violations, scanned } = scanProductVocabulary(container, "finding evidence");
    expect(scanned).toBeGreaterThan(0);
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("selects one record into the address and links its stored record by exact accepted ID", async () => {
    const client = fake({ status: "loaded", value: body() });
    await mount(client, `?revision_id=${R2}`);
    const id = record(2).evidence_id;
    fireEvent.click(q(`[data-evidence-select='${id}']`) as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}&record=${id}`);
    const panel = q(`[data-evidence-record='${id}']`) as HTMLElement;
    expect(panel).toHaveTextContent("msg-2");
    expect(panel).toHaveTextContent("Foundation version 3");
    expect(q("[data-evidence-envelope-verified]")).not.toBeNull();
    expect(q(`[data-evidence-record-link='${id}']`)).toHaveAttribute("href", LINKS.record(id));
    expect(client.asked.every((a) => a.revisionId === R2)).toBe(true);
    const { violations } = scanProductVocabulary(document.body, "finding evidence record");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("pages to the full cited set through the address, keeping the version", async () => {
    const page1 = Array.from({ length: 50 }, (_, i) => record(i + 1));
    const page2 = Array.from({ length: 20 }, (_, i) => record(i + 51));
    const client = fake((a) => ({
      status: "loaded",
      value: body(
        {
          selection: { ...body().selection, selected_by: "EXACT_REVISION_ID" },
          page: a.offset === 0
            ? { offset: 0, limit: 50, total: 70, returned: 50, next_offset: 50 }
            : { offset: 50, limit: 50, total: 70, returned: 20, next_offset: null },
        },
        a.offset === 0 ? page1 : page2,
      ),
    }));
    await mount(client, `?revision_id=${R2}`);
    expect(q("[data-evidence-page-range]")).toHaveTextContent("Records 1–50 of 70");
    fireEvent.click(q("[data-evidence-page='next']") as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}&offset=50`);
    expect(q("[data-evidence-page-range]")).toHaveTextContent("Records 51–70 of 70");
    expect(client.asked.at(-1)).toEqual({ revisionId: R2, offset: 50, limit: 50 });
    fireEvent.click(q("[data-evidence-page='previous']") as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}`);
  });

  it("leads an earlier version with its non-current status", async () => {
    const value = body({
      selection: { revision_id: R1, revision_no: 1, selected_by: "EXACT_REVISION_ID", latest_revision_id: R2, is_latest: false, replay: "" },
    });
    await mount(fake({ status: "loaded", value }), `?revision_id=${R1}`);
    const lead = q("[data-evidence-earlier-version]") as HTMLElement;
    expect(lead).toHaveTextContent("Earlier version 1");
    expect(lead.querySelector("a")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}`);
    expect(q("[data-evidence-latest-at-read]")).toBeNull();
  });

  it("shows a closed source as a record only, with no Dispatch link", async () => {
    const base = body();
    const value = body({
      source_gate: { permitted: false, reason: "CUTOVER_CLOSED" },
      audit_only: { non_current: true, reason: "CUTOVER_CLOSED", statement: "Audit material only" },
      currentness: { state: "SOURCE_CLOSED" },
      selection: { ...base.selection, selected_by: "EXACT_REVISION_ID" },
      links: { ...base.links, performance: { status: "CLOSED" }, assessment_revisions: {} },
    });
    await mount(fake({ status: "loaded", value }), `?revision_id=${R2}`);
    const lead = q("[data-evidence-audit-only]") as HTMLElement;
    expect(lead).toHaveTextContent("Record only");
    // W1-UX-02: the record-only note is the first note of the answer card's state line, right after the state sentence.
    const card = lead.closest("[data-headline-card='finding-evidence']") as HTMLElement;
    expect(expectStateLineVisible(card)).toBe("For the record only");
    expect(statusNotes(lead)[0]).toBe(lead);
    expect(q("[data-evidence-dispatch-link]")).toBeNull();
    expect(q("[data-evidence-dispatch-withheld]")).toHaveTextContent("Not linked: record only");
  });

  it("names broken links in plain words and withholds the positive lineage claim", async () => {
    const missing = record(9, {
      resolved: false,
      lineage_status: "BROKEN",
      broken_links: ["ACCEPTED_EVIDENCE"],
      withheld: "no accepted record with this reference exists for this site, so no measurement, source or message is shown",
    });
    const tampered = record(2, { lineage_status: "BROKEN", broken_links: ["ENVELOPE_DIGEST"], envelope: { sha256: "ff", digest_verified: false } });
    const records = [record(1), tampered, missing];
    const value = body(
      {
        lineage: {
          ...body().lineage,
          status: "BROKEN",
          cited_set_digest: { status: "NOT_VERIFIED", recorded: "d1", reason: "cited IDs do not resolve" },
          broken_records: [
            { evidence_id: tampered.evidence_id, links: ["ENVELOPE_DIGEST"] },
            { evidence_id: missing.evidence_id, links: ["ACCEPTED_EVIDENCE"] },
          ],
        },
        counts: { ...body().counts, cited_unresolved: 1, cited_resolved: 2, cited_with_broken_lineage: 2 },
      },
      records,
    );
    await mount(fake({ status: "loaded", value }), `?revision_id=${R2}&record=${missing.evidence_id}`);
    expect(q("[data-evidence-lineage-complete]")).toBeNull();
    expect(q("[data-evidence-lineage-broken]")).not.toBeNull();
    expect(q(`[data-evidence-broken-record='${tampered.evidence_id}']`)).toHaveTextContent(
      "the stored original message does not match the check value saved with it",
    );
    expect(q("[data-evidence-page-range]")).toHaveTextContent("of 3");
    expect(q(`tr[data-evidence-id='${missing.evidence_id}'] [data-evidence-withheld]`)).toHaveTextContent("no measurement, source or message");
    expect(q(`[data-evidence-record='${missing.evidence_id}']`)).toHaveTextContent("No accepted record with this reference");
    expect(q("[data-evidence-record-link]")).toBeNull();
    const { violations } = scanProductVocabulary(document.body, "finding evidence broken");
    expect(violations, describeViolations(violations)).toEqual([]);
    expect(q("[data-evidence-inspector-withheld]")).not.toBeNull();
  });

  it("leads with the version's recorded state in plain words, for merged and not-confirmed versions", async () => {
    const base = body();
    for (const [lifecycle, words] of [
      ["MERGED", "joined into an earlier Finding"],
      ["UNCONFIRMED", "cannot confirm the earlier result"],
      ["NO_LONGER_SUPPORTED", "finds no possibly avoidable time"],
    ] as const) {
      const value = body({ revision: { ...base.revision, lifecycle } });
      const { unmount } = await mount(fake({ status: "loaded", value }));
      const lead = q("[data-evidence-lifecycle]") as HTMLElement;
      expect(lead).toHaveAttribute("data-evidence-lifecycle", lifecycle);
      expect(lead).toHaveTextContent(words);
      // N2: the Evidence page lists no versions below, so it never says so.
      expect(lead).not.toHaveTextContent("available below");
      if (lifecycle === "UNCONFIRMED") {
        expect(lead).toHaveTextContent("stay available in this Finding's history");
      }
      // W1-UX-02: the recorded state is the first note of the answer card's state line, beside the headline.
      expect(lead.closest(".headline-card__status")).not.toBeNull();
      expect(statusNotes(lead)[0]).toBe(lead);
      expectStateLineVisible(lead.closest("[data-headline-card='finding-evidence']") as HTMLElement);
      unmount();
    }
  });

  it("shows an unreadable avoidable-time value as a dash, not as zero minutes", async () => {
    const base = body();
    const value = body({ revision: { ...base.revision, minutes: { candidate: "not-a-number", necessary: "0", indeterminate: "0" } } });
    await mount(fake({ status: "loaded", value }));
    const fact = Array.from(document.querySelectorAll("dt")).find((d) => d.textContent === "Possibly avoidable time");
    expect(fact?.nextElementSibling).toHaveTextContent("–");
    expect(fact?.nextElementSibling).not.toHaveTextContent("0 min");
  });

  it("says a stored message is missing, not that it does not match", async () => {
    const gone = record(2, { lineage_status: "BROKEN", broken_links: ["ENVELOPE"], envelope: { sha256: "ab12cd34ef56", digest_verified: false } });
    const value = body({}, [record(1), gone]);
    await mount(fake({ status: "loaded", value }));
    const row = q(`tr[data-evidence-id='${gone.evidence_id}']`) as HTMLElement;
    expect(row).toHaveTextContent("stored message missing");
    expect(row).not.toHaveTextContent("(does not match)");
  });

  it("summarises inputs by measurement over the whole cited set, not the page, and states coverage and use as missing", async () => {
    // 102 cited records, 3 on this page: a page recount could never reach the whole-set totals.
    const value = body({ page: { offset: 0, limit: 50, total: 102, returned: 3, next_offset: 50 } });
    const { container } = await mount(fake({ status: "loaded", value }));
    const rows = Array.from(document.querySelectorAll("tr[data-evidence-input-role]"));
    // The read's whole-set aggregate, not a recount of the page's records.
    expect(rows.map((r) => [r.getAttribute("data-evidence-input-role"), r.getAttribute("data-evidence-input-count")])).toEqual(
      value.provenance.cited_evidence_by_role.map((g) => [g.role, String(g.count)]),
    );
    expect(rows.reduce((n, r) => n + Number(r.getAttribute("data-evidence-input-count")), 0)).toBe(value.counts.cited_total);
    expect(q("[data-evidence-inputs-scope]")).toHaveTextContent(`all ${value.counts.cited_total} cited records`);
    expect(q("[data-evidence-inputs-scope]")).not.toHaveTextContent("when opened");
    const coverage = q("[data-gap-id='G-finding-evidence-coverage']") as HTMLElement;
    const use = q("[data-gap-id='G-finding-evidence-use']") as HTMLElement;
    expect(coverage).toHaveAttribute("data-gap-placement", "finding-evidence.bundle.coverage");
    expect(use).toHaveAttribute("data-gap-placement", "finding-evidence.bundle.use");
    expect(coverage).toHaveTextContent("not available yet");
    expect(coverage.textContent).not.toContain("G-finding");
    const { violations } = scanProductVocabulary(container, "finding evidence inputs");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("never shows engineering text for an unknown link code and keeps the positive claim withheld", async () => {
    const odd = record(2, { lineage_status: "BROKEN", broken_links: ["NEW_UNREVIEWED_LINK"] });
    const base = body();
    const value = body(
      {
        lineage: {
          ...base.lineage,
          status: "BROKEN",
          words: { NEW_UNREVIEWED_LINK: "the envelope binding mapping cited_evidence_sha256 failed" },
          set_breaks: [{ link: "ANOTHER_NEW_LINK", detail: "raw backend envelope text" }],
          broken_records: [{ evidence_id: odd.evidence_id, links: ["NEW_UNREVIEWED_LINK"] }],
        },
      },
      [record(1), odd],
    );
    await mount(fake({ status: "loaded", value }), `?record=${odd.evidence_id}`);
    expect(q("[data-evidence-lineage-complete]")).toBeNull();
    expect(document.body.textContent).toContain("A record link could not be checked");
    expect(document.body.textContent).not.toMatch(/envelope|binding|mapping|cited_evidence_sha256/i);
    expect(q("[data-evidence-unknown-link='NEW_UNREVIEWED_LINK'] [data-evidence-technical-detail]")).toHaveTextContent("NEW_UNREVIEWED_LINK");
    expect(q("[data-evidence-set-break='ANOTHER_NEW_LINK']")).toHaveTextContent("A record link could not be checked");
  });

  it("does not show another record in place of one that is not on the page", async () => {
    await mount(fake({ status: "loaded", value: body() }), `?revision_id=${R2}&record=other-id`);
    expect(q("[data-evidence-record-absent]")).not.toBeNull();
    expect(q("[data-evidence-record]")).toBeNull();
  });

  it.each([
    ["unauthenticated", { status: "unauthenticated", message: null }],
    ["forbidden", { status: "forbidden", message: null }],
    ["not_found", { status: "not_found", message: "No such Finding or revision for this Site." }],
    ["closed", { status: "closed", message: null, note: null }],
    ["unavailable", { status: "unavailable", message: null }],
  ] as const)("states a %s refusal in plain language", async (status, result) => {
    await mount(fake(result as FindingReadResult<FindingEvidenceBody>), "?revision_id=foreign");
    expect(q(`[data-finding-read='${status}']`)).not.toBeNull();
    expect(q("[data-finding-evidence]")).toBeNull();
    expect(where()).toBe(`/sites/${SITE}/findings/${F}/evidence?revision_id=foreign`);
  });

  it("keeps an unknown pinned version in the address and offers the latest only as a choice", async () => {
    const client = fake({ status: "not_found", message: null });
    await mount(client, "?revision_id=foreign");
    expect(client.asked).toEqual([{ revisionId: "foreign", offset: 0, limit: 50 }]);
    expect(q("[data-finding-read='not_found']")).toHaveTextContent("not shown in its place");
    expect(q("[data-evidence-open-latest]")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence`);
  });
});

describe("Finding frame sections (S4-03 phase 2)", () => {
  const detail: SiteDetailClient = { getSite: async () => ({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

  async function frame(path: string, client: FindingClient) {
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          {["/sites/:siteId/findings/:findingId", "/sites/:siteId/findings/:findingId/:findingView"].map((p) => (
            <Route
              key={p}
              path={p}
              element={
                <>
                  <SiteFindingFrame detail={detail} sitesPath="/sites" findings={client} />
                  <Where />
                </>
              }
            />
          ))}
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
  }

  it("renders Evidence as a child view whose section links keep the exact version", async () => {
    const client = fake({ status: "loaded", value: body() });
    await frame(`/sites/${SITE}/findings/${F}/evidence?revision_id=${R1}`, client);
    expect(client.asked[0]?.revisionId).toBe(R1);
    expect(q("[data-finding-section='evidence']")).toHaveAttribute("aria-current", "page");
    expect(q("[data-finding-section='finding']")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}?revision_id=${R1}`);
    expect(q("[data-finding-section='evidence']")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence?revision_id=${R1}`);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Finding evidence");
  });

  it("refuses an unknown section name instead of showing another view", async () => {
    const client = fake({ status: "loaded", value: body() });
    await frame(`/sites/${SITE}/findings/${F}/ledger`, client);
    expect(q("[data-finding-read='not_found']")).toHaveTextContent("no section with that name");
    expect(client.asked).toEqual([]);
  });
});

describe("Old assessment-keyed Evidence tab (S4-03 phase 2)", () => {
  function windowClient(result: FindingReadResult<FindingWindowBody>): FindingClient & { days: string[] } {
    const days: string[] = [];
    return {
      days,
      getFinding: async () => ({ status: "not_found", message: null }),
      getFindingEvidence: async () => ({ status: "not_found", message: null }),
      getFindingHistory: async () => ({ status: "not_found", message: null }),
      getFindingWindow: async (_s, day) => {
        days.push(day);
        return result;
      },
    };
  }
  const windowBody = (ids: string[]): FindingWindowBody => ({
    day: "2026-10-09",
    state: "ASSESSED",
    note: "",
    assessment_status: "CURRENT",
    findings: ids.map((id) => ({
      finding_id: id,
      lifecycle: "SUPPORTED",
      episode_start: "2026-10-09T10:00:00+00:00",
      episode_end: "2026-10-09T11:00:00+00:00",
      cites_current_window_selection: true,
    })),
  });

  async function legacy(
    client: FindingClient,
    window: { start: string; end: string } = { start: "2026-10-09T10:00:00+00:00", end: "2026-10-09T11:00:00+00:00" },
  ) {
    render(
      <MemoryRouter initialEntries={[`/findings/${SITE}/assessment-1/evidence`]}>
        <Routes>
          <Route
            path="/findings/:siteId/:assessmentId/evidence"
            element={
              <LegacyFindingEvidence
                siteId={SITE}
                assessedWindow={window}
                findings={client}
                durableEvidenceHref={(id) => `/sites/${SITE}/findings/${id}/evidence`}
                recordsHref={`/sites/${SITE}/evidence`}
              />
            }
          />
          <Route path="*" element={<Where />} />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
  }

  it("shows a single day-level candidate as a labelled link and never redirects", async () => {
    const client = windowClient({ status: "loaded", value: windowBody([F]) });
    await legacy(client);
    expect(client.days).toEqual(["2026-10-09"]);
    expect(screen.getByRole("heading", { name: "Findings recorded for this day" })).toBeInTheDocument();
    expect(q("[data-legacy-evidence='candidates']")).toHaveTextContent("does not say this assessment created or cites it");
    const link = q(`[data-legacy-evidence-link='${F}']`);
    expect(link).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence`);
    expect(link).not.toHaveTextContent("Evidence for this Finding");
    // Still on the legacy route: nothing navigated.
    expect(screen.queryByTestId("where")).toBeNull();
  });

  it("lists several overlapping Findings as links", async () => {
    await legacy(windowClient({ status: "loaded", value: windowBody([F, "other-finding"]) }));
    expect(q("[data-legacy-evidence='candidates']")).toHaveTextContent("2 saved Findings overlap");
    expect(document.querySelectorAll("[data-legacy-evidence-link]")).toHaveLength(2);
  });

  it("excludes an unrelated same-day Finding and one that only touches the window start", async () => {
    const mk = (id: string, start: string, end: string) => ({
      finding_id: id,
      lifecycle: "SUPPORTED" as const,
      episode_start: start,
      episode_end: end,
      cites_current_window_selection: false,
    });
    const value: FindingWindowBody = {
      ...windowBody([]),
      findings: [
        mk("unrelated", "2026-10-09T14:00:00+00:00", "2026-10-09T15:00:00+00:00"),
        mk("touches-start", "2026-10-09T09:00:00+00:00", "2026-10-09T10:00:00+00:00"),
        mk("touches-end", "2026-10-09T11:00:00+00:00", "2026-10-09T12:00:00+00:00"),
        mk("overlaps", "2026-10-09T10:30:00+00:00", "2026-10-09T12:00:00+00:00"),
      ],
    };
    await legacy(windowClient({ status: "loaded", value }));
    expect(Array.from(document.querySelectorAll("[data-legacy-evidence-link]")).map((e) => e.getAttribute("data-legacy-evidence-link"))).toEqual([
      "overlaps",
    ]);
  });

  it("excludes a Finding that ends exactly at 00:00 of the window's day", async () => {
    const value: FindingWindowBody = {
      ...windowBody([]),
      findings: [
        {
          finding_id: "yesterday",
          lifecycle: "SUPPORTED",
          episode_start: "2026-10-08T22:00:00+00:00",
          episode_end: "2026-10-09T00:00:00+00:00",
          cites_current_window_selection: false,
        },
      ],
    };
    await legacy(windowClient({ status: "loaded", value }), { start: "2026-10-09T00:00:00+00:00", end: "2026-10-09T01:00:00+00:00" });
    expect(q("[data-legacy-evidence='none']")).not.toBeNull();
    expect(q("[data-legacy-evidence-link]")).toBeNull();
  });

  it("reads every UTC day a window crossing midnight touches", async () => {
    const byDay: Record<string, string> = { "2026-10-09": "day-one", "2026-10-10": "day-two" };
    const days: string[] = [];
    const client: FindingClient = {
      getFinding: async () => ({ status: "not_found", message: null }),
      getFindingEvidence: async () => ({ status: "not_found", message: null }),
      getFindingHistory: async () => ({ status: "not_found", message: null }),
      getFindingWindow: async (_s, day) => {
        days.push(day);
        return {
          status: "loaded",
          value: {
            ...windowBody([]),
            day,
            findings: [
              {
                finding_id: byDay[day],
                lifecycle: "SUPPORTED",
                episode_start: day === "2026-10-09" ? "2026-10-09T23:30:00+00:00" : "2026-10-10T00:00:00+00:00",
                episode_end: day === "2026-10-09" ? "2026-10-10T00:00:00+00:00" : "2026-10-10T00:20:00+00:00",
                cites_current_window_selection: false,
              },
            ],
          },
        };
      },
    };
    await legacy(client, { start: "2026-10-09T23:00:00+00:00", end: "2026-10-10T01:00:00+00:00" });
    expect(days.sort()).toEqual(["2026-10-09", "2026-10-10"]);
    expect(document.querySelectorAll("[data-legacy-evidence-link]")).toHaveLength(2);
    // N3: two days are named as such, never "this day" / "the same day".
    expect(screen.getByRole("heading", { name: "Findings recorded for these days" })).toBeInTheDocument();
    for (const link of Array.from(document.querySelectorAll("[data-legacy-evidence-link]"))) {
      expect(link).toHaveTextContent("(recorded for an overlapping day)");
      expect(link).not.toHaveTextContent("same day");
    }
  });

  it("states that no saved Finding is recorded for the period", async () => {
    await legacy(windowClient({ status: "loaded", value: windowBody([]) }));
    expect(q("[data-legacy-evidence='none']")).toHaveTextContent("No saved Finding overlaps this assessed period (2026-10-09)");
  });

  it("states an unreadable Finding read without showing a second evidence list", async () => {
    await legacy(windowClient({ status: "unavailable", message: null }));
    expect(q("[data-legacy-evidence='unavailable']")).not.toBeNull();
    expect(q("[data-evidence-id]")).toBeNull();
  });
});

describe("Finding Evidence client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("asks for the exact version and page and maps a closed source", async () => {
    const paths: string[] = [];
    vi.stubGlobal("fetch", async (path: string) => {
      paths.push(path);
      return new Response(JSON.stringify({ detail: { code: "PERFORMANCE_CUTOVER_CLOSED", message: "closed" } }), { status: 409 });
    });
    const read = await createFindingClient().getFindingEvidence("KOBO-001", F, "rev 1", 50, 50);
    expect(paths).toEqual([`/api/sites/KOBO-001/findings/${F}/evidence?revision_id=rev+1&offset=50&limit=50`]);
    expect(read.status).toBe("closed");
  });

  it("loads a well-formed body and refuses a malformed one as unavailable", async () => {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify(body()), { status: 200 }));
    expect((await createFindingClient().getFindingEvidence("KOBO-001", F, null, 0, 50)).status).toBe("loaded");
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify({ records: [] }), { status: 200 }));
    expect((await createFindingClient().getFindingEvidence("KOBO-001", F, null, 0, 50)).status).toBe("unavailable");
  });

  it("names a mixed stored source with its problem records in a closed disclosure (S4-05b)", async () => {
    const { container } = await mount(fake({ status: "loaded", value: body({ source_provenance: stored("MIXED") }) }));
    await settledScreen();
    const notice = container.querySelector("[data-source-provenance-subject='evidence']") as HTMLElement;
    expect(notice).toHaveAttribute("data-source-provenance", "MIXED");
    expect(notice).toHaveTextContent("Sources do not agree.");
    expect(notice.querySelector("details")).not.toHaveAttribute("open");
    expect(notice.querySelector("[data-source-reason='BOUND_AND_UNBOUND']")).not.toBeNull();
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

/** The card's default reading: its text without the closed exact-reference disclosure. */
function defaultReading(card: HTMLElement): string {
  const copy = card.cloneNode(true) as HTMLElement;
  copy.querySelectorAll("details[data-exact-references]").forEach((d) => d.remove());
  return copy.textContent ?? "";
}

describe("W1-UX-02: Finding Evidence answer card", () => {
  it("rewords only backend-held link codes on screen, keeping every code and banning the W1 word", () => {
    for (const key of Object.keys(LINK_DISPLAY_OVERRIDES)) expect(Object.keys(LINK_WORDS)).toContain(key);
    expect(Object.keys(LINK_DISPLAY_WORDS).sort()).toEqual(Object.keys(LINK_WORDS).sort());
    for (const text of Object.values(LINK_DISPLAY_WORDS)) expect(text).not.toMatch(/fingerprint/i);
  });

  const card = () => document.querySelector("[data-headline-card='finding-evidence']") as HTMLElement;
  const main = () => document.querySelector("main") as HTMLElement;
  const steps = () => Array.from(card().querySelectorAll("[data-step-strip] li")).map((li) => [li.querySelector(".step-strip__label")?.textContent, li.getAttribute("data-step")]);

  it("W1-UX-02: leads with the supporting records and a record trail; exact references last; W1 vocabulary on <main>", async () => {
    await mount(fake({ status: "loaded", value: body() }));
    const answer = card();
    expect(answer.querySelector(".headline-card__question")?.textContent).toBe("Which accepted records support this Finding?");
    expect(answer.querySelector("h2")?.textContent).toBe("Evidence for version 2");
    expect(answer.querySelector(".headline-card__headline")?.textContent).toBe("3 cited records, each traced back to its accepted record");
    // The latest-at-read version is not claimed current: neutral words, plain "as of" the version's recorded time.
    expect(expectStateLineVisible(answer)).toBe("Latest recorded version when read");
    expect(answer.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(answer.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 9 Oct 2026, 12:00 UTC");
    expect(steps()).toEqual([
      ["Accepted record", "done"], ["Delivery batch", "done"], ["Stored message", "done"], ["Site setup", "done"], ["Assessment", "done"],
    ]);
    // Model version and exact references are labelled detail, not the default reading.
    expect(defaultReading(answer)).not.toContain("dispatch-3.1");
    expect(defaultReading(answer)).not.toContain(F);
    const refs = answer.querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(refs.open).toBe(false);
    expect(answer.querySelector(".headline-card__body")?.lastElementChild).toBe(refs);
    expect(Array.from(refs.querySelectorAll("dt")).map((dt) => dt.textContent)).toEqual([
      "Finding reference", "Shown version reference", "Latest version reference", "How the version was chosen", "Assessment method reference", "Cited set check code",
    ]);
    // Exact selectors keep working from the card.
    expect(q("[data-evidence-back-to-finding]")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}?revision_id=${R2}`);
    expect(q("[data-evidence-pin]")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}`);
    // MissingClaims for coverage and use stay in place.
    expect(q("[data-gap-id='G-finding-evidence-coverage']")).toHaveAttribute("data-gap-placement", "finding-evidence.bundle.coverage");
    expect(q("[data-gap-id='G-finding-evidence-use']")).toHaveAttribute("data-gap-placement", "finding-evidence.bundle.use");
    const w1 = scanProductVocabulary(main(), "finding evidence (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(40);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const disclosure = scanDisclosureVocabulary(answer, "finding evidence exact references");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(5);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
  });

  it("W1-UX-02: an earlier (historical) version and a record-only version keep their state line visible", async () => {
    const earlier = body({
      selection: { revision_id: R1, revision_no: 1, selected_by: "EXACT_REVISION_ID", latest_revision_id: R2, is_latest: false, replay: "" },
    });
    const a = await mount(fake({ status: "loaded", value: earlier }), `?revision_id=${R1}`);
    expect(expectStateLineVisible(card())).toBe("Earlier version, kept for the record");
    expect(card().querySelector("[data-evidence-earlier-version] a")).toHaveAttribute("href", `/sites/${SITE}/findings/${F}/evidence?revision_id=${R2}`);
    let w1 = scanProductVocabulary(main(), "finding evidence earlier (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    a.unmount();

    const base = body();
    const closed = body({
      audit_only: { non_current: true, reason: "CUTOVER_CLOSED", statement: "Audit material only" },
      selection: { ...base.selection, selected_by: "EXACT_REVISION_ID" },
      links: { ...base.links, performance: { status: "CLOSED" }, assessment_revisions: {} },
    });
    await mount(fake({ status: "loaded", value: closed }), `?revision_id=${R2}`);
    expect(expectStateLineVisible(card())).toBe("For the record only");
    w1 = scanProductVocabulary(main(), "finding evidence record only (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("W1-UX-02: a broken trail marks only the broken steps; an unknown link leaves the others not known, never done", async () => {
    const tampered = record(2, { lineage_status: "BROKEN", broken_links: ["ENVELOPE_DIGEST"], envelope: { sha256: "ff", digest_verified: false } });
    const broken = body(
      { lineage: { ...body().lineage, status: "BROKEN", broken_records: [{ evidence_id: tampered.evidence_id, links: ["ENVELOPE_DIGEST"] }] } },
      [record(1), tampered],
    );
    const a = await mount(fake({ status: "loaded", value: broken }));
    expect(card().querySelector(".headline-card__headline")?.textContent).toBe("2 cited records; part of the record trail does not resolve");
    expect(steps()).toEqual([
      ["Accepted record", "done"], ["Delivery batch", "done"], ["Stored message", "problem"], ["Site setup", "done"], ["Assessment", "done"],
    ]);
    expectStateLineVisible(card());
    const w1 = scanProductVocabulary(main(), "finding evidence broken (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    a.unmount();

    const odd = body({ lineage: { ...body().lineage, status: "BROKEN", set_breaks: [{ link: "ANOTHER_NEW_LINK", detail: "x" }] } });
    await mount(fake({ status: "loaded", value: odd }));
    expect(steps().every(([, state]) => state === "not-known")).toBe(true);
    expectStateLineVisible(card());
  });

  it("W1-UX-02: an unknown stored source is named beside the state line (S4-05), never as a positive source", async () => {
    await mount(fake({ status: "loaded", value: body() }));
    const source = card().querySelector("[data-source-provenance-subject='evidence']") as HTMLElement;
    expect(source).toHaveAttribute("data-source-provenance", "UNKNOWN");
    expect(source).toHaveTextContent("Source unverified.");
    expect(source.closest(".headline-card__status")).not.toBeNull();
    expect(visibleOutsideClosedDisclosure(source)).toBe(true);
    expectStateLineVisible(card());
  });

  it.each([
    ["not_found", "This record was not found"],
    ["forbidden", "This cannot be shown to you"],
    ["closed", "Not released for use yet"],
    ["unavailable", "This could not be read right now"],
  ] as const)("W1-UX-02: a %s read shows a plain state line, not an empty evidence list", async (status, label) => {
    const result = (status === "closed" ? { status, message: null, note: null } : { status, message: null }) as FindingReadResult<FindingEvidenceBody>;
    await mount(fake(result), "?revision_id=foreign");
    expect(expectUntimedStateLine(card())).toBe(label);
    expect(q("[data-finding-evidence]")).toBeNull();
    const w1 = scanProductVocabulary(main(), `finding evidence ${status} (W1)`, { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });
});
