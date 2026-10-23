/**
 * W6-01c C2: the work request Overview (`.agent/W6-01-build-spec.md` "C1-C3 pre-flight rulings" P-C2-1..14 and
 * P-X-1..3, section 2, CL3-5 as amended). Typed responses only; the persisted positive, historical, 403, 404,
 * stress and linked-source states are captured against the real API in `.agent/W6-01-evidence/C2/`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { WORK_REQUEST_ROUTE_PATH } from "../../shell/operatorSiteRoutes";
import { expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import {
  createGlobalWorkClient,
  type GlobalWorkClient,
  type GlobalWorkDetailBody,
  type GlobalWorkDetailQuery,
  type GlobalWorkDetailResult,
  type WorkCaseDetailEvent,
} from "../globalWorkClient";
import { WorkRequestOverviewFrame } from "../WorkRequestOverview";

const CASE = "6f1c2d3e-4a5b-4c6d-8e7f-001122334455";
const ROUTE = WORK_REQUEST_ROUTE_PATH;
const PAGE = `/maintenance/requests/${CASE}?site_id=KOBO-001`;
const KNOWN = "2026-10-20T12:00:01Z";
const OVERVIEW = `/maintenance/requests/${CASE}?site_id=KOBO-001`;
const RECORD = `/maintenance/requests/${CASE}/record?site_id=KOBO-001`;
const HISTORY = `/maintenance/requests/${CASE}/history?site_id=KOBO-001`;
const TITLE200 = "Startermotorandcontrolpanelinspection".repeat(6).slice(0, 200);
const NARRATIVE = "Inspection narrative ".repeat(200).slice(0, 4000);

function event(n: number, kind: string, payload: Record<string, unknown> = {}): WorkCaseDetailEvent {
  return {
    id: `00000000-0000-4000-8000-${String(300 + n).padStart(12, "0")}`,
    kind,
    payload,
    occurred_at: `2026-10-20T11:59:0${n}Z`,
    recorded_at: `2026-10-20T11:59:0${n}Z`,
    actor_kind: "SERVICE",
    actor_id: "service:w401-fixture",
  };
}

function detail(over: Partial<GlobalWorkDetailBody> = {}, state = "IN_PROGRESS"): GlobalWorkDetailBody {
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
        state,
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
      events: [
        event(0, "CREATED"),
        event(1, "ASSIGN", { assignee: "Field team A" }),
        event(2, "COMMENT", { text: "Parts ordered" }),
        event(4, "COMPLETE", { maintenance_record_id: "00000000-0000-4000-8000-000000000401" }),
        event(5, "REOPEN", { reason: "Fault returned" }),
      ],
      records: [
        {
          id: "00000000-0000-4000-8000-000000000401",
          activity: "Replaced starter relay and tested the start.",
          outcome_note: null,
          occurred_at: "2026-10-20T11:59:03Z",
          recorded_at: "2026-10-20T11:59:03Z",
          supersedes_record_id: null,
        },
      ],
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
    history: { revisions: [], operational_records: [] },
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
        <Route path={ROUTE} element={<WorkRequestOverviewFrame client={reads} />} />
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
const cellText = (key: string) => text(q(`[data-mheader-cell="${key}"] dd`));
const kv = (key: string) => text(q(`[data-key-value="${key}"] dd`));
const subtitle = () => text(q(".page-header p"));
const doneSteps = () =>
  Array.from(document.querySelectorAll("[data-lifecycle-step]"))
    .filter((li) => li.classList.contains("done"))
    .map((li) => li.getAttribute("data-lifecycle-step"));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W6-01c C2: work request Overview", () => {
  it("renders the mock header, breadcrumb, Open site, tabs, date bar, mheader and the two panels", async () => {
    const reads = client(loaded(detail()));
    mount(PAGE, reads);
    await settled();

    expect(reads.calls).toEqual([{ case_id: CASE, site_id: "KOBO-001", known_at: null }]);
    expect(screen.getByRole("heading", { level: 1, name: "Inspect starter and control circuit again" })).toBeInTheDocument();
    expect(subtitle()).toBe("WR-000001 · Kobo · corrective");

    // P-C2-2: Maintenance link (no window), WR code and Overview as text, Site link.
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(crumbs).getByRole("link", { name: "Maintenance" })).toHaveAttribute("href", "/maintenance");
    expect(within(crumbs).queryByRole("link", { name: "WR-000001" })).toBeNull();
    expect(text(crumbs)).toContain("WR-000001");
    expect(within(crumbs).getByRole("link", { name: "Kobo" })).toHaveAttribute("href", "/sites/KOBO-001");
    expect(text(q("[data-work-request-breadcrumb-site]"))).toBe("· site: Kobo");

    // P-C2-3: Open site heading action.
    expect(screen.getByRole("link", { name: "Open site" })).toHaveAttribute("href", "/sites/KOBO-001");

    // P-C2-5: Context tabs in mock order; Overview live and current. W6-01c C3 (P-C3-5): Maintenance record is a
    // live `/record` link with the same Site. W6-01d C4 (P-C4-2): History is a live `/history` link with the same
    // Site; Verification stays unavailable.
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(tabs.querySelector(".site-tabs__list")).not.toBeNull();
    const overview = within(tabs).getByRole("link", { name: "Overview" });
    expect(overview).toHaveAttribute("href", OVERVIEW);
    expect(overview).toHaveAttribute("aria-current", "page");
    const record = within(tabs).getByRole("link", { name: "Maintenance record" });
    expect(record).toHaveAttribute("href", RECORD);
    expect(record).not.toHaveAttribute("aria-current");
    const history = within(tabs).getByRole("link", { name: "History" });
    expect(history).toHaveAttribute("href", HISTORY);
    expect(history).not.toHaveAttribute("aria-current");
    expect(within(tabs).getAllByRole("link")).toHaveLength(3);
    expect(Array.from(tabs.querySelectorAll("li")).map((li) => text(li))).toEqual([
      "Overview",
      "Maintenance record",
      "Verification · Not available yet",
      "History",
    ]);

    // P-C2-4: As known at + Reload in the date bar.
    const bar = q(".site-date-bar");
    expect(text(bar?.querySelector("[data-work-request-asof]") ?? null)).toBe("As known at 22 Oct 2026, 12:00 UTC");
    expect(within(bar as HTMLElement).getByRole("button", { name: "Reload" })).toBeInTheDocument();

    // CL3-5 mheader.
    expect(q(".v69-mheader")).not.toBeNull();
    expect(text(q('[data-work-request-preview="owner"]'))).toBe("Field team A");
    expect(cellText("due")).toBe("Not set");
    expect(cellText("state")).toBe("In progress · outcome not established");
    expect(text(q('[data-work-request-preview="source"]'))).toBe("Not recorded");
    expect(cellText("success")).toBe("Not recorded");
    expect(text(q('[data-work-request-full="owner"] summary'))).toBe("Full owner text");
    expect(text(q('[data-work-request-full="source"] summary'))).toBe("Full source text");

    // P-C2-6: Work done prose, Latest activity, then the four mock rows.
    expect(text(q('[data-work-request-clamp="narrative"]'))).toBe("Starter inspection requested.");
    expect(text(q("[data-work-request-latest]"))).toBe("Latest activity:");
    expect(text(q('[data-work-request-clamp="activity"]'))).toBe("Replaced starter relay and tested the start.");
    expect(Array.from(document.querySelectorAll("[data-key-value]")).map((x) => x.getAttribute("data-key-value"))).toEqual([
      "type",
      "asset",
      "warranty",
      "linked_action",
    ]);
    expect(kv("type")).toBe("Corrective");
    expect(kv("asset")).toBe("No asset recorded");
    expect(kv("warranty")).toBe("Warranty not recorded");
    expect(kv("linked_action")).toBe("No linked action recorded");

    // P-C2-7/8: six steps, REOPEN after COMPLETE leaves Completed not done; chart-note inside Lifecycle; no footers.
    expect(Array.from(document.querySelectorAll("[data-lifecycle-step]")).map((x) => text(x))).toEqual([
      "Finding",
      "Triage",
      "Assigned",
      "Visit",
      "Completed",
      "Verified",
    ]);
    expect(doneSteps()).toEqual(["Triage", "Assigned", "Visit"]);
    const lifecycle = q("[data-work-request-lifecycle]")?.closest(".panel");
    expect(text(lifecycle?.querySelector("[data-work-request-chart-note]") ?? null)).toBe(
      "Completed is not Verified. No work-case outcome evaluator is available.",
    );
    expect(document.querySelectorAll(".panel__description")).toHaveLength(0);
    expectV69Panels("wr-overview");
  });

  it("states loading with the ruled heading literals, a Site-less breadcrumb and a text Open site", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    mount(PAGE, client(loaded(detail()), gate));
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Work request" })).toBeInTheDocument();
    expect(subtitle()).toBe("Loading the work request.");
    expect(text(q("[data-global-work-loading]"))).toBe("Loading the work request.");
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(text(crumbs)).toBe("MaintenanceWork requestOverview");
    expect(q("[data-work-request-breadcrumb-site]")).toBeNull();
    expect(screen.queryByRole("link", { name: "Open site" })).toBeNull();
    expect(text(q('[data-work-request-open-site="text"]'))).toBe("Open site");
    // The Overview anchor is built from validated inputs before the response (C4: so is History).
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", OVERVIEW);
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("href", HISTORY);
    expect(screen.queryByRole("button", { name: "Reload" })).toBeNull();
    expect(q(".v69-mheader")).toBeNull();
    release();
    await settled();
    expect(screen.getByRole("heading", { level: 1, name: "Inspect starter and control circuit again" })).toBeInTheDocument();
  });

  it.each([
    ["UNAUTHENTICATED", "Sign in to see work records."],
    ["SITE_SCOPE_FORBIDDEN", "No access to this Site's work request."],
    ["SITE_NOT_FOUND", "No imported Site found for this request."],
    ["WORK_CASE_NOT_FOUND", "No work case with this ID at this site."],
    ["INVALID_KNOWN_AT", "Choose a valid cutoff time."],
    ["WORK_STORE_UNAVAILABLE", "Work records could not be read. Reload."],
  ] as const)("states the %s refusal with the ruled heading and copy", async (code, sentence) => {
    const reads = client({ status: "refused", code });
    mount(PAGE, reads);
    await settled();
    expect(screen.getByRole("heading", { level: 1, name: "Work request" })).toBeInTheDocument();
    expect(subtitle()).toBe("Request details could not be shown.");
    expect(text(q(`[data-page-refusal="${code}"]`))).toBe(sentence);
    expect(text(q("[data-work-request-unavailable]"))).toBe("Work request unavailable.");
    expect(text(q('[data-work-request-open-site="text"]'))).toBe("Open site");
    expect(q(".v69-mheader")).toBeNull();
    // The tab row still renders with the validated Overview anchor; the panels keep their slots.
    expect(within(screen.getByRole("navigation", { name: "Context tabs" })).getByRole("link", { name: "Overview" })).toHaveAttribute(
      "href",
      OVERVIEW,
    );
    expectV69Panels("wr-overview");
    // Reload repeats the same query.
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await settled();
    expect(reads.calls).toHaveLength(2);
    expect(reads.calls[1]).toEqual(reads.calls[0]);
  });

  it.each([
    ["absent site_id", `/maintenance/requests/${CASE}`, "NO_SITE", "Choose a request at a site.", "No work case with this ID at this site.", false],
    ["empty site_id", `/maintenance/requests/${CASE}?site_id=`, "NO_SITE", "Choose a request at a site.", "No work case with this ID at this site.", false],
    [
      "repeated site_id",
      `/maintenance/requests/${CASE}?site_id=KOBO-001&site_id=KOBO-002`,
      "WORK_CASE_NOT_FOUND",
      "Request details could not be shown.",
      "No work case with this ID at this site.",
      false,
    ],
    [
      "malformed case ID",
      "/maintenance/requests/not-a-uuid?site_id=KOBO-001",
      "WORK_CASE_NOT_FOUND",
      "Request details could not be shown.",
      "No work case with this ID at this site.",
      false,
    ],
    [
      "invalid known_at",
      `${PAGE}&known_at=yesterday`,
      "INVALID_KNOWN_AT",
      "Request details could not be shown.",
      "Choose a valid cutoff time.",
      true,
    ],
    [
      "repeated known_at",
      `${PAGE}&known_at=${KNOWN}&known_at=${KNOWN}`,
      "INVALID_KNOWN_AT",
      "Request details could not be shown.",
      "Choose a valid cutoff time.",
      true,
    ],
  ] as const)("does not fetch for an %s", async (_name, path, hook, sub, sentence, overviewLive) => {
    const reads = client(loaded(detail()));
    mount(path, reads);
    await settled();
    expect(reads.calls).toEqual([]);
    expect(screen.getByRole("heading", { level: 1, name: "Work request" })).toBeInTheDocument();
    expect(subtitle()).toBe(sub);
    expect(text(q(`[data-page-refusal="${hook}"]`))).toBe(sentence);
    expect(screen.queryByRole("button", { name: "Reload" })).toBeNull();
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    if (overviewLive) expect(within(tabs).getByRole("link", { name: "Overview" })).toHaveAttribute("href", OVERVIEW);
    else expect(within(tabs).queryByRole("link")).toBeNull();
    expect(text(tabs)).toContain("Overview");
  });

  it("ignores unknown query keys and fetches a valid unrecognized Site code", async () => {
    const reads = client({ status: "refused", code: "SITE_NOT_FOUND" });
    mount(`/maintenance/requests/${CASE}?site_id=NOPE-404&tab=x&from=2026-10-14T00:00:00Z`, reads);
    await settled();
    expect(reads.calls).toEqual([{ case_id: CASE, site_id: "NOPE-404", known_at: null }]);
    expect(text(q('[data-page-refusal="SITE_NOT_FOUND"]'))).toBe("No imported Site found for this request.");
  });

  it("labels an explicit cutoff Historical and keeps it on the Overview tab", async () => {
    const href = `${OVERVIEW}&known_at=${encodeURIComponent(KNOWN)}`;
    const reads = client(
      loaded(
        detail({
          selected: { ...detail().selected, known_at: "2026-10-20T12:00:01.000000Z" },
          links: {
            ...detail().links,
            overview: { label: "Overview", href },
            record: { label: "Maintenance record", href: `${RECORD}&known_at=${encodeURIComponent(KNOWN)}` },
            history: { label: "History", href: `${HISTORY}&known_at=${encodeURIComponent(KNOWN)}` },
          },
        }),
      ),
    );
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}`, reads);
    await settled();
    expect(reads.calls).toEqual([{ case_id: CASE, site_id: "KOBO-001", known_at: KNOWN }]);
    expect(text(q("[data-work-request-asof]"))).toBe("Historical as of 20 Oct 2026, 12:00 UTC");
    expect(within(screen.getByRole("navigation", { name: "Context tabs" })).getByRole("link", { name: "Overview" })).toHaveAttribute(
      "href",
      href,
    );
    // W6-01c C3: the explicit cutoff stays on the live Maintenance record tab.
    expect(within(screen.getByRole("navigation", { name: "Context tabs" })).getByRole("link", { name: "Maintenance record" })).toHaveAttribute(
      "href",
      `${RECORD}&known_at=${encodeURIComponent(KNOWN)}`,
    );
    // W6-01d C4 (P-C4-2): the explicit cutoff stays on the live History tab; Verification stays unavailable.
    const tabs = screen.getByRole("navigation", { name: "Context tabs" });
    expect(within(tabs).getByRole("link", { name: "History" })).toHaveAttribute("href", `${HISTORY}&known_at=${encodeURIComponent(KNOWN)}`);
    expect(text(tabs)).toContain("Verification · Not available yet");
  });

  it("marks Completed and Finding only on stored facts; Cancelled adds its note and never Completed", async () => {
    const pinned = {
      finding_links: [{ finding_id: "f1", finding_revision_id: "r1" }],
      events: [event(0, "CREATED"), event(4, "COMPLETE", { maintenance_record_id: "00000000-0000-4000-8000-000000000401" })],
      records: [],
    };
    const completed = detail({}, "COMPLETED");
    mount(PAGE, client(loaded({ ...completed, work_detail: { ...completed.work_detail, ...pinned } })));
    await settled();
    expect(doneSteps()).toEqual(["Finding", "Completed"]);
    expect(text(q("[data-work-request-latest]"))).toBe("Latest activity: No maintenance activity recorded");
    expect(cellText("state")).toBe("Completed · outcome not established");
    expect(text(q('[data-work-request-preview="owner"]'))).toBe("Not assigned");
    expect(q("[data-work-request-cancelled]")).toBeNull();
    cleanup();

    const cancelled = detail({}, "CANCELLED");
    mount(PAGE, client(loaded({ ...cancelled, work_detail: { ...cancelled.work_detail, events: [event(0, "CREATED"), event(8, "CANCEL", { reason: "No longer needed" })], records: [] } })));
    await settled();
    expect(doneSteps()).toEqual([]);
    expect(text(q("[data-work-request-cancelled]"))).toBe("Cancelled · work stopped");
    expect(cellText("state")).toBe("Cancelled · outcome not established");
  });

  it("renders Source as the incident then lineage-true Finding links, and Linked action from outer links", async () => {
    const reads = client(
      loaded(
        detail({
          work_asset: { code: "GEN-001", type: "generator" },
          links: {
            ...detail().links,
            source_incident: { label: "Incident INC-000004", href: "/sites/KOBO-001/work/incidents?from=a&to=b" },
            findings: [
              { label: "Finding a1b2c3d4", href: "/sites/KOBO-001/findings/f1?revision_id=r1" },
              { label: "Finding e5f6a7b8", href: null },
            ],
            actions: [{ label: "Action c9d0e1f2", href: "/sites/KOBO-001/actions/a1" }],
          },
        }),
      ),
    );
    mount(PAGE, reads);
    await settled();
    const source = q('[data-work-request-preview="source"]') as HTMLElement;
    expect(within(source).getAllByRole("link").map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      ["Incident INC-000004", "/sites/KOBO-001/work/incidents?from=a&to=b"],
      ["Finding a1b2c3d4", "/sites/KOBO-001/findings/f1?revision_id=r1"],
    ]);
    expect(text(source)).toBe("Incident INC-000004 · Finding a1b2c3d4 · Finding e5f6a7b8 · Link unavailable at this cutoff");
    expect(text(q('[data-work-request-full="source"]'))).toContain("Finding e5f6a7b8 · Link unavailable at this cutoff");
    expect(kv("asset")).toBe("GEN-001 · generator");
    const action = within(q('[data-key-value="linked_action"]') as HTMLElement).getByRole("link", { name: "Action c9d0e1f2" });
    expect(action).toHaveAttribute("href", "/sites/KOBO-001/actions/a1");
  });

  it("wraps a 200-character title and previews a 4000-character narrative with its full-text disclosure", async () => {
    const base = detail();
    mount(
      PAGE,
      client(loaded({ ...base, work_detail: { ...base.work_detail, selected_revision: { ...base.work_detail.selected_revision, title: TITLE200, narrative: NARRATIVE } } })),
    );
    await settled();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(TITLE200);
    expect(q('[data-work-request-clamp="narrative"]')?.classList.contains("global-work-clamp")).toBe(true);
    const full = q('[data-work-request-full="narrative"]') as HTMLDetailsElement;
    expect(text(full.querySelector("summary"))).toBe("Full narrative text");
    expect(full.textContent).toContain(NARRATIVE);
  });

  it("reads a client without the optional detail method as a store refusal, never a throw", async () => {
    mount(PAGE, { incidents: async () => ({ status: "refused", code: "WORK_STORE_UNAVAILABLE" }) });
    await settled();
    expect(text(q('[data-page-refusal="WORK_STORE_UNAVAILABLE"]'))).toBe("Work records could not be read. Reload.");
  });
});

describe("W6-01c C2: the detail client", () => {
  it("reads /api/work/requests/{id}, validates global-work-detail-1 and maps refusals by status", async () => {
    const seen: string[] = [];
    const base = detail();
    const withEvents = (events: WorkCaseDetailEvent[]) => ({ ...base, work_detail: { ...base.work_detail, events } });
    const noCreated = withEvents(base.work_detail.events.filter((e) => e.kind !== "CREATED"));
    const assignNoAssignee = withEvents([event(0, "CREATED"), event(1, "ASSIGN", {})]);
    const malformed = { ...detail(), links: { ...detail().links, findings: [{ label: 3, href: null }] } };
    const answers: [number, unknown][] = [
      [200, detail()],
      [200, malformed],
      [200, noCreated],
      [200, assignNoAssignee],
      [200, { ...detail(), schema_version: "global-work-index-1" }],
      [403, { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "x" } }],
      [404, { detail: { code: "SITE_NOT_FOUND", message: "x" } }],
      [404, { detail: { code: "WORK_CASE_NOT_FOUND", message: "x" } }],
      [401, { detail: { code: "UNAUTHENTICATED", message: "x" } }],
      [422, { detail: { code: "INVALID_KNOWN_AT", message: "x" } }],
      [503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "x" } }],
      [404, { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "x" } }],
      [500, null],
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        seen.push(url);
        const [status, json] = answers.shift() ?? [500, null];
        return new Response(JSON.stringify(json), { status });
      }),
    );
    const reads = createGlobalWorkClient();
    const query = { case_id: CASE, site_id: "KOBO-001", known_at: null };
    const results = [];
    for (let i = 0; i < 13; i += 1) results.push(await reads.detail!(i === 1 ? { ...query, known_at: KNOWN } : query));
    expect(results.map((r) => (r.status === "loaded" ? "loaded" : r.code))).toEqual([
      "loaded",
      "WORK_STORE_UNAVAILABLE",
      "WORK_STORE_UNAVAILABLE",
      "WORK_STORE_UNAVAILABLE",
      "WORK_STORE_UNAVAILABLE",
      "SITE_SCOPE_FORBIDDEN",
      "SITE_NOT_FOUND",
      "WORK_CASE_NOT_FOUND",
      "UNAUTHENTICATED",
      "INVALID_KNOWN_AT",
      "WORK_STORE_UNAVAILABLE",
      "WORK_STORE_UNAVAILABLE",
      "WORK_STORE_UNAVAILABLE",
    ]);
    expect(seen[0]).toBe(`/api/work/requests/${CASE}?site_id=KOBO-001`);
    expect(seen[1]).toBe(`/api/work/requests/${CASE}?site_id=KOBO-001&known_at=2026-10-20T12%3A00%3A01Z`);
  });

  it("rejects network failure as the store sentence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("offline");
      }),
    );
    expect(await createGlobalWorkClient().detail!({ case_id: CASE, site_id: "KOBO-001", known_at: null })).toEqual({
      status: "refused",
      code: "WORK_STORE_UNAVAILABLE",
    });
  });
});

describe("W6-01c C2: the request route in the app shell", () => {
  it("mounts the Overview under the operator shell with the rail's Maintenance root current", async () => {
    expect(WORK_REQUEST_ROUTE_PATH).toBe("/maintenance/requests/:caseId");
    const reads = client(loaded(detail()));
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <App flags={featureFlagsWith(false)} globalWork={reads} />
      </MemoryRouter>,
    );
    await settled();
    expect(screen.getByRole("main", { name: "Inspect starter and control circuit again" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    expect(within(rail).getByRole("link", { name: "Maintenance" })).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});
