/**
 * IA-P P2 (spec §5.2, §6 "P2"): the three live lists on fixture bodies. Each figure is a literal.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import { createEstateClient, invalidWindowCopy, type EstateClient, type EstatePortfolioBody, type EstatePortfolioRow, type EstateResult } from "../estateClient";
import { actionsDef, decisionStateKey, DecisionsListPage, ActionsListPage, FindingsListPage, decisionsDef } from "../homeLists";
import { actionRow, actionsBody, findingRow, findingsBody, loaded } from "./estateFixtures";
import { portfolioBody, row } from "./portfolioFixtures";
import { homeListModel } from "../../ui/homeListModel";

beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

const RANGE = "from=2026-10-13T00:00:00Z&to=2026-10-20T00:00:00Z";

function id(n: number): string {
  return `f1f1f1f1-0000-4000-8000-${String(n).padStart(12, "0")}`;
}

/** n placed Findings: the 1st is Monitor (watching), the 2nd has an Action (underway), the rest wait. */
function decisionRows(n: number, over: (i: number) => Partial<EstatePortfolioRow> = () => ({})): EstatePortfolioRow[] {
  return Array.from({ length: n }, (_, k) => {
    const i = k + 1;
    const base: Partial<EstatePortfolioRow> = {
      finding_id: id(i),
      finding_revision_id: id(1000 + i),
      title: `Decision ${i}`,
      site_name: i % 2 === 0 ? "Kobo" : "Aliyu",
      lens_flags: i % 3 === 0 ? ["RISK"] : ["COST"],
      links: { site: "/sites/KOBO-001", finding: `/sites/KOBO-001/findings/${id(i)}?revision_id=${id(1000 + i)}`, action: null },
    };
    if (i === 1) base.placement = { policy_version: "estate-placement/1", group: "MONITOR", group_rank: 5, reasons: [] };
    if (i === 2) base.action_id = "a2a2a2a2-0000-4000-8000-000000000002";
    return row({ ...base, ...over(i) });
  });
}

function portfolioPages(rows: EstatePortfolioRow[], over: Partial<EstatePortfolioBody> = {}, size = 50): EstateResult<EstatePortfolioBody>[] {
  const pages: EstateResult<EstatePortfolioBody>[] = [];
  for (let at = 0; at < Math.max(rows.length, 1); at += size) {
    const last = at + size >= rows.length;
    pages.push(
      loaded(
        portfolioBody({
          ...over,
          rows: rows.slice(at, at + size),
          total_count: rows.length,
          next_cursor: last ? null : `c${at + size}`,
        }),
      ),
    );
  }
  return pages;
}

function client(rows: EstatePortfolioRow[], over: Partial<EstatePortfolioBody> = {}, size = 50): EstateClient & { calls: { cursor: string | null }[] } {
  const pages = portfolioPages(rows, over, size);
  const calls: { cursor: string | null }[] = [];
  return {
    calls,
    findings: async () => loaded(findingsBody("all")),
    actions: async () => loaded(actionsBody()),
    scope: async () => Promise.reject(new Error("no scope")),
    portfolio: async (query) => {
      calls.push({ cursor: query.cursor });
      const at = query.cursor === null ? 0 : Number(query.cursor.slice(1)) / size;
      return pages[at];
    },
  };
}

function Search() {
  const { search } = useLocation();
  return <output data-testid="search">{search}</output>;
}

function mount(ui: JSX.Element, at: string, path = "/decisions") {
  return render(
    <MemoryRouter initialEntries={[at]}>
      <Routes>
        <Route path={path} element={ui} />
      </Routes>
      <Search />
    </MemoryRouter>,
  );
}

const rowsOf = () => Array.from(document.querySelectorAll("tbody tr[data-row]"));

describe("decisionStateKey (D-IAP.29)", () => {
  it("an Action makes it underway; MONITOR with none is watching; the rest wait", () => {
    const r = decisionRows(3);
    expect(r.map(decisionStateKey)).toEqual(["watching", "underway", "waiting"]);
  });
  it("NEEDS_INVESTIGATION stays waiting", () => {
    const r = row({ placement: { policy_version: "x", group: "NEEDS_INVESTIGATION", group_rank: 1, reasons: [] } });
    expect(decisionStateKey(r)).toBe("waiting");
  });
});

