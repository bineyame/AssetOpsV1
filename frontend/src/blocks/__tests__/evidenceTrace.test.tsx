import { afterEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import { fakeOutcomeBoard } from "../../test/outcomeBoardFixture";
import { OutcomeBoard } from "../../sites/OutcomeBoard";
import { CategoryCards } from "../../estate/PortfolioOutcomes";
import { portfolioBody } from "../../estate/__tests__/portfolioFixtures";
import { WHY_SCHEMA, type ChainClient, type WhyBody, type WhyRead, type WhyWindow } from "../../sites/chainClient";
import { WHY_HEADS, WHY_LOADING, WHY_UNAVAILABLE } from "../EvidenceTrace";

/** CH-5b3: the "Why?" buttons, the trace dialog (focus, both widths) and its loading / failure / empty states. */

function body(over: Partial<WhyBody["text"]> = {}): WhyBody {
  return {
    schema_version: WHY_SCHEMA,
    category: "OPTIMIZE_COST",
    text: {
      title: "Kobo · Optimize cost and efficiency",
      say: "12.40 to 18.75 USD exposure in this hour",
      comes_from: ["Generator use on 1 checked day", "Battery report missing, seen 1 time since 6 Oct"],
      days_used: "6 Oct partly checked",
      would_change: "Checking 1 more day",
      evidence_ref: { kind: "EVIDENCE", site: "KOBO-001", capability: "dispatch" },
      evidence_label: "Kobo evidence →",
      ...over,
    },
  };
}

function fakeChain(read: WhyRead | (() => Promise<WhyRead>) = { status: "loaded", value: body() }) {
  const site: { code: string; category: string; query: unknown }[] = [];
  const estate: { category: string; window: WhyWindow }[] = [];
  const answer = () => (typeof read === "function" ? read() : Promise.resolve(read));
  const client: ChainClient = {
    getSiteWhy: (code, category, query) => {
      site.push({ code, category, query });
      return answer();
    },
    getEstateWhy: (category, window) => {
      estate.push({ category, window });
      return answer();
    },
  };
  return { client, site, estate };
}

const QUERY = { date: "2026-10-06" };

async function renderBoard(chain = fakeChain()) {
  render(
    <MemoryRouter>
      <OutcomeBoard client={fakeOutcomeBoard().client} siteCode="KOBO-001" query={QUERY} why={chain.client} />
    </MemoryRouter>,
  );
  await settledScreen();
  return chain;
}

const rowEl = (category: string) => document.querySelector(`[data-outcome-row='${category}']`) as HTMLElement;
const dialog = () => document.querySelector("[data-why-dialog]") as HTMLDialogElement | null;
const width = window.innerWidth;

afterEach(() => {
  Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: width });
});

describe("CH-5b3 Why buttons", () => {
  it("everyMeasuredBoardRowHasWhyAndNotMeasuredHasNone", async () => {
    await renderBoard();
    const rows = Array.from(document.querySelectorAll<HTMLElement>("[data-outcome-row]"));
    expect(rows.length).toBeGreaterThan(0);
    const measured = rows.filter((r) => r.getAttribute("data-outcome-state") !== "NOT_MEASURED");
    expect(measured.length).toBeGreaterThan(0);
    for (const r of rows) {
      const btn = r.querySelector("[data-why-button]");
      if (r.getAttribute("data-outcome-state") === "NOT_MEASURED") expect(btn).toBeNull();
      else {
        expect(btn?.getAttribute("aria-label")).toMatch(/^Why\? /);
        expect(btn?.textContent).toBe("Why?");
        expect(btn?.getAttribute("aria-haspopup")).toBe("dialog");
      }
    }
    expect(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: "Why? Optimize cost and efficiency" })).toBeTruthy();
  });

  it("theDaysLineIsOnlyInTheDialog", async () => {
    await renderBoard();
    expect(document.body.textContent).not.toContain(WHY_HEADS.days);
    expect(document.querySelector(".ob-days, .oc-pfdays")).toBeNull();
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    expect(within(dialog()!).getByText(WHY_HEADS.days)).toBeTruthy();
    expect(dialog()!.querySelector("[data-why-days]")?.textContent).toBe("6 Oct partly checked");
  });

  it("theButtonDoesNotOpenOrCloseItsRow", async () => {
    await renderBoard();
    const grow = rowEl("GROW_REVENUE") as HTMLDetailsElement;
    const before = grow.open;
    fireEvent.click(within(grow).getByRole("button", { name: /^Why\?/ }));
    expect(grow.open).toBe(before);
    await settledScreen();
  });

  it("theBoardAsksForItsOwnWindowAndCategory", async () => {
    const chain = await renderBoard();
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    expect(chain.site).toEqual([{ code: "KOBO-001", category: "OPTIMIZE_COST", query: QUERY }]);
  });

  it("theFourPortfolioCardsHaveWhyAndAskTheEstate", async () => {
    const chain = fakeChain();
    const window = { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", known_at: null };
    render(
      <MemoryRouter>
        <CategoryCards body={portfolioBody()} window={window} why={chain.client} />
      </MemoryRouter>,
    );
    const cards = Array.from(document.querySelectorAll<HTMLElement>("[data-portfolio-card]"));
    expect(cards).toHaveLength(4);
    for (const card of cards) {
      const name = card.querySelector("[data-portfolio-card-name]")?.textContent;
      const btn = within(card).getByRole("button", { name: `Why? ${name}` });
      // A div card: the button is not inside the card's link.
      expect(card.tagName).toBe("DIV");
      expect(btn.closest("a")).toBeNull();
    }
    expect(document.body.textContent).not.toContain(WHY_HEADS.days);
    fireEvent.click(within(cards[2]).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    expect(chain.estate).toEqual([{ category: "PROTECT_ASSET", window }]);
    expect(within(dialog()!).getByText(WHY_HEADS.days)).toBeTruthy();
  });
});

