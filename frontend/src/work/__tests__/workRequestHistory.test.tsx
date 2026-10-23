/**
 * W6-01d C4: the work request History (`.agent/W6-01-build-spec.md` "C4 pre-flight rulings" P-C4-1..22). Typed
 * responses only; the persisted current, historical, CANCEL, linked, stress and refusal states are captured against
 * the real API in `.agent/W6-01-evidence/C4/`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { WORK_REQUEST_HISTORY_ROUTE_PATH } from "../../shell/operatorSiteRoutes";
import { expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import {
  createGlobalWorkClient,
  type GlobalWorkClient,
  type GlobalWorkDetailBody,
  type GlobalWorkDetailQuery,
  type GlobalWorkDetailResult,
  type GlobalWorkDetailRevision,
  type WorkCaseDetailEvent,
} from "../globalWorkClient";
import { WorkRequestHistoryFrame, historyReadable, historyRows, historyUtc } from "../WorkRequestHistory";

const CASE = "6f1c2d3e-4a5b-4c6d-8e7f-001122334455";
const BASE = `/maintenance/requests/${CASE}`;
const PAGE = `${BASE}/history?site_id=KOBO-001`;
const OVERVIEW = `${BASE}?site_id=KOBO-001`;
const RECORD = `${BASE}/record?site_id=KOBO-001`;
const KNOWN = "2026-10-20T11:59:04Z";
const ACTOR = "service:w401-fixture";
const GAPS = ["Site visit start not recorded", "Verification pending · no outcome assessment recorded"];

function event(n: number, kind: string, payload: Record<string, unknown> = {}, over: Partial<WorkCaseDetailEvent> = {}): WorkCaseDetailEvent {
  return {
    id: `00000000-0000-4000-8000-${String(300 + n).padStart(12, "0")}`,
    kind,
    payload,
    occurred_at: `2026-10-19T08:00:0${n}.000000Z`,
    recorded_at: `2026-10-20T11:59:0${n}.000000Z`,
    actor_kind: "SERVICE",
    actor_id: ACTOR,
    ...over,
  } as WorkCaseDetailEvent;
}

function revision(no: number, n: number, over: Partial<GlobalWorkDetailRevision> = {}): GlobalWorkDetailRevision {
  return {
    id: `00000000-0000-4000-8000-${String(200 + no).padStart(12, "0")}`,
    revision_no: no,
    supersedes_revision_id: no === 1 ? null : `00000000-0000-4000-8000-${String(199 + no).padStart(12, "0")}`,
    title: no === 1 ? "Inspect starter" : "Inspect starter and control circuit again",
    reason: no === 1 ? null : "Scope widened",
    occurred_at: `2026-10-19T09:00:0${n}.000000Z`,
    recorded_at: `2026-10-20T11:59:0${n}.000000Z`,
    actor_kind: "SERVICE",
    actor_id: ACTOR,
    ...over,
  };
}

/** The B1 `detail` first request: CREATED :00, ASSIGN :01, COMMENT :02, COMPLETE :04, REOPEN :05, Correction :06. */
const DETAIL_EVENTS = [
  event(0, "CREATED"),
  event(1, "ASSIGN", { assignee: "Field team A" }),
  event(2, "COMMENT", { text: "Parts ordered" }),
  event(4, "COMPLETE", { maintenance_record_id: "00000000-0000-4000-8000-000000000401" }),
  event(5, "REOPEN", { reason: "Fault returned" }),
];