describe("Decisions list on 25 placed Findings", () => {
  it("tile 1 = shown + hidden = Show all n; the waiting tile counts the waiting rows", async () => {
    mount(<DecisionsListPage client={client(decisionRows(25))} />, `/decisions?${RANGE}`);
    await settledScreen();
    expect(rowsOf()).toHaveLength(10);
    const tile1 = document.querySelector('[data-tile="total"] strong')!;
    expect(tile1.textContent).toBe("25");
    expect(screen.getByRole("link", { name: "Show all 25" })).toBeTruthy();
    // 25 rows: 1 watching, 1 underway, 23 waiting.
    expect(screen.getByText("Waiting for a choice", { selector: ".hl-tile__label" }).parentElement!.textContent).toContain("23");
  });

  it("the waiting tile equals E0 waiting_count when the body carries it", async () => {
    const body = decisionRows(25);
    mount(<DecisionsListPage client={client(body, { summary: { ...portfolioBody().summary, waiting_count: 23 } })} />, `/decisions?${RANGE}`);
    await settledScreen();
    const waiting = screen.getByText("Waiting for a choice", { selector: ".hl-tile__label" }).parentElement!;
    expect(Number(waiting.querySelector("strong")!.textContent)).toBe(23);
  });

  it("M1: under a State facet the parts are counted from the filtered rows and never exceed tile 1", async () => {
    mount(<DecisionsListPage client={client(decisionRows(25), { summary: { ...portfolioBody().summary, waiting_count: 23 } })} />, `/decisions?${RANGE}&state=watching`);
    await settledScreen();
    expect(document.querySelector('[data-tile="total"] strong')!.textContent).toBe("1");
    const waiting = screen.getByText("Waiting for a choice", { selector: ".hl-tile__label" }).parentElement!;
    expect(waiting.querySelector("strong")!.textContent).toBe("0");
  });

  it("tier 2 draws the facets, Sort and Search; the form is labelled", async () => {
    mount(<DecisionsListPage client={client(decisionRows(25))} />, `/decisions?${RANGE}`);
    await settledScreen();
    const form = screen.getByRole("search", { name: "Filter and sort decisions" });
    expect(within(form).getByLabelText("State")).toBeTruthy();
    expect(within(form).getByLabelText("Finding type")).toBeTruthy();
    expect(within(form).getByLabelText("Sort")).toBeTruthy();
    expect(within(form).getByLabelText("Search")).toBeTruthy();
  });

  it("tier 1 (3 to 10 rows) draws Sort only; tier 0 (2 rows) draws no tools", async () => {
    mount(<DecisionsListPage client={client(decisionRows(5))} />, `/decisions?${RANGE}`);
    await settledScreen();
    const form = screen.getByRole("search", { name: "Sort decisions" });
    expect(within(form).queryByLabelText("Search")).toBeNull();
    expect(within(form).queryByLabelText("State")).toBeNull();
    cleanup();
    mount(<DecisionsListPage client={client(decisionRows(2))} />, `/decisions?${RANGE}`);
    await settledScreen();
    expect(screen.queryByRole("search")).toBeNull();
  });

  it("one interactive element per row, and it is the title link", async () => {
    mount(<DecisionsListPage client={client(decisionRows(10))} />, `/decisions?${RANGE}`);
    await settledScreen();
    for (const tr of rowsOf()) {
      const interactive = tr.querySelectorAll("a, button, input, select, textarea, [tabindex]");
      expect(interactive).toHaveLength(1);
      expect(interactive[0].closest("th")).not.toBeNull();
    }
  });

  it("a row without a ref is shown as text with the words, and counted", async () => {
    const rows = decisionRows(5, (i) => (i === 3 ? { links: { site: null, finding: null, action: null }, link_refs: {} } : {}));
    mount(<DecisionsListPage client={client(rows)} />, `/decisions?${RANGE}`);
    await settledScreen();
    expect(rowsOf()).toHaveLength(5);
    const tr = document.querySelector(`tr[data-row="${id(3)}"]`)!;
    expect(tr.querySelector("a")).toBeNull();
    expect(tr.textContent).toContain("Detail not available yet");
    expect(document.querySelector('[data-tile="total"] strong')!.textContent).toBe("5");
  });

  it("a mini-grid FINDING row opens the recommendation view (I8)", async () => {
    mount(<DecisionsListPage client={client(decisionRows(3))} />, `/decisions?${RANGE}`);
    await settledScreen();
    const href = document.querySelector(`tr[data-row="${id(3)}"] a`)!.getAttribute("href")!;
    expect(href).toContain(`/sites/KOBO-001/findings/${id(3)}/recommendation`);
  });

  it("Due and Who decides say Not available yet", async () => {
    mount(<DecisionsListPage client={client(decisionRows(3))} />, `/decisions?${RANGE}`);
    await settledScreen();
    const tr = document.querySelector(`tr[data-row="${id(3)}"]`)!;
    expect(tr.querySelector('[data-label="Due"]')!.textContent).toBe("Not available yet");
    expect(tr.querySelector('[data-label="Who decides"]')!.textContent).toBe("Not available yet");
    expect(tr.querySelector('[data-label="State"]')!.textContent).toBe("Waiting for a choice");
  });
});

