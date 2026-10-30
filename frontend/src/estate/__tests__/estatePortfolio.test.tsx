/**
 * W3-03 run 2: the estate Portfolio page under a local MemoryRouter (Lane A mounts the shell route), against the
 * v69 `portfolio` panels and `.agent/W3-03-build-spec.md` closures 1-5, r1a, r1b, r1b2 and r1b4 literals.
 */
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { describeViolations, forbiddenPhrases, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import type { EstateClient, EstatePortfolioStatus } from "../estateClient";
import { EstatePortfolioPage } from "../EstatePortfolio";
import { mechanismWords } from "../portfolioWords";
import { outcomeWarning, planWarning } from "../../test/outcomeBoardFixture";
import type { OutcomeWarning } from "../../sites/outcomeBoardClient";
import {
  COLD_ROW,
  coverageSite,
  loadedPortfolio,
  portfolioBody,
  portfolioClient,
  refused,
  row,
  SITES,
  outcomeSummaryBody,
  STATUS_BODIES,
  withOutcomeSummary,
} from "./portfolioFixtures";

const ENTRY = "/portfolio?from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z";

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

function renderAt(entry: string, client: EstateClient) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/portfolio" element={<main><EstatePortfolioPage client={client} /></main>} />
        <Route path="*" element={<main><Where /></main>} />
      </Routes>
      <Where />
    </MemoryRouter>,
  );
}