function detail(events: WorkCaseDetailEvent[] = DETAIL_EVENTS, revisions = [revision(1, 0), revision(2, 6)], over: Partial<GlobalWorkDetailBody> = {}): GlobalWorkDetailBody {
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
        id: "00000000-0000-4000-8000-000000000202",
        revision_no: 2,
        supersedes_revision_id: "00000000-0000-4000-8000-000000000201",
        title: "Inspect starter and control circuit again",
        narrative: "Starter inspection requested.",
        reason: "Scope widened",
        recorded_at: "2026-10-20T11:59:06Z",
        actor_kind: "SERVICE",
        actor_id: ACTOR,
        occurred_at: "2026-10-20T11:59:06Z",
      },
      finding_links: [],
      action_links: [],
      cited_accepted_evidence_ids: [],
      events,
      records: [],
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
    history: { revisions, operational_records: [] },
    links: {
      site: { label: "Kobo", href: "/sites/KOBO-001" },
      overview: { label: "Overview", href: OVERVIEW },
      record: { label: "Maintenance record", href: RECORD },
      history: { label: "History", href: PAGE },
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
      throw new Error("the request page never reads incidents");
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
        <Route path={WORK_REQUEST_HISTORY_ROUTE_PATH} element={<WorkRequestHistoryFrame client={reads} />} />
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
const kinds = () => qa("[data-history-row]").map((tr) => tr.getAttribute("data-history-row"));
const events = () => qa("[data-history-row] [data-history-event]").map((td) => text(td.firstElementChild?.matches(".global-work-clamp") ? td.firstElementChild : td));
const gapRows = () => qa("[data-history-gap]").map((tr) => qa("td", tr).map((td) => text(td)));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W6-01d C4: history presentation", () => {
  it("history_labels_all_seven: every known kind, Correction and its null-reason form from a typed DTO", () => {
    // A request can never persist CLOSE (W4 TRANSITIONS); this typed DTO feeds the presentation function directly.
    const body = detail(
      [
        event(0, "CREATED"),
        event(1, "ASSIGN", { assignee: "Field team A" }),
        event(2, "COMMENT", { text: "Parts ordered" }),
        event(3, "COMPLETE", { maintenance_record_id: "00000000-0000-4000-8000-000000000401" }),
        event(4, "CLOSE", { reason: "Work accepted" }),
        event(5, "REOPEN", { reason: "Fault returned" }),
        event(6, "CANCEL", { reason: "Duplicate request" }),
      ],
      [revision(1, 0), revision(2, 7), revision(3, 8, { reason: null, title: "Third title" })],
    );
    expect(historyRows(body).map((r) => r.text)).toEqual([
      "Created",
      "Assigned to Field team A",
      "Commented: Parts ordered",
      "Completed · outcome not established · maintenance record 00000000-0000-4000-8000-000000000401",
      "Closed: Work accepted",
      "Reopened: Fault returned",
      "Cancelled: Duplicate request",
      "Correction: Scope widened\nTitle: Inspect starter and control circuit again",
      "Correction · reason not recorded\nTitle: Third title",
    ]);
  });

  it("omits revision 1 and orders by the exact recorded_at string, then the lowercase ID", () => {
    const tieA = event(1, "COMMENT", { text: "B" }, { id: "BBBBBBBB-0000-4000-8000-000000000001", recorded_at: "2026-10-20T11:59:03.000010Z" });
    const tieB = event(2, "COMMENT", { text: "A" }, { id: "aaaaaaaa-0000-4000-8000-000000000001", recorded_at: "2026-10-20T11:59:03.000010Z" });
    const earlier = event(3, "COMMENT", { text: "micro" }, { recorded_at: "2026-10-20T11:59:03.000002Z" });
    const rows = historyRows(detail([event(0, "CREATED"), tieA, tieB, earlier], [revision(1, 0)]));
    expect(rows.map((r) => r.text)).toEqual(["Created", "Commented: micro", "Commented: A", "Commented: B"]);
    expect(rows.some((r) => r.kind === "CORRECTION")).toBe(false);
    // Same-second display: seconds are shown, the microsecond string decides the order.
    expect(historyUtc("2026-10-20T11:59:03.000010Z")).toBe("20 Oct 2026, 11:59:03 UTC");
    expect(historyUtc("2026-10-06T09:05:00Z")).toBe("6 Oct 2026, 09:05:00 UTC");
  });

  it("fails closed on a typed body without CREATED or with a missing known payload", () => {
    expect(historyReadable(detail())).toBe(true);
    expect(historyReadable(detail(DETAIL_EVENTS.slice(1)))).toBe(false);
    expect(historyReadable(detail([event(0, "CREATED"), event(1, "ASSIGN", {})]))).toBe(false);
    expect(historyReadable(detail([event(0, "CREATED"), event(1, "OPEN_VERIFICATION", { anything: 1 })]))).toBe(true);
  });
});

