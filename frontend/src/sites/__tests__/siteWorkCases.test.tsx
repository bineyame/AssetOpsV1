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
import { rowLabels } from "../../test/unavailableEntry";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import { defaultWorkWindow, type WorkIndexBody, type WorkRow } from "../workClient";
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

function serve(gets: Record<string, Served>) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    const path = decodeURIComponent(String(url));
    requests.push(path);
    const hit = gets[path];
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: path } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return requests;
}

const api = (kind: string, w: { from: string; to: string }, extra = "") =>
  `/api/sites/KOBO-001/work/${kind}?from=${w.from}&to=${w.to}&limit=5${extra}`;
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
  expect(text(notices[0])).toBe("Case history is stored with this site. A global work page and create flow are not available yet.");
  expect(text(strips[0])).toContain("These are work records at this site");
  expect(main.textContent).not.toMatch(/INC-203|WR-019|Manage in \w+ →|global create flow with this site filled in/);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

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
    });
    mount(page("incidents", DAY));
    await settledScreen();
    expectSlots("sitework-incidents");
    expectPlantedPanelRejected("sitework-incidents");
    expect(text(strip())).toContain("Scoped to Kobo · 7 incidents");
    expect(text(strip())).toContain("Manage in Incidents · Not available yet");
    expect(strip().querySelector("a")).toBeNull();
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
    cleanup();
    vi.unstubAllGlobals();

    // Empty: an exact zero from a complete read keeps the mock's empty block, no fake row.
    serve({ [api("incidents", DAY)]: { status: 200, body: body([]) } });
    mount(page("incidents", DAY));
    await settledScreen();
    expectSlots("sitework-incidents");
    expect(text(strip())).toContain("Scoped to Kobo · 0 incidents");
    const empty = panelTitled("Incidents at this site").querySelector("[data-work-empty]") as HTMLElement;
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
      expect(document.querySelector("main [data-work-empty], main tbody tr")).toBeNull();
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
    expect(text(strip())).toContain("Manage in Maintenance · Not available yet");
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
    expect(text(empty.querySelector("h3"))).toBe("No maintenance work at this site");
    expect(text(empty.querySelector("p"))).toBe("No inspection or repair has been raised here in the selected period.");
    // One Work subrow, Actions first, both lists live; no Incidents/Maintenance unavailable entry or Site tab.
    const row = screen.getByRole("navigation", { name: "Work lists" });
    expect(rowLabels(row)).toEqual(["Actions", "Incidents", "Maintenance"]);
    expect(within(row).getAllByRole("link").map((l) => [l.textContent, l.getAttribute("aria-current")])).toEqual([
      ["Actions", null],
      ["Incidents", null],
      ["Maintenance", "page"],
    ]);
    expect(document.querySelectorAll("main nav[aria-label='Work lists']")).toHaveLength(1);
    expect(document.querySelectorAll("main [data-tab-unavailable='Incidents'], main [data-tab-unavailable='Maintenance']")).toHaveLength(0);
    // The global Manage link is static text; the notice has no link.
    expect(notice().querySelector("a")).toBeNull();
    expect(text(strip().querySelector("[data-work-manage]"))).toBe("Manage in Maintenance · Not available yet");
    // The page heading is the mock's (site name and the screen subtitle).
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain(HYBRID_MINI_GRID_SITE.display_name);
    expect(document.body.textContent).toContain("Site-scoped work · maintenance");
    // The subrow moves to Incidents at the same default window.
    fireEvent.click(within(row).getByRole("link", { name: "Incidents" }));
    await settledScreen();
    expect(requests).toEqual([api("maintenance", w), api("incidents", w)]);
    expectSlots("sitework-incidents");
    expect(document.body.textContent).toContain("Site-scoped work · incidents");
    // At narrow width the table keeps its minimum width inside its own scroller (CSS; measured in the captures).
    expect(document.querySelector("main .w1f4-changes-work.work-cases")).not.toBeNull();
  });
});