describe("each control's value is the address; a fresh mount at the address is the in-page result", () => {
  it("the controls read the address", async () => {
    mount(<DecisionsListPage client={client(decisionRows(25))} />, `/decisions?${RANGE}&state=waiting&sort=site&q=decision`);
    await settledScreen();
    expect((screen.getByLabelText("State") as HTMLSelectElement).value).toBe("waiting");
    expect((screen.getByLabelText("Sort") as HTMLSelectElement).value).toBe("site");
    expect((screen.getByLabelText("Search") as HTMLInputElement).value).toBe("decision");
  });

  it("a change writes the canonical address and the same list is drawn on a fresh mount", async () => {
    const c = client(decisionRows(25));
    mount(<DecisionsListPage client={c} />, `/decisions?${RANGE}&sort=site`);
    await settledScreen();
    fireEvent.change(screen.getByLabelText("State"), { target: { value: "waiting" } });
    await settledScreen();
    const search = screen.getByTestId("search").textContent!;
    expect(search).toBe(`?from=2026-10-13T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z&state=waiting&sort=site`);
    const inPage = rowsOf().map((r) => r.getAttribute("data-row"));
    cleanup();
    mount(<DecisionsListPage client={c} />, `/decisions${search}`);
    await settledScreen();
    expect(rowsOf().map((r) => r.getAttribute("data-row"))).toEqual(inPage);
    expect(inPage).toHaveLength(10);
  });

  it("the sort in the address is applied on the first render (Site order)", async () => {
    mount(<DecisionsListPage client={client(decisionRows(25))} />, `/decisions?${RANGE}&sort=site&show=all`);
    await settledScreen();
    const sites = rowsOf().map((r) => r.querySelector('[data-label="Site"]')!.textContent);
    expect(sites.slice(0, 13).every((s) => s === "Aliyu")).toBe(true);
    expect(sites.slice(13).every((s) => s === "Kobo")).toBe(true);
  });

  it("a set facet whose select is not drawn is a chip with its way out, and Clear filters at two", async () => {
    mount(<DecisionsListPage client={client(decisionRows(5))} />, `/decisions?${RANGE}&state=waiting&lens=cost`);
    await settledScreen();
    const chips = screen.getByLabelText("In this view");
    expect(chips.textContent).toContain("Waiting for a choice · All states");
    expect(chips.textContent).toContain("Cost · All findings");
    expect(within(chips).getByRole("link", { name: "Clear filters" })).toBeTruthy();
  });

  it("filters that leave nothing say so and keep the tools", async () => {
    mount(<DecisionsListPage client={client(decisionRows(25))} />, `/decisions?${RANGE}&q=zzz`);
    await settledScreen();
    expect(screen.getByText(/Nothing matches these filters\./)).toBeTruthy();
    expect(screen.getByRole("search", { name: "Filter and sort decisions" })).toBeTruthy();
  });

  it("an empty store says the def's words", async () => {
    mount(<DecisionsListPage client={client([])} />, `/decisions?${RANGE}`);
    await settledScreen();
    expect(screen.getByText("No decisions in this range.")).toBeTruthy();
  });
});

