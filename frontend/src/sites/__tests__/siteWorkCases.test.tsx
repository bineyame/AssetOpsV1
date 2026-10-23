/**
 * W4-01 commit 5: the v69 `sitework-incidents` and `sitework-maintenance`
 * screens over `GET /api/sites/{site}/work/{incidents|maintenance}`
 * (`.agent/W4-01-build-spec.md` B1/B9/B10, S19-S31, Run 7 commit-5 dry-read).
 *
 * Both routes mount through the real `App`; `fetch` serves `site-work-index-1`
 * bodies with exactly the row keys the backend list tests assert
 * (`backend/tests/test_w401_site_indexes_postgres.py` COMMON/MAINTENANCE). The
 * IDs are test constants, not product seed.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { siteFindingHref } from "../../shell/operatorSiteRoutes";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import { defaultWorkWindow, type WorkIndexBody, type WorkRow } from "../workClient";
import { globalWorkManageHref } from "../siteWorkCases";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

const DAY = { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z" };
const K = "2026-10-07T00:00:00.000000Z";
const EMPTY_PROVENANCE = {
  classification: "UNKNOWN",
  state: "UNKNOWN",
  source_ids: [],
  evidence_ids: [],
  basis_sha256: null,
  reasons: [{ code: "EMPTY_CITATION_SET", accepted_evidence_ids: [] }],
};
const FINDING = "a1b2c3d4-0000-4000-8000-000000000201";
const FINDING_REV = "a1b2c3d4-0000-4000-8000-000000000202";

function incidentRow(n: number, over: Partial<WorkRow> = {}): WorkRow {
  const id = `10000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`;
  return {
    case_id: id,
    revision_id: id.replace("10000000", "20000000"),
    code: `INC-${String(n).padStart(6, "0")}`,
    title: "Witnessed start request failed",
    narrative: "Operator observed a failed start request; cause not established.",
    occurred_at: "2026-10-06T16:11:00.000000Z",
    recorded_at: "2026-10-06T16:12:00.000000Z",
    state: "OPEN",
    asset_id: null,
    asset_label: null,
    finding_links: [],
    action_links: [],
    url: null,
    source_provenance: EMPTY_PROVENANCE,
    ...over,
  };
}

function requestRow(n: number, over: Partial<WorkRow> = {}): WorkRow {
  return {
    ...incidentRow(n),
    code: `WR-${String(n).padStart(6, "0")}`,
    title: "Inspect starter circuit",
    narrative: "Witnessed failure requires inspection.",
    request_state: "OPEN",
    incident_id: null,
    record_id: null,
    activity: null,
    outcome_note: null,
    outcome_state: "UNVERIFIED",
    next_evidence: null,
    next_evidence_copy: "No next evidence recorded",
    ...over,
  };
}

function body(rows: WorkRow[], over: Partial<WorkIndexBody> = {}): WorkIndexBody {
  return {
    schema_version: "site-work-index-1",
    site_code: "KOBO-001",
    site_name: "Kobo Mini-grid",
    window: { from: "2026-10-06T00:00:00.000000Z", to: "2026-10-07T00:00:00.000000Z", bounds: "[from, to)" },
    known_at: K,
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null },
    source_provenance: EMPTY_PROVENANCE,
    total_count: rows.length,
    rows,
    next_cursor: null,
    selection_token: `sha256:${"0".repeat(64)}`,
    ...over,
  };
}

const refusal = (code: string, message: string) => ({ detail: { code, message, rows: null, total_count: null } });

type Served = { status: number; body: unknown };

/** The subtab-count reads (`limit=1`), kept apart from the page's own list reads. */
let countRequests: string[] = [];
/** W4-03 unit 8: the decision-context overlay reads, kept apart from the W4-01 list reads. */
let contextRequests: string[] = [];

/** The default overlay answer: every requested case unlinked (`[]`), at the requested cutoff. */
function unlinkedContexts(path: string): Served {
  const query = new URLSearchParams(path.split("?")[1] ?? "");
  const ids = (query.get("case_ids") ?? "").split(",");
  return {
    status: 200,
    body: {
      schema_version: "mini-work-contexts-1",
      known_at: query.get("known_at"),
      contexts: Object.fromEntries(ids.map((id) => [id, []])),
    },
  };
}

function serve(gets: Record<string, Served>) {
  const requests: string[] = [];
  countRequests = [];
  contextRequests = [];
  vi.stubGlobal("fetch", async (url: string) => {
    const path = decodeURIComponent(String(url));
    const overlay = path.includes("/work/decision-contexts?");
    (overlay ? contextRequests : /[?&]limit=1(&|$)/.test(path) ? countRequests : requests).push(path);
    const hit = gets[path] ?? (overlay ? unlinkedContexts(path) : undefined);
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: path } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return requests;
}

const api = (kind: string, w: { from: string; to: string }, extra = "") =>
  `/api/sites/KOBO-001/work/${kind}?from=${w.from}&to=${w.to}&limit=5${extra}`;
const countPath = (kind: string, w: { from: string; to: string }) =>
  kind === "actions"
    ? `/api/sites/KOBO-001/action-index?from=${w.from}&to=${w.to}&limit=1`
    : `/api/sites/KOBO-001/work/${kind}?from=${w.from}&to=${w.to}&limit=1`;
const actionCount = (total: number) => ({
  status: 200,
  body: { schema_version: "site-action-index-1", status: "CURRENT", rows: [], total_count: total, fence: "f", window: {}, read_at: K },
});
const page = (kind: string, w: { from: string; to: string }) =>
  `/sites/KOBO-001/work/${kind}?${new URLSearchParams(w).toString()}`;

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;
const directory: SiteDirectoryClient = {
  listSites: async () => ({ status: "loaded", sites: [HYBRID_MINI_GRID_SITE] }),
} as SiteDirectoryClient;

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} />
    </MemoryRouter>,
  );
}