const panel = (title: string) => panelTitled(title);
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
    // R5: the Site-owned value is formatted from the exact selected line (outward to the minor unit); now on Optimize.
    expect(text(cards[1].querySelector("[data-portfolio-card-value]"))).toBe("$3.31–$3.97");
    expect(text(cards[1])).toContain("Kobo · Candidate operating-cost exposure · 6 Oct 2026 · 14:20–15:20 UTC");
    expect(cards[1].tagName).toBe("A");
    expect(cards[1].getAttribute("href")).toBe("/financials?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z");
    // R6 / A.4: no category counts on this body, so Protect reads `Not assessed` and links to the risk root.
    expect(text(cards[2].querySelector("[data-portfolio-card-value]"))).toBe("Not assessed");
    expect(cards[2].getAttribute("href")).toMatch(/^\/findings\/risks\?/);
    expect(cards[0].getAttribute("href")).toMatch(/^\/findings\/opportunities\?/);
    expect(cards[3].getAttribute("href")).toMatch(/^\/evidence\?/);
    expect(text(document.body)).not.toMatch(/18–20|kW ×|\$2\.50|battery on watch|ACT-0/);
    const pulse = document.querySelector("[data-portfolio-pulse]") as HTMLElement;
    expect(text(pulse)).toContain("Not assessed priority sites");
    expect(text(pulse)).toContain("Distinct consequence categories · no combined savings total");
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
    const first = document.querySelector("[data-portfolio-card='OPTIMIZE_COST']") as HTMLElement;
    expect(text(first.querySelector("[data-portfolio-card-value]"))).toBe("Unpriced");
    expect(text(first)).toContain("GreenHarvest · consequence recorded without a price");
    expect(text(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-value]"))).toBe("Not assessed");
    expect(text(document.querySelector("[data-portfolio-empty]"))).toBe("No matching supported Findings");
    // CC-R2-Q3 ruling: with no rows the panel bottom keeps only the Findings link.
    const bottom = panel("Where management should act first").querySelector(".panel-bottom") as HTMLElement;
    expect(bottom.querySelector("span")).toBeNull();
    expect(within(bottom).getByRole("link", { name: "Open all Findings →" })).toBeTruthy();
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
    expect(text(priority.querySelector("[data-portfolio-count]"))).toBe("2 selected Findings · coverage incomplete");
    const partialObjectives = document.querySelector("[data-portfolio-panel='objectives']") as HTMLElement;
    expect(text(partialObjectives)).not.toContain("Site detail is unavailable for these cells.");
    expect(text(partialObjectives)).not.toContain("Select a linked cell for context.");
    const w1 = priority.querySelector(`[data-portfolio-row^='f1f1f1f1']`) as HTMLElement;
    const cells = Array.from(w1.querySelectorAll("td")).map(lines);
    expect(cells[0]).toBe("Kobo Mini-grid Opens current Site view");
    expect(cells[1]).toBe("Extended generator support Finding KOBO-001 · f1f1f1f1-0000-4000-8000-000000000001 · Possible extended generator support");
    expect(cells[2]).toBe("$3.31–$3.97 Basis not recorded 6 Oct 2026 · 14:20–15:20 UTC");
    // CC-R2: the server's placement group and reason line; the derived confidence words and reasons.
    expect(cells[3]).toBe("Compare value Priced cost exposure; no like line to compare with");
    expect(cells[4]).toBe("Supported, coherent source Supported Finding · Prepared example data source");
    expect(cells[5]).toBe("No accepted Action Next move not recorded Recommendation not accepted Review Finding");
    const cold = priority.querySelector(`[data-portfolio-row^='f2f2f2f2']`) as HTMLElement;
    expect(text(cold)).toContain("Finding detail unavailable");
    expect(cold.querySelector("[data-portfolio-finding-link]")).toBeNull();
    // CC-R2-Q3 ruling: the subtitle and the bottom line (no longer computed from priority).
    expect(text(priority)).toContain(
      "Selected Findings across accessible Sites, grouped by where to look first, with evidence confidence alongside.",
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
      ["GreenHarvest", "/sites/COLD-001"],
      ["Depot", "/sites/EV-LAB-001/ev"],
      ["Harbour", "/sites/EV-LAB-002/ev"],
    ]);
    expect(matrix.querySelectorAll("[data-portfolio-outcome-cell]")).toHaveLength(16);
    const cell = (code: string, cat: string) => matrix.querySelector(`[data-portfolio-outcome-cell^='${code}|${cat}|']`) as HTMLElement;
    expect(lines(cell("KOBO-001", "OPTIMIZE_COST"))).toBe("Needs attention Generator fuel");
    expect(cell("KOBO-001", "OPTIMIZE_COST").className).toBe("oc-cell tone-amber");
    expect(cell("KOBO-001", "OPTIMIZE_COST").getAttribute("href")).toBe("/sites/KOBO-001");
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

  it("outcomeCardDotsMatchTheMatrixAndGrowTakesTheShortValue", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    const matrix = screen.getByRole("table", { name: "Outcomes across the estate" });
    for (const cat of ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
      const dots = Array.from(document.querySelectorAll(`[data-portfolio-card-dots='${cat}'] > span`));
      expect(dots.map((d) => text(d))).toEqual(["Kobo: ", "GreenHarvest: ", "Depot: ", "Harbour: "].map((n, i) => n + text(matrix.querySelectorAll(`[data-portfolio-outcome-row='${cat}'] [data-portfolio-outcome-cell] b`)[i])));
      // Each dot's tone is the matrix cell's tone for the same Site.
      for (const d of dots) {
        const [code, tone] = (d.getAttribute("data-portfolio-dot") ?? "").split("|");
        expect(d.className).toBe(`tone-${tone}`);
        expect(matrix.querySelector(`[data-portfolio-outcome-cell='${code}|${cat}|${tone}']`)).not.toBeNull();
      }
    }
    const kobo = document.querySelector("[data-portfolio-card-dots='OPTIMIZE_COST'] > span") as HTMLElement;
    expect(kobo.getAttribute("title")).toBe("Kobo: Needs attention");
    const grow = document.querySelector("[data-portfolio-card='GROW_REVENUE']") as HTMLElement;
    expect(text(grow.querySelector("[data-portfolio-card-value]"))).toBe("18–20 kW unused");
    expect(grow.className).toContain("green");
    expect(grow.querySelector("[data-missing-claim], .missing-claim")).toBeNull();
  });

  it("growKeepsTheMissingClaimWithoutAShortValueAndTheMatrixStatesUnavailable", async () => {
    const noShort = outcomeSummaryBody();
    noShort.sites = noShort.sites.map((site) => ({ ...site, rows: site.rows.map((r) => ({ ...r, short_value: null })) }));
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: noShort }));
    await settledScreen();
    const grow = document.querySelector("[data-portfolio-card='GROW_REVENUE']") as HTMLElement;
    expect(text(grow.querySelector("[data-portfolio-card-value]"))).toBe("Not available yet");
    expect(grow.className).toContain("neutral");
    cleanup();
    // A refused summary and a client without the read both show the panel's alert; the cards keep empty dots.
    for (const client of [
      withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), refused(503, "ESTATE_STORE_UNAVAILABLE", "The estate store is unavailable.") as never),
      portfolioClient(loadedPortfolio(portfolioBody())),
    ]) {
      renderAt(ENTRY, client);
      await settledScreen();
      const outcomes = panel("Outcomes across the estate");
      expect(within(outcomes).getByRole("alert").textContent).toBe("Outcome status is not available right now");
      expect(outcomes.querySelector("[role='table']")).toBeNull();
      expect(document.querySelectorAll("[data-portfolio-dot]")).toHaveLength(0);
      expect(text(document.querySelector("[data-portfolio-card='GROW_REVENUE'] [data-portfolio-card-value]"))).toBe("Not available yet");
      cleanup();
    }
  });

  it("rendersTypedEvidencePromptAndExactDestinations", async () => {
    renderAt(`${ENTRY}&known_at=2026-10-07T00:00:00Z`, portfolioClient(loadedPortfolio(portfolioBody())));
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

  it("rendersIncompleteAndNoGapPromptWithoutSite", async () => {
    const body = portfolioBody({
      evidence_prompt: { state: "COVERAGE_INCOMPLETE", text: "Evidence coverage incomplete", site_id: null, site_code: null, gap_code: null, destination: "/evidence" },
    });
    renderAt(ENTRY, portfolioClient(loadedPortfolio(body)));
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
      const view = renderAt(ENTRY, client);
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
    renderAt(ENTRY, client);
    await settledScreen();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Load more Findings" }));
    });
    expect(document.querySelectorAll("[data-portfolio-row]")).toHaveLength(3);
    expect(document.querySelectorAll("[data-portfolio-card]")).toHaveLength(4);
    // OUT-B B6 (R521): the outcome matrix (4 categories x 4 Sites) stays; Load more does not re-read the summary.
    expect(document.querySelectorAll("[data-portfolio-outcome-cell]")).toHaveLength(16);
    expect(client.summaryCalls).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Load more Findings" })).toBeNull();
  });

  it("keepsUnsupportedOpportunitySlotsInert", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const opportunity = panel("An opportunity beyond reducing cost");
    expect(text(opportunity)).toContain("GROW USEFUL DEMAND");
    expect(text(opportunity)).toContain("No reviewed scenario");
    expect(text(opportunity)).toContain("No eligible headroom or demand basis");
    expect(text(opportunity)).toContain("A scenario needs reviewed physical headroom, demand and an authored economic assumption.");
    expect(opportunity.querySelector("a, button")).toBeNull();
    expect(within(opportunity).getByLabelText("Review opportunity Finding, Not available yet")).toBeTruthy();
    expect(within(opportunity).getByLabelText("Inspect physical headroom, Not available yet")).toBeTruthy();
  });

  it("rendersChangeDisclosureWithoutRecoveredMoney", async () => {
    const progressRow = (id: string, selected: boolean) => ({
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
    });
    // Page size 1 and a nonmatching lens: the disclosure uses the server boolean, never the paged Finding rows.
    const body = portfolioBody({
      lens: "opportunities",
      rows: [],
      total_count: 0,
      progress: { ...portfolioBody().progress, pending_trial_count: null, verified_resolution_count: 2, rows: [progressRow("act-1", true), progressRow("act-2", false)] },
    });
    renderAt(`${ENTRY}&lens=opportunities`, portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    const progress = panel("What changed in this review");
    expect(text(progress)).toContain("Completed activity · Not established");
    expect(text(progress)).toContain("Policy trial awaiting outcome · Unknown");
    expect(text(progress)).toContain("Verified resolutions · 2");
    expect(text(progress)).toContain("Recovered value not established");
    expect(text(progress)).toContain(
      "No previous comparable Portfolio snapshot is selected; change deltas and recovered-value trends are withheld.",
    );
    expect(progress.querySelectorAll("[data-portfolio-origin-unselected]")).toHaveLength(1);
    expect(text(progress.querySelector("[data-portfolio-progress-row='act-2']"))).toContain("Origin Finding revision not selected");
    expect(text(progress.querySelector("[data-portfolio-progress-row='act-1']"))).not.toContain("Origin Finding revision not selected");
    expect(text(progress)).not.toMatch(/\$|USD/);
  });

  it("rendersEmptyPendingHistoricalAndSourceConflict", async () => {
    const expected: Record<EstatePortfolioStatus, string> = {
      CURRENT: "Selected Site records",
      HISTORICAL: "Historical as of 30 Sep 2026 · 00:00 UTC",
      PENDING: "Updating selected Sites",
      UNKNOWN: "Some Sites cannot be compared yet",
      EMPTY_SCOPE: "No accessible Sites",
    };
    const statuses = Object.keys(STATUS_BODIES) as EstatePortfolioStatus[];
    expect(statuses.sort()).toEqual(["CURRENT", "EMPTY_SCOPE", "HISTORICAL", "PENDING", "UNKNOWN"]);
    for (const status of statuses) {
      const view = renderAt(ENTRY, portfolioClient(loadedPortfolio(STATUS_BODIES[status])));
      await settledScreen();
      expect(document.querySelector("[data-portfolio-context]")?.getAttribute("data-portfolio-context")).toBe(status);
      expect(text(document.querySelector("[data-portfolio-context]"))).toContain(expected[status]);
      expect(document.querySelectorAll("section.panel")).toHaveLength(4);
      if (status === "PENDING") expect(text(document.querySelector("[data-portfolio-row^='f2f2f2f2'] [data-portfolio-value]"))).toBe("Updating · Unpriced");
      if (status === "EMPTY_SCOPE") {
        expect(text(document.querySelector("[data-portfolio-count]"))).toBe("0 selected Findings");
        expect(text(document.querySelector("[data-portfolio-panel='priority']"))).not.toMatch(/coverage incomplete/i);
        expect(text(document.querySelector("[data-portfolio-empty]"))).toBe("No selected Findings for this window");
        expect(text(document.querySelector("[data-portfolio-domains]"))).toBe("0 accessible Sites · 0 mini-grid / 0 cold-chain / 0 EV charging");
      }
      view.unmount();
    }
    // A historical Site prefixes the first Value line and withholds the current amount.
    const historic = portfolioBody({
      coverage: { ...portfolioBody().coverage, sites: [coverageSite(SITES[0].site_id, "HISTORICAL")] },
    });
    const view = renderAt(ENTRY, portfolioClient(loadedPortfolio(historic)));
    await settledScreen();
    expect(text(document.querySelector("[data-portfolio-row^='f1f1f1f1'] [data-portfolio-value]"))).toBe("Historical · Value withheld");
    view.unmount();
    // Mixed/unknown source: the operating-cost card is withheld, never zero.
    const withheld = portfolioBody({
      value_cards: portfolioBody().value_cards.map((c) =>
        c.key === "OPERATING_COST" ? { ...c, state: "WITHHELD" as const, display_value: "Not comparable for this selection", detail: "Inspect Site records and exclusions", basis_text: "No combined operating-cost amount", tone: "neutral" as const } : c,
      ),
    });
    renderAt(ENTRY, portfolioClient(loadedPortfolio(withheld)));
    await settledScreen();
    expect(text(document.querySelector("[data-portfolio-card='OPTIMIZE_COST'] [data-portfolio-card-value]"))).toBe("Not comparable for this selection");
  });

  it("noLineCardUsesExactShortLiteralFromApiAndFallback", async () => {
    // r3b: the API value and the missing-display_value fallback are both exactly "No supported value".
    const noLine = (display_value: string | null) => portfolioBody({
      value_cards: portfolioBody().value_cards.map((c) =>
        c.key === "OPERATING_COST" ? { ...c, state: "NO_LINE" as const, display_value, detail: "No selected operating-cost consequence", basis_text: "No value line", tone: "neutral" as const } : c,
      ),
    });
    const sel = "[data-portfolio-card='OPTIMIZE_COST'] [data-portfolio-card-value]";
    const first = renderAt(ENTRY, portfolioClient(loadedPortfolio(noLine("No supported value"))));
    await settledScreen();
    expect(text(document.querySelector(sel))).toBe("No supported value");
    first.unmount();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(noLine(null as unknown as string))));
    await settledScreen();
    expect(text(document.querySelector(sel))).toBe("No supported value");
  });

  it("preservesWindowAndCutoffAcrossGlobalRoots", async () => {
    renderAt(`${ENTRY}&known_at=2026-10-07T00:00:00Z&lens=cost`, portfolioClient(loadedPortfolio(portfolioBody({ lens: "cost" }))));
    await settledScreen();
    const tuple = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00Z";
    const hrefs = Array.from(document.querySelectorAll("a")).map((a) => a.getAttribute("href") ?? "");
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
    const view = renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const footer = () => document.querySelector("[data-portfolio-footer]") as HTMLElement;
    expect(text(footer())).toContain("Business context: Depot delivered 120 kWh in selected records; $36.00 gross tariff scenario.");
    const basis = footer().querySelector("details") as HTMLDetailsElement;
    expect(text(basis.querySelector("summary"))).toBe("Energy basis ↗");
    fireEvent.click(basis.querySelector("summary") as HTMLElement);
    const basisText = text(basis);
    expect(basisText).toContain("Selected window: 6 Oct 2026 · 08:00–16:00 UTC.");
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
    renderAt(ENTRY, portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    expect(text(footer())).toContain("Cross-Site energy and tariff totals are not established.");
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
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody({ rows: [row(), twin] })))));
    await settledScreen();
    const labels = Array.from(document.querySelectorAll("[data-portfolio-row] td:nth-child(2) small:first-of-type")).map(text);
    expect(new Set(labels).size).toBe(2);
    expect(labels).toEqual([
      "Finding KOBO-001 · f1f1f1f1-0000-4000-8000-000000000001 · Possible extended generator support",
      "Finding KOBO-001 · f1f1f1f1-0000-4000-8000-0000000000aa · Possible extended generator support",
    ]);
    expect(document.querySelectorAll("[data-portfolio-finding-link]")).toHaveLength(2);
    expectV69Panels("portfolio");
    expectPlantedPanelRejected("portfolio");
    const main = document.querySelector(".estate-portfolio") as HTMLElement;
    const order = ["[data-portfolio-context]", "[data-portfolio-cards]", "[data-portfolio-pulse]", ".portfolio-main", ".portfolio-bottom", "[data-portfolio-footer]"];
    const nodes = order.map((sel) => main.querySelector(sel) as HTMLElement);
    nodes.forEach((n) => expect(n).not.toBeNull());
    for (let i = 1; i < nodes.length; i += 1) {
      expect(nodes[i - 1].compareDocumentPosition(nodes[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
    const side = main.querySelector("[data-portfolio-side]") as HTMLElement;
    expect(side.querySelector("[data-portfolio-panel='objectives']")).not.toBeNull();
    expect(side.querySelector("[data-portfolio-prompt]")).not.toBeNull();
    expect(main.querySelector("[data-portfolio-scroll='findings'] table")).not.toBeNull();
    // OUT-B B6 (R521): the outcome matrix replaces the objectives matrix in the same scroll container.
    expect(main.querySelector("[data-portfolio-scroll='objectives'] .oc-matrix")).not.toBeNull();
    expect(main.querySelector(".objective-matrix")).toBeNull();
    expect(Array.from(main.querySelectorAll(".portfolio-bottom > section.panel")).map((p) => p.getAttribute("data-portfolio-panel"))).toEqual([
      "opportunity",
      "progress",
    ]);
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
    const live = { ...COLD_ROW, links: { ...COLD_ROW.links, finding: coldLink } };
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

  it("scopeDisclosureSummarisesAssessmentsTranslatesCodesAndNestsLongIds", async () => {
    const longIds = Array.from({ length: 60 }, (_, i) => `e1e1e1e1-0000-4000-8000-${String(i).padStart(12, "0")}`);
    const base = portfolioBody();
    const sites = base.scope_disclosure.sites.map((s, i) => ({
      ...s,
      selected_revision_ids: i === 0 ? longIds : i === 1 ? ["e2e2e2e2-0000-4000-8000-000000000002"] : [],
      coverage: coverageSite(s.site_id, i === 3 ? "UNKNOWN" : "CURRENT"),
    }));
    const exclusions = [
      { line_key: "w1-line", group_key: "g-w1", reason_codes: ["UNPRICED"] },
      { line_key: "cold_chain:c9", group_key: null, reason_codes: ["SOMETHING_NEW"] },
    ];
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ scope_disclosure: { sites, exclusions } }))));
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
    idsSummary.focus();
    expect(document.activeElement).toBe(idsSummary);
    fireEvent.click(idsSummary);
    expect(ids.open).toBe(true);
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
    expect(items[1].querySelector("details summary")?.textContent).toBe("Record details");
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
    expect(text(document.querySelector("[data-estate-window]"))).toBe("Window 2026-10-06 to 2026-10-06 (UTC days)");
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
    expect(lines(cold)).toBe("Act now No end is recorded for this episode · No accepted Action; open the recommendation");
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

  it("omitsTheCountWhenPlacementCountsAreNull", async () => {
    const counts = { NEEDS_INVESTIGATION: null, ACT_NOW: null, COMPARE_VALUE: null, UNPRICED_RISK: null, MONITOR: null };
    const base = portfolioBody();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ summary: { ...base.summary, placement_counts: counts } }))));
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
    renderAt(ENTRY, client);
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
    "The latest assessment no longer confirms this Finding; check its basis",
    "Cost is withheld because its basis is not current",
    "No end is recorded for this episode",
    "Returned after an earlier episode (Finding 1a2b3c4d)",
    "Reopened after it had closed",
    "No accepted Action; open the recommendation",
    "Action accepted, not yet applied",
    "Change applied; verification result pending",
    "Earlier resolution withdrawn after new evidence",
    "Priced cost exposure; compares with like lines in Financials",
    "Priced cost exposure; no like line to compare with",
    "Product temperature risk; no price basis",
    "Backup start failure; no price basis",
    "Charging service interruption; no price basis",
    "No price basis for this Finding",
    "Change verified on test data; watch for a return",
    "Change applied; no verified result yet",
    "No open signal",
  ];
  const CONFIDENCE: [string, string[]][] = [
    ["SUPPORTED_SOURCE_COHERENT", ["Supported Finding", "Generated test data source"]],
    ["LIMITED", ["Unconfirmed Finding", "Prepared example data source", "Cost basis withheld"]],
    ["UNKNOWN", ["Supported Finding", "Mixed sources", "Site coverage incomplete; other Findings may be missing"]],
    ["UNKNOWN", ["Unconfirmed Finding", "Source not resolved"]],
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
  const counts = (n: number | null) => ({
    GROW_REVENUE: { open_findings: null, sites_with_primary_finding: null },
    OPTIMIZE_COST: { open_findings: null, sites_with_primary_finding: null },
    PROTECT_ASSET: { open_findings: n, sites_with_primary_finding: n },
    ASSURE_PERFORMANCE: { open_findings: null, sites_with_primary_finding: null },
  });
  const withSummary = (patch: Partial<ReturnType<typeof portfolioBody>["summary"]>, scopeSites?: number) => {
    const base = portfolioBody();
    return portfolioBody({
      summary: { ...base.summary, ...patch },
      ...(scopeSites === undefined ? {} : { scope: { ...base.scope, authorized_site_count: scopeSites } }),
    });
  };

  it("fourCardsInOrderWithIconNameDefinitionAndExactCopy", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(withSummary({ category_counts: counts(2) }))));
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
    expect(text(card("PROTECT_ASSET").querySelector("[data-portfolio-card-detail]"))).toBe("Service disruptions recorded in Findings · loss not priced");
    expect(text(card("PROTECT_ASSET").querySelector("[data-portfolio-card-basis]"))).toBe("Measured events, counted separately · loss not priced");
    expect(card("PROTECT_ASSET").className).toContain("red");
    // Assure: the fixture has 1 evidence gap among 4 Sites.
    expect(value("ASSURE_PERFORMANCE")).toBe("Not established");
    expect(text(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-detail]"))).toBe(
      "No verified result yet · no targets declared · evidence gap at 1 site",
    );
    expect(text(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-basis]"))).toBe("Completed work does not establish savings");
    // Window kept on every link.
    for (const [key, root] of [
      ["GROW_REVENUE", "/findings/opportunities"],
      ["OPTIMIZE_COST", "/financials"],
      ["PROTECT_ASSET", "/findings/risks"],
      ["ASSURE_PERFORMANCE", "/evidence"],
    ]) {
      expect(card(key).getAttribute("href")).toBe(`${root}?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z`);
    }
    // The w1 scan over the four cards. The Optimize detail is the existing operating-cost card's detail verbatim
    // (A6 table); its ledger category label ("Candidate operating-cost exposure") predates this slice and is the
    // only text taken out of the scan.
    const grid = (document.querySelector("[data-portfolio-cards]") as HTMLElement).cloneNode(true) as HTMLElement;
    grid.querySelector("[data-portfolio-card='OPTIMIZE_COST'] [data-portfolio-card-detail]")?.remove();
    const scan = scanProductVocabulary(grid, "portfolio", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(10);
    expect(describeViolations(scan.violations)).toBe("");
    expectV69Panels("portfolio");
  });

  it("protectValueForTwoOneZeroAndNullAndAbsentCounts", async () => {
    const cases: [ReturnType<typeof counts> | undefined, string, string][] = [
      [counts(2), "2 sites disrupted", "red"],
      [counts(1), "1 site disrupted", "red"],
      [counts(0), "No sites disrupted", "neutral"],
      [counts(null), "Not assessed", "neutral"],
      [undefined, "Not assessed", "neutral"],
    ];
    for (const [category_counts, expected, tone] of cases) {
      const view = renderAt(ENTRY, portfolioClient(loadedPortfolio(withSummary({ category_counts }))));
      await settledScreen();
      expect(value("PROTECT_ASSET")).toBe(expected);
      expect(card("PROTECT_ASSET").classList.contains(tone)).toBe(true);
      if (expected.endsWith("disrupted") && !expected.startsWith("No")) {
        expect(card("PROTECT_ASSET").querySelector("[data-portfolio-card-value] small")?.textContent).toMatch(/^sites? disrupted$/);
      }
      view.unmount();
    }
  });

  it("optimizeValueEqualsTheOldOperatingCostValueByteForByte", async () => {
    // The old OPERATING_COST card rendered "$3.31–$3.97" for this fixture (rendersContextFiveCardsPulseAndSelectedRows).
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const node = card("OPTIMIZE_COST").querySelector("[data-portfolio-card-value]") as HTMLElement;
    expect(node.textContent).toBe("$3.31–$3.97");
    expect(text(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-detail]"))).toBe(
      "Kobo · Candidate operating-cost exposure · 6 Oct 2026 · 14:20–15:20 UTC",
    );
    expect(text(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-basis]"))).toBe("Site-owned selected consequence");
    expect(card("OPTIMIZE_COST").className).toContain("amber");
  });

  it("optimizeCardStaysInUnknownWordingWhenOperatingCostIsMissing", async () => {
    // Addendum 2: a body without OPERATING_COST is malformed; the card stays, in the unknown wording.
    const value_cards = portfolioBody().value_cards.filter((c) => c.key !== "OPERATING_COST");
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ value_cards }))));
    await settledScreen();
    expect(value("OPTIMIZE_COST")).toBe("Not assessed");
    expect(text(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-detail]"))).toBe(
      "Operating cost is not assessed for this selection",
    );
    expect(text(card("OPTIMIZE_COST").querySelector("[data-portfolio-card-basis]"))).toBe("No value line");
    expect(card("OPTIMIZE_COST").className).toContain("neutral");
    expect(card("OPTIMIZE_COST").getAttribute("href")).toBe(
      "/financials?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z",
    );
  });

  it("assureGapTextForAllSomeOneZeroAndNull", async () => {
    const cases: [number | null, number, string][] = [
      [3, 3, "evidence gaps at all 3 sites"],
      [2, 4, "evidence gaps at 2 of 4 sites"],
      [1, 4, "evidence gap at 1 site"],
      [0, 4, "no evidence gaps"],
      [null, 4, "evidence gaps not assessed"],
    ];
    for (const [gaps, sites, expected] of cases) {
      const view = renderAt(ENTRY, portfolioClient(loadedPortfolio(withSummary({ evidence_gap_site_count: gaps }, sites))));
      await settledScreen();
      expect(text(card("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-detail]"))).toBe(
        `No verified result yet · no targets declared · ${expected}`,
      );
      view.unmount();
    }
  });
});