describe("every page is read, and a later refusal restarts once (I9)", () => {
  it("reads 3 pages of 50 for 120 rows", async () => {
    const c = client(decisionRows(120), {}, 50);
    mount(<DecisionsListPage client={c} />, `/decisions?${RANGE}&show=all`);
    await settledScreen();
    expect(c.calls.map((x) => x.cursor)).toEqual([null, "c50", "c100"]);
    expect(rowsOf()).toHaveLength(120);
  });

  it("a later page refused with ESTATE_BASIS_CHANGED restarts from page one once; a second refusal is shown", async () => {
    const rows = decisionRows(120);
    const base = client(rows, {}, 50);
    let refusals = 0;
    const flaky: EstateClient = {
      ...base,
      portfolio: async (q) => {
        if (q.cursor === "c50") {
          refusals += 1;
          return { status: "refused", httpStatus: 409, code: "ESTATE_BASIS_CHANGED", copy: "The list changed. Reload the first page." };
        }
        return base.portfolio(q);
      },
    };
    mount(<DecisionsListPage client={flaky} />, `/decisions?${RANGE}`);
    await settledScreen();
    expect(refusals).toBe(2);
    expect(screen.getByText("The list changed. Reload the first page.")).toBeTruthy();
  });
});

describe("Findings list", () => {
  it("joins its decision on finding_id and says No decision open otherwise", async () => {
    const f1 = findingRow(1, { finding_id: id(3), title: "Has a decision" });
    const f2 = findingRow(2, { finding_id: id(99), title: "Has none" });
    const c: EstateClient = {
      ...client(decisionRows(3)),
      findings: async () => loaded(findingsBody("all", { rows: [f1, f2], total_count: 2 })),
    };
    mount(<FindingsListPage client={c} />, `/findings?${RANGE}`, "/findings");
    await settledScreen();
    expect(document.querySelector(`tr[data-row="${id(3)}"] [data-label="Its decision"]`)!.textContent).toBe("Waiting for a choice");
    expect(document.querySelector(`tr[data-row="${id(99)}"] [data-label="Its decision"]`)!.textContent).toBe("No decision open");
    expect(screen.getByText("Decision waiting for a choice", { selector: ".hl-tile__label" }).parentElement!.textContent).toContain("1");
  });
});

describe("Findings list at scope=site:{id} (D-IAP.47: where the COLD and EV Site Findings alias lands)", () => {
  const COLD = "COLD-LAB-001";
  const rows = [
    findingRow(1, { finding_id: id(11), title: "Chamber above policy", site_code: COLD }),
    findingRow(2, { finding_id: id(12), title: "Other Site finding", site_code: "KOBO-001" }),
  ];
  const c: EstateClient = { ...client(decisionRows(1)), findings: async () => loaded(findingsBody("all", { rows, total_count: 2 })) };

  it("keeps only that Site's Findings and reads the range from the address", async () => {
    mount(<FindingsListPage client={c} />, `/findings?${RANGE}&scope=site:${COLD}`, "/findings");
    await settledScreen();
    expect(rowsOf().map((r) => r.getAttribute("data-row"))).toEqual([id(11)]);
  });

  it("says the def's words when the Site has no Finding in the range (the old index's empty state)", async () => {
    mount(<FindingsListPage client={c} />, `/findings?${RANGE}&scope=site:NONE-001`, "/findings");
    await settledScreen();
    expect(rowsOf()).toEqual([]);
    expect(document.body.textContent).toMatch(/No Findings in this (range|scope)|Nothing matches/);
  });
});