describe("CH-5b3 Why dialog", () => {
  it("opensTakesFocusTrapsTabAndClosesOnEscapeReturningFocus", async () => {
    await renderBoard();
    const button = within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ });
    fireEvent.click(button);
    await settledScreen();
    const d = dialog()!;
    expect(d).not.toBeNull();
    expect(d.getAttribute("aria-labelledby")).toBeTruthy();
    expect(document.getElementById(d.getAttribute("aria-labelledby")!)?.textContent).toBe("Kobo · Optimize cost and efficiency");
    const close = within(d).getByRole("button", { name: "Close" });
    const link = within(d).getByRole("link", { name: "Kobo evidence →" });
    expect(link.getAttribute("href")).toBeTruthy();
    expect(document.activeElement).toBe(close);
    link.focus();
    fireEvent.keyDown(d, { key: "Tab" });
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(d, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(link);
    fireEvent.keyDown(d, { key: "Escape" });
    expect(dialog()).toBeNull();
    expect(document.activeElement).toBe(button);
  });

  it("closeButtonClosesAndShowsTheServerText", async () => {
    await renderBoard();
    const button = within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ });
    fireEvent.click(button);
    await settledScreen();
    const d = dialog()!;
    expect(within(d).getByText("12.40 to 18.75 USD exposure in this hour")).toBeTruthy();
    expect(within(d).getByText(WHY_HEADS.from)).toBeTruthy();
    expect(within(d).getAllByRole("listitem").map((li) => li.textContent)).toEqual([
      "Generator use on 1 checked day",
      "Battery report missing, seen 1 time since 6 Oct",
    ]);
    expect(within(d).getByText("Checking 1 more day")).toBeTruthy();
    fireEvent.click(within(d).getByRole("button", { name: "Close" }));
    expect(dialog()).toBeNull();
    expect(document.activeElement).toBe(button);
  });

  it("isAPlacedModalAbove600px", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: 1440 });
    await renderBoard();
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    const d = dialog()!;
    expect(d.classList.contains("why-pop")).toBe(true);
    expect(d.classList.contains("sheet")).toBe(false);
    expect(d.style.width).not.toBe("");
    expect(d.style.top).not.toBe("");
    const close = within(d).getByRole("button", { name: "Close" });
    expect(close.hidden).toBe(false);
  });

  it("isABottomSheetAt390px", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: 390 });
    await renderBoard();
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    const d = dialog()!;
    expect(d.classList.contains("sheet")).toBe(true);
    expect(d.style.width).toBe("");
    expect(within(d).getByRole("button", { name: "Close" }).hidden).toBe(false);
  });

  it("showsTheLoadingLineWhileTheReadIsInFlight", async () => {
    let resolve: (r: WhyRead) => void = () => undefined;
    const pending = new Promise<WhyRead>((r) => (resolve = r));
    await renderBoard(fakeChain(() => pending));
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    const d = dialog()!;
    expect(d.querySelector("[data-why-state]")?.getAttribute("data-why-state")).toBe("loading");
    expect(within(d).getByText(WHY_LOADING)).toBeTruthy();
    // Until the server title arrives the row label is the title.
    expect(document.getElementById(d.getAttribute("aria-labelledby")!)?.textContent).toBe("Optimize cost and efficiency");
    resolve({ status: "loaded", value: body() });
    await settledScreen();
    expect(within(d).queryByText(WHY_LOADING)).toBeNull();
  });

  it.each<[string, WhyRead]>([
    ["422", { status: "refused", httpStatus: 422, code: "CATEGORY_UNKNOWN" }],
    ["500", { status: "refused", httpStatus: 500, code: "" }],
    ["unavailable", { status: "unavailable" }],
  ])("everyFailureReadsTheSameLine (%s)", async (_name, read) => {
    await renderBoard(fakeChain(read));
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    const d = dialog()!;
    expect(within(d).getByText(WHY_UNAVAILABLE)).toBeTruthy();
    expect(within(d).queryByText(WHY_HEADS.from)).toBeNull();
    expect(within(d).queryByRole("link")).toBeNull();
  });

  it("aRejectedReadReadsTheFailureLine", async () => {
    await renderBoard(fakeChain(() => Promise.reject(new Error("boom"))));
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    expect(within(dialog()!).getByText(WHY_UNAVAILABLE)).toBeTruthy();
  });

  it("anEmptyTraceShowsNoEmptySections", async () => {
    await renderBoard(
      fakeChain({
        status: "loaded",
        value: body({ comes_from: [], days_used: null, would_change: null, evidence_ref: null }),
      }),
    );
    fireEvent.click(within(rowEl("OPTIMIZE_COST")).getByRole("button", { name: /^Why\?/ }));
    await settledScreen();
    const d = dialog()!;
    expect(within(d).getByText("12.40 to 18.75 USD exposure in this hour")).toBeTruthy();
    for (const head of Object.values(WHY_HEADS)) expect(within(d).queryByText(head)).toBeNull();
    expect(d.querySelector("ul")).toBeNull();
    expect(within(d).queryByRole("link")).toBeNull();
    expect(screen.queryByText(WHY_UNAVAILABLE)).toBeNull();
  });
});
