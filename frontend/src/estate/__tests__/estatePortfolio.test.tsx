/**
 * W3-03 run 2: the estate Portfolio page under a local MemoryRouter (Lane A mounts the shell route), against the
 * v69 `portfolio` panels and `.agent/W3-03-build-spec.md` closures 1-5, r1a, r1b, r1b2 and r1b4 literals.
 */
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { Route, Routes, useLocation } from "react-router-dom";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { describe, expect, it } from "vitest";
import { leadingIntruders, panelTitled, renderedPanelTitles, strayBetweenPanels, strayOutsidePanels, stripIntruders } from "../../test/panelStructure";
import { describeViolations, forbiddenPhrases, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type {
  EstateCheckedDays,
  EstateClient,
  EstateOutcomeSummaryBody,
  EstatePortfolioBody,
  EstatePortfolioCard,
  EstatePortfolioQuery,
  EstatePortfolioScopeIdsBody,
  EstatePortfolioStatus,
  EstateResult,
} from "../estateClient";

type EstateOutcomeSummaryRead = EstateResult<EstateOutcomeSummaryBody>;
import { EstatePortfolioPage } from "../EstatePortfolio";
import { mechanismWords, OPPORTUNITY_PANEL, PRIORITY_PANEL } from "../portfolioWords";
import { outcomeWarning, planWarning } from "../../test/outcomeBoardFixture";
import type { OutcomeWarning } from "../../sites/outcomeBoardClient";
import {
  ASSURE_WITH_VALUES,
  PROTECT_WITH_FUEL,
  COLD_EVENT_HREF,
  COLD_ROW,
  coverageSite,
  loadedPortfolio,
  opportunityItem,
  OPTIMIZE_NONE,
  OPTIMIZE_ONE_SITE,
  portfolioBody,
  portfolioClient,
  refused,
  row,
  SITES,
  outcomeSummaryBody,
  partialBody,
  serverCard,
  serverCards,
  STATUS_BODIES,
  withOutcomeSummary,
} from "./portfolioFixtures";
import { withLinkRefs } from "../../test/linkRefs";

const ENTRY = "/portfolio?from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z";
/** PF-T: the same window on a section tab. */
const tabEntry = (segment: string) => ENTRY.replace("/portfolio?", `/portfolio/${segment}?`);
const ACT = tabEntry("act-first");

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

function renderAt(entry: string, client: EstateClient) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/portfolio/:tab?" element={<main><EstatePortfolioPage client={client} /></main>} />
        <Route path="*" element={<main><Where /></main>} />
      </Routes>
      <Where />
    </MemoryRouter>,
  );
}

/**
 * PF-T: the panels now sit on section tabs of the one mounted page. `showTab` follows a tab link in place (no new
 * read: the page keeps its reads), so a pre-PF-T assertion on a panel opens that panel's tab first.
 */
function showTab(label: string) {
  const nav = document.querySelector("nav[aria-label='Portfolio sections']");
  const link = Array.from(nav?.querySelectorAll("a") ?? []).find((a) => text(a.querySelector("[data-pf-tab-label]")) === label);
  if (link === undefined) throw new Error(`No Portfolio tab "${label}".`);
  if (link.getAttribute("aria-current") !== "page") fireEvent.click(link);
}
const PANEL_TAB: Record<string, string> = {
  "Where management should act first": "Act first",
  "Outcomes across the estate": "Outcomes by site",
  "An opportunity beyond reducing cost": "Opportunity",
  "What changed in this review": "What changed",
};
const panel = (title: string) => {
  if (PANEL_TAB[title] !== undefined) showTab(PANEL_TAB[title]);
  return panelTitled(title);
};
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
/** Leaf-element texts joined by one space (a cell's stacked lines). */
const lines = (el: Element) =>
  Array.from(el.querySelectorAll("*"))
    .filter((e) => e.children.length === 0)
    .map(text)
    .join(" ");

