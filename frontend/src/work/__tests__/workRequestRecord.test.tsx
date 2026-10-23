/**
 * W6-01c C3: the work request Maintenance record page (`wr-record`), against `.agent/W6-01-build-spec.md` "C1-C3
 * pre-flight rulings" P-C3-1..5 (six mock rows per selected head, earlier versions, the REC notice and its staged
 * plain-text codes), A2Q7 (footer as Panel description), CL3-1 loading copy and R7 settling.
 */
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { WORK_REQUEST_RECORD_ROUTE_PATH } from "../../shell/operatorSiteRoutes";
import { expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type {
  GlobalWorkClient,
  GlobalWorkDetailBody,
  GlobalWorkDetailOperationalRecord,
  GlobalWorkDetailQuery,
  GlobalWorkDetailResult,
  WorkCaseDetailRecord,
} from "../globalWorkClient";
import { WorkRequestRecordFrame } from "../WorkRequestRecord";

const CASE = "6f1c2d3e-4a5b-4c6d-8e7f-001122334455";
const PAGE = `/maintenance/requests/${CASE}/record?site_id=KOBO-001`;
const OVERVIEW = `/maintenance/requests/${CASE}?site_id=KOBO-001`;
const RECORD = PAGE;
const HISTORY = `/maintenance/requests/${CASE}/history?site_id=KOBO-001`;
const KNOWN = "2026-10-20T12:00:01Z";
const ACTIVITY4000 = "Starter relay re-made and torqued ".repeat(150).slice(0, 4000);
const ITEMS = [
  "Technician notes",
  "Parts",
  "Time on site",
  "Return-to-service reading",
  "Configuration readback",
  "Witnessed automatic start",
];

function rec(id: string, over: Partial<WorkCaseDetailRecord> = {}): WorkCaseDetailRecord {
  return {
    id: `00000000-0000-4000-8000-000000000${id}`,
    activity: "Replaced starter relay and tested the start.",
    outcome_note: null,
    occurred_at: "2026-10-20T11:59:03Z",
    recorded_at: "2026-10-20T11:59:03Z",
    supersedes_record_id: null,
    ...over,
  };
}

function oprec(code: string, kind: string, n: number): GlobalWorkDetailOperationalRecord {
  return {
    canonical_record_id: `00000000-0000-4000-8000-00000000050${n}`,
    head_id: `00000000-0000-4000-8000-00000000050${n}`,
    code,
    kind,
    body: "Operator checked the panel.",
    root_occurred_at: "2026-10-18T12:00:00Z",
    occurred_at: "2026-10-18T12:00:00Z",
    recorded_at: "2026-10-20T11:59:09Z",
  };
}

function detail(records: WorkCaseDetailRecord[] = [rec("401")], over: Partial<GlobalWorkDetailBody> = {}): GlobalWorkDetailBody {
  return {
    schema_version: "global-work-detail-1",
    selected: {
      site_code: "KOBO-001",
      site_id: "00000000-0000-4000-8000-000000000002",
      case_id: CASE,
      case_code: "WR-000001",
      case_kind: "MAINTENANCE_REQUEST",
      known_at: "2026-10-22T12:00:00.000000Z",
    },
    work_detail: {
      schema_version: "work-case-detail-1",
      site_code: "KOBO-001",
      case: {
        id: CASE,
        code: "WR-000001",
        kind: "MAINTENANCE_REQUEST",
        asset_id: null,
        occurred_at: "2026-10-18T10:00:00Z",
        created_at: "2026-10-20T11:59:00Z",
        state: "IN_PROGRESS",
        incident_id: null,
      },
      selected_revision: {
        id: "00000000-0000-4000-8000-000000000201",
        revision_no: 2,
        supersedes_revision_id: "00000000-0000-4000-8000-000000000200",
        title: "Inspect starter and control circuit again",
        narrative: "Starter inspection requested.",
        reason: "Scope widened",
        recorded_at: "2026-10-20T11:59:06Z",
        actor_kind: "SERVICE",
        actor_id: "service:w401-fixture",
        occurred_at: "2026-10-20T11:59:06Z",
      },
      finding_links: [],
      action_links: [],
      cited_accepted_evidence_ids: [],
      events: [],
      records,
      source_provenance: {
        classification: "AUTHORED_DEMONSTRATION",
        state: "KNOWN",
        source_ids: [],
        evidence_ids: [],
        basis_sha256: `sha256:${"0".repeat(64)}`,
        reasons: [],
      },
      coverage: { state: "COMPLETE", reason: null },
    },
    work_asset: null,
    history: { revisions: [], operational_records: [oprec("REC-000003", "OPERATOR_LOG", 1)] },
    links: {
      site: { label: "Kobo", href: "/sites/KOBO-001" },
      overview: { label: "Overview", href: OVERVIEW },
      record: { label: "Maintenance record", href: RECORD },
      history: { label: "History", href: HISTORY },
      source_incident: null,
      findings: [],
      actions: [],
    },
    ...over,
  };
}

function client(answer: GlobalWorkDetailResult, gate?: Promise<void>): GlobalWorkClient & { calls: GlobalWorkDetailQuery[] } {
  const calls: GlobalWorkDetailQuery[] = [];
  return {
    calls,
    async incidents() {
      throw new Error("the record page never reads incidents");
    },
    async detail(query) {
      calls.push(query);
      if (gate) await gate;
      return answer;
    },
  };
}

const loaded = (value: GlobalWorkDetailBody): GlobalWorkDetailResult => ({ status: "loaded", value });

function mount(path: string, reads: GlobalWorkClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={WORK_REQUEST_RECORD_ROUTE_PATH} element={<WorkRequestRecordFrame client={reads} />} />
      </Routes>
    </MemoryRouter>,
  );
}