describe("Findings list, Its decision while the Decisions read is not loaded (M2)", () => {
  const f1 = findingRow(1, { finding_id: id(3), title: "Has a decision" });
  const findings = async () => loaded(findingsBody("all", { rows: [f1], total_count: 1 }));
  const decisionCell = () => document.querySelector(`tr[data-row="${id(3)}"] [data-label="Its decision"]`)!.textContent;
  const tile = () => screen.getByText("Decision waiting for a choice", { selector: ".hl-tile__label" }).parentElement!.textContent;

  it("a refused Decisions read says Not available yet, never No decision open or 0", async () => {
    const c: EstateClient = { ...client([]), findings, portfolio: async () => ({ status: "refused", httpStatus: 503, code: "UNAVAILABLE", copy: "no" }) };
    mount(<FindingsListPage client={c} />, `/findings?${RANGE}`, "/findings");
    await settledScreen();
    expect(decisionCell()).toBe("Not available yet");
    expect(tile()).toContain("Not available yet");
    expect(tile()).not.toMatch(/\b0\b/);
  });

  it("while the Decisions read is in flight it says Loading, never No decision open or 0", async () => {
    const c: EstateClient = { ...client([]), findings, portfolio: () => new Promise(() => {}) };
    mount(<FindingsListPage client={c} />, `/findings?${RANGE}`, "/findings");
    await settledScreen();
    expect(decisionCell()).toBe("Loading…");
    expect(tile()).toContain("Loading…");
  });
});

describe("Actions list", () => {
  it("keeps the four server figures as a caption line and one tile per state present", async () => {
    const rows = [actionRow({ action_id: "a1", application_state: "PENDING" }), actionRow({ action_id: "a2", application_state: "APPLIED", owner: "Ada", due_at: "2026-10-30T00:00:00Z" })];
    const c: EstateClient = { ...client([]), actions: async () => loaded(actionsBody({ rows, total_count: 2 })) };
    mount(<ActionsListPage client={c} />, `/actions?${RANGE}`, "/actions");
    await settledScreen();
    expect(document.querySelector(".hl-caption")!.textContent).toMatch(/Open actions .* · Due \/ overdue .* · Verification window .* · Verified in 30 days /);
    const labels = Array.from(document.querySelectorAll(".hl-tile__label")).map((e) => e.textContent);
    expect(labels).toEqual(["Actions", "Pending", "Applied"]);
    expect(document.querySelector('tr[data-row="a1"] [data-label="Owner"]')!.textContent).toBe("Not recorded");
    expect(document.querySelector('tr[data-row="a1"] [data-label="Due"]')!.textContent).toBe("No deadline");
  });

  it("M1: the state parts sum to tile 1 under a facet", async () => {
    const rows = [actionRow({ action_id: "a1", application_state: "PENDING" }), actionRow({ action_id: "a2", application_state: "APPLIED" }), actionRow({ action_id: "a3", application_state: "APPLIED" })];
    const c: EstateClient = { ...client([]), actions: async () => loaded(actionsBody({ rows, total_count: 3 })) };
    mount(<ActionsListPage client={c} />, `/actions?${RANGE}&state=APPLIED`, "/actions");
    await settledScreen();
    const tiles = Array.from(document.querySelectorAll(".hl-tile")).map((t) => [t.querySelector(".hl-tile__label")!.textContent, t.querySelector("strong")!.textContent]);
    expect(tiles).toEqual([["Actions", "2"], ["Applied", "2"]]);
  });

  it("the Due sort puts no date last, in ISO order", () => {
    const def = actionsDef();
    const rows = [actionRow({ action_id: "x", due_at: null }), actionRow({ action_id: "y", due_at: "2026-11-02T00:00:00Z" }), actionRow({ action_id: "z", due_at: "2026-10-30T00:00:00Z" })];
    expect(homeListModel(def, rows, { sort: "due" }).rows.map((r) => r.action_id)).toEqual(["z", "y", "x"]);
  });
});

describe("the defs", () => {
  it("the Decisions facets are State and Finding type with the spec's words", () => {
    const def = decisionsDef();
    expect(def.facets.map((f) => [f.key, f.label, f.all])).toEqual([
      ["state", "State", "All states"],
      ["lens", "Finding type", "All findings"],
    ]);
    expect(def.facets[0].options.map((o) => o.word)).toEqual(["Waiting for a choice", "Being watched", "Under way"]);
    expect(def.facets[1].options.map((o) => o.word)).toEqual(["Cost", "Risks", "Opportunities"]);
  });
});