describe("estate Portfolio page", () => {
  it("rendersContextFiveCardsPulseAndSelectedRows", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio Value & Operations");
    const context = document.querySelector("[data-portfolio-context]") as HTMLElement;
    expect(text(context)).toContain("Selected Site records");
    expect(text(context)).toContain("Portfolio: Review selected Sites");
    expect(text(context)).toContain("4 accessible Sites · 1 mini-grid / 1 cold-chain / 2 EV charging");
    expect(text(context)).not.toMatch(/simulated|Needs attention/);
    // OUT-A A6: four outcome category cards replace the five value cards (canonical order).
    const cards = Array.from(document.querySelectorAll("[data-portfolio-card]"));
    expect(cards.map((c) => c.getAttribute("data-portfolio-card"))).toEqual([
      "GROW_REVENUE",
      "OPTIMIZE_COST",
      "PROTECT_ASSET",
      "ASSURE_PERFORMANCE",
    ]);
    // CH5d1-R: Optimize is a server card; with no outcome summary read it says `Not known yet`, never the body's
    // `value_cards` money line.
    expect(text(cards[1].querySelector("[data-portfolio-card-value]"))).toBe("Not known yet");
    expect(text(cards[1])).not.toContain("$3.31–$3.97");
    expect(text(cards[1])).not.toContain("Candidate operating-cost exposure");
    expect(cards[1].querySelector("[data-portfolio-card-link]")?.tagName).toBe("A");
    expect(cards[1].querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toBe("/financials?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z");
    // CH-6b2: with no outcome summary read there is no server card, so Protect reads `Not known yet` (never a
    // browser-built value) and still links to the risk root.
    expect(text(cards[2].querySelector("[data-portfolio-card-value]"))).toBe("Not known yet");
    expect(cards[2].querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toMatch(/^\/findings\/risks\?/);
    expect(cards[0].querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toMatch(/^\/findings\/opportunities\?/);
    expect(cards[3].querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toMatch(/^\/evidence\?/);
    expect(text(document.body)).not.toMatch(/18–20|kW ×|\$2\.50|battery on watch|ACT-0/);
    const pulse = document.querySelector("[data-portfolio-pulse]") as HTMLElement;
    expect(text(pulse)).toContain("Not assessed priority sites");
    expect(text(pulse)).toContain("Distinct consequence categories · no combined savings total");
    showTab("Act first");
    const rows = Array.from(document.querySelectorAll("[data-portfolio-row]"));
    expect(rows).toHaveLength(2);
    expect(text(rows[0])).toContain("Unpriced");
  });

  it("showsCustomerMechanismWordsNotRawCodes", async () => {
    expect(mechanismWords("GENERATOR_SUPPORT_CANDIDATE")).toBe("Possible extended generator support");
    expect(mechanismWords("COLD_EXCURSION")).toBe("Chamber temperature above policy");
    expect(mechanismWords("COLD_START_FAILURE")).toBe("Automatic start failed");
    expect(mechanismWords("EV_INTERRUPTION")).toBe("Charging session interrupted");
    expect(mechanismWords(null)).toBe("Mechanism not recorded");
    expect(mechanismWords("SOMETHING_NEW")).toBe("Mechanism not recorded");
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const priority = panel("Where management should act first");
    expect(text(priority)).toContain("Possible extended generator support");
    expect(text(priority)).toContain("Chamber temperature above policy");
    expect(text(priority)).not.toMatch(/[A-Z]+_[A-Z_]+/);
  });

  it("rendersUnpricedCardAndEmptyRisksLensNotAssessed", async () => {
    const cards = portfolioBody().value_cards.map((c) =>
      c.key === "OPERATING_COST"
        ? { ...c, state: "UNPRICED" as const, line_keys: ["cold"], detail: "GreenHarvest · consequence recorded without a price", basis_text: "Price not established" }
        : c,
    );
    renderAt(`${ENTRY}&lens=risks`, portfolioClient(loadedPortfolio(portfolioBody({ value_cards: cards, rows: [], total_count: 0, lens: "risks" }))));
    await settledScreen();
    // PF-T: the old lens address opens Act first.
    expect(text(document.querySelector("[data-portfolio-empty]"))).toBe("No matching supported Findings");
    // CC-R2-Q3 ruling: with no rows the panel bottom keeps only the Findings link.
    const bottom = panel("Where management should act first").querySelector(".panel-bottom") as HTMLElement;
    expect(bottom.querySelector("span")).toBeNull();
    expect(within(bottom).getByRole("link", { name: "Open all Findings →" })).toBeTruthy();
    showTab("Overview");
    await settledScreen();
    // CH5d1-R: the body's `value_cards` stay on the wire unrendered (BL-51); Optimize is the server card only.
    const first = document.querySelector("[data-portfolio-card='OPTIMIZE_COST']") as HTMLElement;
    expect(text(first.querySelector("[data-portfolio-card-value]"))).toBe("Not known yet");
    expect(text(first)).not.toContain("consequence recorded without a price");
    expect(text(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-value]"))).toBe("Not known yet");
  });

  it("rendersEveryFindingColumnAndFourLensStates", async () => {
    const client = portfolioClient(
      loadedPortfolio(portfolioBody({ coverage: { ...portfolioBody().coverage, finding_state: "PARTIAL" } })),
    );
    renderAt(ENTRY, client);
    await settledScreen();
    const priority = panel("Where management should act first");
    expect(Array.from(priority.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Site",
      "Finding / operating mechanism",
      "Value / consequence",
      "Placement", // CC-R2: was "Priority"
      "Confidence",
      "Action / next move",
    ]);
    expect(text(priority.querySelector("[data-portfolio-count]"))).toBe("2 findings · so far, some days incomplete");
    const partialObjectives = document.querySelector("[data-portfolio-panel='objectives']") as HTMLElement;
    expect(text(partialObjectives)).not.toContain("Site detail is unavailable for these cells.");
    expect(text(partialObjectives)).not.toContain("Select a linked cell for context.");
    const w1 = priority.querySelector(`[data-portfolio-row^='f1f1f1f1']`) as HTMLElement;
    const cells = Array.from(w1.querySelectorAll("td")).map(lines);
    expect(cells[0]).toBe("Kobo Mini-grid Current view");
    expect(cells[1]).toBe("Extended generator support Possible extended generator support");
    expect(cells[2]).toBe("$3.31–$3.97 6 Oct 2026, 14:20–15:20");
    // CC-R2: the server's placement group and reason line; the derived confidence words and reasons.
    expect(cells[3]).toBe("Compare value Priced cost exposure; no like line to compare with");
    expect(cells[4]).toBe("Well supported Supported finding · Prepared example data source");
    expect(cells[5]).toBe("No action yet No action agreed yet Review finding");
    const cold = priority.querySelector(`[data-portfolio-row^='f2f2f2f2']`) as HTMLElement;
    expect(text(cold)).toContain("Finding detail unavailable");
    expect(cold.querySelector("[data-portfolio-finding-link]")).toBeNull();
    // CC-R2-Q3 ruling: the subtitle and the bottom line (no longer computed from priority).
    expect(text(priority)).toContain(
      "Selected findings across accessible Sites, grouped by where to look first, with evidence confidence alongside.",
    );
    expect(text(priority.querySelector(".panel-bottom span"))).toBe("Placement and confidence answer different questions.");
    const lenses = within(priority).getAllByRole("button").filter((b) => b.closest("[aria-label='Finding lens']"));
    expect(lenses.map((b) => [b.textContent, b.getAttribute("aria-pressed")])).toEqual([
      ["All findings", "true"],
      ["Cost", "false"],
      ["Risks", "false"],
      ["Opportunities", "false"],
    ]);
    for (const [label, lens] of [["Cost", "cost"], ["Risks", "risks"], ["Opportunities", "opportunities"]] as const) {
      await act(async () => {
        fireEvent.click(within(panel("Where management should act first")).getByRole("button", { name: label }));
      });
      await settledScreen();
      expect(screen.getAllByTestId("where")[0].textContent).toContain(`lens=${lens}`);
      expect(client.calls.at(-1)).toMatchObject({ lens, cursor: null, limit: 50 });
    }
    expect(client.calls.map((c) => c.lens)).toEqual(["all", "cost", "risks", "opportunities"]);
  });

  // OUT-B B6 (R521): the five-row objectives matrix is replaced by the four-row outcome matrix from the outcome summary
  // read; the portfolio body's `objectives` wire is no longer rendered.
  it("rendersFiveObjectiveRowsForEveryAuthorizedSite", async () => {
    const client = withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())));
    renderAt(`${ENTRY}&known_at=2026-10-07T00:00:00Z`, client);
    await settledScreen();
    const outcomes = panel("Outcomes across the estate");
    expect(text(outcomes)).toContain("How each site is doing on what matters");
    const matrix = within(outcomes).getByRole("table", { name: "Outcomes across the estate" });
    expect(Array.from(matrix.querySelectorAll("[data-portfolio-outcome-row]")).map((r) => r.getAttribute("data-portfolio-outcome-row"))).toEqual([
      "GROW_REVENUE",
      "OPTIMIZE_COST",
      "PROTECT_ASSET",
      "ASSURE_PERFORMANCE",
    ]);
    const defs = outcomeSummaryBody().categories;
    within(matrix).getAllByRole("rowheader").forEach((h, i) => {
      expect(text(h.querySelector("span:not(.oc-hidden)"))).toBe(defs[i].label);
      expect(text(h.querySelector(".oc-hidden"))).toBe(defs[i].definition);
    });
    const heads = Array.from(matrix.querySelectorAll("[data-portfolio-matrix-site] a"));
    expect(heads.map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      ["Kobo", "/sites/KOBO-001"],
      ["GreenHarvest", COLD_EVENT_HREF],
      ["Depot", "/sites/EV-LAB-001/ev"],
      ["Harbour", "/sites/EV-LAB-002/ev"],
    ]);
    expect(matrix.querySelectorAll("[data-portfolio-outcome-cell]")).toHaveLength(16);
    const cell = (code: string, cat: string) => matrix.querySelector(`[data-portfolio-outcome-cell^='${code}|${cat}|']`) as HTMLElement;
    expect(lines(cell("KOBO-001", "OPTIMIZE_COST"))).toBe("Needs attention Generator fuel");
    expect(cell("KOBO-001", "OPTIMIZE_COST").className).toBe("oc-cell tone-amber");
    expect(cell("KOBO-001", "OPTIMIZE_COST").getAttribute("href")).toBe("/sites/KOBO-001");
    // OUT-W: GreenHarvest was judged on its latest event, so its header and every cell open the Site on that window;
    // Depot (no event, judged on the period) opens with a plain link.
    expect(COLD_EVENT_HREF).toContain("?from=");
    const coldCells = Array.from(matrix.querySelectorAll("[data-portfolio-outcome-cell^='COLD-001|']"));
    expect(coldCells).toHaveLength(4);
    for (const el of coldCells) expect(el.getAttribute("href")).toBe(COLD_EVENT_HREF);
    const depotCells = Array.from(matrix.querySelectorAll("[data-portfolio-outcome-cell^='EV-LAB-001|']"));
    expect(depotCells).toHaveLength(4);
    for (const el of depotCells) expect(el.getAttribute("href")).toBe("/sites/EV-LAB-001/ev");
    expect(lines(cell("COLD-001", "GROW_REVENUE"))).toBe("Not measured yet Product sales");
    expect(cell("COLD-001", "GROW_REVENUE").className).toBe("oc-cell tone-none");
    expect(cell("EV-LAB-001", "ASSURE_PERFORMANCE").className).toBe("oc-cell tone-blue");
    // A Site whose board read failed: Unknown, no lead outcome line.
    expect(lines(cell("EV-LAB-002", "PROTECT_ASSET"))).toBe("Unknown");
    expect(cell("EV-LAB-002", "PROTECT_ASSET").querySelector("small")).toBeNull();
    expect(Array.from(outcomes.querySelectorAll("[data-portfolio-outcome-key] > span")).map((k) => [text(k), k.querySelector("i")?.className])).toEqual([
      ["Needs attention", "tone-amber"],
      ["Watch", "tone-blue"],
      ["Opportunity", "tone-green"],
      ["On track", "tone-green"],
      ["Unknown", "tone-gray"],
      ["Not measured yet", "tone-none"],
    ]);
    // The old objectives wire is not rendered, and no outcome code reaches the screen.
    expect(outcomes.querySelectorAll("[data-portfolio-cell], [data-portfolio-objective]")).toHaveLength(0);
    expect(text(outcomes)).not.toContain("Site-owned assessments");
    expect(text(outcomes)).not.toMatch(/NEEDS_ATTENTION|NOT_MEASURED|NO_OBJECTIVE|GROW_REVENUE|X-1/);
    // Read in parallel with the portfolio, for the same window.
    expect(client.summaryCalls).toEqual([{ from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", known_at: "2026-10-07T00:00:00Z" }]);
  });

  it("outcomeCardDotsMatchTheMatrixAndGrowRendersTheServerHeadline", async () => {
    const growCards = serverCards({
      GROW_REVENUE: serverCard({ value: { text: "18–20 kW", small: "unused" }, tone: "green", basis_text: "Opportunities · revenue not measured yet" }),
    });
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: outcomeSummaryBody({ cards: growCards }) }));
    await settledScreen();
    // PF-T: the matrix is on Outcomes by site and the cards on the Overview; compare against a copy of the matrix.
    showTab("Outcomes by site");
    const matrix = screen.getByRole("table", { name: "Outcomes across the estate" }).cloneNode(true) as HTMLElement;
    showTab("Overview");
    for (const cat of ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
      const dots = Array.from(document.querySelectorAll(`[data-portfolio-card-dots='${cat}'] > span`));
      expect(dots.map((d) => text(d))).toEqual(["Kobo: ", "GreenHarvest: ", "Depot: ", "Harbour: "].map((n, i) => n + text(matrix.querySelectorAll(`[data-portfolio-outcome-row='${cat}'] [data-portfolio-outcome-cell] b`)[i]).replace("No objective declared", "No target for this outcome")));
      // Each dot's tone is the matrix cell's tone for the same Site.
      for (const d of dots) {
        const [code, tone] = (d.getAttribute("data-portfolio-dot") ?? "").split("|");
        expect(d.className).toBe(`tone-${tone}`);
        expect(matrix.querySelector(`[data-portfolio-outcome-cell='${code}|${cat}|${tone}']`)).not.toBeNull();
      }
    }
    const kobo = document.querySelector("[data-portfolio-card-dots='OPTIMIZE_COST'] > span") as HTMLElement;
    expect(kobo.getAttribute("title")).toBe("Kobo: Needs attention");
    // CH-6b2: the Grow value is the server card's text and small, joined only as markup; the tone is the server's.
    const grow = document.querySelector("[data-portfolio-card='GROW_REVENUE']") as HTMLElement;
    expect(text(grow.querySelector("[data-portfolio-card-value]"))).toBe("18–20 kW unused");
    expect(grow.querySelector("[data-portfolio-card-value] small")?.textContent).toBe("unused");
    expect(grow.className).toContain("green");
    expect(grow.querySelector("[data-missing-claim], .missing-claim")).toBeNull();
  });

  it("growKeepsTheMissingClaimWhenTheServerCardIsMissingAndTheMatrixStatesUnavailable", async () => {
    // The default server Grow card is `missing`: the kept gap G-portfolio-grow-revenue renders, neutral.
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    const grow = document.querySelector("[data-portfolio-card='GROW_REVENUE']") as HTMLElement;
    expect(text(grow.querySelector("[data-portfolio-card-value]"))).toBe("Not available yet");
    expect(grow.className).toContain("neutral");
    expect(grow.querySelector("[data-portfolio-grow-parts]")).toBeNull();
    cleanup();
    // A refused summary and a client without the read both show the panel's alert; the cards keep empty dots and
    // say `Not known yet` (no server card, so no browser-built value).
    for (const client of [
      withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), refused(503, "ESTATE_STORE_UNAVAILABLE", "The estate store is unavailable.") as never),
      portfolioClient(loadedPortfolio(portfolioBody())),
    ]) {
      renderAt(ENTRY, client);
      await settledScreen();
      const outcomes = panel("Outcomes across the estate");
      expect(within(outcomes).getByRole("alert").textContent).toBe("Outcome status is not available right now");
      expect(outcomes.querySelector("[role='table']")).toBeNull();
      showTab("Overview");
      expect(document.querySelectorAll("[data-portfolio-card]")).toHaveLength(4);
      expect(document.querySelectorAll("[data-portfolio-dot]")).toHaveLength(0);
      for (const key of ["GROW_REVENUE", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
        expect(text(document.querySelector(`[data-portfolio-card='${key}'] [data-portfolio-card-value]`))).toBe("Not known yet");
        expect(document.querySelector(`[data-portfolio-card='${key}'] [data-portfolio-card-detail]`)).toBeNull();
      }
      cleanup();
    }
  });

  it("rendersTypedEvidencePromptAndExactDestinations", async () => {
    renderAt(`${ACT}&known_at=2026-10-07T00:00:00Z`, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const aside = document.querySelector("[data-portfolio-prompt]") as HTMLElement;
    expect(aside.getAttribute("data-portfolio-prompt")).toBe("AVAILABLE");
    expect(text(aside)).toContain("Restore the battery report at Kobo to address the selected evidence gap.");
    // R9/L3: the server-selected code is rendered as-is, with no invented Site link.
    expect(aside.querySelector("[data-portfolio-prompt-site]")?.getAttribute("data-portfolio-prompt-site")).toBe("KOBO-001");
    const links = within(aside).getAllByRole("link");
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      "/evidence?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00Z",
    ]);
    const priority = panel("Where management should act first");
    const w1 = priority.querySelector(`[data-portfolio-row^='f1f1f1f1']`) as HTMLElement;
    expect(w1.querySelector("[data-portfolio-site-link]")?.getAttribute("href")).toBe("/sites/KOBO-001");
    expect(w1.querySelector("[data-portfolio-finding-link]")?.getAttribute("href")).toBe(
      "/sites/KOBO-001/findings/f1f1f1f1-0000-4000-8000-000000000001?revision_id=e1e1e1e1-0000-4000-8000-000000000001",
    );
    expect(within(priority).getByRole("link", { name: "Open all Findings →" }).getAttribute("href")).toBe(
      "/findings?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00Z",
    );
  });

  it("PB-3 review M1: an open episode shows its start; no time only when neither end is held; no basis claim", async () => {
    const open = { ...COLD_ROW, episode_start: "2026-10-30T16:15:00Z", episode_end: null };
    const none = { ...COLD_ROW, finding_id: "f3f3f3f3-0000-4000-8000-000000000003", episode_start: null, episode_end: null };
    renderAt(ACT, portfolioClient(loadedPortfolio(portfolioBody({ rows: [open, none], total_count: 2 }))));
    await settledScreen();
    const cell = (id: string) => text(document.querySelector(`[data-portfolio-row^='${id}'] td:nth-child(3)`));
    expect(cell("f2f2f2f2")).toContain("From 30 Oct 2026, 16:15 · no end time yet");
    expect(cell("f3f3f3f3")).toContain("No time recorded yet");
    expect(text(document.body)).not.toContain("cost basis");
  });

  it("rendersIncompleteAndNoGapPromptWithoutSite", async () => {
    const body = portfolioBody({
      evidence_prompt: { state: "COVERAGE_INCOMPLETE", text: "Evidence coverage incomplete", site_id: null, site_code: null, gap_code: null, destination: "/evidence" },
    });
    renderAt(ACT, portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    const aside = document.querySelector("[data-portfolio-prompt]") as HTMLElement;
    expect(text(aside)).toContain("Evidence coverage incomplete");
    expect(aside.querySelector("[data-portfolio-prompt-site]")).toBeNull();
  });

  it("clearsPrivilegedRowsOn401And503", async () => {
    for (const [status, code, copy] of [
      [401, "UNAUTHENTICATED", "Sign in to see estate records."],
      [503, "ESTATE_STORE_UNAVAILABLE", "Estate records are unavailable right now. Try again."],
      [409, "ESTATE_BASIS_CHANGED", "The list changed. Reload the first page."],
    ] as const) {
      const client = portfolioClient(loadedPortfolio(portfolioBody({ next_cursor: "opaque-cursor" })), refused(status, code, copy));
      const view = renderAt(ACT, client);
      await settledScreen();
      expect(text(document.body)).toContain("GreenHarvest");
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Load more Findings" }));
      });
      expect(client.calls[1]).toMatchObject({ cursor: "opaque-cursor", lens: "all" });
      expect(document.querySelector(`[data-page-refusal='${code}']`)).not.toBeNull();
      expect(text(document.body)).toContain(copy);
      for (const stale of ["GreenHarvest", "Kobo", "KOBO-001", "Depot", "f1f1f1f1"]) expect(text(document.body)).not.toContain(stale);
      expect(document.querySelectorAll("[data-portfolio-row], [data-portfolio-card]")).toHaveLength(0);
      view.unmount();
    }
  });

  it("appendsOnlyFindingRowsOnLoadMore", async () => {
    const extra = row({ finding_id: "f3f3f3f3-0000-4000-8000-000000000003", finding_revision_id: "e3e3e3e3-0000-4000-8000-000000000003" });
    const pageTwo = portfolioBody({ rows: [extra], next_cursor: null, value_cards: [], objectives: [] });
    const client = withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody({ next_cursor: "c1" })), loadedPortfolio(pageTwo)));
    renderAt(ACT, client);
    await settledScreen();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Load more Findings" }));
    });
    expect(document.querySelectorAll("[data-portfolio-row]")).toHaveLength(3);
    expect(screen.queryByRole("button", { name: "Load more Findings" })).toBeNull();
    showTab("Overview");
    expect(document.querySelectorAll("[data-portfolio-card]")).toHaveLength(4);
    // OUT-B B6 (R521): the outcome matrix (4 categories x 4 Sites) stays; Load more does not re-read the summary.
    showTab("Outcomes by site");
    expect(document.querySelectorAll("[data-portfolio-outcome-cell]")).toHaveLength(16);
    expect(client.summaryCalls).toHaveLength(1);
  });

  it("ch4_opportunity_panel_none_reads_nothing_found_and_links_to_findings_opportunities", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const opportunity = panel("An opportunity beyond reducing cost");
    expect(opportunity.getAttribute("data-portfolio-opportunity-state")).toBe("NONE");
    expect(text(opportunity)).toContain("GROW USEFUL DEMAND");
    expect(text(opportunity.querySelector("[data-portfolio-opportunity-quantity]"))).toBe(
      "No opportunity found in this periodNothing seen on days with complete readings",
    );
    expect(text(opportunity)).toContain("No what-if yet");
    expect(text(opportunity)).toContain("No what-if value worked out yet");
    expect(text(opportunity)).not.toMatch(/scenario/i);
    expect(text(opportunity.querySelector("[data-portfolio-opportunity-note]"))).toBe(
      "A what-if needs reviewed physical headroom, demand and an agreed cost assumption.",
    );
    const links = within(opportunity).getAllByRole("link");
    expect(links.map((l) => text(l))).toEqual(["Findings › Opportunities →"]);
    expect(links[0].getAttribute("href")).toMatch(/^\/findings\/opportunities\?from=/);
    expect(opportunity.querySelector("[data-gap-id], .portfolio-inert")).toBeNull();
    expect(opportunity.textContent).not.toContain("Not available yet");
  });

  it("ch4_opportunity_panel_found_shows_the_first_item_and_names_the_rest", async () => {
    const first = opportunityItem();
    const sized = opportunityItem({
      thread_id: "77777777-0000-4000-8000-000000000002",
      title: "Daytime solar unused at Kobo North",
      study: { ...first.study, status: "SUPPORTED", headroom_kw: { low: "18", high: "20" }, headroom_unit: "kW over 1 daylight hour" },
    });
    const found = (items: ReturnType<typeof opportunityItem>[]) =>
      portfolioBody({
        opportunity: { state: "FOUND", items, finding_id: null, scenario_amount: null, headroom: items[0].study.headroom_kw, destination: "/findings/opportunities" },
      });
    renderAt(ENTRY, portfolioClient(loadedPortfolio(found([first]))));
    await settledScreen();
    let opportunity = panel("An opportunity beyond reducing cost");
    expect(opportunity.getAttribute("data-portfolio-opportunity-state")).toBe("FOUND");
    expect(text(opportunity.querySelector("[data-portfolio-opportunity-quantity]"))).toBe("Size not worked out yetDaytime solar unused at Kobo");
    expect(text(opportunity)).toContain("No what-if yet");
    expect(text(opportunity.querySelector("[data-portfolio-opportunity-note]"))).toBe(
      "Seen on 2 of 4 well-observed days · 28 Oct–1 Nov · Limited evidence: readings come from mixed sources, so the size is not worked out yet",
    );
    let links = within(opportunity).getAllByRole("link");
    expect(links.map((l) => text(l))).toEqual(["Review opportunity Finding →", "Inspect physical headroom →"]);
    expect(links[0].getAttribute("href")).toBe(first.links.opportunity);
    expect(links[1].getAttribute("href")).toBe(first.links.evidence);
    cleanup();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(found([sized, first]))));
    await settledScreen();
    opportunity = panel("An opportunity beyond reducing cost");
    const quantity = opportunity.querySelector("[data-portfolio-opportunity-quantity]") as HTMLElement;
    // CH6b2-R Q7c: the unit is the server's `study.headroom_unit`, never browser-built and never "at midday".
    expect(text(quantity)).toBe("18–20 kW over 1 daylight hourDaytime solar unused at Kobo North");
    expect(text(quantity.querySelector(".opportunity-quantity small"))).toBe("kW over 1 daylight hour");
    expect(text(quantity)).not.toContain("midday");
    links = within(opportunity).getAllByRole("link");
    expect(links.map((l) => text(l))).toEqual([
      "Review opportunity Finding →",
      "Inspect physical headroom →",
      "1 more under Findings › Opportunities →",
    ]);
    expect(links[2].getAttribute("href")).toMatch(/^\/findings\/opportunities\?from=/);
    // Whatever unit the server sends is what renders (the server's own fallback wording).
    cleanup();
    const unhoured = { ...sized, study: { ...sized.study, window_hours: null, headroom_unit: "kW over daylight hours" } };
    renderAt(ENTRY, portfolioClient(loadedPortfolio(found([unhoured]))));
    await settledScreen();
    opportunity = panel("An opportunity beyond reducing cost");
    expect(text(opportunity.querySelector(".opportunity-quantity small"))).toBe("kW over daylight hours");
  });

  it("ch4_opportunity_panel_reads_an_older_body_as_none", async () => {
    const older = portfolioBody({
      opportunity: { state: "UNSUPPORTED", finding_id: null, scenario_amount: null, headroom: null, destination: null } as unknown as ReturnType<typeof portfolioBody>["opportunity"],
    });
    renderAt(ENTRY, portfolioClient(loadedPortfolio(older)));
    await settledScreen();
    const p = panel("An opportunity beyond reducing cost");
    expect(p.getAttribute("data-portfolio-opportunity-state")).toBe("NONE");
    expect(text(p)).toContain("No opportunity found in this period");
  });

  it("ch4_m1_opportunity_panel_says_a_failed_read_could_not_be_read_not_none", async () => {
    const failed = portfolioBody({
      opportunity: { state: "UNKNOWN", items: [], finding_id: null, scenario_amount: null, headroom: null, destination: "/findings/opportunities" } as unknown as ReturnType<typeof portfolioBody>["opportunity"],
    });
    renderAt(ENTRY, portfolioClient(loadedPortfolio(failed)));
    await settledScreen();
    const p = panel("An opportunity beyond reducing cost");
    expect(p.getAttribute("data-portfolio-opportunity-state")).toBe("UNKNOWN");
    expect(text(p)).toContain("Opportunities could not be read");
    expect(text(p)).not.toContain("No opportunity found");
    expect(text(p)).not.toContain("Nothing seen on days with complete readings");
  });

  it("rendersChangeDisclosureWithoutRecoveredMoney", async () => {
    const progressRow = (id: string, selected: boolean, origin?: boolean) => ({
      action_id: id,
      action_code: "A1",
      selected_action_event_id: "ev",
      verification_plan_id: null,
      verification_outcome_id: null,
      application_state: "APPLIED" as const,
      resolution_state: null,
      verification_outcome: null,
      recorded_at: "2026-10-06T10:00:00Z",
      origin_revision_selected: selected,
      ...(origin === undefined ? {} : { origin_selected: origin }),
    });
    // Page size 1 and a nonmatching lens: the disclosure uses the server boolean, never the paged Finding rows.
    const body = portfolioBody({
      lens: "opportunities",
      rows: [],
      total_count: 0,
      progress: { ...portfolioBody().progress, pending_trial_count: null, verified_resolution_count: 2, rows: [progressRow("act-1", true), progressRow("act-2", false), progressRow("act-3", false, true), progressRow("act-4", true, false)] },
    });
    renderAt(`${ENTRY}&lens=opportunities`, portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    const progress = panel("What changed in this review");
    expect(text(progress)).toContain("Completed activity · Not known yet");
    expect(text(progress)).toContain("Trials waiting for a result · Unknown");
    expect(text(progress)).toContain("Fixes confirmed · 2");
    expect(text(progress)).toContain("Recovered value not known yet");
    expect(text(progress)).toContain(
      "No previous comparable Portfolio snapshot is selected; change deltas and recovered-value trends are withheld.",
    );
    // CH-5a2 B6: `origin_selected` (thread + segment) decides when present; an older body falls back to the revision flag.
    expect(progress.querySelectorAll("[data-portfolio-origin-unselected]")).toHaveLength(2);
    expect(progress.querySelector("[data-portfolio-progress-row='act-3'] [data-portfolio-origin-unselected]")).toBeNull();
    expect(progress.querySelector("[data-portfolio-progress-row='act-4'] [data-portfolio-origin-unselected]")).not.toBeNull();
    expect(text(progress.querySelector("[data-portfolio-progress-row='act-2']"))).toContain("The version of the finding it came from is not the one selected");
    expect(text(progress.querySelector("[data-portfolio-progress-row='act-1']"))).not.toContain("The version of the finding it came from");
    // POLISH §3 ids: the raw action, event, plan and outcome ids sit only inside Technical details.
    for (const li of Array.from(progress.querySelectorAll("[data-portfolio-progress-row]"))) {
      expect(text(li.querySelector("[data-portfolio-progress-words]"))).not.toMatch(/act-|event|plan/);
      expect(li.querySelector("[data-technical-details]")?.textContent).toContain("event");
    }
    expect(text(progress)).not.toMatch(/\$|USD/);
  });

  it("rendersEmptyPendingHistoricalAndSourceConflict", async () => {
    const expected: Record<EstatePortfolioStatus, string> = {
      CURRENT: "Selected Site records",
      HISTORICAL: "Historical as of 30 Sep 2026, 00:00",
      PENDING: "Updating selected Sites",
      PARTIAL: "Some days incomplete",
      UNKNOWN: "Some Sites cannot be compared yet",
      EMPTY_SCOPE: "No accessible Sites",
    };
    const statuses = Object.keys(STATUS_BODIES) as EstatePortfolioStatus[];
    expect(statuses.sort()).toEqual(["CURRENT", "EMPTY_SCOPE", "HISTORICAL", "PARTIAL", "PENDING", "UNKNOWN"]);
    for (const status of statuses) {
      const view = renderAt(ACT, portfolioClient(loadedPortfolio(STATUS_BODIES[status])));
      await settledScreen();
      expect(document.querySelector("[data-portfolio-context]")?.getAttribute("data-portfolio-context")).toBe(status);
      expect(text(document.querySelector("[data-portfolio-context]"))).toContain(expected[status]);
      // PF-T: Act first holds the ranked panel; the other three panels are on their own tabs.
      expect(Array.from(document.querySelectorAll("section.panel")).map((p) => p.getAttribute("data-portfolio-panel"))).toEqual(["priority"]);
      if (status === "PENDING") expect(text(document.querySelector("[data-portfolio-row^='f2f2f2f2'] [data-portfolio-value]"))).toBe("Updating · Unpriced");
      if (status === "EMPTY_SCOPE") {
        expect(text(document.querySelector("[data-portfolio-count]"))).toBe("0 findings");
        expect(text(document.querySelector("[data-portfolio-panel='priority']"))).not.toMatch(/some days incomplete/i);
        expect(text(document.querySelector("[data-portfolio-empty]"))).toBe("No selected Findings for this window");
        expect(text(document.querySelector("[data-portfolio-domains]"))).toBe("0 accessible Sites · 0 mini-grid / 0 cold-chain / 0 EV charging");
      }
      view.unmount();
    }
    // A historical Site prefixes the first Value line and withholds the current amount.
    const historic = portfolioBody({
      coverage: { ...portfolioBody().coverage, sites: [coverageSite(SITES[0].site_id, "HISTORICAL")] },
    });
    const view = renderAt(ACT, portfolioClient(loadedPortfolio(historic)));
    await settledScreen();
    expect(text(document.querySelector("[data-portfolio-row^='f1f1f1f1'] [data-portfolio-value]"))).toBe("Historical · Value withheld");
    view.unmount();
  });

  it("optimizeCardRendersOnePricedSiteServerCard", async () => {
    // CH5d1-R 2.3: the summary's Optimize card, the one priced Site's cost claim; a WITHHELD body money line no
    // longer reaches the card (it stays on the wire, unrendered).
    const withheld = portfolioBody({
      value_cards: portfolioBody().value_cards.map((c) =>
        c.key === "OPERATING_COST" ? { ...c, state: "WITHHELD" as const, display_value: "Not comparable for this selection", tone: "neutral" as const } : c,
      ),
    });
    const answer = { status: "loaded" as const, value: outcomeSummaryBody({ cards: serverCards({ OPTIMIZE_COST: OPTIMIZE_ONE_SITE }) }) };
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(withheld)), answer));
    await settledScreen();
    const optimize = document.querySelector("[data-portfolio-card='OPTIMIZE_COST']") as HTMLElement;
    expect(text(optimize.querySelector("[data-portfolio-card-value]"))).toBe("3.31 USD possible extra fuel cost");
    expect(optimize.querySelector("[data-portfolio-card-value] small")?.textContent).toBe("possible extra fuel cost");
    expect(text(optimize.querySelector("[data-portfolio-card-detail]"))).toBe("At Kobo · not added across sites");
    expect(text(optimize.querySelector("[data-portfolio-card-basis]"))).toBe(
      "Modelled from the stored record and the declared price · not a saving",
    );
    expect(optimize.className).toContain("amber");
    expect(optimize.querySelector("[data-portfolio-card-days]")).toBeNull();
    expect(optimize.querySelector("[data-portfolio-card-note]")).toBeNull();
    expect(text(optimize)).not.toContain("Not comparable for this selection");
    expect(text(document.body)).not.toMatch(/\/api/);
  });

  it("optimizeCardRendersTheNoPricedSiteServerCard", async () => {
    const answer = { status: "loaded" as const, value: outcomeSummaryBody({ cards: serverCards({ OPTIMIZE_COST: OPTIMIZE_NONE }) }) };
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), answer));
    await settledScreen();
    const optimize = document.querySelector("[data-portfolio-card='OPTIMIZE_COST']") as HTMLElement;
    expect(text(optimize.querySelector("[data-portfolio-card-value]"))).toBe("Not known yet");
    expect(optimize.querySelector("[data-portfolio-card-value] small")).toBeNull();
    expect(text(optimize.querySelector("[data-portfolio-card-detail]"))).toBe("No cost worked out yet at any site");
    expect(text(optimize.querySelector("[data-portfolio-card-basis]"))).toBe("A cost needs a priced record");
    expect(optimize.className).toContain("neutral");
    expect(text(document.body)).not.toMatch(/\/api/);
  });

  it("preservesWindowAndCutoffAcrossGlobalRoots", async () => {
    renderAt(`${ENTRY}&known_at=2026-10-07T00:00:00Z&lens=cost`, portfolioClient(loadedPortfolio(portfolioBody({ lens: "cost" }))));
    await settledScreen();
    const tuple = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00Z";
    // PF-T: the lens address opens Act first; the card links are on the Overview. Collect both tabs' links.
    const hrefs = Array.from(document.querySelectorAll("a")).map((a) => a.getAttribute("href") ?? "");
    showTab("Overview");
    await settledScreen();
    hrefs.push(...Array.from(document.querySelectorAll("a")).map((a) => a.getAttribute("href") ?? ""));
    for (const root of ["/findings?", "/findings/risks?", "/evidence?", "/financials?"]) {
      const hit = hrefs.filter((h) => h.startsWith(root));
      expect(hit.length).toBeGreaterThan(0);
      for (const h of hit) {
        expect(h).toBe(`${root}${tuple}`);
        expect(h).not.toMatch(/cursor|lens/);
      }
    }
  });

  it("rendersEvFooterAndMissingEnergyBasis", async () => {
    const view = renderAt(tabEntry("scope"), portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const footer = () => document.querySelector("[data-portfolio-footer]") as HTMLElement;
    expect(text(footer())).toContain("Business context: Depot delivered 120 kWh in selected records; $36.00 at the recorded tariff, before costs (a what-if).");
    expect(footer()?.querySelector("[data-technical-details] [data-portfolio-footer-source]")).not.toBeNull();
    const basis = footer().querySelector("details") as HTMLDetailsElement;
    expect(text(basis.querySelector("summary"))).toBe("Energy basis ↗");
    fireEvent.click(basis.querySelector("summary") as HTMLElement);
    const basisText = text(basis);
    expect(basisText).toContain("Selected window: 6 Oct 2026, 08:00–16:00.");
    expect(basisText).toContain("Source basis");
    expect(basisText).toContain("Classification: SITE_RECORD");
    expect(basisText).toContain("State: KNOWN");
    expect(basisText).toContain("Source IDs: src-ev-1");
    expect(basisText).toContain("Evidence IDs: None selected");
    expect(basisText).toContain("Basis SHA-256: ab12cd34");
    expect(basisText).toContain("Reasons: WINDOW_SELECTED");
    expect(within(footer()).getByRole("link", { name: "Inspect energy basis →" }).getAttribute("href")).toBe("/sites/EV-LAB-001/ev/evidence");
    expect(text(footer().querySelector("[data-portfolio-footer-coverage]"))).toBe("Categories and windows remain separate.");
    view.unmount();
    // R12: no eligible footer line, and another applicable EV Site with UNKNOWN coverage.
    const body = portfolioBody({
      footer: null,
      coverage: { ...portfolioBody().coverage, sites: SITES.map((s, i) => coverageSite(s.site_id, i === 3 ? "UNKNOWN" : "CURRENT")) },
    });
    renderAt(tabEntry("scope"), portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    expect(text(footer())).toContain("Cross-Site energy and tariff totals are not known yet.");
    expect(text(footer())).toContain("Energy basis unavailable");
    expect(footer().querySelector("a")).toBeNull();
    expect(footer().querySelector("details")).toBeNull();
    expect(text(footer())).not.toContain("Energy basis ↗");
    expect(text(footer().querySelector("[data-portfolio-footer-coverage]"))).toBe("Other Sites may lack comparable full-window coverage.");
  });

  it("rendersMeasuredPanelHierarchyAndScrollContainers", async () => {
    const twin = row({
      finding_id: "f1f1f1f1-0000-4000-8000-0000000000aa",
      finding_revision_id: "e1e1e1e1-0000-4000-8000-0000000000aa",
      links: { ...row().links, finding: "/sites/KOBO-001/findings/aa" },
    });
    renderAt(ACT, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody({ rows: [row(), twin] })))));
    await settledScreen();
    const labels = Array.from(document.querySelectorAll("[data-portfolio-row] td:nth-child(2) small:first-of-type")).map(text);
    // POLISH §3.1: the mechanism words only; the Finding ids stay on the row attribute, never in the text.
    expect(labels).toEqual(["Possible extended generator support", "Possible extended generator support"]);
    const visible = document.querySelector("[data-portfolio-panel='priority']")!.cloneNode(true) as HTMLElement;
    visible.querySelectorAll("[data-technical-details]").forEach((e) => e.remove());
    expect(visible.textContent).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-|Finding KOBO-001/);
    expect(document.querySelectorAll("[data-portfolio-finding-link]")).toHaveLength(2);
    const main = document.querySelector(".estate-portfolio") as HTMLElement;
    // PF-T (v71 `portfolio-tabs.html` supersedes the v69 one-page composition): the date bar, title and context row
    // sit above the tab row, and the tab's panel follows it.
    const order = ["[data-portfolio-datebar]", "h1", "[data-portfolio-context]", "[data-portfolio-tabs]", "[data-portfolio-tab-panel]"];
    const nodes = order.map((sel) => main.querySelector(sel) as HTMLElement);
    nodes.forEach((n) => expect(n).not.toBeNull());
    for (let i = 1; i < nodes.length; i += 1) {
      expect(nodes[i - 1].compareDocumentPosition(nodes[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
    // Act first keeps the evidence prompt beside the ranked list (as in v70); the matrix has its own tab.
    const side = main.querySelector("[data-portfolio-side]") as HTMLElement;
    expect(side.querySelector("[data-portfolio-prompt]")).not.toBeNull();
    expect(side.querySelector("[data-portfolio-panel='objectives']")).toBeNull();
    expect(main.querySelector("[data-portfolio-scroll='findings'] table")).not.toBeNull();
    // Each v69 panel now sits on its own tab; each tab shows exactly its panel titles.
    const perTab: [string, string[]][] = [
      ["Overview", ["Overview", "Where management should act first"]],
      ["Act first", ["Where management should act first"]],
      ["Outcomes by site", ["Outcomes across the estate"]],
      ["Opportunity", ["An opportunity beyond reducing cost"]],
      ["What changed", ["What changed in this review"]],
      ["Scope & coverage", ["Scope & coverage"]],
    ];
    for (const [label, titles] of perTab) {
      showTab(label);
      expect(renderedPanelTitles(), label).toEqual(titles);
      expect(leadingIntruders(main, "portfolio"), `${label}: before panel 1`).toEqual([]);
      expect(strayOutsidePanels(main), `${label}: outside panels`).toEqual([]);
      expect(stripIntruders(main), `${label}: in a status strip`).toEqual([]);
      expect(strayBetweenPanels(main), `${label}: between panels`).toEqual([]);
      // Non-vacuity: a planted panel on this tab is rejected by the same checks, then removed.
      const first = main.querySelector("[data-portfolio-tab-panel] section.panel") as HTMLElement;
      const plant = document.createElement("section");
      plant.className = "panel";
      plant.innerHTML = "<h2>Planted extra panel</h2>";
      first.parentElement!.insertBefore(plant, first);
      try {
        expect(renderedPanelTitles(), `${label}: planted`).not.toEqual(titles);
      } finally {
        plant.remove();
      }
      expect(renderedPanelTitles(), `${label}: plant removed`).toEqual(titles);
    }
    showTab("Outcomes by site");
    // OUT-B B6 (R521): the outcome matrix replaces the objectives matrix in the same scroll container.
    expect(main.querySelector("[data-portfolio-scroll='objectives'] .oc-matrix")).not.toBeNull();
    expect(main.querySelector(".objective-matrix")).toBeNull();
    expect(COLD_ROW.links.finding).toBeNull();
  });
});

