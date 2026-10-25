/**
 * W6-01b B3: the global Maintenance root, Preventive view (`.agent/W6-01-build-spec.md` section 2, section 3.1
 * A2Q1-A2Q10/X1-X8/CL3-1 and the "B1-B3 pre-flight rulings" P-B3-1..11). Typed responses only: the persisted DRAFT,
 * corrected historical, zero, 503 and long-PM states are captured against the real API in `.agent/W6-01-evidence/B3/`.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { MAINTENANCE_PREVENTIVE_PATH } from "../../shell/operatorSiteRoutes";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { disclosureNames, stubCellOverflow } from "./cellDisclosureStub";
import { GlobalPreventiveFrame } from "../GlobalPreventive";
import {
  createGlobalWorkClient,
  defaultGlobalWorkWindow,
  type GlobalPreventiveBody,
  type GlobalPreventiveRow,
  type GlobalWorkClient,
  type GlobalWorkQuery,
  type GlobalWorkResult,
} from "../globalWorkClient";

const FROM = "2026-10-14T00:00:00Z";
const TO = "2026-10-21T00:00:00Z";
const KNOWN = "2026-10-20T12:00:03Z";
const PAGE = `/maintenance/preventive?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const CORRECTIVE = `/maintenance?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const TITLE200 = "Quarterlyfilterandbeltinspection".repeat(7).slice(0, 200);

function row(n: number, over: Partial<GlobalPreventiveRow> = {}): GlobalPreventiveRow {
  const id = `00000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`;
  return {
    site_code: "KOBO-001",
    site_name: "Kobo",
    site_id: "00000000-0000-4000-8000-000000000002",
    site_code_key: "kobo-001",
    site_domain: "MINIGRID",
    canonical_plan_id: id,
    root_id: id,
    head_id: id,
    code: `PM-${String(n).padStart(6, "0")}`,
    title: `Plan ${n}`,
    trigger_kind: "CALENDAR",
    next_due_at: "2026-10-29T00:00:00Z",
    next_due_hours: null,
    state: "DRAFT",
    asset_id: null,
    asset_label: null,
    root_occurred_at: "2026-10-18T11:00:00Z",
    occurred_at: "2026-10-18T11:00:00Z",
    recorded_at: "2026-10-20T11:59:00Z",
    supersedes_plan_id: null,
    correction_reason: null,
    source_provenance: {
      classification: "UNKNOWN",
      state: "UNKNOWN",
      source_ids: [],
      evidence_ids: [],
      basis_sha256: `sha256:${"0".repeat(64)}`,
      reasons: [],
    },
    links: { site: { label: "Kobo", href: "/sites/KOBO-001" } },
    ...over,
  };
}

function body(rows: GlobalPreventiveRow[], over: Partial<GlobalPreventiveBody> = {}): GlobalPreventiveBody {
  return {
    schema_version: "global-work-index-1",
    scope: { tenant_id: "00000000-0000-4000-8000-000000000001", authorized_site_count: 2, covered_site_count: 2, access_basis: "sha256:x" },
    window: { from: FROM, to: TO, bounds: "[from, to)" },
    known_at: "2026-10-21T12:00:00Z",
    status: "CURRENT",
    coverage: { state: "COMPLETE", reason: null, sites: [] },
    total_count: rows.length,
    state_counts: null,
    rows,
    next_cursor: null,
    selection_token: "sha256:token",
    ...over,
  };
}

type Answer = GlobalWorkResult<GlobalPreventiveBody>;

function client(answers: Record<string, Answer>, gate?: Promise<void>): GlobalWorkClient & { calls: GlobalWorkQuery[] } {
  const calls: GlobalWorkQuery[] = [];
  return {
    calls,
    async incidents() {
      throw new Error("the Preventive page never reads incidents");
    },
    async preventive(query) {
      calls.push(query);
      if (gate) await gate;
      const answer = answers[query.cursor ?? "page-one"];
      if (answer === undefined) throw new Error(`no answer for ${JSON.stringify(query)}`);
      return answer;
    },
  };
}

const loaded = (value: GlobalPreventiveBody): Answer => ({ status: "loaded", value });

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

function mount(path: string, reads: GlobalWorkClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={MAINTENANCE_PREVENTIVE_PATH} element={<GlobalPreventiveFrame client={reads} />} />
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

describe("W6-01b B3: global Maintenance (Preventive)", () => {
  it("renders the mock header, tabs, strip, cards, plan cells, notice and pager over a typed five-row page", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const rows = [
      row(1, { title: TITLE200 }),
      row(2, { trigger_kind: "RUN_HOURS", next_due_at: null, next_due_hours: "500", title: "Generator 500-hour service" }),
      row(3, {
        head_id: "00000000-0000-4000-8000-000000000999",
        supersedes_plan_id: "00000000-0000-4000-8000-000000000103",
        correction_reason: "Due date corrected after review",
        next_due_at: "2026-11-03T00:00:00Z",
        source_provenance: { ...row(3).source_provenance, classification: "AUTHORED_DEMONSTRATION" },
      }),
      row(4, { next_due_at: null, asset_label: "GEN-001 · generator" }),
      row(5, { site_code: "KOBO-002", site_name: "Kobo 2", links: { site: { label: "Kobo 2", href: "/sites/KOBO-002" } } }),
    ];
    const reads = client(
      {
        "page-one": loaded(body(rows, { total_count: 6, next_cursor: "CURSOR-2" })),
        "CURSOR-2": loaded(body([row(6)], { total_count: 6 })),
      },
      gate,
    );
    mount(PAGE, reads);

    // CL3-1: the loading sentence stands in for the cards and table body; the heading, tabs and controls stay.
    expect(text(document.querySelector("[data-global-work-loading]"))).toBe("Loading the preventive plans across the estate.");
    expect(screen.getByRole("heading", { level: 1, name: "Maintenance" })).toBeInTheDocument();
    expect(document.querySelector("[data-global-work-tabs]")).not.toBeNull();
    expect(cards()).toBeNull();
    release();
    await settled();

    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: null, cursor: null }]);
    expectV69Panels("maintenance-preventive");
    expectPlantedPanelRejected("maintenance-preventive");
    expect(screen.getByRole("main", { name: "Maintenance" })).toBeInTheDocument();

    // P-B3-7/8: breadcrumb, subtitle and the two-tab nav; Corrective is live, Preventive current.
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(Array.from(crumbs.querySelectorAll("li")).map(text)).toEqual(["Maintenance", "Preventive · scheduled"]);
    expect(within(crumbs).getByRole("link", { name: "Maintenance" })).toHaveAttribute("href", CORRECTIVE);
    expect(document.body.textContent).toContain("Scheduled maintenance by calendar or running hours");
    const tabs = screen.getByRole("navigation", { name: "Maintenance views" });
    expect(Array.from(tabs.querySelectorAll("li")).map(text)).toEqual(["Corrective", "Preventive · scheduled"]);
    expect(within(tabs).getByRole("link", { name: "Corrective" })).toHaveAttribute("href", CORRECTIVE);
    expect(tabs.querySelector('[aria-current="page"]')?.textContent).toBe("Preventive · scheduled");
    expect(tabs.querySelector("[data-tab-unavailable]")).toBeNull();

    // P-B3-4: the amber strip between the date bar and the cards; Assets is an unavailable entry, not a link.
    const strip = document.querySelector("[data-global-work-strip]") as HTMLElement;
    expect(strip.className).toContain("status-strip");
    expect(text(strip.querySelector(".status-strip__lead"))).toBe("Due status not assessed");
    expect(text(strip.querySelector(".v69-statusbar__other"))).toBe("Scheduled by calendar or running hours · due dates are plan facts");
    expect(text(strip.querySelector(".status-strip__action"))).toBe("Assets · Not available yet");
    expect(strip.querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "amber");
    expect(strip.querySelector("a, [href]")).toBeNull();
    const bar = document.querySelector("[data-global-work-bar]") as HTMLElement;
    expect(bar.compareDocumentPosition(strip) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(strip.compareDocumentPosition(cards()!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(bar).getByRole("form", { name: "Preventive window" })).toBeInTheDocument();

    // P-B3-3: the four mock card headings; Scheduled items is the full selected count.
    expect(
      Array.from(cards()!.querySelectorAll("li.v69-metric")).map((li) => [
        text(li.querySelector(".v69-metric__label")),
        text(li.querySelector(".v69-metric__value")),
        text(li.querySelector(".v69-metric__note")),
      ]),
    ).toEqual([
      ["Scheduled items", "6", "Across 2 sites"],
      ["Overdue", "Not assessed", "No due evaluator"],
      ["Due in 14 days", "Not assessed", "No due evaluator"],
      ["Feeds evidence", "Not established", "No accepted-evidence link"],
    ]);
    const overdue = cards()!.querySelector('[data-global-work-card="overdue"]') as HTMLElement;
    expect(overdue.className).toContain("v69-metric--assessment");
    expect(overdue.className).toContain("v69-metric--amber");
    expect(document.body.textContent).not.toMatch(/PM-0455|PM-0452|INC-203|GreenHarvest|GEN-CR-01|Monthly|\bQuarterly\b|2 overdue/);

    // P-B3-5/6: footer, columns and cells.
    const panel = panelTitled("Preventive plan");
    expect(text(panel.querySelector(".panel__description"))).toBe(
      "Completing a draft plan here is unavailable; a performed record and later evidence are separate.",
    );
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Plan item",
      "Asset / site",
      "Trigger",
      "Last done",
      "Next due",
      "State",
      "What it proves",
    ]);
    const trs = Array.from(panel.querySelectorAll("tbody tr"));
    expect(trs).toHaveLength(5);
    expect(text(cell(trs[0], 0).querySelector("[data-global-work-title]"))).toBe(`PM-000001 · ${TITLE200}`);
    expect(cell(trs[0], 0).querySelector("[data-global-work-title] a")).toBeNull();
    expect(text(cell(trs[0], 0).querySelector("[data-global-work-full-title]"))).toBe(`Full title text${TITLE200}`);
    expect(text(cell(trs[0], 0).querySelector("[data-global-work-source] summary"))).toBe("Source unverified");
    expect(cell(trs[0], 0).querySelector("[data-global-work-correction]")).toBeNull();
    expect(text(cell(trs[0], 1))).toBe("No asset recorded · Kobo");
    expect(within(cell(trs[0], 1)).getByRole("link", { name: "Kobo" })).toHaveAttribute("href", "/sites/KOBO-001");
    expect([2, 3, 4, 5, 6].map((i) => text(cell(trs[0], i)))).toEqual([
      "Calendar",
      "Not linked",
      "29 Oct 2026",
      "Draft",
      "Nothing verified by this plan",
    ]);
    expect(cell(trs[0], 5).querySelector("[data-global-work-tone]")).toHaveAttribute("data-global-work-tone", "neutral");
    expect(text(cell(trs[1], 2))).toBe("Every 500 running hours");
    expect(text(cell(trs[1], 4))).toBe("500 running hours");
    expect(text(cell(trs[2], 0).querySelector("[data-global-work-correction]"))).toBe("Correction: Due date corrected after review");
    const supersedes = cell(trs[2], 0).querySelector("[data-global-work-supersedes]") as HTMLDetailsElement;
    expect(supersedes.tagName).toBe("DETAILS");
    expect(text(supersedes)).toBe("Earlier plan version00000000-0000-4000-8000-000000000103");
    expect(text(cell(trs[2], 0).querySelector("[data-global-work-source] summary"))).toBe("Prepared example data");
    expect(text(cell(trs[3], 4))).toBe("Not set");
    expect(text(cell(trs[3], 1))).toBe("GEN-001 · generator · Kobo");
    expect(cell(trs[3], 1).querySelectorAll("a")).toHaveLength(1);

    const notice = document.querySelector("[data-global-work-notice]") as HTMLElement;
    expect(notice.className).toContain("v69-notice--blue");
    expect(text(notice)).toBe("No incident link or cause is established by these draft plans.");
    expect(panel.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    // Pager (A2Q10) keeps the full selected count.
    expect(screen.getByRole("navigation", { name: "Preventive pages" })).toBeInTheDocument();
    expect(text(panel.querySelector("[data-global-work-showing]"))).toBe("Showing 1–5 of 6");
    fireEvent.click(panel.querySelector("[data-global-work-next]") as HTMLElement);
    await settled();
    expect(reads.calls[1]).toEqual({ from: FROM, to: TO, known_at: null, cursor: "CURSOR-2" });
    expect(screen.getByTestId("where").textContent).toBe(`${PAGE}&cursor=CURSOR-2`);
    expect(text(panelTitled("Preventive plan").querySelector("[data-global-work-showing]"))).toBe("Showing 6–6 of 6");
    // The Corrective tab never carries the cursor.
    expect(within(screen.getByRole("navigation", { name: "Maintenance views" })).getByRole("link", { name: "Corrective" })).toHaveAttribute(
      "href",
      CORRECTIVE,
    );
  });

  it("labels an explicit earlier cutoff as historical and carries it on the Corrective tab", async () => {
    const reads = client({ "page-one": loaded(body([row(1)], { status: "HISTORICAL", known_at: KNOWN })) });
    mount(`${PAGE}&known_at=${encodeURIComponent(KNOWN)}`, reads);
    await settled();
    expect(reads.calls).toEqual([{ from: FROM, to: TO, known_at: KNOWN, cursor: null }]);
    // Post-W6 W6 Q14 (R372): seconds on the historical line.
    expect(text(document.querySelector("[data-global-work-status]"))).toBe("Historical as of 20 Oct 2026, 12:00:03 UTC");
    expect(within(screen.getByRole("navigation", { name: "Maintenance views" })).getByRole("link", { name: "Corrective" })).toHaveAttribute(
      "href",
      `${CORRECTIVE}&known_at=${encodeURIComponent(KNOWN)}`,
    );
  });

  it("uses the seven-day default window on the Corrective tab when the URL has none", async () => {
    const reads = client({ "page-one": loaded(body([row(1)])) });
    mount("/maintenance/preventive", reads);
    await settled();
    const window = defaultGlobalWorkWindow();
    expect(reads.calls[0]).toEqual({ ...window, known_at: null, cursor: null });
    expect(within(screen.getByRole("navigation", { name: "Maintenance views" })).getByRole("link", { name: "Corrective" })).toHaveAttribute(
      "href",
      `/maintenance?from=${encodeURIComponent(window.from)}&to=${encodeURIComponent(window.to)}`,
    );
  });

  it("states a complete zero as zero, with cards", async () => {
    const reads = client({ "page-one": loaded(body([])) });
    mount(PAGE, reads);
    await settled();
    expectV69Panels("maintenance-preventive");
    expect(text(cards()!.querySelector(".v69-metric__value"))).toBe("0");
    expect(Array.from(document.querySelectorAll("[data-global-work-zero] p")).map(text)).toEqual([
      "No draft plans in this window.",
      "Change the UTC window or open a Site record.",
    ]);
    expect(document.querySelector("table")).toBeNull();
  });

  it.each([
    ["UNAUTHENTICATED", "Sign in to see work records.", false],
    ["INVALID_CURSOR", "The list changed. Reload the first page.", true],
    ["WORK_BASIS_CHANGED", "The list changed. Reload the first page.", true],
    ["WORK_STORE_UNAVAILABLE", "Work records could not be read. Reload.", false],
  ] as const)("refusal %s states its sentence and never a zero", async (code, sentence, firstPage) => {
    const reads = client({ "page-one": { status: "refused", code }, C9: { status: "refused", code } });
    mount(`${PAGE}&cursor=C9`, reads);
    await settled();
    expectV69Panels("maintenance-preventive");
    const block = document.querySelector(`[data-global-work-refusal="${code}"]`) as HTMLElement;
    expect(text(block.querySelector("p"))).toBe(sentence);
    expect(cards()).toBeNull();
    expect(document.querySelector("table, [data-global-work-zero], [data-global-work-status]")).toBeNull();
    const link = block.querySelector("[data-global-work-first-page]");
    if (firstPage) expect(link).toHaveAttribute("href", PAGE);
    else expect(link).toBeNull();
  });

  it("states no accessible Sites without cards (typed EMPTY_SCOPE only)", async () => {
    const reads = client({
      "page-one": loaded(body([], { status: "EMPTY_SCOPE", coverage: { state: "EMPTY_SCOPE", reason: "NO_ACCESSIBLE_SITES", sites: [] } })),
    });
    mount(PAGE, reads);
    await settled();
    expectV69Panels("maintenance-preventive");
    expect(text(document.querySelector("[data-global-work-empty-scope]"))).toBe("No accessible Sites.");
    expect(cards()).toBeNull();
  });

  it("reads a client without the optional preventive method as a store refusal, never a throw", async () => {
    const reads: GlobalWorkClient = { incidents: async () => ({ status: "refused", code: "WORK_STORE_UNAVAILABLE" }) };
    mount(PAGE, reads);
    await settled();
    expect(document.querySelector('[data-global-work-refusal="WORK_STORE_UNAVAILABLE"]')).not.toBeNull();
  });
});

describe("W6-01b B3: the preventive client", () => {
  it("reads /api/work/preventive with limit=5 and accepts only null state counts (P-B3-1)", async () => {
    const seen: string[] = [];
    const answers: unknown[] = [body([row(1)]), { ...body([row(1)]), state_counts: { OPEN: 1 } }];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        seen.push(url);
        return new Response(JSON.stringify(answers.shift() ?? null), { status: 200 });
      }),
    );
    const reads = createGlobalWorkClient();
    const query = { from: FROM, to: TO, known_at: null, cursor: null };
    expect((await reads.preventive!(query)).status).toBe("loaded");
    expect(await reads.preventive!(query)).toEqual({ status: "refused", code: "WORK_STORE_UNAVAILABLE" });
    expect(seen[0]).toBe("/api/work/preventive?from=2026-10-14T00%3A00%3A00Z&to=2026-10-21T00%3A00%3A00Z&limit=5");
  });
});

describe("W6-01b B3: the /maintenance/preventive route in the app shell", () => {
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
    expect(within(rail).getByRole("link", { name: "Maintenance" })).toHaveAttribute("aria-current", "page");
    expect(reads.calls).toHaveLength(1);
  });
});

describe("Post-W6 W6: global Preventive corrections", () => {
  afterEach(cleanup);

  it("M1: Next from a URL-opened later page still states no numeric range (the offset stays unknown)", async () => {
    mount(
      `${PAGE}&cursor=CURSOR-2`,
      client({
        "CURSOR-2": loaded(body([row(6)], { total_count: 12, next_cursor: "CURSOR-3" })),
        "CURSOR-3": loaded(body([row(7)], { total_count: 12 })),
      }),
    );
    await settled();
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Later page · 1 of 12");
    fireEvent.click(document.querySelector("[data-global-work-next]") as HTMLElement);
    await settled();
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Later page · 1 of 12");
    expect(document.querySelector("[data-global-work-showing]")?.textContent).not.toMatch(/\d+–\d+/);
  });

  it("Q7/R354/R361: membership line, URL-opened later page caption and the refusal alert", async () => {
    mount(`${PAGE}&cursor=CURSOR-2`, client({ "CURSOR-2": loaded(body([row(6)], { total_count: 6 })) }));
    await settled();
    expect(text(document.querySelector("[data-global-work-membership]"))).toBe("Listed by the time each plan was first recorded.");
    expect(text(document.querySelector("[data-global-work-showing]"))).toBe("Later page · 1 of 6");
    cleanup();
    mount(PAGE, client({ "page-one": { status: "refused", code: "WORK_STORE_UNAVAILABLE" } }));
    await settled();
    expect(within(screen.getByRole("main")).getByRole("alert")).toHaveAttribute("data-global-work-refusal", "WORK_STORE_UNAVAILABLE");
  });
});

describe("Post-W6 W6 caps ruling 4: in-cell disclosure on Preventive plan", () => {
  it("gives each listed clamped cell a Show full button only when its value overflows the two-line preview", async () => {
    const restore = stubCellOverflow(0);
    try {
      mount(PAGE, client({ "page-one": loaded(body([row(1)])) }));
      await settled();
      const tr = panelTitled("Preventive plan").querySelector("tbody tr") as HTMLElement;
      expect(disclosureNames(tr)).toEqual([
      "Show full Asset / site for PM-000001",
      "Show full Trigger for PM-000001",
      "Show full Last done for PM-000001",
      "Show full Next due for PM-000001",
      "Show full What it proves for PM-000001",
      ]);
      for (const button of Array.from(tr.querySelectorAll("button[data-cell-disclosure-toggle]"))) {
        expect(button.textContent).toBe("Show full");
        expect(button.closest("a")).toBeNull();
      }
      const first = tr.querySelector("button[data-cell-disclosure-toggle]") as HTMLButtonElement;
      fireEvent.click(first);
      expect(first.textContent).toBe("Show less");
      expect(first.getAttribute("aria-label")).toBe("Show less Asset / site for PM-000001");
    } finally {
      restore();
    }
  });

  it("gives a correction line in the first column its own Show full disclosure", async () => {
    const restore = stubCellOverflow(0);
    try {
      mount(PAGE, client({ "page-one": loaded(body([row(1, { correction_reason: "Corrected after review" })])) }));
      await settled();
      const tr = document.querySelector("tbody tr") as HTMLElement;
      expect(disclosureNames(tr)).toContain("Show full Plan item correction for PM-000001");
      const correction = tr.querySelector("[data-global-work-correction]") as HTMLElement;
      expect(correction.className).toContain("cell-disclosure__value");
      expect(correction.textContent).toBe("Correction: Corrected after review");
    } finally {
      restore();
    }
  });

  it("shows values that fit plainly, with no disclosure buttons", async () => {
    const restore = stubCellOverflow(100000);
    try {
      mount(PAGE, client({ "page-one": loaded(body([row(1)])) }));
      await settled();
      const tr = panelTitled("Preventive plan").querySelector("tbody tr") as HTMLElement;
      expect(tr.querySelectorAll("[data-cell-disclosure]")).toHaveLength(5);
      expect(disclosureNames(tr)).toEqual([]);
    } finally {
      restore();
    }
  });
});
