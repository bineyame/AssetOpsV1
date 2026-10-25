/**
 * W6-01b B2: the global Maintenance root, Corrective view (`.agent/W6-01-build-spec.md` section 2, section 3.1
 * A2Q1-A2Q10/X1-X8/CL3-1 and the "B1-B3 pre-flight rulings" P-B2-1..15). Typed responses only: the persisted
 * positive, zero, historical, refused, cursor-changed, stress and linked states are captured against the real API in
 * `.agent/W6-01-evidence/B2/`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { MAINTENANCE_PATH } from "../../shell/operatorSiteRoutes";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { GlobalMaintenanceFrame } from "../GlobalMaintenance";
import {
  createGlobalWorkClient,
  type GlobalMaintenanceBody,
  type GlobalMaintenanceRow,
  type GlobalWorkClient,
  type GlobalWorkQuery,
  type GlobalWorkResult,
} from "../globalWorkClient";

const FROM = "2026-10-14T00:00:00Z";
const TO = "2026-10-21T00:00:00Z";
const KNOWN = "2026-10-21T12:00:00Z";
const PAGE = `/maintenance?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const SITE_MAINTENANCE = `/sites/KOBO-001/work/maintenance?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&known_at=2026-10-21T12%3A00%3A00Z`;
const TITLE200 = "Startermotorandcontrolpanelinspection".repeat(6).slice(0, 200);
const OWNER128 = "Fieldmaintenancesupervisorteam".repeat(5).slice(0, 128);
const COUNTS = { OPEN: 4, IN_PROGRESS: 1, COMPLETED: 1, CANCELLED: 1 };

function row(n: number, over: Partial<GlobalMaintenanceRow> = {}): GlobalMaintenanceRow {
  return {
    site_code: "KOBO-001",
    site_name: "Kobo",
    site_id: "00000000-0000-4000-8000-000000000002",
    site_code_key: "kobo-001",
    site_domain: "MINIGRID",
    case_id: `00000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`,
    code: `WR-${String(n).padStart(6, "0")}`,
    kind: "MAINTENANCE_REQUEST",
    revision_id: `00000000-0000-4000-8000-${String(200 + n).padStart(12, "0")}`,
    title: `Request ${n}`,
    narrative: "Inspection requested.",
    occurred_at: "2026-10-18T10:00:00Z",
    created_at: "2026-10-20T11:59:00Z",
    recorded_at: "2026-10-20T11:59:00Z",
    state: "OPEN",
    owner: null,
    asset_id: null,
    asset_label: null,
    incident_id: null,
    record_id: null,
    activity: null,
    outcome_note: null,
    finding_links: [],
    action_links: [],
    source_provenance: {
      classification: "UNKNOWN",
      state: "UNKNOWN",
      source_ids: [],
      evidence_ids: [],
      basis_sha256: `sha256:${"0".repeat(64)}`,
      reasons: [],
    },
    links: {
      site: { label: "Kobo", href: "/sites/KOBO-001" },
      site_maintenance: { label: "Site maintenance", href: SITE_MAINTENANCE },
      detail: null,
    },
    ...over,
  };
}

function body(rows: GlobalMaintenanceRow[], over: Partial<GlobalMaintenanceBody> = {}): GlobalMaintenanceBody {
  return {
    schema_version: "global-work-index-1",
    scope: { tenant_id: "00000000-0000-4000-8000-000000000001", authorized_site_count: 2, covered_site_count: 2, access_basis: "sha256:x" },
    window: { from: FROM, to: TO, bounds: "[from, to)" },
    known_at: KNOWN,
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null, sites: [] },
    total_count: rows.length,
    state_counts: { OPEN: rows.length, IN_PROGRESS: 0, COMPLETED: 0, CANCELLED: 0 },
    rows,
    next_cursor: null,
    selection_token: "sha256:token",
    ...over,
  };
}

type Answer = GlobalWorkResult<GlobalMaintenanceBody>;

function client(answers: Record<string, Answer>, gate?: Promise<void>): GlobalWorkClient & { calls: GlobalWorkQuery[] } {
  const calls: GlobalWorkQuery[] = [];
  return {
    calls,
    async incidents() {
      throw new Error("the Maintenance page never reads incidents");
    },
    async maintenance(query) {
      calls.push(query);
      if (gate) await gate;
      const answer = answers[query.cursor ?? "page-one"];
      if (answer === undefined) throw new Error(`no answer for ${JSON.stringify(query)}`);
      return answer;
    },
  };
}

const loaded = (value: GlobalMaintenanceBody): Answer => ({ status: "loaded", value });

function Where() {
  const location = useLocation();
  return (
    <output data-testid="where" data-trail={JSON.stringify((location.state as { globalWorkTrail?: unknown } | null)?.globalWorkTrail ?? null)}>
      {`${location.pathname}${location.search}`}
    </output>
  );
}

function mount(path: string, reads: GlobalWorkClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={MAINTENANCE_PATH} element={<GlobalMaintenanceFrame client={reads} />} />
      </Routes>
      <Where />
    </MemoryRouter>,
  );
}

async function settled() {
  await waitFor(() => expect(document.querySelector("[data-global-work-loading]")).toBeNull());
  await settledScreen();
}

const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const cards = () => document.querySelector("[data-global-work-cards]");
const cell = (tr: Element, i: number) => tr.querySelectorAll("td")[i] as HTMLElement;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W6-01b B2: global Maintenance (Corrective)", () => {
  it("renders the mock header, tabs, cards, panel, cells, notice and pager over a typed five-row page", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const rows = [
      row(1, { title: TITLE200, owner: OWNER128, state: "IN_PROGRESS", activity: "Replaced starter relay." }),
      row(2, {
        state: "COMPLETED",
        owner: "Field team C",
        finding_links: [{ label: "Finding a1b2c3d4", href: "/sites/KOBO-001/findings/f1?revision_id=r1" }],
        action_links: [{ label: "Action e5f6a7b8", href: "/sites/KOBO-001/actions/a1" }],
        source_provenance: { ...row(2).source_provenance, classification: "AUTHORED_DEMONSTRATION" },
      }),
      row(3, { state: "CANCELLED", asset_label: "GEN-001 · generator" }),
      row(4, { action_links: [{ label: "Action e5f6a7b8", href: null }] }),
      row(5, { site_code: "KOBO-002", site_name: "Kobo 2", links: { ...row(5).links, site: { label: "Kobo 2", href: "/sites/KOBO-002" } } }),
    ];
    const reads = client(
      {
        "page-one": loaded(body(rows, { total_count: 7, state_counts: COUNTS, next_cursor: "CURSOR-2" })),
        "CURSOR-2": loaded(body([row(6), row(7)], { total_count: 7, state_counts: COUNTS })),
      },
      gate,
    );
    mount(PAGE, reads);

    // CL3-1: the loading sentence stands in for the cards and table body; the heading, tabs and controls stay.
    expect(text(document.querySelector("[data-global-work-loading]"))).toBe("Loading the work requests across the estate.");
    expect(screen.getByRole("heading", { level: 1, name: "Maintenance" })).toBeInTheDocument();
    expect(document.querySelector("[data-global-work-controls]")).not.toBeNull();
    expect(document.querySelector("[data-global-work-tabs]")).not.toBeNull();
    expect(cards()).toBeNull();
    expect(document.querySelector("table")).toBeNull();
    release();
    await settled();

    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: null, cursor: null }]);
    expectV69Panels("maintenance");
    expectPlantedPanelRejected("maintenance");
    expect(screen.getByRole("main", { name: "Maintenance" })).toBeInTheDocument();

    // P-B2-9/10: breadcrumb (plain current location), h1, subtitle, then the view tabs before the date bar.
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(text(crumbs)).toBe("Maintenance");
    expect(within(crumbs).queryByRole("link")).toBeNull();
    expect(document.body.textContent).toContain("Physical maintenance work and outcome verification");
    const tabs = screen.getByRole("navigation", { name: "Maintenance views" });
    const items = Array.from(tabs.querySelectorAll("li"));
    // W6-01b B3: the Preventive view is live (CL3-2, P-B3-8); see `preventive_card_and_tab_link_after_b3`.
    expect(items.map(text)).toEqual(["Corrective", "Preventive · scheduled"]);
    expect(tabs.querySelector('[aria-current="page"]')?.textContent).toBe("Corrective");
    const header = document.querySelector("header.page-header") as HTMLElement;
    const bar = document.querySelector("[data-global-work-bar]") as HTMLElement;
    expect(header.compareDocumentPosition(tabs) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(tabs.compareDocumentPosition(bar) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    // Controls (section 2) and the status line; no cutoff input (A2Q5).
    expect(bar.getAttribute("class")).toContain("site-date-bar");
    expect(within(bar).getByRole("form", { name: "Maintenance window" })).toBeInTheDocument();
    expect(within(bar).getByLabelText("From (UTC)")).toHaveValue("2026-10-14");
    expect(within(bar).getByLabelText("To (UTC, exclusive)")).toHaveValue("2026-10-21");
    expect(bar.querySelectorAll("input")).toHaveLength(2);
    expect(text(document.querySelector("[data-global-work-status]"))).toBe("As known at 21 Oct 2026, 12:00 UTC");

    // P-B2-3/4: the four mock cards; Open work over the full selection; the separate View detail slot unavailable.
    expect(
      Array.from(cards()!.querySelectorAll("li.v69-metric")).map((li) => [
        text(li.querySelector(".v69-metric__label")),
        text(li.querySelector(".v69-metric__value")),
      ]),
    ).toEqual([
      ["Open work", "5"],
      ["Verification overdue", "Not assessed"],
      ["Preventive due in 30 days", "Not assessed"],
      ["Repeat findings", "Not assessed"],
    ]);
    const notes = Array.from(cards()!.querySelectorAll(".v69-metric__note"));
    expect(text(notes[0])).toBe("5 requests in progress or open");
    expect(text(notes[1])).toBe("No work-outcome verification clock");
    expect(text(notes[2].querySelector("[data-global-work-preventive-note]"))).toBe("See Preventive");
    expect(text(notes[2].querySelector("[data-global-work-preventive-link]"))).toBe("View detail →");
    expect(text(notes[3])).toBe("No repeat-finding assessment");
    const overdue = cards()!.querySelector('[data-global-work-card="verification_overdue"]') as HTMLElement;
    expect(overdue.className).toContain("v69-metric--assessment");
    expect(overdue.className).toContain("v69-metric--amber");
    expect(document.body.textContent).not.toMatch(/WR-019|WR-021|GreenHarvest|GEN-CR-01|Charging operations lead|Claimable/);

    // P-B2-5/7: the footer is the panel sub-line; columns and cells.
    const panel = panelTitled("Corrective work requests");
    expect(text(panel.querySelector(".panel__description"))).toBe("Completed is activity evidence only; outcome is verified separately");
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Work request",
      "Asset / site",
      "Owner",
      "State",
      "Verification",
      "Warranty",
    ]);
    expect(Array.from(panel.querySelectorAll("col")).map((c) => (c as HTMLElement).style.width)).toEqual([
      "220px",
      "210px",
      "160px",
      "120px",
      "170px",
      "150px",
    ]);
    const trs = Array.from(panel.querySelectorAll("tbody tr"));
    expect(trs).toHaveLength(5);
    const first = trs[0];
    const titleLink = within(cell(first, 0)).getAllByRole("link")[0];
    expect(titleLink.textContent).toBe(`WR-000001 · ${TITLE200}`);
    expect(titleLink.getAttribute("href")).toBe(SITE_MAINTENANCE);
    const full = cell(first, 0).querySelector("[data-global-work-full-title]") as HTMLDetailsElement;
    expect(full.tagName).toBe("DETAILS");
    expect(text(full)).toBe(`Full title text${TITLE200}`);
    expect(text(cell(first, 0).querySelector("[data-global-work-lineage]"))).toBe("No linked Finding or Action");
    expect(text(cell(first, 0).querySelector("[data-global-work-source] summary"))).toBe("Source unverified");
    expect(text(cell(first, 1))).toBe("No asset recorded · Kobo");
    expect(within(cell(first, 1)).getByRole("link", { name: "Kobo" })).toHaveAttribute("href", "/sites/KOBO-001");
    expect(text(cell(first, 2))).toBe(OWNER128);
    expect(text(cell(first, 3))).toBe("In progress");
    expect(cell(first, 3).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "blue");
    expect(text(cell(first, 4))).toBe("Not established");
    expect(cell(first, 4).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "amber");
    expect(text(cell(first, 5))).toBe("Not recorded");
    expect(cell(first, 5).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "neutral");
    for (const i of [0, 1, 2]) expect(cell(first, i).querySelector(".global-work-clamp")).not.toBeNull();

    // P-B2-8: the exact selected Finding and Action links beneath the primary link (the maintenance-linked proof).
    const second = trs[1];
    expect(text(cell(second, 0).querySelector("[data-global-work-lineage]"))).toBe("Finding a1b2c3d4 · Action e5f6a7b8");
    expect(
      within(cell(second, 0).querySelector("[data-global-work-lineage]") as HTMLElement)
        .getAllByRole("link")
        .map((a) => [a.textContent, a.getAttribute("href")]),
    ).toEqual([
      ["Finding a1b2c3d4", "/sites/KOBO-001/findings/f1?revision_id=r1"],
      ["Action e5f6a7b8", "/sites/KOBO-001/actions/a1"],
    ]);
    expect(text(cell(second, 0).querySelector("[data-global-work-source] summary"))).toBe("Prepared example data");
    expect(text(cell(second, 2))).toBe("Field team C");
    expect(text(cell(second, 3))).toBe("Completed");
    expect(text(cell(trs[2], 3))).toBe("Cancelled");
    expect(cell(trs[2], 3).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "neutral");
    expect(text(cell(trs[2], 1))).toBe("GEN-001 · generator · Kobo");
    expect(text(cell(trs[3], 0).querySelector("[data-global-work-lineage]"))).toBe("Action e5f6a7b8");
    expect(within(cell(trs[3], 0).querySelector("[data-global-work-lineage]") as HTMLElement).queryByRole("link")).toBeNull();
    expect(text(cell(trs[3], 2))).toBe("Not assigned");
    expect(text(cell(trs[3], 3))).toBe("Open");
    expect(cell(trs[3], 3).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "amber");

    // P-B2-6: the blue lifecycle notice after the panel, with the bounded copy (MOCK DEVIATION).
    const notice = document.querySelector("[data-global-work-notice]") as HTMLElement;
    expect(notice.className).toContain("v69-notice--blue");
    expect(text(notice)).toBe("A completed request records activity; an equipment outcome remains unverified.");
    expect(panel.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    // Scroll affordance and pager (A2Q10).
    expect(text(panel.querySelector("[data-global-work-scroll-hint]"))).toBe("Scroll table horizontally");
    expect(screen.getByRole("navigation", { name: "Maintenance pages" })).toBeInTheDocument();
    expect(text(panel.querySelector("[data-global-work-showing]"))).toBe("Showing 1–5 of 7");
    expect(panel.querySelector("[data-global-work-previous]")).toBeNull();
    fireEvent.click(panel.querySelector("[data-global-work-next]") as HTMLElement);
    await settled();
    expect(reads.calls[1]).toEqual({ from: FROM, to: TO, known_at: null, cursor: "CURSOR-2" });
    expect(screen.getByTestId("where").textContent).toBe(`${PAGE}&cursor=CURSOR-2`);
    expect(screen.getByTestId("where").getAttribute("data-trail")).toBe("[null]");
    const page2 = panelTitled("Corrective work requests");
    expect(text(page2.querySelector("[data-global-work-showing]"))).toBe("Showing 6–7 of 7");
    expect(page2.querySelector("[data-global-work-next]")).toBeNull();
    expect(text(cards()!.querySelector(".v69-metric__value"))).toBe("5");
    fireEvent.click(page2.querySelector("[data-global-work-previous]") as HTMLElement);
    await settled();
    expect(screen.getByTestId("where").textContent).toBe(PAGE);
  });

  it("preventive_card_and_tab_link_after_b3", async () => {
    const reads = client({ "page-one": loaded(body([row(1)], { status: "HISTORICAL" })), C2: loaded(body([row(2)])) });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&cursor=C2`, reads);
    await settled();
    const preventive = `/maintenance/preventive?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;
    // The separate card link keeps the mock `See Preventive` note; neither link carries the cursor.
    const note = cards()!.querySelector('[data-global-work-card="preventive_due"] .v69-metric__note') as HTMLElement;
    expect(text(note.querySelector("[data-global-work-preventive-note]"))).toBe("See Preventive");
    const cardLink = within(note).getByRole("link", { name: "View detail →" });
    expect(cardLink).toHaveAttribute("href", preventive);
    const tabs = screen.getByRole("navigation", { name: "Maintenance views" });
    expect(tabs.querySelector("[data-tab-unavailable]")).toBeNull();
    const tab = within(tabs).getByRole("link", { name: "Preventive · scheduled" });
    expect(tab).toHaveAttribute("href", preventive);
    expect(within(tabs).queryByRole("link", { name: "Corrective" })).toBeNull();
    fireEvent.click(tab);
    await waitFor(() => expect(screen.getByTestId("where").textContent).toBe(preventive));
  });

  it("labels an explicit earlier cutoff as historical and forwards it unchanged", async () => {
    const reads = client({ "page-one": loaded(body([row(1)], { status: "HISTORICAL" })) });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&site_id=KOBO-001`, reads);
    await settled();
    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: KNOWN, cursor: null }]);
    // Post-W6 W6 Q14 (R372): seconds on the historical line.
    expect(text(document.querySelector("[data-global-work-status]"))).toBe("Historical as of 21 Oct 2026, 12:00:00 UTC");
    expect(cards()).not.toBeNull();
  });

  it("states a complete zero as zero, with cards", async () => {
    const reads = client({ "page-one": loaded(body([], { state_counts: { OPEN: 0, IN_PROGRESS: 0, COMPLETED: 0, CANCELLED: 0 } })) });
    mount(PAGE, reads);
    await settled();
    expectV69Panels("maintenance");
    expect(text(cards()!.querySelector(".v69-metric__value"))).toBe("0");
    expect(text(cards()!.querySelector(".v69-metric__note"))).toBe("0 requests in progress or open");
    expect(Array.from(document.querySelectorAll("[data-global-work-zero] p")).map(text)).toEqual([
      "No work requests in this window.",
      "Change the UTC window or open a Site record.",
    ]);
    expect(document.querySelector("table")).toBeNull();
  });

  it("states no accessible Sites without cards or a zero (typed EMPTY_SCOPE only)", async () => {
    const reads = client({
      "page-one": loaded(
        body([], {
          status: "EMPTY_SCOPE",
          coverage: { state: "EMPTY_SCOPE", reason: "NO_ACCESSIBLE_SITES", sites: [] },
          state_counts: { OPEN: 0, IN_PROGRESS: 0, COMPLETED: 0, CANCELLED: 0 },
        }),
      ),
    });
    mount(PAGE, reads);
    await settled();
    expectV69Panels("maintenance");
    expect(text(document.querySelector("[data-global-work-empty-scope]"))).toBe("No accessible Sites.");
    expect(cards()).toBeNull();
    expect(document.querySelector("[data-global-work-zero]")).toBeNull();
  });

  it.each([
    ["UNAUTHENTICATED", "Sign in to see work records.", false],
    ["INVALID_WINDOW", "Choose a valid date range of at most 31 days.", false],
    ["INVALID_KNOWN_AT", "Choose a valid cutoff time.", false],
    ["INVALID_LIMIT", "Choose a page size from 1 to 100.", false],
    ["INVALID_CURSOR", "The list changed. Reload the first page.", true],
    ["WORK_BASIS_CHANGED", "The list changed. Reload the first page.", true],
    ["WORK_STORE_UNAVAILABLE", "Work records could not be read. Reload.", false],
  ] as const)("refusal %s states its sentence and never a zero", async (code, sentence, firstPage) => {
    const reads = client({ "page-one": { status: "refused", code }, C9: { status: "refused", code } });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}&cursor=C9`, reads);
    await settled();
    expectV69Panels("maintenance");
    const block = document.querySelector(`[data-global-work-refusal="${code}"]`) as HTMLElement;
    expect(text(block.querySelector("p"))).toBe(sentence);
    expect(cards()).toBeNull();
    expect(document.querySelector("table, [data-global-work-zero], [data-global-work-status]")).toBeNull();
    const link = block.querySelector("[data-global-work-first-page]");
    if (firstPage) expect(link).toHaveAttribute("href", `${PAGE}&known_at=${encodeURIComponent(KNOWN)}`);
    else expect(link).toBeNull();
  });

  it("an invalid page query is refused without a fetch", async () => {
    const reads = client({});
    mount(`/maintenance?from=${encodeURIComponent(FROM)}`, reads);
    await settled();
    expect(reads.calls).toEqual([]);
    expect(document.querySelector('[data-global-work-refusal="INVALID_WINDOW"]')).not.toBeNull();
  });

  it("reads a client without the optional maintenance method as a store refusal, never a throw", async () => {
    const reads: GlobalWorkClient = { incidents: async () => ({ status: "refused", code: "WORK_STORE_UNAVAILABLE" }) };
    mount(PAGE, reads);
    await settled();
    expect(document.querySelector('[data-global-work-refusal="WORK_STORE_UNAVAILABLE"]')).not.toBeNull();
    expect(cards()).toBeNull();
  });
});

describe("W6-01c C2: the request Overview link", () => {
  it("detail_href_after_c2", async () => {
    const detail = `/maintenance/requests/${row(1).case_id}?site_id=KOBO-001&known_at=2026-10-21T12%3A00%3A00.000000Z`;
    const reads = client({
      "page-one": loaded(body([row(1, { links: { ...row(1).links, detail: { label: "WR-000001", href: detail } } }), row(2)])),
    });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}`, reads);
    await settled();
    const [first, second] = Array.from(document.querySelectorAll("[data-global-work-row]"));
    expect(within(first as HTMLElement).getByRole("link", { name: "WR-000001 · Request 1" })).toHaveAttribute("href", detail);
    // A row without a detail link keeps the Site maintenance fallback.
    expect(within(second as HTMLElement).getByRole("link", { name: "WR-000002 · Request 2" })).toHaveAttribute("href", SITE_MAINTENANCE);
  });
});

describe("W6-01b B2: the maintenance client", () => {
  it("reads /api/work/maintenance with limit=5 and accepts only object state counts", async () => {
    const seen: string[] = [];
    const answers: [number, unknown][] = [
      [200, body([row(1)])],
      [200, body([row(1)], { state_counts: null as unknown as GlobalMaintenanceBody["state_counts"] })],
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
    const query = { from: FROM, to: TO, known_at: null, cursor: null };
    expect((await reads.maintenance!(query)).status).toBe("loaded");
    expect(await reads.maintenance!(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    expect(seen[0]).toBe("/api/work/maintenance?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&limit=5");
  });
});

describe("W6-01b B2: the /maintenance route in the app shell", () => {
  it("mounts the page under the operator shell with the rail's Maintenance root current", async () => {
    const reads = client({ "page-one": loaded(body([row(1)])) });
    render(
      <MemoryRouter initialEntries={[PAGE]}>
        <App flags={featureFlagsWith(false)} globalWork={reads} />
      </MemoryRouter>,
    );
    await settled();
    expect(screen.getByRole("main", { name: "Maintenance" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    const link = within(rail).getByRole("link", { name: "Maintenance" });
    expect(link).toHaveAttribute("href", "/maintenance");
    expect(link).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});

describe("Post-W6 W6: global Maintenance corrections", () => {
  afterEach(cleanup);

  it("R352: cold and EV Findings are plain text; a mini-grid Finding keeps its link", async () => {
    const finding = { label: "Finding a1b2c3d4", href: "/sites/X/findings/f1?revision_id=r1" };
    const rows = [
      row(1, { site_domain: "MINIGRID", finding_links: [finding] }),
      row(2, { site_domain: "COLDCHAIN", finding_links: [finding] }),
      row(3, { site_domain: "EV_CHARGING", finding_links: [finding] }),
    ];
    mount(PAGE, client({ "page-one": loaded(body(rows)) }));
    await settled();
    const lineage = Array.from(document.querySelectorAll('[data-global-work-lineage="linked"]'));
    expect(lineage).toHaveLength(3);
    expect(within(lineage[0] as HTMLElement).getByRole("link", { name: "Finding a1b2c3d4" })).toHaveAttribute("href", finding.href);
    for (const cell of lineage.slice(1)) {
      expect(text(cell)).toBe("Finding a1b2c3d4");
      expect(within(cell as HTMLElement).queryByRole("link")).toBeNull();
    }
  });

  it("Q18: one open request is singular; asset labels read as plain words", async () => {
    const rows = [
      row(1, { state: "OPEN", asset_label: "c1 · EV_CONNECTOR" }),
      row(2, { state: "COMPLETED", asset_label: "generator-1 · GENERATOR" }),
    ];
    mount(PAGE, client({ "page-one": loaded(body(rows, { state_counts: { OPEN: 1, IN_PROGRESS: 0, COMPLETED: 1, CANCELLED: 0 } })) }));
    await settled();
    expect(text(document.querySelector('[data-global-work-card="open"]'))).toContain("1 request in progress or open");
    const assets = Array.from(document.querySelectorAll("[data-global-work-asset-site]")).map(text);
    expect(assets[0]).toMatch(/^EV connector c1 · /);
    expect(assets[1]).toMatch(/^Backup generator · generator-1 · /);
    expect(document.body.textContent).not.toMatch(/EV_CONNECTOR|· GENERATOR/);
  });

  it("R354: a later page opened from its URL states its count without a range", async () => {
    mount(`${PAGE}&cursor=CURSOR-2`, client({ "CURSOR-2": loaded(body([row(6)], { total_count: 6 })) }));
    await settled();
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Later page · 1 of 6");
  });

  it("Q7/Q8/Q17: membership line, alert refusal and the R355/R358 labels", async () => {
    mount(PAGE, client({ "page-one": loaded(body([row(1)])) }));
    await settled();
    expect(text(document.querySelector("[data-global-work-membership]"))).toBe("Listed by the time each request was opened.");
    const panel = panelTitled("Corrective work requests");
    expect(text(panel.querySelector('[data-mock-deviation="R355"]'))).toBe("MOCK DEVIATION D1 (R355)");
    expect(text(panel.querySelector('[data-mock-deviation="R358"]'))).toBe("MOCK DEVIATION D1 (R358)");
    cleanup();
    mount(PAGE, client({ "page-one": { status: "refused", code: "UNAUTHENTICATED" } }));
    await settled();
    expect(within(screen.getByRole("main")).getByRole("alert")).toHaveAttribute("data-global-work-refusal", "UNAUTHENTICATED");
  });
});