describe("OUT-C U5: Portfolio early warnings", () => {
  const pulseWarnings = () => text(document.querySelector("[data-portfolio-pulse-warnings]"));
  const protectDetail = () => text(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-detail]"));
  const withWarnings = (warnings: OutcomeWarning[], protect = 0) => {
    const base = outcomeSummaryBody();
    return outcomeSummaryBody({
      warnings,
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
    const list = document.querySelector("[data-portfolio-panel='priority'] [data-early-warnings]") as HTMLElement;
    expect(list.previousElementSibling?.getAttribute("data-portfolio-scroll")).toBe("findings");
    const items = Array.from(list.querySelectorAll("li"));
    expect(items).toHaveLength(4);
    expect(text(items[0].querySelector("small"))).toMatch(/^GreenHarvest · Optimize cost and efficiency · /);
    expect(text(items[2].querySelector("small"))).toMatch(/^Kobo · /);
    expect(text(list)).not.toContain("Peak close to the import limit");
    expect(protectDetail()).toBe("Service disruptions recorded in Findings · 4 early warnings, counted separately · loss not priced");
    expect(/[$€£]|\b(USD|EUR|GBP|KES|ETB)\b/.test(text(list))).toBe(false);
    expect(describeViolations(scanProductVocabulary(list, "portfolio", { set: "w1" }).violations)).toBe("");
  });

  it("oneWarningIsSingularAndZeroIsShownWithNoList", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings([planWarning()], 1) }));
    await settledScreen();
    expect(pulseWarnings()).toBe("1 warning not yet priced");
    expect(protectDetail()).toBe("Service disruptions recorded in Findings · 1 early warning, counted separately · loss not priced");
    cleanup();
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings([], 0) }));
    await settledScreen();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(pulseWarnings()).toBe("0 warnings not yet priced");
    expect(protectDetail()).toBe("Service disruptions recorded in Findings · 0 early warnings, counted separately · loss not priced");
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });

  it("summaryNotLoadedReadsUnknownAndKeepsTheProtectText", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }));
    await settledScreen();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(pulseWarnings()).toBe("Unknown warnings not yet priced");
    expect(protectDetail()).toBe("Service disruptions recorded in Findings · loss not priced");
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });
});
