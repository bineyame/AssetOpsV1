import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
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
    await renderBoard();
    expect(rowEl("OPTIMIZE_COST").querySelector(".ob-head")?.textContent).toBe("12.40 to 18.75 USD exposure in this hour");
    expect(rowEl("GROW_REVENUE").querySelector(".ob-head")?.textContent).toBe("18–20 kW of daytime solar unused");
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

  it("showsNoOutcomeCodeAndPassesTheW1VocabularyScan", async () => {
    await renderBoard();
    const text = board().textContent ?? "";
    for (const code of ["MG-1", "MG-2", "MG-3", "X-1", "OPTIMIZE_COST", "NEEDS_ATTENTION"]) expect(text).not.toContain(code);
    const scan = scanProductVocabulary(board(), "site-overview", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(20);
    expect(describeViolations(scan.violations)).toBe("");
  });
});