describe("post-W6 W3-estate Portfolio links, scope disclosure and refused window", () => {
  const WIN = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A05%3A00Z";
  // Q10: the server's mounted domain routes per objective (portfolio.py table); EV Backup has none.
  const ROUTES: Record<string, Record<string, string | null>> = {
    MINIGRID: {
      SERVICE_PRODUCT: "/sites/KOBO-001/performance/service",
      BACKUP: "/sites/KOBO-001/performance/backup",
      ASSET_CONDITION: "/sites/KOBO-001/health",
      COST_CONTROL: "/sites/KOBO-001/financials",
      EVIDENCE: "/sites/KOBO-001/evidence",
    },
    COLDCHAIN: {
      SERVICE_PRODUCT: "/sites/COLD-001/performance/temperature",
      BACKUP: "/sites/COLD-001/performance/backup",
      ASSET_CONDITION: "/sites/COLD-001/health",
      COST_CONTROL: `/sites/COLD-001/financials?${WIN}`,
      EVIDENCE: `/sites/COLD-001/evidence?${WIN}`,
    },
    EV_CHARGING: {
      SERVICE_PRODUCT: "/sites/EV-LAB-001/performance/sessions",
      BACKUP: null,
      ASSET_CONDITION: "/sites/EV-LAB-001/health",
      COST_CONTROL: `/sites/EV-LAB-001/ev/financials?${WIN}`,
      EVIDENCE: `/sites/EV-LAB-001/ev/evidence?${WIN}`,
    },
  };

  // OUT-B B6 (R521): the objectives wire (with its per-objective destinations) is no longer rendered; every outcome cell
  // opens its Site's overview at the server's `overview_href`, EV Sites at `/ev`.
  it("objectiveCellsLinkServerDestinationsAndEvBackupHasNoConfiguredObjective", async () => {
    const base = portfolioBody();
    const objectives = base.objectives.slice(0, 3).map((site) => ({
      ...site,
      cells: site.cells.map((cell) => ({ ...cell, destination: ROUTES[site.domain][cell.key] })),
    }));
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody({ objectives })))));
    await settledScreen();
    const outcomes = panel("Outcomes across the estate");
    expect(outcomes.querySelectorAll("[data-portfolio-cell-link]")).toHaveLength(0);
    for (const site of objectives) for (const c of site.cells) if (c.destination !== null) expect(outcomes.querySelector(`a[href='${c.destination}']`)).toBeNull();
    const summary = outcomeSummaryBody();
    for (const site of summary.sites) {
      const cells = Array.from(outcomes.querySelectorAll(`[data-portfolio-outcome-cell^='${site.site_code}|']`));
      expect(cells).toHaveLength(4);
      for (const el of cells) {
        expect(el.tagName).toBe("A");
        expect(el.getAttribute("href")).toBe(site.overview_href);
      }
    }
    expect(text(outcomes)).not.toContain("No configured objective");
  });

  it("coldAndEvFindingTitlesAreLiveOnlyWithAServerWindowedLink", async () => {
    const coldLink = `/sites/COLD-001/findings/${COLD_ROW.finding_id}?${WIN}`;
    const live = withLinkRefs({ ...COLD_ROW, links: { ...COLD_ROW.links, finding: coldLink } });
    const ev = row({
      site_id: SITES[2].site_id,
      site_code: "EV-LAB-001",
      site_name: "Depot",
      domain: "EV_CHARGING",
      finding_id: "f3f3f3f3-0000-4000-8000-000000000003",
      finding_revision_id: "e3e3e3e3-0000-4000-8000-000000000003",
      title: "Connector fault",
      links: { site: "/sites/EV-LAB-001/ev", finding: null, action: null },
    });
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ rows: [live, ev], total_count: 2 }))));
    await settledScreen();
    const priority = panel("Where management should act first");
    const coldRow = priority.querySelector("[data-portfolio-row^='f2f2f2f2']") as HTMLElement;
    expect(coldRow.querySelector("[data-portfolio-finding-link]")?.getAttribute("href")).toBe(coldLink);
    expect(text(coldRow)).not.toContain("Finding detail unavailable");
    const evRow = priority.querySelector("[data-portfolio-row^='f3f3f3f3']") as HTMLElement;
    expect(evRow.querySelector("[data-portfolio-finding-link]")).toBeNull();
    expect(text(evRow)).toContain("Finding detail unavailable");
    expect(evRow.querySelector("[data-portfolio-site-link]")?.getAttribute("href")).toBe("/sites/EV-LAB-001/ev");
  });

  it("rowWithoutLinkRefsRendersNoLinkWhateverItsLinksSay", async () => {
    // CH5a2-R4(c): the row keeps its legacy `links` text but carries no `link_refs`.
    const bare = row({ link_refs: {} });
    expect(bare.links.site).not.toBeNull();
    expect(bare.links.finding).not.toBeNull();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ rows: [bare], total_count: 1 }))));
    await settledScreen();
    const tr = panel("Where management should act first").querySelector("[data-portfolio-row]") as HTMLElement;
    expect(tr).not.toBeNull();
    expect(tr.querySelector("[data-portfolio-site-link]")).toBeNull();
    expect(tr.querySelector("[data-portfolio-finding-link]")).toBeNull();
    expect(tr.querySelectorAll("a[href^='/sites/']")).toHaveLength(0);
    expect(text(tr)).toContain("Finding detail unavailable");
  });

  it("scopeIdsLoadOnOpenShowsLoadingThenRefusalCopy", async () => {
    // CH-5c Q9: an honest loading state while the on-open read is in flight, and the refusal copy if it fails.
    const sites = portfolioBody().scope_disclosure.sites.map((s, i) => ({ ...s, selected_revision_count: i === 0 ? 2 : 0 }));
    let answer: (result: EstateResult<EstatePortfolioScopeIdsBody>) => void = () => undefined;
    const fake = {
      ...portfolioClient(loadedPortfolio(portfolioBody({ scope_disclosure: { sites, exclusions: [] } }))),
      portfolioScopeIds: () =>
        new Promise<EstateResult<EstatePortfolioScopeIdsBody>>((resolve) => {
          answer = resolve;
        }),
    };
    renderAt(tabEntry("scope"), fake);
    await settledScreen();
    const first = document.querySelector("[data-portfolio-drawer='scope'] [data-portfolio-scope-site] details") as HTMLDetailsElement;
    expect(first.querySelector("[data-portfolio-assessment-ids-loading]")).not.toBeNull(); // closed: nothing read yet
    fireEvent.click(first.querySelector("summary") as HTMLElement);
    await act(async () => {
      first.dispatchEvent(new Event("toggle"));
      await Promise.resolve();
    });
    expect(text(first.querySelector("[data-portfolio-assessment-ids-loading]"))).toBe("Assessment IDs…");
    expect(first.querySelector("[data-portfolio-assessment-ids]")).toBeNull();
    await act(async () => {
      answer({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "Estate records are unavailable right now. Try again." });
      await Promise.resolve();
    });
    expect(text(first.querySelector("[data-portfolio-assessment-ids-error]"))).toBe(
      "Estate records are unavailable right now. Try again.",
    );
    expect(first.querySelector("[data-portfolio-assessment-ids]")).toBeNull();
  });

  it("scopeDisclosureSummarisesAssessmentsTranslatesCodesAndNestsLongIds", async () => {
    const longIds = Array.from({ length: 60 }, (_, i) => `e1e1e1e1-0000-4000-8000-${String(i).padStart(12, "0")}`);
    const base = portfolioBody();
    const sites = base.scope_disclosure.sites.map((s, i) => ({
      ...s,
      selected_revision_count: i === 0 ? longIds.length : i === 1 ? 1 : 0,
      coverage: coverageSite(s.site_id, i === 3 ? "UNKNOWN" : "CURRENT"),
    }));
    const idsBody: EstatePortfolioScopeIdsBody = {
      schema_version: "estate-portfolio-scope-ids-1",
      window: null,
      sites: sites.map((s, i) => ({
        site_id: s.site_id,
        selected_revision_ids: i === 0 ? longIds : i === 1 ? ["e2e2e2e2-0000-4000-8000-000000000002"] : [],
      })),
    };
    const exclusions = [
      { line_key: "w1-line", group_key: "g-w1", reason_codes: ["UNPRICED"] },
      { line_key: "cold_chain:c9", group_key: null, reason_codes: ["SOMETHING_NEW"] },
    ];
    const idCalls: EstatePortfolioQuery[] = [];
    const fake = {
      ...portfolioClient(loadedPortfolio(portfolioBody({ scope_disclosure: { sites, exclusions } }))),
      portfolioScopeIds: (query: EstatePortfolioQuery) => {
        idCalls.push(query);
        return Promise.resolve({ status: "loaded", value: idsBody } as EstateResult<EstatePortfolioScopeIdsBody>);
      },
    };
    renderAt(tabEntry("scope"), fake);
    await settledScreen();
    const drawer = document.querySelector("[data-portfolio-drawer='scope']") as HTMLElement;
    const summary = (code: string) => text(drawer.querySelector(`[data-portfolio-scope-site='${code}'] [data-portfolio-scope-summary]`));
    expect(summary("KOBO-001")).toBe("Kobo · 60 selected assessments");
    expect(summary("COLD-001")).toBe("GreenHarvest · 1 selected assessment");
    expect(summary("EV-LAB-001")).toBe("Depot · No selected assessment");
    // The IDs are inside a nested `Assessment IDs` disclosure with its own scroll box, never in the summary.
    const kobo = drawer.querySelector("[data-portfolio-scope-site='KOBO-001']") as HTMLElement;
    expect(summary("KOBO-001")).not.toContain("e1e1e1e1");
    const ids = kobo.querySelector("details") as HTMLDetailsElement;
    const idsSummary = ids.querySelector("summary") as HTMLElement;
    expect(idsSummary.textContent).toBe("Assessment IDs");
    expect(ids.firstElementChild).toBe(idsSummary); // the native summary is the keyboard toggle
    expect(ids.open).toBe(false);
    // CH-5c Q9: nothing is read until the disclosure opens; then one scope-ids read for the same window and lens.
    expect(idCalls).toHaveLength(0);
    idsSummary.focus();
    expect(document.activeElement).toBe(idsSummary);
    fireEvent.click(idsSummary);
    expect(ids.open).toBe(true);
    await act(async () => {
      ids.dispatchEvent(new Event("toggle"));
      await Promise.resolve();
    });
    expect(idCalls).toHaveLength(1);
    expect(idCalls[0]).toMatchObject({ from: fake.calls[0].from, to: fake.calls[0].to, lens: fake.calls[0].lens });
    await settledScreen();
    expect(kobo.querySelectorAll("[data-portfolio-assessment-ids] > div")).toHaveLength(60);
    expect(kobo.querySelector("[data-portfolio-assessment-ids]")?.textContent).toContain(longIds[59]);
    expect(drawer.querySelector("[data-portfolio-scope-site='EV-LAB-001'] details")).toBeNull();
    // Coverage words, not raw states.
    expect(text(drawer.querySelector("[data-portfolio-scope-site='EV-LAB-002'] [data-portfolio-scope-coverage]"))).toBe(
      "EV charging · Not yet assessed",
    );
    expect(text(drawer.querySelector("[data-portfolio-scope-site='KOBO-001'] [data-portfolio-scope-coverage]"))).toContain("Mini-grid · Current");
    const coverageText = Array.from(drawer.querySelectorAll("[data-portfolio-scope-coverage]")).map((td) => td.textContent).join(" ");
    expect(coverageText).not.toMatch(/UNKNOWN|CURRENT/);
    // Exclusions: Site/line label and reason words; an unknown code reads `Excluded from comparison`, raw in detail.
    const items = Array.from(drawer.querySelectorAll("[data-portfolio-exclusion]")) as HTMLElement[];
    expect(items.map((li) => text(li.querySelector("[data-portfolio-exclusion-words]")))).toEqual([
      "Kobo · No price is recorded",
      "Cold-chain line · Excluded from comparison",
    ]);
    expect(items[1].querySelector("details summary")?.textContent).toBe("Technical details");
    expect(items[1].querySelector("details")?.hasAttribute("data-technical-details")).toBe(true);
    expect(ids.hasAttribute("data-technical-details")).toBe(true);
    expect(items[1].querySelector("details")?.textContent).toContain("cold_chain:c9 · no group · SOMETHING_NEW");
    // CSS: 160px inner scroll for the IDs; the drawer keeps 320px.
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const css = fs.readFileSync(`${cwd}/src/estate/estatePortfolio.css`, "utf8");
    expect(css).toMatch(/\.portfolio-scope-ids\{max-height:160px;overflow:auto/);
    expect(css).toMatch(/\.portfolio-drawer\{max-height:320px;overflow:auto/);
  });

  it("refusedWindowUsesTheSharedSentencesAndNeverEchoesDates", async () => {
    const cases: [string, string][] = [
      ["/portfolio?from=2026-10-07T00:00:00Z&to=2026-10-05T00:00:00Z", "The selected window needs both a start and an end, with the start before the end."],
      ["/portfolio?from=2026-08-01T00:00:00Z&to=2026-10-01T00:00:00Z", "The selected window is longer than 31 days."],
      [ENTRY, "The selected window is invalid."],
    ];
    for (const [entry, copy] of cases) {
      const view = renderAt(entry, portfolioClient(refused(422, "INVALID_WINDOW", "server copy")));
      await settledScreen();
      expect(text(document.querySelector("[data-page-refusal='INVALID_WINDOW'] p"))).toBe(copy);
      expect(text(document.querySelector("[data-page-refusal='INVALID_WINDOW'] [data-refusal-title]"))).toBe("Window cannot be read");
      expect(text(document.querySelector("[data-estate-window]"))).toBe("Window not valid");
      expect(text(document.querySelector("[data-estate-date-bar]"))).not.toContain("2026-10-07 to");
      view.unmount();
    }
    // A non-window refusal keeps its own copy and the requested window line.
    const view = renderAt(ENTRY, portfolioClient(refused(503, "ESTATE_STORE_UNAVAILABLE", "Estate records are unavailable right now. Try again.")));
    await settledScreen();
    expect(text(document.querySelector("[data-page-refusal]"))).toBe("Estate records are unavailable right now. Try again.");
    expect(text(document.querySelector("[data-estate-window]"))).toBe("6 Oct 2026");
    view.unmount();
  });
});