const strip = () => document.querySelector("main .status-strip") as HTMLElement;
const notice = () => document.querySelector("main [data-work-notice]") as HTMLElement;
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();

/** The mock's three slots, in order: status strip, the one panel, the notice. */
function expectSlots(screenId: "sitework-incidents" | "sitework-maintenance") {
  expectV69Panels(screenId);
  const main = document.querySelector("main") as HTMLElement;
  const strips = main.querySelectorAll(".status-strip");
  const panels = main.querySelectorAll("section.panel");
  const notices = main.querySelectorAll("[data-work-notice]");
  expect([strips.length, panels.length, notices.length]).toEqual([1, 1, 1]);
  expect(strips[0].compareDocumentPosition(panels[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(panels[0].compareDocumentPosition(notices[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(text(notices[0])).toBe(
    "Case history is stored with this site. Incidents and Maintenance can be managed globally. The create flow is not available yet.",
  );
  expect(text(strips[0])).toContain("These are work records at this site");
  expect(main.textContent).not.toMatch(/INC-203|WR-019|Manage in \w+ →|global create flow with this site filled in/);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const FRONTEND_CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const WORK_CSS = NODE_FS.readFileSync(`${FRONTEND_CWD}/src/sites/w4-work-cases.css`, "utf8").replace(/\s+/g, " ");

describe("W4-01: Site > Work > Incidents", () => {
  it("incident_stocked_empty_and_refused", async () => {
    // Stocked: seven cases, page one holds five; the count is the full set.
    const rows = [1, 2, 3, 4, 5].map((n) => incidentRow(n));
    rows[1] = incidentRow(2, { state: "IN_PROGRESS" });
    rows[2] = incidentRow(3, { state: "CLOSED" });
    const requests = serve({
      [api("incidents", DAY)]: { status: 200, body: body(rows, { total_count: 7, next_cursor: "CURSOR-2" }) },
      [api("incidents", DAY, `&known_at=${K}&cursor=CURSOR-2`)]: {
        status: 200,
        body: body([incidentRow(6), incidentRow(7)], { total_count: 7, status: "HISTORICAL" }),
      },
      [api("incidents", DAY, `&known_at=${K}`)]: {
        status: 200,
        body: body(rows, { total_count: 7, next_cursor: "CURSOR-2", status: "HISTORICAL" }),
      },
    });
    mount(page("incidents", DAY));
    await settledScreen();
    expectSlots("sitework-incidents");
    expectPlantedPanelRejected("sitework-incidents");
    expect(text(strip())).toContain("Scoped to Kobo · 7 incidents");
    // W6-01a A2: the Incidents strip links to the live global page with the Site window and the loaded cutoff.
    expect(text(strip())).toContain("Manage in Incidents");
    expect(text(strip())).not.toContain("Not available yet");
    expect(Array.from(strip().querySelectorAll("a")).map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      [
        "Manage in Incidents",
        "/incidents?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00.000000Z",
      ],
    ]);
    // H3: CURRENT adds no status word and no fourth slot; the strip is lead, detail, Manage.
    expect(strip().querySelector(".status-strip__state, [data-work-status]")).toBeNull();
    expect(text(strip())).not.toContain("Read in full");
    expect(strip().querySelectorAll(":scope > span")).toHaveLength(3);
    const panel = panelTitled("Incidents at this site");
    expect(text(panel)).toContain("A case links chronology, findings and work without copying them");
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Case",
      "Window",
      "What happened",
      "Linked findings",
      "State",
    ]);
    const trs = panel.querySelectorAll("tbody tr");
    expect(trs).toHaveLength(5);
    const first = trs[0] as HTMLElement;
    expect(text(first.querySelector("[data-work-case-title]"))).toBe("INC-000001 · Witnessed start request failed");
    // `url: null`: plain text, no link, handler or tab stop.
    expect(first.querySelector("td:first-child a, td:first-child [tabindex], td:first-child button")).toBeNull();
    expect(text(first.querySelector("[data-work-window]"))).toBe("6 Oct · from 19:11");
    expect(text(first)).toContain("2026-10-06 16:11 UTC");
    expect(text(first)).toContain("No linked finding");
    expect(Array.from(panel.querySelectorAll("[data-work-state]")).map((c) => [c.textContent, c.getAttribute("data-work-tone")])).toEqual([
      ["Open", "red"],
      ["In progress", "blue"],
      ["Closed", "neutral"],
      ["Open", "red"],
      ["Open", "red"],
    ]);
    expect(text(panel.querySelector("[data-work-showing]"))).toBe("Showing 1–5 of 7");
    expect(panel.querySelector("[data-work-previous]")).toBeNull();
    // Next keeps the window and binds the cutoff the first page was read at.
    fireEvent.click(panel.querySelector("[data-work-next]") as HTMLElement);
    await settledScreen();
    expect(requests).toContain(api("incidents", DAY, `&known_at=${K}&cursor=CURSOR-2`));
    const page2 = panelTitled("Incidents at this site");
    expect(page2.querySelectorAll("tbody tr")).toHaveLength(2);
    expect(text(page2.querySelector("[data-work-showing]"))).toBe("Showing 6–7 of 7");
    expect(page2.querySelector("[data-work-next]")).toBeNull();
    expect(page2.querySelector("[data-work-previous]")).not.toBeNull();
    expect(text(strip())).toContain("Scoped to Kobo · 7 incidents");
    // M1: page two reads as of the first page's K (explicitly sent); the strip stays three slots.
    expect(text(strip())).toContain("Read as of 2026-10-07 00:00 UTC");
    expect(strip().querySelectorAll(":scope > span")).toHaveLength(3);
    // Previous sends the same K again, and the page still reads as of it.
    fireEvent.click(page2.querySelector("[data-work-previous]") as HTMLElement);
    await settledScreen();
    expect(requests.at(-1)).toBe(api("incidents", DAY, `&known_at=${K}`));
    expect(text(strip())).toContain("Read as of 2026-10-07 00:00 UTC");
    cleanup();
    vi.unstubAllGlobals();

    // Empty: an exact zero from a complete read keeps the mock's empty block, no fake row.
    serve({ [api("incidents", DAY)]: { status: 200, body: body([]) } });
    mount(page("incidents", DAY));
    await settledScreen();
    expectSlots("sitework-incidents");
    expect(text(strip())).toContain("Scoped to Kobo · 0 incidents");
    const empty = panelTitled("Incidents at this site").querySelector("[data-work-empty]") as HTMLElement;
    // H2: the mock's evidence icon, decorative, in the empty block.
    const icon = empty.querySelector("[data-work-empty-icon]") as HTMLElement;
    expect(icon.getAttribute("aria-hidden")).toBe("true");
    expect(icon.querySelector("svg[data-rail-icon='evidence']")).not.toBeNull();
    expect(text(empty.querySelector("h3"))).toBe("No incidents at this site");
    expect(text(empty.querySelector("p"))).toBe(
      "No operational case was opened in the selected period. A case comes from a linked chain of events, not from a single data gap.",
    );
    expect(document.querySelectorAll("main tbody tr")).toHaveLength(0);
    cleanup();
    vi.unstubAllGlobals();

    // Refused: 503 and 403 show the refusal copy, no rows and no count (never a zero).
    for (const [status, code, copy] of [
      [503, "WORK_STORE_UNAVAILABLE", "Work records are unavailable right now. Try again."],
      [403, "SITE_SCOPE_FORBIDDEN", "You do not have access to this site's work."],
      [401, "UNAUTHENTICATED", "Sign in to see work at this site."],
      [404, "SITE_NOT_FOUND", "This site was not found."],
    ] as const) {
      serve({ [api("incidents", DAY)]: { status, body: refusal(code, "server message") } });
      mount(page("incidents", DAY));
      await settledScreen();
      expectSlots("sitework-incidents");
      expect(text(strip())).toContain("Count unknown · work source unavailable");
      expect(text(strip())).not.toMatch(/\b0 incidents/);
      const refused = panelTitled("Incidents at this site").querySelector("[data-work-refused]") as HTMLElement;
      expect(refused.getAttribute("data-work-code")).toBe(code);
      expect(text(refused)).toContain(copy);
      expect(document.querySelector("main [data-work-empty], main [data-work-empty-icon], main tbody tr")).toBeNull();
      // A refusal without a read timestamp says so; it never shows a read time or a zero.
      expect(text(refused)).toContain("As of: time not recorded");
      cleanup();
      vi.unstubAllGlobals();
    }

    // A changed list on page two is 409: reload page one, never an invented empty set.
    serve({
      [api("incidents", DAY, `&known_at=${K}&cursor=STALE`)]: {
        status: 409,
        body: refusal("WORK_BASIS_CHANGED", "The work list changed; request page one without a cursor."),
      },
      [api("incidents", DAY)]: { status: 200, body: body([incidentRow(1)]) },
    });
    mount(`${page("incidents", DAY)}&known_at=${K}&cursor=STALE`);
    await settledScreen();
    const changed = panelTitled("Incidents at this site").querySelector("[data-work-refused]") as HTMLElement;
    expect(changed.getAttribute("data-work-refused")).toBe("basis_changed");
    expect(text(changed)).toContain("The list changed. Reload the first page.");
    fireEvent.click(changed.querySelector("[data-work-restart]") as HTMLElement);
    await settledScreen();
    expect(text(strip())).toContain("Scoped to Kobo · 1 incidents");
  });

  it("finding_link_uses_pinned_revision", async () => {
    const pinned = incidentRow(1, {
      finding_links: [
        { finding_id: FINDING, finding_revision_id: FINDING_REV, label: `Finding ${FINDING.slice(0, 8)}`, href: "/x" },
        {
          finding_id: "ffffffff-0000-4000-8000-000000000301",
          finding_revision_id: "ffffffff-0000-4000-8000-000000000302",
          label: "Finding ffffffff",
          href: null,
        },
      ],
    });
    serve({
      [api("incidents", DAY)]: {
        status: 200,
        body: body([pinned], { status: "UNKNOWN", coverage: { state: "UNKNOWN", reason: "LINK_SELECTION_MISSING" } }),
      },
    });
    mount(page("incidents", DAY));
    await settledScreen();
    expectSlots("sitework-incidents");
    const panel = panelTitled("Incidents at this site");
    const link = within(panel).getByRole("link", { name: `Finding ${FINDING.slice(0, 8)}` });
    expect(link.getAttribute("href")).toBe(siteFindingHref("KOBO-001", FINDING, FINDING_REV));
    expect(link.getAttribute("href")).toContain(`revision_id=${FINDING_REV}`);
    // A pin without selectable lineage is plain text: no dead link.
    const unlinked = panel.querySelector("[data-work-finding-unlinked]") as HTMLElement;
    expect(unlinked.textContent).toBe("Finding ffffffff");
    expect(unlinked.closest("a")).toBeNull();
    expect(panel.textContent).not.toMatch(/\bF-\d+/);
    // The missing selected source is a neutral link qualification, the case count stays exact.
    expect(text(strip())).toContain("Scoped to Kobo · 1 incidents");
    expect(text(strip())).toContain("No selected source for linked evidence");
    expect(panel.querySelector("[data-work-coverage-line='LINK_SELECTION_MISSING']")).not.toBeNull();
  });
});

describe("W4-01: Site > Work > Maintenance", () => {
  it("maintenance_activity_without_outcome", async () => {
    const rows = [
      requestRow(2, {
        request_state: "COMPLETED",
        state: "COMPLETED",
        asset_id: "40000000-0000-4000-8000-000000000401",
        asset_label: "GEN-01 · generator",
        record_id: "50000000-0000-4000-8000-000000000504",
        activity: "Starter connection inspected",
        outcome_note: null,
      }),
      requestRow(3, { request_state: "OPEN", state: "OPEN" }),
      requestRow(4, { request_state: "CANCELLED", state: "CANCELLED", outcome_note: "Duplicate request" }),
    ];
    serve({
      [api("maintenance", DAY)]: {
        status: 200,
        body: body(rows, { status: "PENDING_RECOMPUTE", coverage: { state: "PARTIAL", reason: "LINK_WORK_PENDING" } }),
      },
    });
    mount(page("maintenance", DAY));
    await settledScreen();
    expectSlots("sitework-maintenance");
    expectPlantedPanelRejected("sitework-maintenance");
    expect(text(strip())).toContain("Scoped to Kobo · 3 maintenance");
    // W6-01b B2: the Maintenance strip links to the live global page with the Site window and the loaded cutoff.
    expect(text(strip())).not.toContain("Not available yet");
    expect(Array.from(strip().querySelectorAll("a")).map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      [
        "Manage in Maintenance",
        "/maintenance?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00.000000Z",
      ],
    ]);
    expect(text(strip())).toContain("Linked evidence is being reassessed");
    const panel = panelTitled("Maintenance at this site");
    expect(text(panel)).toContain("Completed work is activity; the outcome is verified separately");
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Work request",
      "Asset",
      "Activity",
      "Outcome",
      "Next evidence",
    ]);
    const [done, open, cancelled] = Array.from(panel.querySelectorAll("tbody tr")) as HTMLElement[];
    expect(text(done.querySelector("[data-work-case-title]"))).toBe("WR-000002 · Inspect starter circuit");
    expect(text(done.querySelector("[data-work-asset]"))).toBe("GEN-01 · generator");
    expect(done.querySelector("[data-work-state]")?.getAttribute("data-work-tone")).toBe("blue");
    expect(text(done.querySelector("[data-work-activity]"))).toBe("Starter connection inspected");
    // Completed is activity only: the outcome stays Unverified with no verified result.
    for (const row of [done, open, cancelled]) {
      expect(text(row.querySelector("[data-work-outcome]"))).toBe("Unverified");
      expect(row.querySelector("[data-work-outcome]")?.className).toContain("w1f4-action-badge--amber");
      expect(text(row.querySelectorAll("td")[4])).toBe("No next evidence recorded");
    }
    expect(text(done.querySelector("[data-work-outcome-note]"))).toBe("No outcome recorded");
    expect(text(cancelled.querySelector("[data-work-outcome-note]"))).toBe("Duplicate request");
    expect(text(open.querySelectorAll("td")[1].firstElementChild)).toBe("No asset linked");
    expect(open.querySelectorAll("td")[1].querySelector("a")).toBeNull();
    expect(text(open.querySelector("[data-work-activity]"))).toBe("No activity recorded");
    expect(open.querySelector("[data-work-state]")?.getAttribute("data-work-tone")).toBe("amber");
    expect(cancelled.querySelector("[data-work-state]")?.getAttribute("data-work-tone")).toBe("neutral");
    expect(panel.textContent).not.toMatch(/\bVerified\b|Outcome met|Witnessed automatic-start test/);
    expect(panel.querySelector("[data-work-coverage-line='LINK_WORK_PENDING']")).not.toBeNull();
  });

  it("narrow_mock_panels_and_unavailable_links", async () => {
    // First load with no window: the seven complete UTC days ending today 00:00 UTC, five rows.
    const w = defaultWorkWindow();
    expect(new Date(w.to).getTime() - new Date(w.from).getTime()).toBe(7 * 86_400_000);
    expect(w.to.endsWith("T00:00:00Z")).toBe(true);
    const requests = serve({
      [api("maintenance", w)]: { status: 200, body: body([]) },
      [api("incidents", w)]: { status: 200, body: body([]) },
    });
    mount("/sites/KOBO-001/work/maintenance");
    await settledScreen();
    expect(requests).toEqual([api("maintenance", w)]);
    expectSlots("sitework-maintenance");
    const empty = panelTitled("Maintenance at this site").querySelector("[data-work-empty]") as HTMLElement;
    expect(empty.querySelector("[data-work-empty-icon] svg[data-rail-icon='evidence']")).not.toBeNull();
    expect(text(empty.querySelector("h3"))).toBe("No maintenance work at this site");
    expect(text(empty.querySelector("p"))).toBe("No inspection or repair has been raised here in the selected period.");
    // One Work subrow, Actions first, both lists live; no Incidents/Maintenance unavailable entry or Site tab.
    const row = screen.getByRole("navigation", { name: "Work lists" });
    // H1: three known counts (full total_count, one row requested), shown as the mock's `Label (n)`.
    await vi.waitFor(() =>
      expect(within(row).getAllByRole("link").map((l) => [l.textContent, l.getAttribute("aria-current")])).toEqual([
        ["Actions (—)", null],
        ["Incidents (—)", null],
        ["Maintenance (—)", "page"],
      ]),
    );
    expect(document.querySelectorAll("main nav[aria-label='Work lists']")).toHaveLength(1);
    expect(document.querySelectorAll("main [data-tab-unavailable='Incidents'], main [data-tab-unavailable='Maintenance']")).toHaveLength(0);
    // W6-01b B2: the Maintenance global Manage entry is a live link; the notice has no link.
    expect(notice().querySelector("a")).toBeNull();
    expect(text(strip().querySelector("[data-work-manage]"))).toBe("Manage in Maintenance");
    expect(strip().querySelector("[data-work-manage] a")?.getAttribute("href")).toMatch(/^\/maintenance\?from=/);
    // The page heading is the mock's (site name and the screen subtitle).
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain(HYBRID_MINI_GRID_SITE.display_name);
    expect(document.body.textContent).toContain("Site-scoped work · maintenance");
    // The subrow moves to Incidents at the same default window.
    fireEvent.click(within(row).getByRole("link", { name: /^Incidents/ }));
    await settledScreen();
    expect(requests).toEqual([api("maintenance", w), api("incidents", w)]);
    expectSlots("sitework-incidents");
    expect(document.body.textContent).toContain("Site-scoped work · incidents");
    // At narrow width the table keeps its minimum width inside its own scroller (CSS; measured in the captures).
    expect(document.querySelector("main .w1f4-changes-work.work-cases")).not.toBeNull();
  });
});

describe("W4-01 fix r1: subtab counts, strip words and coverage copy", () => {
  const labels = () =>
    within(screen.getByRole("navigation", { name: "Work lists" })).getAllByRole("link").map((l) => l.textContent);

  it("work_subtab_counts", async () => {
    // H1: three distinct full counts from each list's own total_count, one row requested, no cursor or cutoff.
    serve({
      [api("incidents", DAY)]: { status: 200, body: body([incidentRow(1)], { total_count: 4 }) },
      [countPath("actions", DAY)]: actionCount(11),
      [countPath("incidents", DAY)]: { status: 200, body: body([incidentRow(1)], { total_count: 4 }) },
      [countPath("maintenance", DAY)]: { status: 200, body: body([], { total_count: 0 }) },
    });
    mount(page("incidents", DAY));
    await settledScreen();
    await vi.waitFor(() => expect(labels()).toEqual(["Actions (11)", "Incidents (4)", "Maintenance (0)"]));
    expect(countRequests.slice().sort()).toEqual(
      [countPath("actions", DAY), countPath("incidents", DAY), countPath("maintenance", DAY)].sort(),
    );
    expect(countRequests.join(" ")).not.toMatch(/known_at|cursor/);
    expect(document.querySelectorAll("main nav[aria-label='Work lists']")).toHaveLength(1);
    cleanup();
    vi.unstubAllGlobals();

    // Pending, refused and a missing/non-finite count read as a dash, never as zero; each count is independent.
    serve({
      [api("maintenance", DAY)]: { status: 200, body: body([]) },
      [countPath("actions", DAY)]: { status: 503, body: refusal("X", "down") },
      [countPath("incidents", DAY)]: { status: 200, body: { ...body([]), total_count: null } },
      [countPath("maintenance", DAY)]: { status: 200, body: body([], { total_count: 3 }) },
    });
    mount(page("maintenance", DAY));
    await settledScreen();
    await vi.waitFor(() => expect(labels()).toEqual(["Actions (—)", "Incidents (—)", "Maintenance (3)"]));
    cleanup();
    vi.unstubAllGlobals();

    // Actions with no selected window requests no counts at all.
    const idle = serve({});
    mount("/sites/KOBO-001/work");
    await settledScreen();
    expect(labels()).toEqual(["Actions (—)", "Incidents (—)", "Maintenance (—)"]);
    expect(idle).toEqual([]);
    expect(countRequests).toEqual([]);
    cleanup();
    vi.unstubAllGlobals();

    // A window change clears the old counts at once and reads the new window.
    const W2 = { from: "2026-10-08T00:00:00Z", to: "2026-10-09T00:00:00Z" };
    serve({
      [api("incidents", DAY)]: { status: 200, body: body([]) },
      [api("incidents", W2)]: { status: 200, body: body([]) },
      [countPath("actions", DAY)]: actionCount(5),
      [countPath("incidents", DAY)]: { status: 200, body: body([], { total_count: 6 }) },
      [countPath("maintenance", DAY)]: { status: 200, body: body([], { total_count: 7 }) },
      [countPath("actions", W2)]: actionCount(8),
      [countPath("incidents", W2)]: { status: 200, body: body([], { total_count: 9 }) },
    });
    mount(page("incidents", DAY));
    await settledScreen();
    await vi.waitFor(() => expect(labels()).toEqual(["Actions (5)", "Incidents (6)", "Maintenance (7)"]));
    fireEvent.change(document.querySelector("[data-work-window] input") as HTMLElement, { target: { value: "2026-10-08" } });
    fireEvent.change(document.querySelectorAll("[data-work-window] input")[1] as HTMLElement, { target: { value: "2026-10-08" } });
    fireEvent.click(screen.getByRole("button", { name: "Show incidents" }));
    await settledScreen();
    // Maintenance for the new window is unserved (599): unknown, and the old 7 is gone.
    await vi.waitFor(() => expect(labels()).toEqual(["Actions (8)", "Incidents (9)", "Maintenance (—)"]));
  });

  it("strip_words_and_coverage_copy", async () => {
    const one = [incidentRow(1)];
    const cases: [Partial<WorkIndexBody>, string | null, string | null][] = [
      [{ status: "PENDING_RECOMPUTE", coverage: { state: "PARTIAL", reason: "LINK_WORK_PENDING" } }, "Linked evidence is being reassessed", "Linked evidence is being reassessed."],
      [{ status: "STALE_SOURCE", coverage: { state: "PARTIAL", reason: "LINK_SOURCE_STALE" } }, "Linked evidence source is out of date", "Linked evidence is being reassessed."],
      [{ status: "UNKNOWN", coverage: { state: "UNKNOWN", reason: "LINK_SELECTION_MISSING" } }, "No selected source for linked evidence", "A linked record has no selected source."],
      [{ status: "HISTORICAL" }, "Read as of 2026-10-07 00:00 UTC", null],
    ];
    for (const [over, word, coverage] of cases) {
      serve({ [api("incidents", DAY)]: { status: 200, body: body(one, over) } });
      mount(page("incidents", DAY));
      await settledScreen();
      expect(strip().querySelectorAll(":scope > span")).toHaveLength(3);
      expect(strip().querySelector(".status-strip__state")).toBeNull();
      expect(text(strip().querySelector("[data-work-status]"))).toBe(word);
      const line = document.querySelector("main [data-work-coverage-line]");
      if (coverage === null) expect(line).toBeNull();
      else {
        expect(text(line)).toContain(coverage);
        expect(text(line)).not.toContain("listed in full");
      }
      cleanup();
      vi.unstubAllGlobals();
    }
    // Loading copy comes from the pending read only.
    vi.stubGlobal("fetch", () => new Promise(() => undefined));
    mount(page("incidents", DAY));
    await vi.waitFor(() => expect(text(strip())).toContain("Reading work records"));
    cleanup();
    vi.unstubAllGlobals();
    // A shared cursor link with no local trail counts the page, never the page length as the total.
    serve({
      [api("incidents", DAY, `&known_at=${K}&cursor=SHARED`)]: {
        status: 200,
        body: body([incidentRow(6), incidentRow(7)], { total_count: 7, status: "HISTORICAL" }),
      },
    });
    mount(`${page("incidents", DAY)}&known_at=${K}&cursor=SHARED`);
    await settledScreen();
    expect(text(panelTitled("Incidents at this site").querySelector("[data-work-showing]"))).toBe("Showing 2 of 7");
  });
});

const OPP = "70000000-0000-4000-8000-000000000701";
const OPP_BARE = "70000000-0000-4000-8000-000000000702";
const SCN = "80000000-0000-4000-8000-000000000801";
const contextsPath = (ids: string[]) =>
  `/api/sites/KOBO-001/work/decision-contexts?case_ids=${ids.join(",")}&known_at=${K}`;
const contextsBody = (contexts: Record<string, unknown[]>) => ({
  status: 200,
  body: { schema_version: "mini-work-contexts-1", known_at: K, contexts },
});

describe("W4-03 unit 8: Site Work decision context", () => {
  it("decision_context_and_unlinked_case", async () => {
    const finding = { finding_id: FINDING, finding_revision_id: FINDING_REV, label: "x", href: "/x" };
    const rows = [incidentRow(1, { finding_links: [finding] }), incidentRow(2), incidentRow(3)];
    const ids = rows.map((r) => r.case_id);
    const requests = serve({
      [api("incidents", DAY)]: { status: 200, body: body(rows, { total_count: 3 }) },
      [contextsPath(ids)]: contextsBody({
        [ids[0]]: [
          { kind: "OPPORTUNITY", id: OPP, label: "OPP-000001", url: `/sites/KOBO-001/opportunities/${OPP}` },
          { kind: "SCENARIO", id: SCN, label: "SCN-000002 · Grain mill one-hour trial", url: null },
        ],
        [ids[1]]: [],
        [ids[2]]: [{ kind: "OPPORTUNITY", id: OPP_BARE, label: "Decision context unavailable", url: null }],
      }),
    });
    mount(page("incidents", DAY));
    await settledScreen();
    expectSlots("sitework-incidents");
    const panel = panelTitled("Incidents at this site");
    await vi.waitFor(() => expect(panel.querySelector("[data-work-decision-context]")).not.toBeNull());
    // One overlay read: this page's case IDs at the list's exact cutoff, outside the W4-01 list reads.
    expect(contextRequests).toEqual([contextsPath(ids)]);
    expect(requests).toEqual([api("incidents", DAY)]);
    const row = (id: string) => panel.querySelector(`[data-work-row="${id}"]`) as HTMLElement;
    const linkedCell = row(ids[0]).querySelectorAll("td")[3] as HTMLElement;
    // After the Finding link, in the same `Linked findings` cell: Opportunity first, then Scenario.
    expect(text(linkedCell)).toBe(
      `Finding ${FINDING.slice(0, 8)}Decision context: OPP-000001 · SCN-000002 · Grain mill one-hour trial (Scenario detail unavailable)`,
    );
    const findingEl = linkedCell.querySelector("[data-work-finding]") as HTMLElement;
    const context = linkedCell.querySelector("[data-work-decision-context='loaded']") as HTMLElement;
    expect(findingEl.compareDocumentPosition(context) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(linkedCell).getByRole("link", { name: "OPP-000001" }).getAttribute("href")).toBe(
      `/sites/KOBO-001/opportunities/${OPP}`,
    );
    expect(within(linkedCell).queryByRole("link", { name: /SCN-000002/ })).toBeNull();
    // The unlinked case shows no context; the unselected root is noninteractive.
    expect(row(ids[1]).querySelector("[data-work-decision-context]")).toBeNull();
    expect(text(row(ids[1]).querySelectorAll("td")[3])).toBe("No linked finding");
    const bare = row(ids[2]).querySelector("[data-work-decision-context]") as HTMLElement;
    expect(text(bare)).toBe("Decision context: Decision context unavailable");
    expect(bare.querySelector("a")).toBeNull();
    // No W4-01 count, column, state or case URL changes.
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Case",
      "Window",
      "What happened",
      "Linked findings",
      "State",
    ]);
    expect(text(strip())).toContain("Scoped to Kobo · 3 incidents");
    expect(panel.querySelectorAll("[data-work-row]")).toHaveLength(3);
    for (const id of ids) expect(row(id).querySelector("[data-work-case-title] a")).toBeNull();
  });

  it("u9b_incident_linked_and_refused_overlay_panels", async () => {
    const finding = { finding_id: FINDING, finding_revision_id: FINDING_REV, label: "x", href: "/x" };
    const rows = [incidentRow(1, { finding_links: [finding] }), incidentRow(2)];
    const ids = rows.map((r) => r.case_id);
    serve({
      [api("incidents", DAY)]: { status: 200, body: body(rows, { total_count: 2 }) },
      [contextsPath(ids)]: contextsBody({
        [ids[0]]: [{ kind: "SCENARIO", id: SCN, label: "SCN-000002 · Grain mill one-hour trial", url: null }],
        [ids[1]]: [],
      }),
    });
    mount(page("incidents", DAY));
    await settledScreen();
    const linked = panelTitled("Incidents at this site");
    await vi.waitFor(() => expect(linked.querySelector("[data-work-decision-context]")).not.toBeNull());
    // The overlay adds no panel: the W4-01 panel structure holds with the linked context rendered.
    expectV69Panels("sitework-incidents");
    expectPlantedPanelRejected("sitework-incidents");
    const line = linked.querySelector("[data-work-decision-context='loaded']") as HTMLElement;
    expect(text(line)).toBe("Decision context: SCN-000002 · Grain mill one-hour trial (Scenario detail unavailable)");
    expect(line.querySelector("a")).toBeNull();
    cleanup();

    // A scoped 503 on the overlay leaves the W4-01 list intact: same rows, same count, literal copy, no prefix.
    // u9c: the refused state is the captured five-row stocked list.
    const five = [rows[0], ...[2, 3, 4, 5].map((n) => incidentRow(n))];
    const fiveIds = five.map((r) => r.case_id);
    serve({
      [api("incidents", DAY)]: { status: 200, body: body(five, { total_count: 5 }) },
      [contextsPath(fiveIds)]: { status: 503, body: { detail: { code: "SERVICE_UNAVAILABLE", message: "x" } } },
    });
    mount(page("incidents", DAY));
    await settledScreen();
    const refused = panelTitled("Incidents at this site");
    await vi.waitFor(() =>
      expect(refused.querySelectorAll("[data-work-decision-context='unavailable']")).toHaveLength(1),
    );
    expectV69Panels("sitework-incidents");
    expectPlantedPanelRejected("sitework-incidents");
    // PR-12.3: exactly one panel-level literal, beside (not inside) the table, scoped to the displayed rows.
    const panelLine = refused.querySelector("[data-work-decision-context='unavailable']") as HTMLElement;
    expect(text(panelLine)).toBe("Decision context unavailable");
    expect(panelLine.closest("table")).toBeNull();
    expect(panelLine.getAttribute("data-work-decision-context-scope")).toBe(fiveIds.join(" "));
    expect(refused.querySelectorAll("table [data-work-decision-context]")).toHaveLength(0); // no row-level copy
    expect(refused.textContent).not.toContain("Decision context:"); // no positive context
    expect(refused.textContent?.split("Decision context unavailable")).toHaveLength(2);
    // The canonical Finding link in the linked row is intact.
    expect(refused.querySelector(`[data-work-row="${ids[0]}"] [data-work-finding-link]`)).not.toBeNull();
    expect(refused.querySelectorAll("[data-work-row]")).toHaveLength(5);
    expect(refused.querySelectorAll("[data-work-finding-link]").length).toBeGreaterThan(0);
    // u9c: at <=760 px the Incident table scrolls vertically at exactly 224 px inside the 460 px panel cap.
    const narrow = WORK_CSS.indexOf("@media (max-width: 760px)");
    const rule = '.work-cases [data-work-table="incidents"] .data-table__scroll { max-height: 224px; overflow: auto; }';
    expect(WORK_CSS).toContain(rule);
    expect(WORK_CSS.indexOf(rule)).toBeGreaterThan(narrow);
    expect(WORK_CSS).not.toContain("max-height: 240px");
    expect(text(strip())).toContain("Scoped to Kobo · 5 incidents");
  });

  it("unverified_maintenance_and_unavailable_destinations", async () => {
    const rows = [
      requestRow(4, { request_state: "COMPLETED", state: "COMPLETED", activity: "Starter connection inspected" }),
      requestRow(5),
    ];
    const ids = rows.map((r) => r.case_id);
    serve({
      [api("maintenance", DAY)]: { status: 200, body: body(rows) },
      [contextsPath(ids)]: contextsBody({
        [ids[0]]: [{ kind: "OPPORTUNITY", id: OPP, label: "OPP-000001", url: `/sites/KOBO-001/opportunities/${OPP}` }],
        [ids[1]]: [],
      }),
    });
    mount(page("maintenance", DAY));
    await settledScreen();
    expectSlots("sitework-maintenance");
    const panel = panelTitled("Maintenance at this site");
    await vi.waitFor(() => expect(panel.querySelector("[data-work-decision-context]")).not.toBeNull());
    const row = (id: string) => panel.querySelector(`[data-work-row="${id}"]`) as HTMLElement;
    // A secondary line under Activity, never a new column; the outcome stays unverified.
    const activity = row(ids[0]).querySelectorAll("td")[2] as HTMLElement;
    const line = activity.querySelector("[data-work-decision-context='loaded']") as HTMLElement;
    expect(text(line)).toBe("Decision context: OPP-000001");
    const activityText = activity.querySelector("[data-work-activity]") as HTMLElement;
    expect(activityText.compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(panel.querySelectorAll("thead th")).toHaveLength(5);
    for (const id of ids) {
      expect(row(id).querySelector("[data-work-outcome]")?.getAttribute("data-work-outcome")).toBe("UNVERIFIED");
      expect(row(id).querySelector("[data-work-case-title] a")).toBeNull();
    }
    expect(row(ids[1]).querySelector("[data-work-decision-context]")).toBeNull();
    expect(text(strip())).toContain("Scoped to Kobo · 2 maintenance");
    cleanup();

    // A refused overlay says so on every row without hiding them or implying they are unlinked.
    serve({
      [api("maintenance", DAY)]: { status: 200, body: body(rows) },
      [contextsPath(ids)]: { status: 404, body: { detail: { code: "WORK_CASE_NOT_FOUND", message: "x" } } },
    });
    mount(page("maintenance", DAY));
    await settledScreen();
    const refusedPanel = panelTitled("Maintenance at this site");
    await vi.waitFor(() =>
      expect(refusedPanel.querySelectorAll("[data-work-decision-context='unavailable']")).toHaveLength(2),
    );
    expect(refusedPanel.querySelectorAll("[data-work-row]")).toHaveLength(2);
    for (const el of Array.from(refusedPanel.querySelectorAll("[data-work-decision-context]"))) {
      expect(text(el)).toBe("Decision context unavailable");
    }
    expect(text(strip())).toContain("Scoped to Kobo · 2 maintenance");
  });
});

describe("W6-01a A2: Site Work global manage href", () => {
  const scope = { from: "2026-10-15T00:00:00Z", to: "2026-10-22T00:00:00Z" };
  it("carries the window and the selected cutoff, never a Site key, cursor or limit", () => {
    expect(globalWorkManageHref("incidents", scope, "2026-10-22T12:00:00Z")).toBe(
      "/incidents?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A00Z",
    );
    expect(globalWorkManageHref("maintenance", scope, "2026-10-22T12:00:00Z")).toBe(
      "/maintenance?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A00Z",
    );
    // An explicit Site cutoff wins over the loaded list's; no cutoff from either source omits `known_at`.
    expect(globalWorkManageHref("incidents", { ...scope, knownAt: "2026-10-20T08:00:00Z", cursor: "C2" }, "2026-10-22T12:00:00Z")).toBe(
      "/incidents?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-20T08%3A00%3A00Z",
    );
    expect(globalWorkManageHref("incidents", scope, null)).toBe("/incidents?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z");
  });
});
