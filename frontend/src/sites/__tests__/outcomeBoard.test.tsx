import { fireEvent, render, screen, within } from "@testing-library/react";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { describe, expect, it } from "vitest";

import { boardBody, boardRows, fakeOutcomeBoard } from "../../test/outcomeBoardFixture";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { boardMoneyText, countsText, OutcomeBoard } from "../OutcomeBoard";
import type { OutcomeBoardRead } from "../outcomeBoardClient";

async function renderBoard(read?: OutcomeBoardRead, query = { date: "2026-10-06" }) {
  const fake = fakeOutcomeBoard(read);
  render(
    <MemoryRouter>
      <OutcomeBoard client={fake.client} siteCode="KOBO-001" query={query} />
    </MemoryRouter>,
  );
  await settledScreen();
  return fake;
}

const board = () => screen.getByRole("region", { name: "Outcomes at this site" });
const rowEl = (category: string) => document.querySelector(`[data-outcome-row='${category}']`) as HTMLElement;

describe("OUT-B B5 Site outcome board", () => {
  it("rendersFourRowsInCanonicalOrderUnderTheHeading", async () => {
    const fake = await renderBoard();
    expect(fake.calls).toEqual([{ siteCode: "KOBO-001", query: { date: "2026-10-06" } }]);
    expect(within(board()).getByRole("heading", { level: 2, name: "How this site is doing" })).toBeInTheDocument();
    const rows = Array.from(board().querySelectorAll("[data-outcome-row]")).map((r) => r.getAttribute("data-outcome-row"));
    expect(rows).toEqual(["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]);
    expect(rowEl("OPTIMIZE_COST").textContent).toContain("Optimize cost and efficiency");
    expect(rowEl("OPTIMIZE_COST").textContent).toContain("Eliminate avoidable expenditure");
  });

  it("opensOnlyNeedsAttentionRows", async () => {
    await renderBoard();
    expect(rowEl("OPTIMIZE_COST").tagName).toBe("DETAILS");
    expect(rowEl("OPTIMIZE_COST")).toHaveAttribute("open");
    expect(rowEl("GROW_REVENUE")).not.toHaveAttribute("open");
    expect(rowEl("PROTECT_ASSET")).not.toHaveAttribute("open");
    expect(rowEl("OPTIMIZE_COST").className).toBe("ob tone-amber");
    expect(rowEl("PROTECT_ASSET").className).toBe("ob tone-blue");
  });

  it("rendersNotMeasuredAsOneLinerWithNoColumns", async () => {
    await renderBoard();
    const later = rowEl("ASSURE_PERFORMANCE");
    expect(later.tagName).toBe("DIV");
    expect(later.className).toBe("ob ob-later");
    expect(later.querySelector(".oc-chip.tone-none")?.textContent).toBe("Not measured yet");
    expect(later.querySelector(".ob-head")?.textContent).toBe("Targets are not declared for this site");
    expect(later.querySelector(".ob-grid")).toBeNull();
    expect(later.querySelector(".ob-counts")).toBeNull();
  });

  it("rendersTheFiveColumnsAndEveryEmptyText", async () => {
    await renderBoard();
    const cost = rowEl("OPTIMIZE_COST");
    const headings = Array.from(cost.querySelectorAll(".ob-col h4")).map((h) => h.textContent);
    expect(headings).toEqual(["What drives it", "Issues", "What can be done", "Already in hand", "Earlier interventions"]);
    // Populated columns on the cost row.
    expect(cost.querySelector("[data-outcome-col='drives']")?.textContent).toContain("30 minutes longer than needed");
    expect(within(cost.querySelector("[data-outcome-col='drives']") as HTMLElement).getByRole("link", { name: "Generator use" })).toHaveAttribute(
      "href",
      "/sites/KOBO-001/performance/dispatch",
    );
    expect(cost.querySelector(".oc-conf")?.textContent).toBe("Low");
    const issues = cost.querySelector("[data-outcome-col='issues']") as HTMLElement;
    expect(Array.from(issues.querySelectorAll(".oc-kind")).map((k) => `${k.className}|${k.textContent}`)).toEqual([
      "oc-kind finding|Finding",
      "oc-kind gap|Evidence gap",
    ]);
    expect(cost.querySelector("[data-outcome-col='hand'] .oc-state")?.textContent).toBe("Plan ready");
    expect(cost.querySelector("[data-outcome-col='prev'] .oc-state")?.textContent).toBe("Did not fix it");
    expect(cost.querySelector(".ob-foot")?.textContent).toBe("Dispatch evidence →");
    // Empty texts on the Protect row; Earlier uses the backend's own text verbatim.
    const protect = rowEl("PROTECT_ASSET");
    const none = (col: string) => protect.querySelector(`[data-outcome-col='${col}'] .ob-none`)?.textContent;
    expect(none("issues")).toBe("None open");
    expect(none("can")).toBe("Nothing proposed yet");
    expect(none("hand")).toBe("No open action or work");
    expect(none("prev")).toBe("No earlier work has been checked for this");
    expect(rowEl("GROW_REVENUE").querySelector("[data-outcome-col='prev'] .ob-none")?.textContent).toBe(
      "Not available yet · no completed work or checked change for this outcome",
    );
  });

  it("earlierFallsBackToNoneRecordedOnlyWhenTheFieldIsAbsent", async () => {
    const rows = boardRows();
    const older = { ...rows[2] } as Partial<(typeof rows)[number]>;
    delete older.earlier_empty_text;
    await renderBoard({ status: "loaded", value: boardBody({ rows: [rows[0], rows[1], older as (typeof rows)[number], rows[3]] }) });
    expect(rowEl("PROTECT_ASSET").querySelector("[data-outcome-col='prev'] .ob-none")?.textContent).toBe("None recorded");
  });

  it("countsTextSingularPluralAndInHand", async () => {
    expect(countsText(0, 0)).toBe("No open issues");
    expect(countsText(1, 0)).toBe("1 issue");
    expect(countsText(2, 0)).toBe("2 issues");
    expect(countsText(0, 1)).toBe("No open issues · 1 in hand");
    expect(countsText(2, 2)).toBe("2 issues · 2 in hand");
    await renderBoard();
    expect(rowEl("OPTIMIZE_COST").querySelector("[data-outcome-counts]")?.textContent).toBe("2 issues · 1 in hand");
    expect(rowEl("GROW_REVENUE").querySelector("[data-outcome-counts]")?.textContent).toBe("1 issue");
    expect(rowEl("PROTECT_ASSET").querySelector("[data-outcome-counts]")?.textContent).toBe("No open issues");
  });

  it("headlineMoneyFormattedInTheFrontendOnly", async () => {
    expect(boardMoneyText({ amount_low: "12.40", amount_high: "18.75", currency: "USD" })).toBe("12.40 to 18.75 USD");
    expect(boardMoneyText({ amount_low: "3.31", amount_high: "3.31", currency: "USD" })).toBe("3.31 USD");
    expect(boardMoneyText(null)).toBeNull();
    // WALK1-6 D3 (R696): every bound shows two decimals by the shared money2 rule (half even), shape unchanged.
    expect(boardMoneyText({ amount_low: "4.50000", amount_high: "4.50000", currency: "USD" })).toBe("4.50 USD");
    expect(boardMoneyText({ amount_low: "42.075", amount_high: "42.075", currency: "USD" })).toBe("42.08 USD");
    expect(boardMoneyText({ amount_low: "8.325", amount_high: "8.325", currency: "USD" })).toBe("8.32 USD");
    expect(boardMoneyText({ amount_low: "12.4", amount_high: "18.756", currency: "USD" })).toBe("12.40 to 18.76 USD");
    expect(boardMoneyText({ amount_low: "3", amount_high: "3.000", currency: null })).toBe("3.00");
    expect(boardMoneyText({ amount_low: null, amount_high: "3", currency: "USD" })).toBeNull();
    await renderBoard();
    expect(rowEl("OPTIMIZE_COST").querySelector(".ob-head .ob-val")?.textContent).toBe("12.40 to 18.75 USD exposure in this hour");
    expect(rowEl("GROW_REVENUE").querySelector(".ob-head .ob-val")?.textContent).toBe("18–20 kW of daytime solar unused");
  });

  it("mustNotHarmPresentWithLinkAndAbsent", async () => {
    await renderBoard();
    const guard = rowEl("OPTIMIZE_COST").querySelector("[data-outcome-guard]") as HTMLElement;
    expect(guard.querySelector("b")?.textContent).toBe("Must not harm");
    expect(within(guard).getByRole("link")).toHaveAttribute("href", "/sites/KOBO-001/actions/a-1/verification?event_id=e-1");
    expect(rowEl("PROTECT_ASSET").querySelector("[data-outcome-guard]")).toBeNull();
    expect(rowEl("GROW_REVENUE").querySelector("[data-outcome-guard]")).toBeNull();
  });

  it("availableReadShowsNoPartialNotice", async () => {
    await renderBoard();
    expect(document.querySelector("[data-outcome-partial]")).toBeNull();
  });

  it("partialReadNoticeUnderTheHeading", async () => {
    await renderBoard({ status: "loaded", value: boardBody({ read_state: "PARTIAL" }) });
    const notices = document.querySelectorAll("[data-outcome-partial]");
    expect(notices).toHaveLength(1);
    expect(notices[0].textContent).toBe("Some readings could not be loaded; those outcomes show Unknown");
    expect(notices[0].previousElementSibling?.className).toBe("ob-board-head");
  });

  it("loadingAndRefusedStates", async () => {
    let resolve: (r: OutcomeBoardRead) => void = () => {};
    const pending = new Promise<OutcomeBoardRead>((r) => (resolve = r));
    render(
      <MemoryRouter>
        <OutcomeBoard client={{ getOutcomeBoard: () => pending }} siteCode="COLD-LAB-001" query={{ from: null, to: null }} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("status").textContent).toBe("Loading how this site is doing…");
    resolve({ status: "refused", httpStatus: 403, code: "SITE_SCOPE_FORBIDDEN" });
    await settledScreen();
    expect(screen.getByRole("alert").textContent).toBe("This view is not available for this site");
    expect(document.querySelectorAll("[data-outcome-row]")).toHaveLength(0);
    expect(screen.queryByRole("button", { name: "About this view" })).toBeNull();
  });

  it("explainerDialogTakesFocusClosesOnEscapeAndReturnsFocus", async () => {
    await renderBoard();
    const info = screen.getByRole("button", { name: "About this view" });
    info.focus();
    fireEvent.click(info);
    const dialog = document.querySelector("[data-outcome-explainer]") as HTMLDialogElement;
    expect(dialog).not.toBeNull();
    expect(dialog).toHaveAttribute("open");
    const close = within(dialog).getByRole("button", { name: "Close" });
    expect(document.activeElement).toBe(close);
    expect(dialog.textContent).toContain("Each row is one of the four things the business is trying to achieve.");
    expect(dialog.textContent).toContain("Money of different kinds is shown separately and never added together.");
    const paragraphs = Array.from(dialog.querySelectorAll("p.prose")).map((p) => p.textContent);
    expect(paragraphs[paragraphs.length - 1]).toBe(
      "A declared objective is a target set for this demonstration so the status can be shown. It is not the customer's target.",
    );
    const cells = Array.from(dialog.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map((td) => td.textContent));
    expect(cells).toHaveLength(4);
    // The name cell carries the named icon (its <title>) and the name.
    expect(cells[1][0]).toContain("Optimize cost and efficiency");
    expect(cells[1][1]).toBe("Eliminate avoidable expenditure and get more output from operational resources");
    // Tab from the last focusable element wraps to the first (focus stays in the dialog).
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(document.querySelector("[data-outcome-explainer]")).toBeNull();
    expect(document.activeElement).toBe(info);
  });

  it("walk1WithheldFindingsReadNoneShownYet", async () => {
    expect(countsText(0, 0, "withheld")).toBe("No open issues shown yet");
    expect(countsText(0, 1, "withheld")).toBe("No open issues shown yet · 1 in hand");
    await renderBoard({
      status: "loaded",
      value: boardBody({ finding_gaps: { text: "No assessed readings on 3 Oct", days: ["2026-10-03"], withheld: true } }),
    });
    const protect = rowEl("PROTECT_ASSET");
    expect(protect.querySelector("[data-outcome-col='issues'] .ob-none")?.textContent).toBe("None shown yet");
    expect(protect.querySelector("[data-outcome-counts]")?.textContent).toBe("No open issues shown yet");
    expect(describeViolations(scanProductVocabulary(board(), "site-overview", { set: "w1" }).violations)).toBe("");
  });

  it("walk1QualifiesNoneOnTheDaysCheckedWhenTheBoardNamesDayGaps", async () => {
    // WALK1-1 (WN-2, R673): with `finding_gaps`, "none" is a claim on the checked days only.
    expect(countsText(0, 0, true)).toBe("No open issues on the days checked");
    expect(countsText(0, 1, true)).toBe("No open issues on the days checked · 1 in hand");
    expect(countsText(2, 0, true)).toBe("2 issues");
    await renderBoard({
      status: "loaded",
      value: boardBody({ finding_gaps: { text: "No assessed readings on 3 Oct", days: ["2026-10-03"] } }),
    });
    const protect = rowEl("PROTECT_ASSET");
    expect(protect.querySelector("[data-outcome-col='issues'] .ob-none")?.textContent).toBe("None found on the days checked");
    expect(protect.querySelector("[data-outcome-counts]")?.textContent).toBe("No open issues on the days checked");
    expect(rowEl("OPTIMIZE_COST").querySelector("[data-outcome-counts]")?.textContent).toBe("2 issues · 1 in hand");
    expect(describeViolations(scanProductVocabulary(board(), "site-overview", { set: "w1" }).violations)).toBe("");
  });

  it("showsNoOutcomeCodeAndPassesTheW1VocabularyScan", async () => {
    await renderBoard();
    const text = board().textContent ?? "";
    for (const code of ["MG-1", "MG-2", "MG-3", "X-1", "OPTIMIZE_COST", "NEEDS_ATTENTION"]) expect(text).not.toContain(code);
    const scan = scanProductVocabulary(board(), "site-overview", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(20);
    expect(describeViolations(scan.violations)).toBe("");
  });

  it("rendersADeclaredObjectiveContributorWithItsChipAndPassesTheScan", async () => {
    // OUT-D U5: the objective line is an ordinary contributor with a chip; no component change.
    const rows = boardRows().map((r) =>
      r.category !== "OPTIMIZE_COST"
        ? r
        : {
            ...r,
            contributors: [
              ...r.contributors,
              {
                key: "declared_objective:MG-2",
                label: "Declared objective",
                text: "Supply cost per kWh: no generator time longer than needed · 12 min longer than needed on this day",
                confidence: { label: "Missed", tone: "amber" },
                href: null,
              },
            ],
          },
    );
    await renderBoard({ status: "loaded", value: boardBody({ rows }) });
    const drives = rowEl("OPTIMIZE_COST").querySelector("[data-outcome-col='drives']") as HTMLElement;
    expect(drives.textContent).toContain("Declared objective");
    expect(drives.textContent).toContain("Supply cost per kWh: no generator time longer than needed · 12 min longer than needed on this day");
    expect(Array.from(drives.querySelectorAll(".oc-conf")).map((c) => c.textContent)).toContain("Missed");
    for (const code of ["MG-2", "MISSED", "declared_objective", "avoidable_generator_minutes"]) expect(board().textContent).not.toContain(code);
    const scan = scanProductVocabulary(board(), "site-overview", { set: "w1" });
    expect(describeViolations(scan.violations)).toBe("");
  });
});

describe("WALK1-3b Grow row: KPI state, performance and potential apart", () => {
  it("rendersTheOpportunityAsASecondChipAfterTheStateChip", async () => {
    const rows = boardRows().map((r) =>
      r.category !== "GROW_REVENUE"
        ? r
        : {
            ...r,
            state: "ON_TRACK",
            state_label: "On track",
            tone: "green",
            potential: { label: "Opportunity", text: "Productive-use headroom" },
            contributors: [
              {
                key: "declared_objective:MG-1",
                label: "Declared objective",
                text:
                  "Productive electricity sales: at least 300 kWh sold for productive use a month · " +
                  "673.3 kWh so far this month, on 6 of 29 days checked",
                confidence: { label: "Met", tone: "green" },
                href: null,
              },
              ...r.contributors,
            ],
          },
    );
    await renderBoard({ status: "loaded", value: boardBody({ rows }) });
    const summary = rowEl("GROW_REVENUE").querySelector(".ob-sum") as HTMLElement;
    const chips = Array.from(summary.querySelectorAll(".oc-chip")).map((c) => c.textContent);
    expect(chips).toEqual(["On track", "Opportunity"]);
    const potential = summary.querySelector("[data-outcome-potential]") as HTMLElement;
    expect(potential.className).toContain("tone-green");
    expect(potential.getAttribute("title")).toBe("Productive-use headroom");
    expect(rowEl("GROW_REVENUE").textContent).toContain("so far this month, on 6 of 29 days checked");
    for (const code of ["MG-1", "MET", "ON_TRACK", "OPPORTUNITY"]) expect(board().textContent).not.toContain(code);
    const scan = scanProductVocabulary(board(), "site-overview", { set: "w1" });
    expect(describeViolations(scan.violations)).toBe("");
  });

  it("rendersOneChipWhenNoPotentialOrOnAnOlderBody", async () => {
    const rows = boardRows().map((r) => (r.category === "GROW_REVENUE" ? { ...r, potential: null } : r));
    await renderBoard({ status: "loaded", value: boardBody({ rows }) });
    for (const row of [rowEl("GROW_REVENUE"), rowEl("OPTIMIZE_COST")]) {
      const summary = row.querySelector(".ob-sum") as HTMLElement;
      expect(summary.querySelectorAll(".oc-chip")).toHaveLength(1);
      expect(summary.querySelector("[data-outcome-potential]")).toBeNull();
    }
  });
});

describe("OUT-E Earlier entry detail", () => {
  const DETAIL =
    "Modelled change after the trial · not realised savings: 0.042–0.046 USD less per kWh of feeder demand · " +
    "Supply cost per kWh before the trial: missed · after: met";

  function withEarlier(earlier: { text: string; href: string | null; result_label: string | null; detail?: string | null }[]) {
    const rows = boardRows();
    rows[1] = { ...rows[1], earlier };
    return { status: "loaded" as const, value: boardBody({ rows }) };
  }

  it("showsTheDetailAfterTheResultInsideTheEntry", async () => {
    await renderBoard(withEarlier([
      { text: "ACT-048 · Generator stop trial", href: "/sites/KOBO-001/actions/a-1", result_label: "Verified on example data", detail: DETAIL },
    ]));
    const item = rowEl("OPTIMIZE_COST").querySelector("[data-outcome-col='prev'] li") as HTMLElement;
    expect(item.querySelector("small")?.textContent).toBe(DETAIL);
    expect(item.querySelector(".oc-state")?.textContent).toBe("Verified on example data");
    expect(item.textContent).toBe(`ACT-048 · Generator stop trial Verified on example data ${DETAIL}`);
  });

  it("rendersNoDetailWhenNullOrAbsent", async () => {
    await renderBoard(withEarlier([
      { text: "ACT-048 · Generator stop trial", href: "/sites/KOBO-001/actions/a-1", result_label: "Pending", detail: null },
      { text: "Generator inspection", href: "/maintenance/requests/c-1", result_label: "Did not fix it" },
    ]));
    expect(rowEl("OPTIMIZE_COST").querySelectorAll("[data-outcome-col='prev'] li small")).toHaveLength(0);
  });

  it("detailPassesTheVocabularyScanAndSavesOnlyInNotRealisedSavings", async () => {
    await renderBoard(withEarlier([
      { text: "ACT-048 · Generator stop trial", href: "/sites/KOBO-001/actions/a-1", result_label: "Verified on example data", detail: DETAIL },
      { text: "ACT-049 · Generator stop trial", href: "/sites/KOBO-001/actions/a-2", result_label: "Not determined",
        detail: "Modelled change not calculated: the trial result is not determined · Status changed; not attributed" },
    ]));
    const scan = scanProductVocabulary(board(), "site-overview", { set: "w1" });
    expect(describeViolations(scan.violations)).toBe("");
    const text = board().textContent ?? "";
    const hits = Array.from(text.matchAll(/sav(e|ed|ing)s?/gi)).map((m) => text.slice(Math.max(0, (m.index ?? 0) - 13), (m.index ?? 0) + m[0].length));
    expect(hits.length).toBeGreaterThan(0);
    expect(hits.every((h) => h === "not realised savings")).toBe(true);
    for (const code of ["MODELLED_IMPROVEMENT", "OUTCOME_INCONCLUSIVE", "UNAVAILABLE", "candidate"]) expect(text).not.toContain(code);
  });
});

// POLISH P-10 (Addendum 12 Q1): the board tells its host the read it resolved, with no second fetch.
describe("POLISH P-10 onRead", () => {
  it("calls onRead once with the resolved read for the current key", async () => {
    const fake = fakeOutcomeBoard({ status: "loaded", value: boardBody() });
    const reads: OutcomeBoardRead[] = [];
    render(
      <MemoryRouter>
        <OutcomeBoard client={fake.client} siteCode="KOBO-001" query={{ date: "2026-10-06" }} onRead={(r) => reads.push(r)} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(fake.calls).toHaveLength(1);
    expect(reads.map((r) => r.status)).toEqual(["loaded"]);
  });
});

describe("CH-6a3 Grow parts", () => {
  // Server vocabulary (chain/vocabulary.py), so a copy regression fails here.
  const claim = (key: string, text: string, days_line: string | null = null, basis = "COMPLETE") => ({
    key, value: null, basis, days: null, text, days_line,
  });
  const growRead = (nodes: unknown) => {
    const body = boardBody();
    body.rows = boardRows().map((r) => (r.category === "GROW_REVENUE" ? ({ ...r, nodes } as typeof r) : r));
    return { status: "loaded", value: body } as OutcomeBoardRead;
  };
  const noTarget = claim("verdict.none", "No target set yet", "No target, so no days are judged yet", "NOT_KNOWN");

  it("giveseachPartItsOwnDaysLineAndSplitsPotentialOnNewline", async () => {
    await renderBoard(
      growRead({
        kpi: claim("verdict.MG-1", "On track", "3 of 3 days checked"),
        potential: claim("potential.value", "18-24.25 kW of daytime solar unused\nat about 0.12 per kWh", null),
        earnings: claim("money.estimated_income", "Not known yet", "1 of 1 days checked", "NOT_KNOWN"),
      }),
    );
    const parts = Array.from(rowEl("GROW_REVENUE").querySelectorAll("[data-outcome-part]"));
    expect(parts.map((p) => p.getAttribute("data-outcome-part"))).toEqual(["kpi", "potential", "earnings"]);
    expect(parts.map((p) => p.querySelector(".ob-plabel")?.textContent)).toEqual(["Target", "Potential", "Estimated income"]);
    expect(Array.from(parts[1].querySelectorAll("b")).map((b) => b.textContent)).toEqual([
      "18-24.25 kW of daytime solar unused",
      "at about 0.12 per kWh",
    ]);
    const days = parts.map((p) => p.querySelector(".ob-days")?.textContent ?? null);
    expect(days).toEqual(["3 of 3 days checked", null, "1 of 1 days checked"]); // potential never borrows a neighbour's line
    expect(rowEl("GROW_REVENUE").querySelectorAll(".ob-days")).toHaveLength(2); // no row-level line
  });

  it("alwaysShowsTheTargetPartWithNoTargetAndItsDaysLine", async () => {
    await renderBoard(
      growRead({
        kpi: noTarget,
        potential: claim("potential.none", "No potential found yet", null, "NOT_KNOWN"),
        earnings: claim("money.not_known", "Not known yet", null, "NOT_KNOWN"),
      }),
    );
    const g = rowEl("GROW_REVENUE");
    expect(g.querySelectorAll("[data-outcome-part]")).toHaveLength(3);
    const target = g.querySelector("[data-outcome-part='kpi']");
    expect(target?.textContent).toContain("No target set yet");
    expect(target?.querySelector(".ob-days")?.textContent).toBe("No target, so no days are judged yet");
  });

  async function readCss(): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
  const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
  return fs.readFileSync(`${cwd}/src/sites/outcomes.css`, "utf8");
}

describe("CH-6a3 R2b grid css", () => {
  it("usesTheV70GridClassAndDropsToOneColumnAt760", async () => {
    const outcomesCss = await readCss();
    expect(outcomesCss).toMatch(/\.ob-grow\s*\{[^}]*grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\)/);
    expect(outcomesCss).toMatch(/@media \(max-width: 760px\)\s*\{\s*\.ob-grow\s*\{\s*grid-template-columns:\s*1fr/);
  });

  it("rendersTheGrowContainerAsTheObGrowGridClass", async () => {
    await renderBoard(growRead({ kpi: noTarget, potential: null, earnings: null }));
    const grid = rowEl("GROW_REVENUE").querySelector("[data-outcome-grow]");
    expect(grid?.className).toBe("ob-grow");
    expect(grid?.querySelectorAll(":scope > .ob-part")).toHaveLength(3);
  });
});
});