describe("CC-R2 Portfolio placement groups (D5)", () => {
  const groupHeads = () =>
    Array.from(document.querySelectorAll("tr.placement-group")).map((tr) => [tr.getAttribute("data-placement-group"), text(tr)]);

  it("headsEachGroupOnceWithItsCountAndShowsEveryRowsReasonLine", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const priority = panel("Where management should act first");
    expect(groupHeads()).toEqual([
      ["ACT_NOW", "Act now · 1"],
      ["COMPARE_VALUE", "Compare value · 1"],
    ]);
    const head = priority.querySelector("tr.placement-group th") as HTMLElement;
    expect(head.getAttribute("scope")).toBe("colgroup");
    expect(head.getAttribute("colspan")).toBe("6");
    // Every row: a group heading precedes it and its Placement cell has the group label and the reason line.
    const body = Array.from(priority.querySelectorAll("tbody tr"));
    expect(body.map((tr) => (tr.classList.contains("placement-group") ? "head" : tr.getAttribute("data-portfolio-row")?.slice(0, 8)))).toEqual([
      "head",
      "f2f2f2f2",
      "head",
      "f1f1f1f1",
    ]);
    const cold = priority.querySelector("[data-portfolio-row^='f2f2f2f2'] [data-portfolio-placement]") as HTMLElement;
    expect(cold.getAttribute("data-portfolio-placement")).toBe("ACT_NOW");
    expect(lines(cold)).toBe("Act now No end is recorded for this episode · No action agreed yet · review the recommendation");
    for (const cell of Array.from(priority.querySelectorAll("[data-portfolio-placement-reasons]"))) {
      expect(text(cell)).not.toBe("");
      expect(text(cell)).not.toMatch(/saving|saved/i);
    }
    expect(Array.from(priority.querySelectorAll("[data-portfolio-confidence]")).map((c) => c.getAttribute("data-portfolio-confidence"))).toEqual([
      "SUPPORTED_SOURCE_COHERENT",
      "SUPPORTED_SOURCE_COHERENT",
    ]);
    // R5.3: the policy text is reachable from the panel, closed by default.
    const policy = priority.querySelector("[data-placement-policy]") as HTMLDetailsElement;
    expect(policy.open).toBe(false);
    expect(text(policy.querySelector("summary"))).toBe("How placement works");
    expect(Array.from(policy.querySelectorAll("li")).map(text)).toEqual([
      "Needs investigation first: the evidence source is mixed or unresolved, the Finding is unconfirmed, or its cost is withheld.",
      "Act now: the episode is open, returned or reopened, and no Action is underway or its resolution was withdrawn.",
      "Monitor (checked next): a change was applied or verified.",
      "Compare value: the Finding has a priced cost exposure.",
      "Unpriced risk: the Finding has no price basis.",
    ]);
    expect(text(policy.querySelector("p"))).toBe(
      "Groups say where to look first; they are not a value ranking. Within a group, most recent first. Policy estate-placement/1.",
    );
    expect(text(priority)).not.toMatch(/\bscore\b/i);
  });

  it("DIESEL-1-R3p: a verified fuel Finding row shows its own interval, the server's Verified and its fuel page link", async () => {
    const fid = "f7f7f7f7-0000-4000-8000-000000000007";
    const href = `/sites/KOBO-001/fuel-findings/${fid}`;
    const fuel = row({
      finding_id: fid,
      finding_revision_id: "e7e7e7e7-0000-4000-8000-000000000007",
      finding_label: "Unexplained fuel overnight",
      title: "Unexplained fuel overnight",
      mechanism: "UNEXPLAINED_FUEL",
      lens_flags: ["RISK"],
      placement: {
        policy_version: "estate-placement/1",
        group: "MONITOR",
        group_rank: 5,
        reasons: [{ code: "VERIFIED_WATCH_RETURN", text: "Verified; watch for a return" }],
      },
      consequence: { state: "PRICED", amount: "41.25", amount_low: "41.25", amount_high: "57.75", currency: "USD", source_revision_id: "c7c7c7c7-0000-4000-8000-000000000007" },
      workflow_label: "Verified",
      links: { site: "/sites/KOBO-001", finding: href, action: null },
      link_refs: { site: { kind: "SITE", site: "KOBO-001" }, finding: { kind: "FUEL_FINDING", site: "KOBO-001", id: fid }, action: null },
    });
    renderAt(ACT, portfolioClient(loadedPortfolio(portfolioBody({ rows: [fuel] }))));
    await settledScreen();
    const tr = document.querySelector(`[data-portfolio-row^='f7f7f7f7']`) as HTMLElement;
    expect(tr).not.toBeNull();
    expect(text(tr)).toContain("$41.25–$57.75");
    expect(text(tr)).toContain("MonitorVerified; watch for a return");
    expect(text(tr)).not.toContain("No action yet");
    expect(text(tr.querySelectorAll("td")[5] as HTMLElement)).toBe("VerifiedReview finding");
    expect(tr.querySelectorAll("[data-portfolio-workflow]").length).toBe(1);
    const anchor = Array.from(tr.querySelectorAll("a")).find((a) => a.getAttribute("href") === href);
    expect(anchor?.textContent).toContain("Unexplained fuel overnight");
    // K8 coordinator ruling: the mechanism line names the recorded mechanism, never "Mechanism not recorded".
    expect(mechanismWords("UNEXPLAINED_FUEL")).toBe("Unexplained fuel overnight");
    expect(Array.from(tr.querySelectorAll("small")).map(text)).toContain("Unexplained fuel overnight");
    expect(text(tr)).not.toContain("Mechanism not recorded");
    const { violations } = scanProductVocabulary(tr, "portfolio fuel row");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("MD-FUEL-K4-1: a fuel row with no thread keeps the no-action fallback", async () => {
    const fid = "f8f8f8f8-0000-4000-8000-000000000008";
    const fuel = row({
      finding_id: fid,
      finding_revision_id: "e8e8e8e8-0000-4000-8000-000000000008",
      mechanism: "UNEXPLAINED_FUEL",
      workflow_label: "No action agreed yet",
      links: { site: "/sites/KOBO-001", finding: `/sites/KOBO-001/fuel-findings/${fid}`, action: null },
      link_refs: { site: { kind: "SITE", site: "KOBO-001" }, finding: { kind: "FUEL_FINDING", site: "KOBO-001", id: fid }, action: null },
    });
    renderAt(ACT, portfolioClient(loadedPortfolio(portfolioBody({ rows: [fuel] }))));
    await settledScreen();
    const tr = document.querySelector(`[data-portfolio-row^='f8f8f8f8']`) as HTMLElement;
    expect(tr).not.toBeNull();
    expect(text(tr)).toContain("No action yetNo action agreed yet");
  });

  it("R4.1: a Cold row with a thread state shows it in bold; one with no action agreed keeps the no-action text", async () => {
    const link = (fid: string) => ({
      links: { site: "/sites/COLD-001", finding: `/sites/COLD-001/findings/${fid}`, action: null },
      link_refs: {
        site: { kind: "SITE" as const, site: "COLD-001" },
        finding: { kind: "FUEL_FINDING" as const, site: "COLD-001", id: fid },
        action: null,
      },
    });
    const pending = row({
      finding_id: "c1c1c1c1-0000-4000-8000-000000000001",
      finding_revision_id: "d1d1d1d1-0000-4000-8000-000000000001",
      mechanism: "COLD_START_FAILURE",
      action_id: null,
      workflow_label: "Pending",
      ...link("c1c1c1c1-0000-4000-8000-000000000001"),
    });
    const none = row({
      finding_id: "c2c2c2c2-0000-4000-8000-000000000002",
      finding_revision_id: "d2d2d2d2-0000-4000-8000-000000000002",
      mechanism: "COLD_EXCURSION",
      action_id: null,
      workflow_label: "No action agreed yet",
      ...link("c2c2c2c2-0000-4000-8000-000000000002"),
    });
    renderAt(ACT, portfolioClient(loadedPortfolio(portfolioBody({ rows: [pending, none] }))));
    await settledScreen();
    const p = document.querySelector(`[data-portfolio-row^='c1c1c1c1']`) as HTMLElement;
    const cell = p.querySelectorAll("td")[5] as HTMLElement;
    expect(cell.querySelector("strong[data-portfolio-workflow]")?.textContent).toBe("Pending");
    expect(text(cell)).not.toContain("No action yet");
    expect(text(cell)).toContain("Review finding");
    const n = document.querySelector(`[data-portfolio-row^='c2c2c2c2']`) as HTMLElement;
    expect(text(n)).toContain("No action yetNo action agreed yet");
  });

  it("namesOnePrioritySiteInTheSingular", async () => {
    const base = portfolioBody();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ summary: { ...base.summary, priority_site_count: 1 } }))));
    await settledScreen();
    const pulse = text(document.querySelector("[data-portfolio-pulse]"));
    expect(pulse).toContain("1 priority site");
    expect(pulse).not.toContain("priority sites");
  });

  it("omitsTheCountWhenPlacementCountsAreNull", async () => {
    const counts = { NEEDS_INVESTIGATION: null, ACT_NOW: null, COMPARE_VALUE: null, UNPRICED_RISK: null, MONITOR: null };
    const base = portfolioBody();
    renderAt(ACT, portfolioClient(loadedPortfolio(portfolioBody({ summary: { ...base.summary, placement_counts: counts } }))));
    await settledScreen();
    expect(groupHeads()).toEqual([
      ["ACT_NOW", "Act now"],
      ["COMPARE_VALUE", "Compare value"],
    ]);
  });

  it("showsAGroupSplitAcrossPagesOnce", async () => {
    const extra = row({ finding_id: "f3f3f3f3-0000-4000-8000-000000000003", finding_revision_id: "e3e3e3e3-0000-4000-8000-000000000003" });
    const pageTwo = portfolioBody({ rows: [extra], next_cursor: null, value_cards: [], objectives: [] });
    const client = portfolioClient(loadedPortfolio(portfolioBody({ next_cursor: "c1" })), loadedPortfolio(pageTwo));
    renderAt(ACT, client);
    await settledScreen();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Load more Findings" }));
    });
    await settledScreen();
    expect(document.querySelectorAll("[data-portfolio-row]")).toHaveLength(3);
    expect(groupHeads()).toEqual([
      ["ACT_NOW", "Act now · 1"],
      ["COMPARE_VALUE", "Compare value · 1"],
    ]);
  });
});