// Re-homed from the retired estateRoots tests (IA-P P2): the refused-window sentences and the Action title rule.
describe("refused window and Action titles on the lists", () => {
  const WIN = "from=2026-10-13T00%3A00%3A00Z&to=2026-10-20T00%3A00%3A00Z";
  const cases: [string, string][] = [
    ["from=2026-10-07T00:00:00Z&to=2026-10-05T00:00:00Z", "The selected window needs both a start and an end, with the start before the end."],
    ["from=2024-08-01T00:00:00Z&to=2026-10-01T00:00:00Z", "The selected window is longer than 31 days."],
    [WIN, "The selected window is invalid."],
  ];
  const refusedRead = { status: "refused" as const, httpStatus: 422, code: "INVALID_WINDOW", copy: "server copy" };
  const refusing: EstateClient = {
    findings: async () => refusedRead,
    actions: async () => refusedRead,
    portfolio: async () => refusedRead,
    scope: async () => refusedRead,
  };

  it("each list says the shared sentence for the window it was asked, and never echoes the dates", async () => {
    const pages: [JSX.Element, string][] = [
      [<DecisionsListPage client={refusing} />, "/decisions"],
      [<FindingsListPage client={refusing} />, "/findings"],
      [<ActionsListPage client={refusing} />, "/actions"],
    ];
    for (const [ui, path] of pages) {
      for (const [query, copy] of cases) {
        const view = mount(ui, `${path}?${query}`, path);
        await settledScreen();
        expect(document.querySelector("[data-page-refusal='INVALID_WINDOW'] p")?.textContent).toBe(copy);
        expect(document.querySelector("[data-estate-window]")?.textContent).toBe("Window not valid");
        view.unmount();
      }
    }
  });

  it("the real client classifies the same way, and a store refusal keeps its own copy", async () => {
    const body = JSON.stringify({ detail: { code: "INVALID_WINDOW", message: "x" } });
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(body, { status: 422 }))));
    const read = await createEstateClient().findings({ from: "2026-10-07T00:00:00Z", to: "2026-10-05T00:00:00Z", known_at: null, cursor: null, lens: "all", state: "all" });
    expect(read).toEqual({ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", copy: "The selected window needs both a start and an end, with the start before the end." });
    vi.unstubAllGlobals();
    expect(invalidWindowCopy({ from: "2026-10-01T00:00:00Z", to: null })).toBe("The selected window needs both a start and an end, with the start before the end.");
    expect(invalidWindowCopy({ from: "2026-10-01T00:00:00Z", to: "2026-11-01T00:00:00Z" })).toBe("The selected window is invalid.");
    expect(invalidWindowCopy({ from: "2026-10-01T00:00:00Z", to: "2026-11-01T00:00:01Z" })).toBe("The selected window is longer than 31 days.");
    const store = { status: "refused" as const, httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "Estate records are unavailable right now. Try again." };
    mount(<ActionsListPage client={{ ...refusing, actions: async () => store }} />, `/actions?${WIN}`, "/actions");
    await settledScreen();
    expect(document.querySelector("[data-page-refusal] p")?.textContent).toBe(store.copy);
    expect(document.querySelector("[data-estate-window]")).toBeNull();
  });

  it("an Action's title is the selected title or the code alone", async () => {
    const titled = actionRow({ action_title: "Review generator stop setting" });
    const untitled = actionRow({ action_id: "10000000-0000-4000-8000-000000000299", action_title: null as unknown as string });
    const c: EstateClient = { ...client([]), actions: async () => loaded(actionsBody({ rows: [titled, untitled], total_count: 2 })) };
    mount(<ActionsListPage client={c} />, `/actions?${RANGE}`, "/actions");
    await settledScreen();
    const titles = Array.from(document.querySelectorAll("tbody tr[data-row] a")).map((a) => a.textContent);
    expect(titles).toEqual(["Review generator stop setting", "ACT-001"]);
    expect(document.body.textContent).not.toContain("Battery reserve trial");
  });
});