/** R7: settle the store read, then wait for the loading line to leave. */
async function settled() {
  await settledScreen();
  await waitFor(() => expect(document.querySelector("[data-global-work-loading]")).toBeNull());
}

const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const q = (selector: string) => document.querySelector(selector);
const qa = (selector: string, root: ParentNode = document) => Array.from(root.querySelectorAll(selector));
/** One row's four cells: item, detail, status, basis. */
const row = (group: Element, item: string) =>
  qa("th, td", group.querySelector(`[data-work-record-item="${item}"]`) as Element).map((c) => text(c));

afterEach(() => {
  cleanup();
});

describe("W6-01c C3: work request Maintenance record", () => {
  it("renders the mock header, live Record tab, the four-column table with six rows, footer and REC notice", async () => {
    const reads = client(loaded(detail()));
    mount(PAGE, reads);
    await settled();

    expect(reads.calls).toEqual([{ case_id: CASE, site_id: "KOBO-001", known_at: null }]);
    expect(screen.getByRole("heading", { level: 1, name: "Inspect starter and control circuit again" })).toBeInTheDocument();
    expect(text(q(".page-header p"))).toBe("WR-000001 · Kobo · corrective");
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(text(crumbs.querySelector("[aria-current='page']"))).toBe("Maintenance record");
    expect(screen.getByRole("link", { name: "Open site" })).toHaveAttribute("href", "/sites/KOBO-001");

    // P-C3-5: Overview and Maintenance record live, Record current. W6-01d C4 (P-C4-2): History live; Verification
    // unavailable.
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", OVERVIEW);
    expect(within(tabs).getByRole("link", { name: "Overview" })).not.toHaveAttribute("aria-current");
    const record = within(tabs).getByRole("link", { name: "Maintenance record" });
    expect(record).toHaveAttribute("href", RECORD);
    expect(record).toHaveAttribute("aria-current", "page");
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("href", HISTORY);
    expect(within(tabs).getByRole("link", { name: "History" })).not.toHaveAttribute("aria-current");
    expect(qa("li", tabs).map((li) => text(li))).toEqual([
      "Overview",
      "Maintenance record",
      "Verification · Not available yet",
      "History",
    ]);
    expect(text(q("[data-work-request-asof]"))).toBe("As known at 22 Oct 2026, 12:00 UTC");
    expect(q(".v69-mheader")).not.toBeNull();

    expectV69Panels("wr-record");
    const panel = screen.getByRole("heading", { level: 2, name: "Maintenance record · activity" }).closest("section") as HTMLElement;
    expect(text(panel)).toContain("What was recorded on site; no outcome verification follows from this entry.");
    expect(qa("thead th", panel).map((th) => text(th))).toEqual(["Item", "Detail", "Status", "Basis"]);
    const groups = qa("[data-work-record-group]", panel);
    expect(groups).toHaveLength(1);
    expect(text(groups[0].querySelector("[data-work-record-group-heading]"))).toBe("Record 1 · 20 Oct 2026, 11:59 UTC");
    expect(qa("[data-work-record-item]", groups[0]).map((tr) => tr.getAttribute("data-work-record-item"))).toEqual(ITEMS);
    const notes = row(groups[0], "Technician notes");
    expect(notes[0]).toBe("Technician notes");
    expect(notes[1]).toContain("Replaced starter relay and tested the start.");
    expect(notes[1]).toContain("Outcome note: No outcome note recorded");
    expect(notes.slice(2)).toEqual(["Recorded", "Authored maintenance record"]);
    expect(row(groups[0], "Time on site")).toEqual(["Time on site", "20 Oct 2026, 11:59 UTC", "Recorded", "Authored time"]);
    for (const item of ["Parts", "Return-to-service reading", "Configuration readback", "Witnessed automatic start"]) {
      expect(row(groups[0], item)).toEqual([item, "Not recorded", "Not established", "No stored field"]);
    }
    expect(q("[data-work-record-earlier]")).toBeNull();
    expect(q("[data-work-record-outcome-basis]")).toBeNull();
    // No pager on the record panel (X7).
    expect(screen.queryByRole("button", { name: "Next" })).toBeNull();

    // P-C3-3: the notice sits under the table, after the panel.
    const notice = q("[data-work-record-notice]") as HTMLElement;
    expect(panel.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  // W6-01e E2 (P-E2-10): the C3 staged plain-text REC codes are promoted to live Operational records links.
  const DAY = `from=${encodeURIComponent("2026-10-18T00:00:00Z")}&to=${encodeURIComponent("2026-10-19T00:00:00Z")}`;

  it("linked_rec_filtered_window_href: one linked REC opens its root-occurrence day and kind, with no cutoff", async () => {
    const body = detail();
    mount(PAGE, client(loaded({ ...body, selected: { ...body.selected, known_at: "2026-10-23T08:00:00.123456Z" } })));
    await settled();
    const notice = q('[data-work-record-notice="linked"]') as HTMLElement;
    expect(text(notice)).toBe("This record is also listed in Operational records as REC-000003 (Operator log).");
    expect(within(notice).getByRole("link", { name: "REC-000003" })).toHaveAttribute(
      "href",
      `/operational-records?${DAY}&kind=OPERATOR_LOG`,
    );
    expect(notice.textContent).not.toContain("being prepared");
  });

  it("linked_rec_filtered_window_href: several linked RECs keep the C1 order; an explicit cutoff is carried exactly", async () => {
    const recs = [oprec("REC-000009", "SITE_VISIT", 1), oprec("REC-000003", "OPERATOR_LOG", 2), oprec("REC-000011", "MANUAL_READING", 3)];
    recs[2] = { ...recs[2], root_occurred_at: "2026-10-31T23:59:59.999999Z" };
    const cut = `&known_at=${encodeURIComponent(KNOWN)}`;
    mount(`${PAGE}${cut}`, client(loaded(detail(undefined, { history: { revisions: [], operational_records: recs } }))));
    await settled();
    const notice = q("[data-work-record-notice]") as HTMLElement;
    expect(text(notice)).toBe(
      "This record is also listed in Operational records as REC-000009 (Site visit), REC-000003 (Operator log), " +
        "REC-000011 (Manual reading).",
    );
    expect(Array.from(notice.querySelectorAll("a")).map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      ["REC-000009", `/operational-records?${DAY}&kind=SITE_VISIT${cut}`],
      ["REC-000003", `/operational-records?${DAY}&kind=OPERATOR_LOG${cut}`],
      [
        "REC-000011",
        `/operational-records?from=${encodeURIComponent("2026-10-31T00:00:00Z")}&to=${encodeURIComponent("2026-11-01T00:00:00Z")}&kind=MANUAL_READING${cut}`,
      ],
    ]);
  });

  it("states No maintenance activity recorded and No linked Operational record. with no records", async () => {
    mount(PAGE, client(loaded(detail([], { history: { revisions: [], operational_records: [] } }))));
    await settled();
    expect(text(q("[data-work-record-empty]"))).toBe("No maintenance activity recorded");
    expect(q(".data-table")).toBeNull();
    expect(text(q('[data-work-record-notice="none"]'))).toBe("No linked Operational record.");
    expectV69Panels("wr-record");
  });

  it("shows the selected correction head with its earlier versions disclosed inside Technician notes", async () => {
    const v1 = rec("401", { activity: "First note: relay loose.", recorded_at: "2026-10-20T11:59:03Z" });
    const v2 = rec("402", {
      activity: "Second note: relay re-made.",
      recorded_at: "2026-10-20T11:59:10Z",
      supersedes_record_id: v1.id,
    });
    const v3 = rec("403", {
      activity: "Corrected note: relay re-made and torqued.",
      outcome_note: "Start succeeded on test.",
      recorded_at: "2026-10-20T11:59:20Z",
      supersedes_record_id: v2.id,
    });
    mount(PAGE, client(loaded(detail([v1, v3, v2]))));
    await settled();
    const groups = qa("[data-work-record-group]");
    expect(groups).toHaveLength(1);
    expect(groups[0].getAttribute("data-work-record-group")).toBe(v3.id);
    const cell = groups[0].querySelector('[data-work-record-item="Technician notes"] td') as HTMLElement;
    expect(text(cell.querySelector('[data-work-record-clamp="activity"]'))).toBe("Corrected note: relay re-made and torqued.");
    expect(text(cell.querySelector('[data-work-record-outcome="recorded"]'))).toBe(
      "Outcome note: Start succeeded on test.Unverified · Authored note",
    );
    const earlier = cell.querySelector("[data-work-record-earlier]") as HTMLElement;
    expect(earlier.tagName).toBe("DETAILS");
    expect(text(earlier.querySelector("summary"))).toBe("Earlier record versions");
    expect(qa("[data-work-record-version]", earlier).map((li) => li.getAttribute("data-work-record-version"))).toEqual([v2.id, v1.id]);
    expect(text(earlier)).toContain("Second note: relay re-made.");
    expect(text(earlier)).toContain("First note: relay loose.");
    // The superseded versions never form their own group.
    expect(text(q(".data-table"))).not.toContain("Record 2");
  });

  it("groups several heads by Record {n} · {occurred_at UTC}, ordered (occurred_at, id), six rows each", async () => {
    const late = rec("401", { activity: "Late visit.", occurred_at: "2026-10-19T09:00:00Z" });
    const tieB = rec("403", { activity: "Tie B.", occurred_at: "2026-10-18T08:00:00Z" });
    const tieA = rec("402", { activity: "Tie A.", occurred_at: "2026-10-18T08:00:00Z" });
    mount(PAGE, client(loaded(detail([late, tieB, tieA]))));
    await settled();
    const groups = qa("[data-work-record-group]");
    expect(groups.map((g) => g.getAttribute("data-work-record-group"))).toEqual([tieA.id, tieB.id, late.id]);
    expect(groups.map((g) => text(g.querySelector("[data-work-record-group-heading]")))).toEqual([
      "Record 1 · 18 Oct 2026, 08:00 UTC",
      "Record 2 · 18 Oct 2026, 08:00 UTC",
      "Record 3 · 19 Oct 2026, 09:00 UTC",
    ]);
    for (const g of groups) expect(qa("[data-work-record-item]", g)).toHaveLength(6);
  });

  it("previews a 4000-character activity in three lines with its Full activity text disclosure", async () => {
    mount(PAGE, client(loaded(detail([rec("401", { activity: ACTIVITY4000 })]))));
    await settled();
    const clamp = q('[data-work-record-clamp="activity"]') as HTMLElement;
    expect(clamp.className).toContain("global-work-clamp");
    expect(clamp.textContent).toBe(ACTIVITY4000);
    const full = q('[data-work-record-full="activity"]') as HTMLElement;
    expect(full.tagName).toBe("DETAILS");
    expect(text(full.querySelector("summary"))).toBe("Full activity text");
    expect(full.textContent).toBe(`Full activity text${ACTIVITY4000}`);
  });

  it("states loading with the ruled literals and builds both live tabs from the validated inputs", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    mount(PAGE, client(loaded(detail()), gate));
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Work request" })).toBeInTheDocument();
    expect(text(q("[data-global-work-loading]"))).toBe("Loading the work request.");
    expect(text(screen.getByRole("navigation", { name: "Breadcrumb" }))).toBe("MaintenanceWork requestMaintenance record");
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", OVERVIEW);
    expect(within(tabs).getByRole("link", { name: "Maintenance record" })).toHaveAttribute("href", RECORD);
    expect(screen.getByRole("heading", { level: 2, name: "Maintenance record · activity" })).toBeInTheDocument();
    expect(q(".data-table")).toBeNull();
    expect(q("[data-work-record-notice]")).toBeNull();
    release();
    await settled();
    expect(q(".data-table")).not.toBeNull();
  });

  it.each([
    ["UNAUTHENTICATED", "Sign in to see work records."],
    ["SITE_SCOPE_FORBIDDEN", "No access to this Site's work request."],
    ["WORK_CASE_NOT_FOUND", "No work case with this ID at this site."],
    ["WORK_STORE_UNAVAILABLE", "Work records could not be read. Reload."],
  ] as const)("states the %s refusal, keeps the panel slot and renders no notice", async (code, sentence) => {
    mount(PAGE, client({ status: "refused", code }));
    await settled();
    expect(screen.getByRole("heading", { level: 1, name: "Work request" })).toBeInTheDocument();
    expect(text(q(`[data-page-refusal="${code}"]`))).toBe(sentence);
    expect(text(q("[data-work-request-unavailable]"))).toBe("Work request unavailable.");
    expect(within(screen.getByRole("navigation", { name: "Context tabs" })).getByRole("link", { name: "Maintenance record" })).toHaveAttribute(
      "href",
      RECORD,
    );
    expect(screen.getByRole("heading", { level: 2, name: "Maintenance record · activity" })).toBeInTheDocument();
    expect(q("[data-work-record-notice]")).toBeNull();
    expectV69Panels("wr-record");
  });

  it("does not fetch without a site_id and renders the tabs as text", async () => {
    const reads = client(loaded(detail()));
    mount(`/maintenance/requests/${CASE}/record`, reads);
    await settled();
    expect(reads.calls).toEqual([]);
    expect(text(q('[data-page-refusal="NO_SITE"]'))).toBe("No work case with this ID at this site.");
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).queryByRole("link")).toBeNull();
    expect(text(tabs)).toContain("Maintenance record");
  });

  it("labels an explicit cutoff Historical and keeps it on both live tabs", async () => {
    const cut = `&known_at=${encodeURIComponent(KNOWN)}`;
    const body = detail(undefined, {
      selected: { ...detail().selected, known_at: "2026-10-20T12:00:01.000000Z" },
      links: {
        ...detail().links,
        overview: { label: "Overview", href: `${OVERVIEW}${cut}` },
        record: { label: "Maintenance record", href: `${RECORD}${cut}` },
        history: { label: "History", href: `${HISTORY}${cut}` },
      },
    });
    const withCut = client(loaded(body));
    mount(`${PAGE}${cut}`, withCut);
    await settled();
    expect(withCut.calls).toEqual([{ case_id: CASE, site_id: "KOBO-001", known_at: KNOWN }]);
    expect(text(q("[data-work-request-asof]"))).toBe("Historical as of 20 Oct 2026, 12:00 UTC");
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", `${OVERVIEW}${cut}`);
    expect(within(tabs).getByRole("link", { name: "Maintenance record" })).toHaveAttribute("href", `${RECORD}${cut}`);
    // W6-01d C4 (P-C4-2): the explicit cutoff stays on the live History tab; Verification stays unavailable.
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("href", `${HISTORY}${cut}`);
    expect(text(tabs)).toContain("Verification · Not available yet");
  });
});

describe("W6-01c C3: the record route in the app shell", () => {
  it("mounts the Maintenance record under the operator shell with the rail's Maintenance root current", async () => {
    expect(WORK_REQUEST_RECORD_ROUTE_PATH).toBe("/maintenance/requests/:caseId/record");
    const reads = client(loaded(detail()));
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <App flags={featureFlagsWith(false)} globalWork={reads} />
      </MemoryRouter>,
    );
    await settled();
    expect(screen.getByRole("main", { name: "Inspect starter and control circuit again" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Maintenance record · activity" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    expect(within(rail).getByRole("link", { name: "Maintenance" })).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});