describe("CC-R2-Q1 placement and confidence words", () => {
  const REASONS = [
    "Evidence comes from mixed sources; check the source before acting",
    "Evidence source is not resolved; check the source before acting",
    "The latest assessment no longer confirms this finding; check its basis",
    "Cost is withheld because its basis is not current",
    "No end is recorded for this episode",
    "Returned after an earlier episode (Finding 1a2b3c4d)",
    "Reopened after it had closed",
    "No action agreed yet · review the recommendation",
    "Action accepted, not yet applied",
    "Change applied; verification result pending",
    "Earlier resolution withdrawn after new evidence",
    "Priced cost exposure; compares with like lines in Financials",
    "Priced cost exposure; no like line to compare with",
    "Product temperature risk; no price basis",
    "Backup start failure; no price basis",
    "Charging service interruption; no price basis",
    "No price basis for this finding",
    "Change verified on example data; watch for it coming back",
    "Change applied; no verified result yet",
    "No open signal",
  ];
  const CONFIDENCE: [string, string[]][] = [
    ["SUPPORTED_SOURCE_COHERENT", ["Supported finding", "example data"]],
    ["LIMITED", ["Unconfirmed finding", "Prepared example data source", "Cost basis withheld"]],
    ["UNKNOWN", ["Supported finding", "Mixed sources", "Site coverage incomplete; other findings may be missing"]],
    ["UNKNOWN", ["Unconfirmed finding", "Source not resolved"]],
  ];

  it("everyPlacementAndConfidenceTextIsFreeOfGuardedWords", async () => {
    const groups = ["NEEDS_INVESTIGATION", "ACT_NOW", "COMPARE_VALUE", "MONITOR"] as const;
    const rows = CONFIDENCE.map(([confidence, reasons], i) =>
      row({
        finding_id: `f${i}f${i}f${i}f${i}-0000-4000-8000-00000000000${i}`,
        finding_revision_id: `e${i}e${i}e${i}e${i}-0000-4000-8000-00000000000${i}`,
        placement: {
          policy_version: "estate-placement/1",
          group: groups[i],
          group_rank: i + 1,
          reasons: REASONS.slice(i * 5, i * 5 + 5).map((t) => ({ code: `C${i}`, text: t })),
        },
        confidence,
        confidence_reasons: reasons,
      }),
    );
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ rows, total_count: rows.length }))));
    await settledScreen();
    const priority = panel("Where management should act first");
    expect(priority.querySelectorAll("[data-portfolio-row]")).toHaveLength(4);
    const shown = text(priority);
    for (const t of [...REASONS, ...CONFIDENCE.flatMap(([, r]) => r)]) expect(shown).toContain(t);
    expect(forbiddenPhrases(priority.textContent ?? "")).toEqual([]);
  });
});

describe("OUT-A A6: Portfolio outcome category cards", () => {
  const card = (key: string) => document.querySelector(`[data-portfolio-card='${key}']`) as HTMLElement;
  const value = (key: string) => text(card(key).querySelector("[data-portfolio-card-value]"));

  it("fourCardsInOrderWithIconNameDefinitionAndExactCopy", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    const cards = Array.from(document.querySelectorAll("[data-portfolio-cards] [data-portfolio-card]"));
    expect(cards).toHaveLength(4);
    expect(
      cards.map((c) => [
        c.getAttribute("data-portfolio-card"),
        text(c.querySelector("[data-portfolio-card-name]")),
        text(c.querySelector("[data-portfolio-card-definition]")),
        c.querySelector("svg[role='img']")?.getAttribute("aria-label"),
      ]),
    ).toEqual([
      ["GROW_REVENUE", "Grow revenue", "Capture more value from existing infrastructure and expand earning potential", "Grow revenue"],
      ["OPTIMIZE_COST", "Optimize cost and efficiency", "Eliminate avoidable expenditure and get more output from operational resources", "Optimize cost and efficiency"],
      ["PROTECT_ASSET", "Protect asset and capital", "Preserve asset value, avoid premature replacement and reduce service disruption", "Protect asset and capital"],
      ["ASSURE_PERFORMANCE", "Assure performance and returns", "Establish with defensible evidence whether the infrastructure is delivering expected results", "Assure performance and returns"],
    ]);
    expect(document.querySelector("[data-portfolio-cards]")?.classList.contains("oc-pfgrid")).toBe(true);
    // Grow (D1 R524; ruling A-Q9).
    expect(value("GROW_REVENUE")).toBe("Not available yet");
    expect(text(card("GROW_REVENUE").querySelector("[data-portfolio-card-detail]"))).toBe("Site income not recorded");
    expect(text(card("GROW_REVENUE").querySelector("[data-portfolio-card-basis]"))).toBe("Opportunities · revenue not measured yet");
    expect(card("GROW_REVENUE").className).toContain("neutral");
    // Protect.
    expect(text(card("PROTECT_ASSET").querySelector("[data-portfolio-card-detail]"))).toBe("Service disruptions recorded as findings · loss not priced");
    expect(text(card("PROTECT_ASSET").querySelector("[data-portfolio-card-basis]"))).toBe("Measured events, counted separately · loss not priced");
    expect(card("PROTECT_ASSET").className).toContain("red");
    // Assure: the server card's words, rendered verbatim.
    expect(value("ASSURE_PERFORMANCE")).toBe("Not known yet");
    expect(text(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-detail]"))).toBe(
      "Verified results not known yet · evidence gap at 1 site",
    );
    expect(text(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-basis]"))).toBe("Completed work does not establish savings");
    // Window kept on every link.
    for (const [key, root] of [
      ["GROW_REVENUE", "/findings/opportunities"],
      ["OPTIMIZE_COST", "/financials"],
      ["PROTECT_ASSET", "/findings/risks"],
      ["ASSURE_PERFORMANCE", "/evidence"],
    ]) {
      expect(card(key).querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toBe(`${root}?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z`);
    }
    // The w1 scan over the four whole cards (CH5d1-R: the Optimize card is server words now, scanned too).
    const grid = (document.querySelector("[data-portfolio-cards]") as HTMLElement).cloneNode(true) as HTMLElement;
    const scan = scanProductVocabulary(grid, "portfolio", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(10);
    expect(describeViolations(scan.violations)).toBe("");
    // PF-T: the Overview tab (v71) holds the cards, the strip and the top-3 panel; per-tab titles are pinned in
    // rendersMeasuredPanelHierarchyAndScrollContainers.
    expect(renderedPanelTitles()).toEqual(["Overview", "Where management should act first"]);
  });

  it("protectRendersTheServerValueSmallAndToneForEveryCount", async () => {
    const cases: [EstatePortfolioCard["value"], string, string, string | null][] = [
      [{ text: "2", small: "sites disrupted" }, "2 sites disrupted", "red", "sites disrupted"],
      [{ text: "1", small: "site disrupted" }, "1 site disrupted", "red", "site disrupted"],
      [{ text: "No sites disrupted", small: null }, "No sites disrupted", "neutral", null],
      [{ text: "Not assessed", small: null }, "Not assessed", "neutral", null],
    ];
    for (const [v, expected, tone, small] of cases) {
      const answer = { status: "loaded" as const, value: outcomeSummaryBody({ cards: serverCards({ PROTECT_ASSET: serverCard({ value: v, tone }) }) }) };
      const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), answer));
      await settledScreen();
      expect(value("PROTECT_ASSET")).toBe(expected);
      expect(card("PROTECT_ASSET").classList.contains(tone)).toBe(true);
      expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-value] small")?.textContent ?? null).toBe(small);
      view.unmount();
    }
  });

  it("optimizeValueIsTheServerCardNotTheBodyMoneyLine", async () => {
    // CH5d1-R: the body's OPERATING_COST line ("$3.31–$3.97" for this fixture) is no longer the card's value.
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    expect(value("OPTIMIZE_COST")).toBe("3.31 USD possible extra fuel cost");
    expect(text(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-detail]"))).toBe("At Kobo · not added across sites");
    expect(text(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-basis]"))).toBe(
      "Modelled from the stored record and the declared price · not a saving",
    );
    expect(card("OPTIMIZE_COST").className).toContain("amber");
    expect(text(card("OPTIMIZE_COST"))).not.toContain("$3.31–$3.97");
  });

  it("optimizeCardSaysNotKnownWhenTheSummaryIsMissing", async () => {
    // CH5d1-R: with no summary card the Optimize card says so (never a browser-built value), even when the body
    // carries no OPERATING_COST line; its link stays.
    const value_cards = portfolioBody().value_cards.filter((c) => c.key !== "OPERATING_COST");
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ value_cards }))));
    await settledScreen();
    expect(value("OPTIMIZE_COST")).toBe("Not known yet");
    expect(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-detail]")).toBeNull();
    expect(card("OPTIMIZE_COST").className).toContain("neutral");
    expect(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toBe(
      "/financials?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z",
    );
  });

  it("assureRendersTheServerDetailVerbatimForEveryGapShape", async () => {
    const cases = [
      "Verified results not known yet · evidence gaps at all 3 sites",
      "Verified results not known yet · evidence gaps at 2 of 4 sites",
      "Verified results not known yet · evidence gap at 1 site",
      "Verified results not known yet · no evidence gaps",
      "Verified results not known yet · evidence gaps not assessed",
    ];
    for (const detail of cases) {
      const answer = { status: "loaded" as const, value: outcomeSummaryBody({ cards: serverCards({ ASSURE_PERFORMANCE: serverCard({ detail }) }) }) };
      const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), answer));
      await settledScreen();
      expect(text(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-detail]"))).toBe(detail);
      view.unmount();
    }
  });

  // OUT-D U5 (R586, review M2): the Assure card clause from objective_site_count and objective_sites_unread.
  const targetsGap = "evidence gap at 1 site";
  async function expectAssureDetail(cases: [EstateOutcomeSummaryRead, string][]) {
    for (const [answer, expected] of cases) {
      const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), answer as never));
      await settledScreen();
      const detail = card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-detail]") as HTMLElement;
      expect(text(detail)).toBe(expected);
      expect(describeViolations(scanProductVocabulary(detail, "portfolio", { set: "w1" }).violations)).toBe("");
      view.unmount();
    }
  }




  it("assureTargetClausesAreServerTextAndSummaryNotLoadedHasNoDetail", async () => {
    const withDetail = (detail: string): EstateOutcomeSummaryRead => ({
      status: "loaded",
      value: outcomeSummaryBody({ cards: serverCards({ ASSURE_PERFORMANCE: serverCard({ detail }) }) }),
    });
    const same = (detail: string): [EstateOutcomeSummaryRead, string] => [withDetail(detail), detail];
    await expectAssureDetail([
      same(`No verified result yet · targets declared at 3 sites, for any outcome · ${targetsGap}`),
      same(`No verified result yet · no targets declared · ${targetsGap}`),
      same(`No verified result yet · targets declared at 2 sites, for any outcome, 1 site not checked · ${targetsGap}`),
      same(`No verified result yet · ${targetsGap}`),
    ]);
    // A refused summary: no server card, so no detail line at all (the browser writes none).
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }));
    await settledScreen();
    expect(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-detail]")).toBeNull();
    expect(value("ASSURE_PERFORMANCE")).toBe("Not known yet");
  });
});