describe("W6-01d C4: work request History page", () => {
  it("renders the shared frame, the History tab current, five authored rows and the in-panel pager", async () => {
    const reads = client(loaded(detail()));
    mount(PAGE, reads);
    await settled();

    expect(reads.calls).toEqual([{ case_id: CASE, site_id: "KOBO-001", known_at: null }]);
    expect(screen.getByRole("heading", { level: 1, name: "Inspect starter and control circuit again" })).toBeInTheDocument();
    expect(text(q(".page-header p"))).toBe("WR-000001 · Kobo · corrective");
    // P-C4-14: the loaded breadcrumb changes only the section.
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(text(crumbs)).toBe("MaintenanceWR-000001History· site: Kobo");
    expect(text(crumbs.querySelector("[aria-current='page']"))).toBe("History");
    expect(screen.getByRole("link", { name: "Open site" })).toHaveAttribute("href", "/sites/KOBO-001");
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(qa("li", tabs).map((li) => text(li))).toEqual(["Overview", "Maintenance record", "Verification · Not available yet", "History"]);
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("aria-current", "page");
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("href", PAGE);
    expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", OVERVIEW);
    expect(text(q("[data-work-request-asof]"))).toBe("As known at 22 Oct 2026, 12:00 UTC");
    expect(q(".v69-mheader")).not.toBeNull();
    expectV69Panels("wr-history");

    // P-C4-5/3: six authored rows (revision 1 omitted), five on page 1, gaps only on the last page.
    const panel = screen.getByRole("heading", { level: 2, name: "History" }).closest("section") as HTMLElement;
    expect(qa("thead th", panel).map((th) => text(th))).toEqual(["Time", "Event", "By"]);
    expect(kinds()).toEqual(["CREATED", "ASSIGN", "COMMENT", "COMPLETE", "REOPEN"]);
    expect(events()).toEqual([
      "Created",
      "Assigned to Field team A",
      "Commented: Parts ordered",
      "Completed · outcome not established · maintenance record 00000000-0000-4000-8000-000000000401",
      "Reopened: Fault returned",
    ]);
    expect(gapRows()).toEqual([]);
    const pager = within(panel).getByRole("navigation", { name: "History pages" });
    expect(pager.closest("section")).toBe(panel);
    expect(pager.compareDocumentPosition(panel.querySelector("table") as Element) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    expect(text(pager.querySelector("[data-global-work-showing]"))).toBe("Showing 1–5 of 6");
    expect(pager.querySelector("[data-global-work-previous]")).toBeNull();
    expect(pager.querySelector("[data-global-work-next]")).toHaveClass("link-button");

    // P-C4-9/10/13: UTC seconds, occurrence disclosure, name gap and stored actor.
    const first = q("[data-history-row]") as HTMLElement;
    expect(text(first.querySelector("[data-history-time]"))).toBe("20 Oct 2026, 11:59:00 UTC");
    expect(text(first.querySelector("[data-history-occurred] summary"))).toBe("Occurrence time");
    expect(text(first.querySelector("[data-history-occurred]"))).toBe("Occurrence timeOccurred 19 Oct 2026, 08:00:00 UTC");
    expect(text(first.querySelector("[data-history-by]"))).toBe("Name not recorded");
    expect(text(first.querySelector("[data-history-actor]"))).toBe(`Stored actorSERVICE · ${ACTOR}`);
    expect(qa("[data-history-occurred]").every((d) => !(d as HTMLDetailsElement).open)).toBe(true);
    expect(text(q('[data-history-row="ASSIGN"] [data-history-full] summary'))).toBe("Full event text");

    fireEvent.click(pager.querySelector("[data-global-work-next]") as Element);
    expect(kinds()).toEqual(["CORRECTION"]);
    expect(text(q('[data-history-row="CORRECTION"] [data-history-clamp]'))).toBe("Correction: Scope widened Title: Inspect starter and control circuit again");
    expect(text(q('[data-history-row="CORRECTION"] [data-history-occurred]'))).toBe("Occurrence timeOccurred 19 Oct 2026, 09:00:06 UTC");
    // P-C4-8: two in-table gaps after the last authored row; no time, actor or disclosure; not counted.
    expect(gapRows()).toEqual(GAPS.map((gap) => ["—", gap, "—"]));
    expect(qa("[data-history-gap] details")).toHaveLength(0);
    const pager2 = screen.getByRole("navigation", { name: "History pages" });
    expect(text(pager2.querySelector("[data-global-work-showing]"))).toBe("Showing 6–6 of 6");
    expect(pager2.querySelector("[data-global-work-next]")).toBeNull();
    expect(pager2.querySelector("[data-global-work-previous]")).not.toBeNull();
    expect(reads.calls).toHaveLength(1);
    expectV69Panels("wr-history");

    // Reload keeps the route and resets the page.
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await settled();
    expect(reads.calls).toHaveLength(2);
    expect(reads.calls[1]).toEqual(reads.calls[0]);
    expect(kinds()).toEqual(["CREATED", "ASSIGN", "COMMENT", "COMPLETE", "REOPEN"]);
  });

  it("shows Previous back to page 1 and issues no read while paging", async () => {
    const reads = client(loaded(detail()));
    mount(PAGE, reads);
    await settled();
    fireEvent.click(q("[data-global-work-next]") as Element);
    fireEvent.click(q("[data-global-work-previous]") as Element);
    expect(text(q("[data-global-work-showing]"))).toBe("Showing 1–5 of 6");
    expect(reads.calls).toHaveLength(1);
  });

  it("reads Raised from the source incident with its authorized href, and plain text without one", async () => {
    const linked = detail(undefined, undefined, {
      links: { ...detail().links, source_incident: { label: "INC-000007", href: "/sites/KOBO-001/incidents?x=1" } },
    });
    mount(PAGE, client(loaded(linked)));
    await settled();
    expect(text(q('[data-history-row="CREATED"] [data-history-event]'))).toBe("Raised from INC-000007");
    expect(within(q('[data-history-row="CREATED"]') as HTMLElement).getByRole("link", { name: "INC-000007" })).toHaveAttribute("href", "/sites/KOBO-001/incidents?x=1");
    cleanup();
    const unlinked = detail(undefined, undefined, { links: { ...detail().links, source_incident: { label: "INC-000007", href: null } } });
    mount(PAGE, client(loaded(unlinked)));
    await settled();
    expect(text(q('[data-history-row="CREATED"] [data-history-event]'))).toBe("Raised from INC-000007");
    expect(q('[data-history-row="CREATED"] a')).toBeNull();
  });

  it("renders an unknown or reserved kind as an authored row with no inferred outcome", async () => {
    mount(PAGE, client(loaded(detail([event(0, "CREATED"), event(1, "OPEN_VERIFICATION", { verdict: "pass" })], [revision(1, 0)]))));
    await settled();
    expect(kinds()).toEqual(["CREATED", "OPEN_VERIFICATION"]);
    expect(events()[1]).toBe("Event OPEN_VERIFICATION · meaning not established");
    expect(text(q(".global-work--history section"))).not.toMatch(/verified|pass/i);
    expect(q("[data-global-work-pager]")).toBeNull();
    expect(gapRows()).toHaveLength(2);
  });

  it("keeps a long assignee and a 500-character correction reason through the clamp and full text (stress, no pager)", async () => {
    const assignee = `${"A".repeat(120)}-owner12`;
    const reason = "Corrected the inspection scope ".repeat(20).slice(0, 500).trimEnd();
    const actor = "x".repeat(128);
    const body = detail(
      [event(0, "CREATED", {}, { actor_id: actor }), event(1, "ASSIGN", { assignee })],
      [revision(1, 0), revision(2, 3, { reason })],
    );
    mount(PAGE, client(loaded(body)));
    await settled();
    expect(kinds()).toEqual(["CREATED", "ASSIGN", "CORRECTION"]);
    expect(q("[data-global-work-pager]")).toBeNull();
    expect(gapRows()).toHaveLength(2);
    expect(text(q('[data-history-row="ASSIGN"] [data-history-full]'))).toBe(`Full event textAssigned to ${assignee}`);
    expect(text(q('[data-history-row="CORRECTION"] [data-history-full]'))).toContain(`Correction: ${reason}`);
    expect(text(q('[data-history-row="CREATED"] [data-history-actor]'))).toBe(`Stored actorSERVICE · ${actor}`);
    expect(text(q('[data-history-row="CREATED"] [data-history-by]'))).toBe("Name not recorded");
  });

  it("labels an explicit cutoff Historical and keeps it on every live tab", async () => {
    const cut = `&known_at=${encodeURIComponent(KNOWN)}`;
    const body = detail(DETAIL_EVENTS.slice(0, 4), [revision(1, 0)], {
      selected: { ...detail().selected, known_at: "2026-10-20T11:59:04.000000Z" },
      links: {
        ...detail().links,
        overview: { label: "Overview", href: `${OVERVIEW}${cut}` },
        record: { label: "Maintenance record", href: `${RECORD}${cut}` },
        history: { label: "History", href: `${PAGE}${cut}` },
      },
    });
    const reads = client(loaded(body));
    mount(`${PAGE}${cut}`, reads);
    await settled();
    expect(reads.calls).toEqual([{ case_id: CASE, site_id: "KOBO-001", known_at: KNOWN }]);
    expect(text(q("[data-work-request-asof]"))).toBe("Historical as of 20 Oct 2026, 11:59 UTC");
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("href", `${PAGE}${cut}`);
    expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", `${OVERVIEW}${cut}`);
    expect(within(tabs).getByRole("link", { name: "Maintenance record" })).toHaveAttribute("href", `${RECORD}${cut}`);
    expect(kinds()).toEqual(["CREATED", "ASSIGN", "COMMENT", "COMPLETE"]);
    expect(q("[data-global-work-pager]")).toBeNull();
  });

  it("states loading with the History breadcrumb and a validated History tab", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    mount(PAGE, client(loaded(detail()), gate));
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Work request" })).toBeInTheDocument();
    expect(text(q("[data-global-work-loading]"))).toBe("Loading the work request.");
    expect(text(screen.getByRole("navigation", { name: "Breadcrumb" }))).toBe("MaintenanceWork requestHistory");
    expect(within(screen.getByRole("navigation", { name: "Context tabs" })).getByRole("link", { name: "History" })).toHaveAttribute("href", PAGE);
    expect(q("[data-history-row]")).toBeNull();
    release();
    await settled();
    expect(kinds()).toHaveLength(5);
  });

  it.each([
    ["SITE_SCOPE_FORBIDDEN", "No access to this Site's work request."],
    ["WORK_CASE_NOT_FOUND", "No work case with this ID at this site."],
    ["WORK_STORE_UNAVAILABLE", "Work records could not be read. Reload."],
  ] as const)("states the %s refusal in the shared frame with the History panel slot", async (code, sentence) => {
    mount(PAGE, client({ status: "refused", code }));
    await settled();
    expect(text(q(`[data-page-refusal="${code}"]`))).toBe(sentence);
    expect(text(screen.getByRole("navigation", { name: "Breadcrumb" }))).toBe("MaintenanceWork requestHistory");
    expect(q("[data-history-row]")).toBeNull();
    expectV69Panels("wr-history");
  });

  it("does not fetch without a site_id and states the 404 sentence", async () => {
    const reads = client(loaded(detail()));
    mount(`${BASE}/history`, reads);
    await settled();
    expect(reads.calls).toEqual([]);
    expect(text(q('[data-page-refusal="NO_SITE"]'))).toBe("No work case with this ID at this site.");
  });

  it("P-C4-12: a typed 200 without CREATED is the 503 sentence with no authored rows", async () => {
    mount(PAGE, client(loaded(detail(DETAIL_EVENTS.slice(1)))));
    await settled();
    expect(text(q('[data-page-refusal="WORK_STORE_UNAVAILABLE"]'))).toBe("Work records could not be read. Reload.");
    expect(text(q("[data-work-request-unavailable]"))).toBe("Work request unavailable.");
    expect(q(".v69-mheader")).toBeNull();
    expect(q("[data-history-row]")).toBeNull();
    expect(q("[data-history-gap]")).toBeNull();
    expectV69Panels("wr-history");
  });

  it("P-C4-12: a fetched malformed 200 without CREATED is refused by the client parser as the 503 sentence", async () => {
    const body = detail(DETAIL_EVENTS.slice(1));
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })));
    mount(PAGE, createGlobalWorkClient());
    await settled();
    expect(text(q('[data-page-refusal="WORK_STORE_UNAVAILABLE"]'))).toBe("Work records could not be read. Reload.");
    expect(q("[data-history-row]")).toBeNull();
  });
});

describe("W6-01d C4: the History route in the app shell", () => {
  it("mounts History under the operator shell with the rail's Maintenance root current", async () => {
    expect(WORK_REQUEST_HISTORY_ROUTE_PATH).toBe("/maintenance/requests/:caseId/history");
    const reads = client(loaded(detail()));
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <App flags={featureFlagsWith(false)} globalWork={reads} />
      </MemoryRouter>,
    );
    await settled();
    expect(screen.getByRole("main", { name: "Inspect starter and control circuit again" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "History" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    expect(within(rail).getByRole("link", { name: "Maintenance" })).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});