describe("OUT-C U5: Portfolio early warnings", () => {
  const pulseWarnings = () => text(document.querySelector("[data-portfolio-pulse-warnings]"));
  const protectDetail = () => text(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-detail]"));
  const withWarnings = (warnings: OutcomeWarning[], protect = 0) => {
    const base = outcomeSummaryBody();
    const early = `${protect} early warning${protect === 1 ? "" : "s"}`;
    return outcomeSummaryBody({
      warnings,
      // CH-6b2: the Protect detail, with its early-warning clause, is one server line.
      cards: serverCards({
        PROTECT_ASSET: serverCard({
          value: { text: "2", small: "sites disrupted" },
          detail: `Service disruptions recorded as findings · ${early}, counted separately · loss not priced`,
        }),
      }),
      categories: base.categories.map((c) => (c.category === "PROTECT_ASSET" ? { ...c, warning_count: protect } : c)),
    });
  };
  const five = () => [
    outcomeWarning(),
    planWarning(),
    planWarning({ key: "PLAN_OVERDUE:p2", title: "Filter change overdue", site_name: "Kobo Mini-grid" }),
    planWarning({ key: "BATTERY_NEAR_RESERVE:b", title: "Battery at or near its reserve", site_name: "Kobo Mini-grid" }),
    planWarning({ key: "PEAK_NEAR_IMPORT_LIMIT:s", title: "Peak close to the import limit", site_name: "Depot Charging" }),
  ];

  it("pulseCountsSummaryWarningsAndTheListUnderTheTableShowsAtMostFourWithTheSite", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings(five(), 4) }));
    await settledScreen();
    expect(pulseWarnings()).toBe("5 warnings not yet priced");
    const pulse = document.querySelector("[data-portfolio-pulse]") as HTMLElement;
    expect(pulse.querySelector("[data-portfolio-pulse-warnings] + .pulse-note")).not.toBeNull();
    expect(pulse.querySelector("[data-portfolio-pulse-warnings] svg")).toBeNull();
    expect(protectDetail()).toBe("Service disruptions recorded as findings · 4 early warnings, counted separately · loss not priced");
    // PF-T: the warning list sits under the ranked table on Act first.
    showTab("Act first");
    const list = document.querySelector("[data-portfolio-panel='priority'] [data-early-warnings]") as HTMLElement;
    expect(list.previousElementSibling?.getAttribute("data-portfolio-scroll")).toBe("findings");
    const items = Array.from(list.querySelectorAll("li"));
    expect(items).toHaveLength(4);
    expect(text(items[0].querySelector("small"))).toMatch(/^GreenHarvest · Optimize cost and efficiency · /);
    expect(text(items[2].querySelector("small"))).toMatch(/^Kobo · /);
    expect(text(list)).not.toContain("Peak close to the import limit");
    expect(/[$€£]|\b(USD|EUR|GBP|KES|ETB)\b/.test(text(list))).toBe(false);
    expect(describeViolations(scanProductVocabulary(list, "portfolio", { set: "w1" }).violations)).toBe("");
  });

  it("oneWarningIsSingularAndZeroIsShownWithNoList", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings([planWarning()], 1) }));
    await settledScreen();
    expect(pulseWarnings()).toBe("1 warning not yet priced");
    expect(protectDetail()).toBe("Service disruptions recorded as findings · 1 early warning, counted separately · loss not priced");
    cleanup();
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings([], 0) }));
    await settledScreen();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(pulseWarnings()).toBe("0 warnings not yet priced");
    expect(protectDetail()).toBe("Service disruptions recorded as findings · 0 early warnings, counted separately · loss not priced");
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });

  it("summaryNotLoadedReadsUnknownAndTheProtectCardHasNoServerText", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }));
    await settledScreen();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(pulseWarnings()).toBe("Unknown warnings not yet priced");
    expect(text(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-value]"))).toBe("Not known yet");
    expect(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-detail]")).toBeNull();
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });

  // COV-PARTIAL U3 + PF-C1/PF-W: a Site with incomplete days never reads zero, Current or on track; its days are
  // stated once, in the coverage line above the tabs, in the D-E5.46 words.
  it("incompleteSiteNamesItsDaysOnceAndWithholdsValue", async () => {
    const body = partialBody();
    const kobo = body.scope_disclosure.sites[0].coverage.days!;
    kobo.gaps = [
      { day: "2026-10-11", state: "UNASSESSED", reason: "NO_READINGS" },
      { day: "2026-10-12", state: "UNASSESSED", reason: "NOT_ANALYSED" },
    ];
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(body)), { status: "loaded", value: outcomeSummaryBody({ coverage_line: COVERAGE_INCOMPLETE }) }));
    await settledScreen();
    const context = document.querySelector("[data-portfolio-context]") as HTMLElement;
    expect(context.getAttribute("data-portfolio-context")).toBe("PARTIAL");
    expect(text(context.querySelector(".portfolio-badge"))).toBe("Some days incomplete");
    expect(text(context.querySelector("[data-portfolio-sentence]"))).toBe("Portfolio: Some sites have incomplete days");
    expect(context.querySelector("[data-portfolio-partial]")).toBeNull(); // R620's per-Site notes are gone
    const line = await coverageLine();
    expect(line.getAttribute("data-portfolio-coverage")).toBe("INCOMPLETE");
    expect(text(line.querySelector("[data-portfolio-coverage-lead]"))).toBe("Some days have incomplete readings · 1 site with incomplete days");
    expect(Array.from(line.querySelectorAll("[data-portfolio-coverage-site]")).map(text)).toEqual([
      "Kobo: complete readings on 5 of 7 days · 1 with partial readings · 11 Oct: no readings · 12 Oct: not analysed yet",
      "GreenHarvest: complete readings on 7 of 7 days",
    ]);
    showTab("Scope & coverage");
    const drawer = document.querySelector("[data-portfolio-drawer='scope']") as HTMLElement;
    const cell = drawer.querySelector("[data-portfolio-scope-site='KOBO-001'] [data-portfolio-scope-coverage]");
    // review L1: the incomplete days sit on their own line under the coverage words
    const beforeBreak = Array.from(cell?.childNodes ?? []);
    expect(beforeBreak.slice(0, beforeBreak.findIndex((n) => n.nodeName === "BR")).map((n) => n.textContent).join("")).toBe(
      "Mini-grid · Incomplete days",
    );
    expect(cell?.querySelector("br + [data-portfolio-scope-gaps]")).not.toBeNull();
    expect(text(cell?.querySelector("[data-portfolio-scope-gaps]") ?? null)).toBe("Incomplete days: 11 Oct: no readings · 12 Oct: not analysed yet");
    showTab("Act first");
    expect(text(document.querySelector("[data-portfolio-row^='f1f1f1f1'] [data-portfolio-value]"))).toBe("Value not shown while this site has incomplete days");
    // the coverage line stays above the tabs on every tab
    expect(document.querySelectorAll("[data-portfolio-coverage]")).toHaveLength(1);
    // no state code on screen, in a title or in an aria-label; no "checked" for data anywhere on the page
    const page = document.body.textContent ?? "";
    expect(page).not.toMatch(/PARTIAL|UNASSESSED|NO_ASSESSED_SELECTION|NO_READINGS|NOT_ANALYSED|estate-coverage/);
    expect(page).not.toMatch(/days? checked|partly checked|not checked yet/i);
    const attrs = Array.from(document.querySelectorAll("[title],[aria-label]")).map((e) => `${e.getAttribute("title") ?? ""} ${e.getAttribute("aria-label") ?? ""}`);
    expect(attrs.join(" ")).not.toMatch(/PARTIAL|UNASSESSED|checked/i);
  });

  // D-E5.46: days sharing a reason are grouped; more than 3 gap days read as one count (the deep tab lists all).
  it("incompleteSiteWithManyGapsReadsACountAndTheScopeTabListsThem", async () => {
    const gaps = ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"];
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(partialBody(gaps, 14))), { status: "loaded", value: outcomeSummaryBody({ coverage_line: COVERAGE_INCOMPLETE }) }));
    await settledScreen();
    const line = await coverageLine();
    expect(text(line.querySelector("[data-portfolio-coverage-site]"))).toBe(
      "Kobo: complete readings on 5 of 7 days · 1 with partial readings · 4 days without a usable result",
    );
    showTab("Scope & coverage");
    // an older body's reason (NO_ASSESSED_SELECTION) reads as system work, never as a code
    expect(text(document.querySelector("[data-portfolio-scope-gaps]"))).toBe("Incomplete days: 1, 2, 3, 4 Oct: not analysed yet");
  });

  it("coverageLineCollapsesWhenEveryDayIsCompleteAndExplainsItsWords", async () => {
    const complete = { ...COVERAGE_INCOMPLETE, state: "COMPLETE" as const, lead: "Complete readings on every day" };
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: outcomeSummaryBody({ coverage_line: complete }) }));
    await settledScreen();
    const line = await coverageLine();
    expect(line.getAttribute("data-portfolio-coverage")).toBe("COMPLETE");
    expect(line.getAttribute("role")).toBe("note");
    expect(text(line.querySelector("[data-portfolio-coverage-lead]"))).toBe("Complete readings on every day");
    expect(line.querySelectorAll("[data-portfolio-coverage-site]")).toHaveLength(0);
    expect(Array.from(line.querySelectorAll("[data-portfolio-glossary] dt")).map(text)).toEqual([
      "Complete readings", "Partial readings", "Too few readings", "No readings received",
      "Not enough readings", "Conflicting readings", "Still processing", "Not analysed yet",
    ]);
    expect(line.querySelector("[data-portfolio-coverage-link]")?.getAttribute("href")).toContain("/portfolio/scope");
    // placement (v71): after the context row, before the tabs
    const order = ["[data-portfolio-context]", "[data-portfolio-coverage]", "[data-portfolio-tabs]"].map((s) => document.querySelector(s)!);
    expect(order[0].compareDocumentPosition(order[1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(order[1].compareDocumentPosition(order[2]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("coverageLineSaysNotKnownUntilTheSummaryLoads", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const line = document.querySelector("[data-portfolio-coverage]") as HTMLElement;
    expect(line.getAttribute("data-portfolio-coverage")).toBe("LOADING");
    expect(text(line.querySelector("[data-portfolio-coverage-lead]"))).toBe("Day readings are not known yet");
  });

  it("nonPartialBodiesShowNoGapLine", async () => {
    for (const body of [portfolioBody(), STATUS_BODIES.UNKNOWN]) {
      // PF-T: on the Scope & coverage tab, where the scope drawer (and its gap lines) render.
      const view = renderAt(tabEntry("scope"), portfolioClient(loadedPortfolio(body)));
      await settledScreen();
      expect(document.querySelector("[data-portfolio-drawer='scope']")).not.toBeNull();
      expect(document.querySelector("[data-portfolio-scope-gaps]")).toBeNull();
      view.unmount();
    }
  });
});

/** PF-C1: a server coverage line (Kobo incomplete, GreenHarvest complete), as `portfolio_coverage` builds it. */
const COVERAGE_INCOMPLETE = {
  state: "INCOMPLETE" as const,
  lead: "Some days have incomplete readings",
  rule: "Figures on this page count days with complete readings.",
  sites: [
    { site_code: "KOBO-001", site_name: "Kobo", complete: false, text: "Kobo: complete readings on 5 of 7 days · 1 with partial readings" },
    { site_code: "COLD-001", site_name: "GreenHarvest", complete: true, text: "GreenHarvest: complete readings on 7 of 7 days" },
  ],
  days_text: "Kobo: Complete readings on 5 of 7 days · 1 with partial readings · GreenHarvest: Complete readings on 7 of 7 days",
};

/** The coverage line once the summary read has settled (it loads after the Portfolio body). */
async function coverageLine(): Promise<HTMLElement> {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  return document.querySelector("[data-portfolio-coverage]") as HTMLElement;
}

describe("WALK1-1: checked days, verified count and Grow estimates", () => {
  const card = (key: string) => document.querySelector(`[data-portfolio-card='${key}']`) as HTMLElement;
  const value = (key: string) => text(card(key).querySelector("[data-portfolio-card-value]"));
  const detail = (key: string) => text(card(key).querySelector("[data-portfolio-card-detail]"));
  const basis = (key: string) => text(card(key).querySelector("[data-portfolio-card-basis]"));
  const pulse = () => text(document.querySelector("[data-portfolio-pulse]"));
  const protect = (n: number | null) => ({
    GROW_REVENUE: { open_findings: null, sites_with_primary_finding: null },
    OPTIMIZE_COST: { open_findings: null, sites_with_primary_finding: null },
    PROTECT_ASSET: { open_findings: n, sites_with_primary_finding: n },
    ASSURE_PERFORMANCE: { open_findings: null, sites_with_primary_finding: null },
  });
  type Summary = ReturnType<typeof portfolioBody>["summary"];
  const kobo: EstateCheckedDays = { site_id: "s-kobo", site_name: "Kobo", checked: 5, requested: 7 };
  const harbour: EstateCheckedDays = { site_id: "s-harbour", site_name: "Harbour", checked: 6, requested: 7 };
  const body = (patch: Partial<Summary>) => {
    const base = portfolioBody();
    return portfolioBody({ summary: { ...base.summary, ...patch } });
  };
  const checked = (n: number, days = [kobo], extra: Partial<Summary> = {}) =>
    body({ count_basis: "CHECKED_DAYS", checked_days: days, category_counts: protect(n), ...extra });
  const scanCards = () => {
    // CH5d1-R: the whole grid, the Optimize card's server words included.
    const grid = (document.querySelector("[data-portfolio-cards]") as HTMLElement).cloneNode(true) as HTMLElement;
    return describeViolations(scanProductVocabulary(grid, "portfolio", { set: "w1" }).violations);
  };

  const serverBody = (cards: NonNullable<EstateOutcomeSummaryBody["cards"]>, notes: Record<string, string | null> = {}, patch: Partial<Summary> = {}) => {
    const base = portfolioBody();
    return {
      page: portfolioBody({ summary: { ...base.summary, ...patch, card_notes: notes } }),
      answer: { status: "loaded" as const, value: outcomeSummaryBody({ cards: serverCards(cards) }) },
    };
  };
  const renderServer = (...args: Parameters<typeof serverBody>) => {
    const { page, answer } = serverBody(...args);
    return renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(page)), answer));
  };
  const dayText = (key: string) => text(card(key).querySelector("[data-portfolio-card-days]"));
  const noteText = (key: string) => text(card(key).querySelector("[data-portfolio-card-note]"));

  it("serverTextsRenderVerbatimOnCheckedDaysOneSite", async () => {
    const clause = "Kobo: Complete readings on 5 of 7 days";
    renderServer(
      {
        PROTECT_ASSET: serverCard({
          value: { text: "None found", small: "on days with complete readings" },
          detail: "Service disruptions recorded as findings · 0 early warnings, counted separately · loss not priced",
          days_line: clause,
        }),
        ASSURE_PERFORMANCE: serverCard({
          detail: "No verified result yet · no targets declared · no evidence gaps on the days assessed",
          days_line: clause,
        }),
      },
      { PROTECT_ASSET: "Findings next to unchecked days are not shown yet", ASSURE_PERFORMANCE: null },
      { count_basis: "CHECKED_DAYS", checked_days: [kobo], evidence_gap_site_count: 0 },
    );
    await settledScreen();
    expect(value("PROTECT_ASSET")).toBe("None found on days with complete readings");
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-value] small")?.textContent).toBe("on days with complete readings");
    expect(card("PROTECT_ASSET").className).toContain("neutral");
    expect(dayText("PROTECT_ASSET")).toBe(`Different days: ${clause}`);   // PF-C2: the exception label
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-days]")?.className).toContain("oc-pfdays");
    // CH6b2-R Q1: the Portfolio-body clause is its own line; the detail is the server's detail, not joined with it.
    expect(noteText("PROTECT_ASSET")).toBe("Findings next to unchecked days are not shown yet");
    expect(detail("PROTECT_ASSET")).not.toContain("not shown yet");
    expect(detail("ASSURE_PERFORMANCE")).toBe("No verified result yet · no targets declared · no evidence gaps on the days assessed");
    expect(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-note]")).toBeNull();
    // CH5d1-R: Optimize is the server cost card; a stored consequence has no days line, and no body note.
    expect(detail("OPTIMIZE_COST")).toBe("At Kobo · not added across sites");
    expect(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-days]")).toBeNull();
    expect(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-note]")).toBeNull();
    // The pulse strip keeps its own (non-card) checked-days wording.
    expect(pulse()).toContain("0 opportunities");
    expect(pulse()).toContain("Site evidence gaps: None found on the days assessed");
    expect(scanCards()).toBe("");
  });

  it("twoSiteDaysLineAndNonZeroCountRenderServerText", async () => {
    renderServer(
      { PROTECT_ASSET: serverCard({ value: { text: "2", small: "sites disrupted" }, tone: "red", days_line: "Kobo: Complete readings on 3 of 5 days · Harbour: Complete readings on 2 of 5 days" }) },
      {},
      { count_basis: "CHECKED_DAYS", checked_days: [kobo, harbour] },
    );
    await settledScreen();
    expect(value("PROTECT_ASSET")).toBe("2 sites disrupted");
    // PF-C2: a card days line is the exception to the coverage line, so it is labelled "Different days:"
    expect(dayText("PROTECT_ASSET")).toBe("Different days: Kobo: Complete readings on 3 of 5 days · Harbour: Complete readings on 2 of 5 days");
    expect(pulse()).toContain("0 opportunities");
    expect(pulse()).toContain("1 site evidence gaps");
  });

  it("withheldFindingsRenderTheServerValueAndNote", async () => {
    renderServer(
      { PROTECT_ASSET: serverCard({ value: { text: "None shown yet", small: null }, days_line: "Kobo: Complete readings on 5 of 7 days" }) },
      { PROTECT_ASSET: "Findings next to unchecked days are not shown yet" },
      { count_basis: "CHECKED_DAYS", checked_days: [{ ...kobo, withheld: true }], evidence_gap_site_count: 0 },
    );
    await settledScreen();
    expect(value("PROTECT_ASSET")).toBe("None shown yet");
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-value] small")).toBeNull();
    expect(noteText("PROTECT_ASSET")).toBe("Findings next to unchecked days are not shown yet");
    // CH-4: the opportunity count comes from the opportunity read, not from Finding coverage.
    expect(pulse()).toContain("0 opportunities");
    expect(pulse()).toContain("Site evidence gaps: None found on the days assessed");
    expect(scanCards()).toBe("");
  });

  it("completeBasisHasNoDaysLineAndNoNote", async () => {
    renderServer({ PROTECT_ASSET: serverCard({ value: { text: "No sites disrupted", small: null } }) }, {}, { count_basis: "COMPLETE", checked_days: [kobo] });
    await settledScreen();
    expect(value("PROTECT_ASSET")).toBe("No sites disrupted");
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-days]")).toBeNull();
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-note]")).toBeNull();
    expect(pulse()).toContain("0 opportunities");
  });

  it("pv1AssureCardRendersEachValueLineThenItsClauseAndTheBodyNoteAlone", async () => {
    // PV-1-R §2/§4: one server line per verified result (never a total), then the card's clause, then the body note.
    renderServer({ ASSURE_PERFORMANCE: ASSURE_WITH_VALUES }, { ASSURE_PERFORMANCE: "evidence gap at 1 site" });
    await settledScreen();
    const assure = card("ASSURE_PERFORMANCE");
    const lines = [...assure.querySelectorAll("[data-portfolio-card-value-line]")];
    expect(lines.map((n) => n.textContent)).toEqual(ASSURE_WITH_VALUES.value_lines);
    expect(lines.every((n) => n.className === "oc-pfnote")).toBe(true);
    expect(text(assure.querySelector("[data-portfolio-card-value-note]"))).toBe(ASSURE_WITH_VALUES.value_note);
    expect(noteText("ASSURE_PERFORMANCE")).toBe("evidence gap at 1 site");
    // Render order: detail, value lines, value note, body note.
    const order = [...assure.querySelectorAll("[data-portfolio-card-detail], [data-portfolio-card-value-line], [data-portfolio-card-value-note], [data-portfolio-card-note]")]
      .map((n) => [...n.attributes].map((a) => a.name).find((a) => a.startsWith("data-portfolio-card-")));
    expect(order).toEqual(["data-portfolio-card-detail", "data-portfolio-card-value-line", "data-portfolio-card-value-line", "data-portfolio-card-value-note", "data-portfolio-card-note"]);
    // No other card carries value lines.
    for (const key of ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET"]) {
      expect(card(key).querySelector("[data-portfolio-card-value-line], [data-portfolio-card-value-note]")).toBeNull();
    }
    expect(scanCards()).toBe("");
  });

  it("k4bProtectCardRendersEachFuelLineThenItsClauseAfterTheDetail", async () => {
    // DIESEL-1-R3j: one server line per unexplained-fuel Finding (never a total), then its clause.
    renderServer({ PROTECT_ASSET: PROTECT_WITH_FUEL });
    await settledScreen();
    const protect = card("PROTECT_ASSET");
    const lines = [...protect.querySelectorAll("[data-portfolio-card-fuel-line]")];
    expect(lines.map((n) => n.textContent)).toEqual(PROTECT_WITH_FUEL.fuel_lines);
    expect(lines.every((n) => n.className === "oc-pfnote")).toBe(true);
    expect(text(protect.querySelector("[data-portfolio-card-fuel-note]"))).toBe(PROTECT_WITH_FUEL.fuel_note);
    const order = [...protect.querySelectorAll("[data-portfolio-card-detail], [data-portfolio-card-fuel-line], [data-portfolio-card-fuel-note]")]
      .map((n) => [...n.attributes].map((a) => a.name).find((a) => a.startsWith("data-portfolio-card-")));
    expect(order).toEqual(["data-portfolio-card-detail", "data-portfolio-card-fuel-line", "data-portfolio-card-fuel-line", "data-portfolio-card-fuel-note"]);
    for (const key of ["GROW_REVENUE", "OPTIMIZE_COST", "ASSURE_PERFORMANCE"]) {
      expect(card(key).querySelector("[data-portfolio-card-fuel-line], [data-portfolio-card-fuel-note]")).toBeNull();
    }
    expect(scanCards()).toBe("");
  });

  it("k4bProtectCardWithoutOrWithEmptyKeysRendersNoFuelLine", async () => {
    renderServer({ PROTECT_ASSET: serverCard({ detail: "Service disruptions recorded as findings · loss not priced", fuel_lines: [], fuel_note: null }) });
    await settledScreen();
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-fuel-line], [data-portfolio-card-fuel-note]")).toBeNull();
  });

  it("pv1AssureCardWithoutTheKeysRendersNeitherLinesNorClause", async () => {
    renderServer({ ASSURE_PERFORMANCE: serverCard({ detail: "no targets declared" }) });
    await settledScreen();
    expect(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-value-line], [data-portfolio-card-value-note]")).toBeNull();
  });

  it("notKnownBasisRendersWithoutAnyClauseAndTheServerWordsStand", async () => {
    // CH6b2-R Q8: a body whose count_basis is NOT_KNOWN is a valid basis; the cards still render the server words.
    renderServer(
      { PROTECT_ASSET: serverCard({ value: { text: "Not assessed", small: null } }) },
      {},
      { count_basis: "NOT_KNOWN", checked_days: [] },
    );
    await settledScreen();
    expect(value("PROTECT_ASSET")).toBe("Not assessed");
    expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-days], [data-portfolio-card-note]")).toBeNull();
    expect(document.querySelector("[data-portfolio-cards]")).not.toBeNull();
  });

  it("bodyWithoutServerCardsOrNotesRendersNoBrowserBuiltText", async () => {
    // A body that predates `cards`/`card_notes` (or a summary that did not load): the browser writes no claim.
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: outcomeSummaryBody({ cards: undefined }) }));
    await settledScreen();
    for (const key of ["GROW_REVENUE", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
      expect(value(key)).toBe("Not known yet");
      expect(card(key).querySelector("[data-portfolio-card-detail], [data-portfolio-card-days], [data-portfolio-card-note], [data-portfolio-grow-parts]")).toBeNull();
    }
  });

  it("ch4_strip_counts_opportunities_from_the_opportunity_read_with_their_labels", async () => {
    // CH-4 (§5): one count from one source; the board's open signal is no longer named beside it.
    const opp = () => text(document.querySelector("[data-portfolio-pulse-opportunity]"));
    const strip = (extra: Partial<Summary>) => withOutcomeSummary(portfolioClient(loadedPortfolio(checked(0, [kobo], extra))));
    renderAt(ENTRY, strip({ opportunity_count: 1, opportunity_labels: ["Kobo daytime solar"] }));
    await settledScreen();
    expect(opp()).toBe("1 opportunity: Kobo daytime solar");
    expect(text(document.querySelector("[data-portfolio-pulse-opportunity] strong"))).toBe("1");
    expect(pulse()).not.toContain("open opportunity on its board");
    cleanup();
    renderAt(ENTRY, strip({ opportunity_count: 2, opportunity_labels: ["Kobo daytime solar", "Depot daytime solar"] }));
    await settledScreen();
    expect(opp()).toBe("2 opportunities: Kobo daytime solar · Depot daytime solar");
    cleanup();
    renderAt(ENTRY, strip({ opportunity_count: 0, opportunity_labels: [] }));
    await settledScreen();
    expect(opp()).toBe("0 opportunities");
    cleanup();
    renderAt(ENTRY, strip({ opportunity_count: null, opportunity_labels: null }));
    await settledScreen();
    expect(opp()).toBe("Unknown opportunities");
  });

  it("walk1_6_d4_card_dots_say_no_target_for_this_outcome", async () => {
    // WALK1-6 D4 (R697): the fixture's Kobo Protect row is NO_OBJECTIVE; its card dot reads per outcome.
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    const dot = card("PROTECT_ASSET").querySelector('[data-portfolio-dot^="KOBO-001|"]') as HTMLElement;
    expect(dot.getAttribute("title")).toBe("Kobo: No target for this outcome");
    expect(text(dot.querySelector(".oc-hidden"))).toContain("No target for this outcome");
    expect(text(card("PROTECT_ASSET"))).not.toContain("No objective declared");
    // Other states keep the server word.
    const other = card("PROTECT_ASSET").querySelector('[data-portfolio-dot^="COLD-001|"]') as HTMLElement;
    expect(other.getAttribute("title")).toContain(": Needs attention");
  });

  it("assureLeadIsTheServerDetailVerbatim", async () => {
    const leads = [
      "No verified result yet",
      "1 verified result",
      "2 verified results",
      "1 verified result, 1 site not checked",
      "Verified results not known yet",
    ];
    for (const lead of leads) {
      const answer = {
        status: "loaded" as const,
        value: outcomeSummaryBody({ cards: serverCards({ ASSURE_PERFORMANCE: serverCard({ detail: `${lead} · no targets declared · evidence gap at 1 site` }) }) }),
      };
      const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), answer));
      await settledScreen();
      expect(detail("ASSURE_PERFORMANCE")).toBe(`${lead} · no targets declared · evidence gap at 1 site`);
      expect(describeViolations(scanProductVocabulary(card("ASSURE_PERFORMANCE"), "portfolio", { set: "w1" }).violations)).toBe("");
      view.unmount();
    }
  });

  const growParts = (over: Partial<NonNullable<EstatePortfolioCard["parts"]>> = {}) => ({
    target: "Not declared",
    potential: "18–20 kW unused",
    income: "4.20 USD estimated",
    income_note: null,
    ...over,
  });
  const part = (name: string) => text(card("GROW_REVENUE").querySelector(`[data-portfolio-grow-part='${name}']`));

  it("growOneSiteEstimateRendersTheServerHeadlineAndThreeParts", async () => {
    renderServer({
      GROW_REVENUE: serverCard({
        value: { text: "4.20 USD", small: "estimated" },
        detail: "Depot 4.20 USD · each site's latest assessed period",
        basis_text: "Declared price × measured kWh · not billed or collected",
        tone: "green",
        parts: growParts({ income_note: "Not billed or collected" }),
      }),
    });
    await settledScreen();
    expect(value("GROW_REVENUE")).toBe("4.20 USD estimated");
    expect(card("GROW_REVENUE").querySelector("[data-portfolio-card-value] small")?.textContent).toBe("estimated");
    expect(detail("GROW_REVENUE")).toBe("Depot 4.20 USD · each site's latest assessed period");
    expect(basis("GROW_REVENUE")).toBe("Declared price × measured kWh · not billed or collected");
    expect(card("GROW_REVENUE").className).toContain("green");
    expect(card("GROW_REVENUE").querySelector("[data-portfolio-card-link]")?.getAttribute("href")).toMatch(/^\/findings\/opportunities\?/);
    // Mock v70 `pfGrowParts`: Target, Potential, Estimated income (+ its note), all server text.
    const parts = card("GROW_REVENUE").querySelector("dl.oc-pfgrow") as HTMLElement;
    expect(Array.from(parts.querySelectorAll("dt")).map((d) => d.textContent)).toEqual(["Target", "Potential", "Estimated income"]);
    expect(part("target")).toBe("Not declared");
    expect(part("potential")).toBe("18–20 kW unused");
    expect(part("income")).toBe("4.20 USD estimated");
    expect(text(parts.querySelector("dd.oc-pfnote"))).toBe("Not billed or collected");
    expect(scanCards()).toBe("");
  });

  it("growTwoSitesNamesEachAndTheBrowserNeverAdds", async () => {
    renderServer({
      GROW_REVENUE: serverCard({
        value: { text: "2 sites with an estimate", small: null },
        detail: "Kobo 1.50 USD · Depot 4.20 USD · each site's latest assessed period",
        tone: "green",
      }),
    });
    await settledScreen();
    expect(value("GROW_REVENUE")).toBe("2 sites with an estimate");
    expect(detail("GROW_REVENUE")).toBe("Kobo 1.50 USD · Depot 4.20 USD · each site's latest assessed period");
    expect(text(card("GROW_REVENUE"))).not.toContain("5.70");
    expect(card("GROW_REVENUE").querySelector("[data-portfolio-grow-parts]")).toBeNull();
    expect(scanCards()).toBe("");
  });

  it("growCardDomStructureFollowsV70 (CH6b2-R2 M2)", async () => {
    // Structure only: the 1440/390 captures are `not run` (owed at E5). v70 `pfGrowParts`: dl.oc-pfgrow holds Target,
    // Potential, then Estimated income with its dd.oc-pfnote; `oc-pfdays` is the days line.
    renderServer({
      GROW_REVENUE: serverCard({
        value: { text: "4.20 USD", small: "estimated" },
        days_line: "Kobo: 7 of 7 days checked",
        parts: growParts({ income_note: "Not billed or collected" }),
      }),
    });
    await settledScreen();
    const grow = card("GROW_REVENUE");
    const dl = grow.querySelector("dl.oc-pfgrow") as HTMLElement;
    expect(Array.from(dl.children).map((row) => row.querySelector("dt")?.textContent)).toEqual([
      "Target",
      "Potential",
      "Estimated income",
    ]);
    const incomeRow = dl.children[2];
    expect(Array.from(incomeRow.children).map((c) => c.tagName + (c.className ? "." + c.className : ""))).toEqual([
      "DT",
      "DD",
      "DD.oc-pfnote",
    ]);
    expect(grow.querySelector("[data-portfolio-card-days]")?.className).toContain("oc-pfdays");
    expect(grow.querySelector(".oc-chip")).toBeNull();
  });

  it("growIncomeNoteIsOmittedWhenTheServerSendsNone", async () => {
    renderServer({ GROW_REVENUE: serverCard({ value: { text: "18–20 kW", small: "unused" }, parts: growParts() }) });
    await settledScreen();
    expect(card("GROW_REVENUE").querySelector("[data-portfolio-grow-parts]")).not.toBeNull();
    expect(card("GROW_REVENUE").querySelector("dd.oc-pfnote")).toBeNull();
  });

  it("growMissingKeepsTheGapAndNoPartsAndNoSummaryReadsNotKnown", async () => {
    const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    expect(value("GROW_REVENUE")).toBe("Not available yet");
    expect(basis("GROW_REVENUE")).toBe("Opportunities · revenue not measured yet");
    expect(card("GROW_REVENUE").querySelector("[data-portfolio-grow-parts]")).toBeNull();
    view.unmount();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(value("GROW_REVENUE")).toBe("Not known yet");
  });
});

describe("PL-1: a lens change keeps the page and loads the panel only", () => {
  type Answer = EstateResult<EstatePortfolioBody>;
  function deferredClient(first: Answer) {
    const pending: Array<{ query: EstatePortfolioQuery; resolve: (a: Answer) => void }> = [];
    const client: EstateClient = {
      findings: () => Promise.reject(new Error("no")),
      actions: () => Promise.reject(new Error("no")),
      scope: () => Promise.reject(new Error("no")),
      portfolio: (query) =>
        query.lens === "all"
          ? Promise.resolve(first)
          : new Promise<Answer>((resolve) => {
              pending.push({ query, resolve });
            }),
    };
    return { client, pending };
  }
  const heldRow = row({ finding_id: "aaaaaaaa-0000-4000-8000-00000000000a", finding_revision_id: "bbbbbbbb-0000-4000-8000-00000000000a", title: "Held all-lens row", finding_label: "Held all-lens row" });
  const costRow = row({ finding_id: "cccccccc-0000-4000-8000-00000000000c", finding_revision_id: "dddddddd-0000-4000-8000-00000000000c", title: "Fresh cost row", finding_label: "Fresh cost row" });
  const riskRow = row({ finding_id: "eeeeeeee-0000-4000-8000-00000000000e", finding_revision_id: "ffffffff-0000-4000-8000-00000000000e", title: "Fresh risk row", finding_label: "Fresh risk row" });
  const start = async (first: Answer) => {
    const d = deferredClient(first);
    // PF-T: the lenses live on Act first.
    renderAt(ACT, d.client);
    await settledScreen();
    return d;
  };
  const click = async (label: string) => {
    await act(async () => {
      fireEvent.click(within(panel("Where management should act first")).getByRole("button", { name: label }));
    });
  };
  const priority = () => document.querySelector("[data-portfolio-panel='priority']") as HTMLElement;

  it("keeps the context, tab row and evidence prompt while the lens read is pending", async () => {
    await start(loadedPortfolio(portfolioBody({ rows: [heldRow], total_count: 1 })));
    await click("Cost");
    expect(document.querySelector("[data-estate-loading]")).toBeNull();
    expect(document.querySelector("[data-portfolio-context]")).not.toBeNull();
    // PF-T: the cards and pulse are on the Overview tab; Act first keeps its tab row and evidence prompt.
    expect(document.querySelector("[data-portfolio-tabs]")).not.toBeNull();
    expect(document.querySelector("[data-portfolio-side] [data-portfolio-prompt]")).not.toBeNull();
  });

  it("shows a loading row, aria-busy and no held row on the priority panel", async () => {
    await start(loadedPortfolio(portfolioBody({ rows: [heldRow], total_count: 1 })));
    await click("Cost");
    const p = priority();
    expect(p.getAttribute("aria-busy")).toBe("true");
    expect(within(p).getByRole("button", { name: "Cost" }).getAttribute("aria-pressed")).toBe("true");
    expect(within(p).getByRole("button", { name: "All findings" }).getAttribute("aria-pressed")).toBe("false");
    expect(text(p.querySelector("[data-portfolio-loading-rows]"))).toBe("Loading the Cost findings.");
    expect(text(p)).not.toContain("Held all-lens row");
    expect(text(p.querySelector("[data-portfolio-count]"))).toBe("Loading findings");
    expect(within(p).queryByText("Load more Findings")).toBeNull();
  });

  it("replaces the page with the lens response: new rows and total_count", async () => {
    const d = await start(loadedPortfolio(portfolioBody({ rows: [heldRow], total_count: 1 })));
    await click("Cost");
    await act(async () => {
      d.pending[0].resolve(loadedPortfolio(portfolioBody({ rows: [costRow], total_count: 7, lens: "cost" })));
    });
    await settledScreen();
    const p = priority();
    expect(p.getAttribute("aria-busy")).not.toBe("true");
    expect(p.querySelector("[data-portfolio-loading-rows]")).toBeNull();
    expect(text(p)).toContain("Fresh cost row");
    expect(text(p)).not.toContain("Held all-lens row");
    expect(text(p.querySelector("[data-portfolio-count]"))).toContain("7 findings");
  });

  it("a refusal on the lens read replaces the page", async () => {
    const d = await start(loadedPortfolio(portfolioBody({ rows: [heldRow], total_count: 1 })));
    await click("Cost");
    await act(async () => {
      d.pending[0].resolve(refused(503, "ESTATE_STORE_UNAVAILABLE", "The estate store is unavailable."));
    });
    await settledScreen();
    expect(document.querySelector("[data-portfolio-panel='priority']")).toBeNull();
    expect(document.querySelector("[data-portfolio-pulse]")).toBeNull();
    expect(document.body.textContent).toContain("The estate store is unavailable.");
  });

  it("cost then risks quickly shows the risks body only", async () => {
    const d = await start(loadedPortfolio(portfolioBody({ rows: [heldRow], total_count: 1 })));
    await click("Cost");
    await click("Risks");
    expect(d.pending.map((c) => c.query.lens)).toEqual(["cost", "risks"]);
    await act(async () => {
      d.pending[1].resolve(loadedPortfolio(portfolioBody({ rows: [riskRow], total_count: 3, lens: "risks" })));
    });
    await act(async () => {
      d.pending[0].resolve(loadedPortfolio(portfolioBody({ rows: [costRow], total_count: 9, lens: "cost" })));
    });
    await settledScreen();
    const p = priority();
    expect(text(p)).toContain("Fresh risk row");
    expect(text(p)).not.toContain("Fresh cost row");
    expect(text(p)).not.toContain("Held all-lens row");
    expect(within(p).getByRole("button", { name: "Risks" }).getAttribute("aria-pressed")).toBe("true");
  });

  it("a refused load-more after a lens change replaces the page", async () => {
    const d = await start(loadedPortfolio(portfolioBody({ rows: [heldRow], total_count: 1 })));
    await click("Cost");
    await act(async () => {
      d.pending[0].resolve(loadedPortfolio(portfolioBody({ rows: [costRow], total_count: 7, lens: "cost", next_cursor: "cur-2" })));
    });
    await settledScreen();
    await click("Load more Findings");
    expect(d.pending[1].query).toMatchObject({ lens: "cost", cursor: "cur-2" });
    await act(async () => {
      d.pending[1].resolve(refused(503, "ESTATE_STORE_UNAVAILABLE", "The estate store is unavailable."));
    });
    await settledScreen();
    expect(document.querySelector("[data-portfolio-panel='priority']")).toBeNull();
    expect(document.body.textContent).not.toContain("Fresh cost row");
    expect(document.body.textContent).toContain("The estate store is unavailable.");
  });
});

/**
 * PF-T: Portfolio section tabs (`.agent/architect-proposal-portfolio-layout-2026-11-10.md` §6, §11; layout
 * `frontend/mockups/v71/portfolio-tabs.html`). One assertion per card rule.
 */
describe("PF-T Portfolio section tabs", () => {
  const WINDOW_QUERY = "from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z&known_at=2026-10-07T00:05:00Z";
  const TAB_NAMES = ["Overview", "Act first", "Outcomes by site", "Opportunity", "What changed", "Scope & coverage"];

  function renderTabs(entry: string, client: EstateClient) {
    return render(
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route path="/portfolio/:tab?" element={<main><EstatePortfolioPage client={client} /></main>} />
        </Routes>
        <Where />
      </MemoryRouter>,
    );
  }
  const tabRow = () => screen.getByRole("navigation", { name: "Portfolio sections" });
  const tabLinks = () => within(tabRow()).getAllByRole("link");
  const tabLink = (name: string) => tabLinks().find((a) => text(a.querySelector("[data-pf-tab-label]")) === name)!;
  const paramsOf = (a: Element) => new URL(a.getAttribute("href")!, "http://x").searchParams;
  const pathOf = (a: Element) => new URL(a.getAttribute("href")!, "http://x").pathname;

  it("renders a Portfolio sections nav of links, the current tab marked aria-current", async () => {
    renderTabs(`/portfolio/outcomes?${WINDOW_QUERY}`, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(tabRow().tagName).toBe("NAV");
    expect(tabLinks().map((a) => text(a.querySelector("[data-pf-tab-label]")))).toEqual(TAB_NAMES);
    expect(tabLinks().filter((a) => a.getAttribute("aria-current") === "page")).toEqual([tabLink("Outcomes by site")]);
  });

  it("every tab link carries from, to and known_at", async () => {
    renderTabs(`/portfolio?${WINDOW_QUERY}`, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    for (const a of tabLinks()) {
      const p = paramsOf(a);
      expect([p.get("from"), p.get("to"), p.get("known_at")]).toEqual(["2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z", "2026-10-07T00:05:00Z"]);
    }
    expect(tabLinks().map(pathOf)).toEqual(["/portfolio", "/portfolio/act-first", "/portfolio/outcomes", "/portfolio/opportunity", "/portfolio/changes", "/portfolio/scope"]);
  });

  it("lens travels on the Act first link only", async () => {
    renderTabs(`/portfolio/act-first?${WINDOW_QUERY}&lens=cost`, portfolioClient(loadedPortfolio(portfolioBody({ lens: "cost" }))));
    await settledScreen();
    expect(tabLinks().map((a) => paramsOf(a).get("lens"))).toEqual([null, "cost", null, null, null, null]);
  });

  it("an unknown count shows no badge, never 0", async () => {
    const base = portfolioBody();
    const body = portfolioBody({ total_count: null, summary: { ...base.summary, opportunity_count: null, accepted_action_count: null } });
    renderTabs(`/portfolio?${WINDOW_QUERY}`, portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    expect(tabRow().querySelectorAll("[data-pf-tab-count]").length).toBe(0);
    expect(text(tabRow())).not.toMatch(/\d/);
  });

  it("known counts show on Act first, Opportunity and What changed", async () => {
    const base = portfolioBody();
    const body = portfolioBody({ total_count: 6, summary: { ...base.summary, opportunity_count: 1, accepted_action_count: 3 } });
    renderTabs(`/portfolio?${WINDOW_QUERY}`, portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    expect(tabLinks().map((a) => a.querySelector("[data-pf-tab-count]")?.textContent ?? null)).toEqual([null, "6", null, "1", "3", null]);
  });

  it("a tab change keeps the page mounted, reads nothing again and moves focus to the panel heading", async () => {
    const client = portfolioClient(loadedPortfolio(portfolioBody()));
    renderTabs(`/portfolio?${WINDOW_QUERY}`, client);
    await settledScreen();
    const h1 = screen.getByRole("heading", { level: 1 });
    fireEvent.click(tabLink("Opportunity"));
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(`/portfolio/opportunity?${new URLSearchParams(WINDOW_QUERY).toString()}`);
    expect(client.calls.length).toBe(1);
    expect(screen.getByRole("heading", { level: 1 })).toBe(h1);
    expect(document.activeElement).toBe(screen.getByRole("heading", { level: 2, name: OPPORTUNITY_PANEL }));
  });

  it("moving from Act first lens=cost to another tab reads nothing again", async () => {
    const client = portfolioClient(loadedPortfolio(portfolioBody()));
    renderTabs(`/portfolio?${WINDOW_QUERY}`, client);
    await settledScreen();
    expect(client.calls.map((c) => c.lens)).toEqual(["all"]);
    // Choosing the Cost lens on Act first is the one new read.
    fireEvent.click(tabLink("Act first"));
    await settledScreen();
    fireEvent.click(within(panel("Where management should act first")).getByRole("button", { name: "Cost" }));
    await settledScreen();
    expect(client.calls.map((c) => c.lens)).toEqual(["all", "cost"]);
    // The whole list is already held by key: any other tab shows it with no new read.
    fireEvent.click(tabLink("Opportunity"));
    await settledScreen();
    fireEvent.click(tabLink("What changed"));
    await settledScreen();
    expect(client.calls.map((c) => c.lens)).toEqual(["all", "cost"]);
  });

  it("Overview shows the four cards, the counts strip as tab links and the top 3 with See all", async () => {
    const rows = [1, 2, 3, 4].map((n) => row({ finding_id: `f-${n}`, finding_revision_id: `r-${n}`, title: `Finding ${n}` }));
    const base = portfolioBody();
    renderTabs(`/portfolio?${WINDOW_QUERY}`, portfolioClient(loadedPortfolio(portfolioBody({ rows, total_count: 4, summary: { ...base.summary, opportunity_count: 1 } }))));
    await settledScreen();
    expect(document.querySelectorAll(".oc-pfcard").length).toBe(4);
    const pulse = document.querySelector("[data-portfolio-pulse]")!;
    expect(Array.from(pulse.querySelectorAll("a")).map(pathOf)).toEqual([
      "/portfolio/act-first",
      "/portfolio/opportunity",
      "/portfolio/scope",
      "/portfolio/changes",
      "/portfolio/act-first",
    ]);
    const top3 = screen.getByRole("region", { name: PRIORITY_PANEL });
    expect(Array.from(top3.querySelectorAll("ol > li")).map((li) => text(li.querySelector("[data-pf-top3-title]")))).toEqual(["Finding 1", "Finding 2", "Finding 3"]);
    const seeAll = within(top3).getByRole("link", { name: "See all 4 findings →" });
    expect(pathOf(seeAll)).toBe("/portfolio/act-first");
    expect(screen.queryByRole("group", { name: "Finding lens" })).toBeNull();
  });

  it("the date bar sits at the top, above the page title and the tabs", async () => {
    renderTabs(`/portfolio?${WINDOW_QUERY}`, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const bar = document.querySelector("[data-estate-date-bar]")!;
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(bar.compareDocumentPosition(h1) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(bar.compareDocumentPosition(tabRow()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("the tab row wraps at 760 px and below", async () => {
    // jsdom has no layout: the wrap rule is asserted on the stylesheet (read from disk, as estateRoots does).
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const css = fs.readFileSync(`${cwd}/src/estate/estatePortfolio.css`, "utf8");
    expect(css).toMatch(/@media \(max-width: ?760px\)\s*\{[^@]*\.pf-tabs \.site-tabs__list\s*\{[^}]*flex-wrap: ?wrap/s);
  });
});
