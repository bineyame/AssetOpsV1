/**
 * W3-03 run 2: the estate Portfolio page under a local MemoryRouter (Lane A mounts the shell route), against the
 * v69 `portfolio` panels and `specs/W3-03/` closures 1-5, r1a, r1b, r1b2 and r1b4 literals.
 */
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { Route, Routes, useLocation } from "react-router-dom";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { describe, expect, it } from "vitest";
import { leadingIntruders, panelTitled, renderedPanelTitles, strayBetweenPanels, strayOutsidePanels, stripIntruders } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { expectOneHeadline, gapIds } from "../../test/headline";
import type {
  EstateCheckedDays,
  EstateClient,
  EstateOutcomeSummaryBody,
  EstatePortfolioCard,
  EstatePortfolioQuery,
  EstatePortfolioScopeIdsBody,
  EstatePortfolioStatus,
  EstateResult,
} from "../estateClient";

type EstateOutcomeSummaryRead = EstateResult<EstateOutcomeSummaryBody>;
import { consequenceFirst, EstatePortfolioPage, PortfolioScopeSection } from "../EstatePortfolio";
import { ResultsPage } from "../Results";
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

// IA-P2 P3b (spec §3, §2.2, D-IAP.2, D-IAP.12): `/portfolio` is the Overview on E2 (`portfolioHub.test.tsx`); the page this
// file tests now draws the Outcomes and Demand & capacity tabs only, so its entry is the Outcomes tab.
const ENTRY = "/portfolio/outcomes?from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z";
/** SR-4 D-SR.2: every Site link carries the address range; D-SR.57: a target's own from/to win, the address known_at is added. */
const RANGE = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z";
const KNOWN_Q = "known_at=2026-10-07T00%3A00%3A00Z";
const ranged = (href: string, q: string = RANGE) => `${href}${href.includes("?") ? "&" : "?"}${q}`;

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const readSrc = (rel: string) => NODE_FS.readFileSync(`${CWD}/src/${rel}`, "utf8");

/** UQ-FI-3: open a Portfolio card's "Why?" (closing any open one) and return the card's qualifiers behind it. */
function whyOf(key: string): HTMLElement {
  const close = document.querySelector("[data-why-dialog] .why-close") as HTMLElement | null;
  if (close) fireEvent.click(close);
  fireEvent.click(document.querySelector(`[data-portfolio-card='${key}'] [data-why-button]`) as HTMLElement);
  return document.querySelector(`[data-portfolio-card-why='${key}']`) as HTMLElement;
}

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

/** IA-P2 P3b: the scope section (coverage line, scope disclosure, footer) is Evidence & records' (spec §2.4). */
function renderScope(client: EstateClient) {
  return render(
    <MemoryRouter initialEntries={[ENTRY.replace("/portfolio/outcomes?", "/evidence?")]}>
      <Routes>
        <Route path="/evidence" element={<main><PortfolioScopeSection client={client} /></main>} />
      </Routes>
    </MemoryRouter>,
  );
}

/** IA-P2 P3b: the "What changed" panel is the Results page's (spec §2.4: `/portfolio/changes` is `/results`). */
function renderResults(client: EstateClient) {
  return render(
    <MemoryRouter initialEntries={[ENTRY.replace("/portfolio/outcomes?", "/results?")]}>
      <Routes>
        <Route path="/results" element={<main><ResultsPage client={client} /></main>} />
      </Routes>
    </MemoryRouter>,
  );
}

/**
 * PF-T: the panels now sit on section tabs of the one mounted page. `showTab` follows a tab link in place (no new
 * read: the page keeps its reads), so a pre-PF-T assertion on a panel opens that panel's tab first.
 */
/**
 * IA-P3 P4b (spec §6 P4b): on Outcomes, the objectives panel ("Outcomes across the estate") sits inside the closed
 * Disclosure "Each Site's objectives" under the cards. Panel-title checks first see it hidden, then open it.
 */
function openObjectives(): void {
  const details = document.querySelector<HTMLDetailsElement>('[data-disclosure="portfolio-objectives"]');
  expect(details).not.toBeNull();
  expect(details!.open).toBe(false);
  expect(renderedPanelTitles()).toEqual([]);
  details!.open = true;
}

function showTab(label: string) {
  const nav = document.querySelector("nav[aria-label='Portfolio sections']");
  const link = Array.from(nav?.querySelectorAll("a") ?? []).find((a) => text(a) === label);
  if (link === undefined) throw new Error(`No Portfolio tab "${label}".`);
  if (link.getAttribute("aria-current") !== "page") fireEvent.click(link);
}
// IA-P2 P3b (spec §2.2): the three tabs are Overview, Outcomes and Demand & capacity; the panels of the retired tabs
// moved (Act first to /decisions, What changed to /results, Scope & coverage to /evidence; spec §2.4).
const PANEL_TAB: Record<string, string> = {
  "Outcomes across the estate": "Outcomes",
  "An opportunity beyond reducing cost": "Demand & capacity",
};
const panel = (title: string) => {
  if (PANEL_TAB[title] !== undefined) showTab(PANEL_TAB[title]);
  return panelTitled(title);
};
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
/** Leaf-element texts joined by one space (a cell's stacked lines); a symbol (svg) does not make a line. */
const lines = (el: Element) =>
  Array.from(el.querySelectorAll("*"))
    .filter((e) => e.closest("svg") === null && Array.from(e.children).every((c) => c.tagName.toLowerCase() === "svg"))
    .map(text)
    .join(" ");

describe("estate Portfolio page", () => {
  it("rendersContextFiveCardsPulseAndSelectedRows", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio");
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
    // IA-P2 P3b (spec §6 P3b, D-IAP.12): the pulse and the top three left the Portfolio with the Overview branch.
    expect(document.querySelector("[data-portfolio-pulse]")).toBeNull();
    // IA-P P2: the ranked Findings table left the Portfolio; the Decisions list holds the rows (homeLists.test).
    expect(document.querySelectorAll("[data-portfolio-row]")).toHaveLength(0);
  });

  it("showsCustomerMechanismWordsNotRawCodes", async () => {
    expect(mechanismWords("GENERATOR_SUPPORT_CANDIDATE")).toBe("Possible extended generator support");
    expect(mechanismWords("COLD_EXCURSION")).toBe("Chamber temperature above policy");
    expect(mechanismWords("COLD_START_FAILURE")).toBe("Automatic start failed");
    expect(mechanismWords("EV_INTERRUPTION")).toBe("Charging session interrupted");
    expect(mechanismWords(null)).toBe("Mechanism not recorded");
    expect(mechanismWords("SOMETHING_NEW")).toBe("Mechanism not recorded");
    // IA-P P2: the ranked panel that rendered these words left the Portfolio; the word map is still the one source.
  });

  it("rendersUnpricedCardAndEmptyRisksLensNotAssessed", async () => {
    const cards = portfolioBody().value_cards.map((c) =>
      c.key === "OPERATING_COST"
        ? { ...c, state: "UNPRICED" as const, line_keys: ["cold"], detail: "GreenHarvest · consequence recorded without a price", basis_text: "Price not established" }
        : c,
    );
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ value_cards: cards, rows: [], total_count: 0, lens: "risks" }))));
    await settledScreen();
    await settledScreen();
    // CH5d1-R: the body's `value_cards` stay on the wire unrendered (BL-51); Optimize is the server card only.
    const first = document.querySelector("[data-portfolio-card='OPTIMIZE_COST']") as HTMLElement;
    expect(text(first.querySelector("[data-portfolio-card-value]"))).toBe("Not known yet");
    expect(text(first)).not.toContain("consequence recorded without a price");
    expect(text(document.querySelector("[data-portfolio-card='PROTECT_ASSET'] [data-portfolio-card-value]"))).toBe("Not known yet");
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
      ["Kobo", ranged("/sites/KOBO-001", `${RANGE}&${KNOWN_Q}`)],
      ["GreenHarvest", ranged(COLD_EVENT_HREF, KNOWN_Q)],
      ["Depot", ranged("/sites/EV-LAB-001/ev", `${RANGE}&${KNOWN_Q}`)],
      ["Harbour", ranged("/sites/EV-LAB-002/ev", `${RANGE}&${KNOWN_Q}`)],
    ]);
    expect(matrix.querySelectorAll("[data-portfolio-outcome-cell]")).toHaveLength(16);
    const cell = (code: string, cat: string) => matrix.querySelector(`[data-portfolio-outcome-cell^='${code}|${cat}|']`) as HTMLElement;
    expect(lines(cell("KOBO-001", "OPTIMIZE_COST"))).toBe("Needs attention Generator fuel");
    expect(cell("KOBO-001", "OPTIMIZE_COST").className).toBe("oc-cell tone-amber");
    expect(cell("KOBO-001", "OPTIMIZE_COST").getAttribute("href")).toBe(ranged("/sites/KOBO-001", `${RANGE}&${KNOWN_Q}`));
    // OUT-W: GreenHarvest was judged on its latest event, so its header and every cell open the Site on that window;
    // Depot (no event, judged on the period) opens with a plain link.
    expect(COLD_EVENT_HREF).toContain("?from=");
    const coldCells = Array.from(matrix.querySelectorAll("[data-portfolio-outcome-cell^='COLD-001|']"));
    expect(coldCells).toHaveLength(4);
    for (const el of coldCells) expect(el.getAttribute("href")).toBe(ranged(COLD_EVENT_HREF, KNOWN_Q));
    const depotCells = Array.from(matrix.querySelectorAll("[data-portfolio-outcome-cell^='EV-LAB-001|']"));
    expect(depotCells).toHaveLength(4);
    for (const el of depotCells) expect(el.getAttribute("href")).toBe(ranged("/sites/EV-LAB-001/ev", `${RANGE}&${KNOWN_Q}`));
    expect(lines(cell("COLD-001", "GROW_REVENUE"))).toBe("Not measured yet Product sales");
    expect(cell("COLD-001", "GROW_REVENUE").className).toBe("oc-cell tone-none");
    expect(cell("EV-LAB-001", "ASSURE_PERFORMANCE").className).toBe("oc-cell tone-blue");
    // A Site whose board read failed: Unknown, no lead outcome line.
    expect(lines(cell("EV-LAB-002", "PROTECT_ASSET"))).toBe("Unknown");
    expect(cell("EV-LAB-002", "PROTECT_ASSET").querySelector("small")).toBeNull();
    expect(Array.from(outcomes.querySelectorAll("[data-portfolio-outcome-key] > span")).map((k) => [text(k), k.getAttribute("data-status-pill")])).toEqual([
      // UQ-FI-3: each key entry is the state's StatusPill, the same look as the cells.
      ["Needs attention", "NEEDS_ATTENTION"],
      ["Watch", "WATCH"],
      ["Opportunity", "OPPORTUNITY"],
      ["On track", "ON_TRACK"],
      ["Unknown", "UNKNOWN"],
      ["Not measured yet", "NOT_MEASURED"],
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
    showTab("Outcomes");
    const matrix = screen.getByRole("table", { name: "Outcomes across the estate" }).cloneNode(true) as HTMLElement;
    for (const cat of ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
      // UQ-FI-3: the per-Site states sit behind the card's "Why?", each a StatusPill like the matrix cell's.
      const dots = Array.from(whyOf(cat).querySelectorAll(`[data-portfolio-card-dots='${cat}'] > span`));
      expect(dots.map((d) => text(d))).toEqual(["Kobo: ", "GreenHarvest: ", "Depot: ", "Harbour: "].map((n, i) => n + text(matrix.querySelectorAll(`[data-portfolio-outcome-row='${cat}'] [data-portfolio-outcome-cell] [data-status-pill]`)[i]).replace("No objective declared", "No target for this outcome")));
      // Each dot's tone is the matrix cell's tone for the same Site.
      for (const d of dots) {
        const [code, tone] = (d.getAttribute("data-portfolio-dot") ?? "").split("|");
        expect(d.className).toBe(`tone-${tone}`);
        expect(matrix.querySelector(`[data-portfolio-outcome-cell='${code}|${cat}|${tone}']`)).not.toBeNull();
      }
    }
    const kobo = whyOf("OPTIMIZE_COST").querySelector("[data-portfolio-card-dots='OPTIMIZE_COST'] > span") as HTMLElement;
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
      // IA-P2 P3b: the cards and the matrix are both on the Outcomes tab.
      expect(document.querySelectorAll("[data-portfolio-card]")).toHaveLength(4);
      expect(document.querySelectorAll("[data-portfolio-dot]")).toHaveLength(0);
      for (const key of ["GROW_REVENUE", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
        expect(text(document.querySelector(`[data-portfolio-card='${key}'] [data-portfolio-card-value]`))).toBe("Not known yet");
        expect(document.querySelector(`[data-portfolio-card='${key}'] [data-portfolio-card-detail]`)).toBeNull();
      }
      cleanup();
    }
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
    expect(links[0].getAttribute("href")).toBe(ranged(first.links.opportunity));
    // D-SR.42(d): the server link names its own window, which wins; the address has no known_at to add.
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
    renderResults(portfolioClient(loadedPortfolio(body)));
    await settledScreen();
    const progress = panelTitled("What changed in this review");
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
      const view = renderAt(ENTRY, portfolioClient(loadedPortfolio(STATUS_BODIES[status])));
      await settledScreen();
      expect(document.querySelector("[data-portfolio-context]")?.getAttribute("data-portfolio-context")).toBe(status);
      expect(text(document.querySelector("[data-portfolio-context]"))).toContain(expected[status]);
      // IA-P2 P3b (D-IAP.12): the top three left the Portfolio; the Outcomes tab holds the objectives panel only. The
      // row-value prefixes (Updating, Historical) are asserted on consequenceFirst below.
      expect(Array.from(document.querySelectorAll("section.panel")).map((p) => p.getAttribute("data-portfolio-panel"))).toEqual(["objectives"]);
      if (status === "EMPTY_SCOPE") {
        expect(text(document.querySelector("[data-portfolio-domains]"))).toBe("0 accessible Sites · 0 mini-grid / 0 cold-chain / 0 EV charging");
      }
      view.unmount();
    }
    // A historical Site prefixes the first Value line and withholds the current amount.
    const historic = portfolioBody({
      coverage: { ...portfolioBody().coverage, sites: [coverageSite(SITES[0].site_id, "HISTORICAL")] },
    });
    expect(consequenceFirst(historic.rows.find((r) => r.finding_id.startsWith("f1f1f1f1"))!, historic.coverage.sites[0])).toBe("Historical · Value withheld");
    const pending = STATUS_BODIES.PENDING;
    expect(consequenceFirst(pending.rows.find((r) => r.finding_id.startsWith("f2f2f2f2"))!, pending.coverage.sites.find((c) => c.site_id === pending.rows.find((r) => r.finding_id.startsWith("f2f2f2f2"))!.site_id))).toBe("Updating · Unpriced");
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
    renderAt(`${ENTRY}&known_at=2026-10-07T00:00:00Z`, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const tuple = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z&known_at=2026-10-07T00%3A00%3A00Z";
    const hrefs = Array.from(document.querySelectorAll("a")).map((a) => a.getAttribute("href") ?? "");
    // IA-P P2: "Open all Findings" sat in the deleted ranked panel; the card links to the old lens paths stay until P3b.
    for (const root of ["/findings/risks?", "/evidence?", "/financials?"]) {
      const hit = hrefs.filter((h) => h.startsWith(root));
      expect(hit.length).toBeGreaterThan(0);
      for (const h of hit) {
        expect(h).toBe(`${root}${tuple}`);
        expect(h).not.toMatch(/cursor|lens/);
      }
    }
  });

  it("rendersEvFooterAndMissingEnergyBasis", async () => {
    const view = renderScope(portfolioClient(loadedPortfolio(portfolioBody())));
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
    expect(within(footer()).getByRole("link", { name: "Inspect energy basis →" }).getAttribute("href")).toBe(ranged("/sites/EV-LAB-001/ev/evidence"));
    expect(text(footer().querySelector("[data-portfolio-footer-coverage]"))).toBe("Categories and windows remain separate.");
    view.unmount();
    // R12: no eligible footer line, and another applicable EV Site with UNKNOWN coverage.
    const body = portfolioBody({
      footer: null,
      coverage: { ...portfolioBody().coverage, sites: SITES.map((s, i) => coverageSite(s.site_id, i === 3 ? "UNKNOWN" : "CURRENT")) },
    });
    renderScope(portfolioClient(loadedPortfolio(body)));
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
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody({ rows: [row(), twin] })))));
    await settledScreen();
    const main = document.querySelector(".estate-portfolio") as HTMLElement;
    // PF-T (v71 `portfolio-tabs.html` supersedes the v69 one-page composition): the title, the cutoff line (SR-1: the
    // range itself is in the shell's shared top bar) and the context row sit above the tab row, and the panel follows.
    const order = ["h1", "[data-portfolio-cutoff]", "[data-portfolio-context]", "[data-section-tabs]", "[data-portfolio-tab-panel]"];
    const nodes = order.map((sel) => main.querySelector(sel) as HTMLElement);
    nodes.forEach((n) => expect(n).not.toBeNull());
    for (let i = 1; i < nodes.length; i += 1) {
      expect(nodes[i - 1].compareDocumentPosition(nodes[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
    // Each v69 panel now sits on its own tab; each tab shows exactly its panel titles.
    // IA-P2 P3b (spec §2.2, §2.4): two tabs remain here; What changed is Results' panel and Scope & coverage is
    // Evidence's section (their panel titles are pinned in Results.test.tsx and estateEvidence.test.tsx). The Overview
    // is E2's page (portfolioHub.test.tsx).
    const perTab: [string, string[]][] = [
      ["Outcomes", ["Outcomes across the estate"]],
      ["Demand & capacity", ["An opportunity beyond reducing cost"]],
    ];
    for (const [label, titles] of perTab) {
      showTab(label);
      if (label === "Outcomes") openObjectives();
      expect(renderedPanelTitles(), label).toEqual(titles);
      if (label === "Outcomes") {
        // IA-P3 P4b (spec §6 P4b): Outcomes leads with E1 (L1 headline, L2 Sites rows), then L3's cards; the objectives
        // panel is last, inside the Disclosure. So "nothing before panel 1" becomes that order, with nothing else before.
        const panel = main.querySelector('[data-disclosure="portfolio-objectives"]') as HTMLElement;
        const l3 = panel.closest('[data-level="L3"]') as HTMLElement;
        expect(l3).not.toBeNull();
        expect(l3.previousElementSibling).not.toBeNull();
        expect([...l3.children].map((c) => c.getAttribute("data-portfolio-cards") !== null || c === panel || c.matches("p.range-part"))).toEqual(
          [...l3.children].map(() => true),
        );
        expect(l3.lastElementChild).toBe(panel);
      } else {
        expect(leadingIntruders(main, "portfolio"), `${label}: before panel 1`).toEqual([]);
      }
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
    showTab("Outcomes");
    // OUT-B B6 (R521): the outcome matrix replaces the objectives matrix in the same scroll container.
    expect(main.querySelector("[data-portfolio-scroll='objectives'] .oc-matrix")).not.toBeNull();
    expect(main.querySelector(".objective-matrix")).toBeNull();
    expect(COLD_ROW.links.finding).toBeNull();
  });

  it("uqfi2_every_tab_has_one_headline_and_keeps_its_gaps", async () => {
    // UQ-FI-2 (D-UQFI.4, rev 6 6.1 P1): one h1 on every tab, the page title, first in its header; the subtitle
    // sentence under it. The Portfolio outcome card and matrix are out of the collapse (D-UQFI.12, rev 6 6.1).
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const ids = gapIds();
    for (const label of ["Outcomes", "Demand & capacity"]) {
      showTab(label);
      // IA-P2 P3b (spec §5.3): the Portfolio header is the title "Portfolio" alone (5c's H1, on all three tabs).
      const h1 = expectOneHeadline("Portfolio");
      expect(h1.closest(".page-header")?.querySelector(".page-header__subtitle")).toBeNull();
    }
    showTab("Outcomes");
    expect(gapIds()).toEqual(ids);
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
    for (const site of objectives) for (const c of site.cells) if (c.destination !== null) expect(outcomes.querySelector(`a[href^='${c.destination}']`)).toBeNull();
    const summary = outcomeSummaryBody();
    for (const site of summary.sites) {
      const cells = Array.from(outcomes.querySelectorAll(`[data-portfolio-outcome-cell^='${site.site_code}|']`));
      expect(cells).toHaveLength(4);
      for (const el of cells) {
        expect(el.tagName).toBe("A");
        // D-SR.42(d): a server href with its own window keeps it; a bare one carries the address range.
        expect(el.getAttribute("href")).toBe(site.overview_href.includes("from=") ? site.overview_href : ranged(site.overview_href));
      }
    }
    expect(text(outcomes)).not.toContain("No configured objective");
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
    renderScope(fake);
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
    renderScope(fake);
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
      ["/portfolio/outcomes?from=2026-10-07T00:00:00Z&to=2026-10-05T00:00:00Z", "The selected window needs both a start and an end, with the start before the end."],
      ["/portfolio/outcomes?from=2024-08-01T00:00:00Z&to=2026-10-01T00:00:00Z", "The selected window is longer than 31 days."],
      [ENTRY, "The selected window is invalid."],
    ];
    for (const [entry, copy] of cases) {
      const view = renderAt(entry, portfolioClient(refused(422, "INVALID_WINDOW", "server copy")));
      await settledScreen();
      expect(text(document.querySelector("[data-page-refusal='INVALID_WINDOW'] p"))).toBe(copy);
      expect(text(document.querySelector("[data-page-refusal='INVALID_WINDOW'] [data-refusal-title]"))).toBe("Window cannot be read");
      expect(text(document.querySelector("[data-estate-window]"))).toBe("Window not valid");
      expect(text(document.querySelector("[data-estate-cutoff-line]"))).not.toMatch(/2026-10-07|Oct/);
      view.unmount();
    }
    // A non-window refusal keeps its own copy; the requested range is the shell's shared bar (SR-1), so the page's
    // cutoff line says nothing about the window.
    const view = renderAt(ENTRY, portfolioClient(refused(503, "ESTATE_STORE_UNAVAILABLE", "Estate records are unavailable right now. Try again.")));
    await settledScreen();
    expect(text(document.querySelector("[data-page-refusal]"))).toBe("Estate records are unavailable right now. Try again.");
    expect(document.querySelector("[data-estate-window]")).toBeNull();
    view.unmount();
  });
});

// IA-P2 P3b (D-IAP.12): `namesOnePrioritySiteInTheSingular` pinned the pulse's "1 priority site"; the pulse left the
// Portfolio with the Overview branch, so the test is retired (no replacement: the pulse no longer exists).

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
        text(whyOf(c.getAttribute("data-portfolio-card") ?? "").querySelector("[data-portfolio-card-definition]")),
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
    // IA-P2 P3b: the Outcomes tab holds the cards and the objectives panel; per-tab titles are pinned in
    // rendersMeasuredPanelHierarchyAndScrollContainers. IA-P3 P4b: the panel is inside the closed Disclosure.
    openObjectives();
    expect(renderedPanelTitles()).toEqual(["Outcomes across the estate"]);
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

  it("uqfi3OneFigureOneSentenceTheBasisAndTheQualifiersBehindWhy", async () => {
    // UQ-FI-3 (rev 7, 7.2; v7.2 sheet "Outcome card"): a card shows one figure, one sentence and the basis line; every
    // other server line is behind its "Why?", none lost and none added.
    const cards = serverCards({
      GROW_REVENUE: serverCard({
        value: { text: "4.20 USD", small: "estimated" },
        detail: "Depot 4.20 USD · each site's latest assessed period",
        basis_text: "Declared price × measured kWh · not billed or collected",
        days_line: "Kobo: Complete readings on 5 of 7 days",
        parts: { target: "Not declared", potential: "18–20 kW unused", income: "4.20 USD estimated", income_note: "Not billed or collected" },
      }),
      PROTECT_ASSET: PROTECT_WITH_FUEL,
      ASSURE_PERFORMANCE: ASSURE_WITH_VALUES,
    });
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: outcomeSummaryBody({ cards }) }));
    await settledScreen();
    const hooks = (root: Element) =>
      [...new Set([...root.querySelectorAll("*")].flatMap((n) => [...n.attributes].map((a) => a.name)).filter((a) => a.startsWith("data-portfolio-")))].sort();
    const onCard = ["data-portfolio-card-basis", "data-portfolio-card-detail", "data-portfolio-card-link", "data-portfolio-card-name", "data-portfolio-card-value"];
    const behind: Record<string, string[]> = {
      GROW_REVENUE: ["data-portfolio-card-days", "data-portfolio-card-definition", "data-portfolio-card-dots", "data-portfolio-dot", "data-portfolio-grow-note", "data-portfolio-grow-part", "data-portfolio-grow-parts"],
      OPTIMIZE_COST: ["data-portfolio-card-definition", "data-portfolio-card-dots", "data-portfolio-dot"],
      PROTECT_ASSET: ["data-portfolio-card-definition", "data-portfolio-card-dots", "data-portfolio-card-fuel-line", "data-portfolio-card-fuel-note", "data-portfolio-dot"],
      ASSURE_PERFORMANCE: ["data-portfolio-card-definition", "data-portfolio-card-dots", "data-portfolio-card-value-line", "data-portfolio-card-value-note", "data-portfolio-dot"],
    };
    for (const key of Object.keys(behind)) {
      const c = card(key);
      expect(c.querySelectorAll("[data-portfolio-card-value]")).toHaveLength(1);
      expect(c.querySelector("[data-portfolio-card-value]")?.classList.contains("oc-pffig")).toBe(true);
      expect(c.querySelectorAll("[data-why-button]")).toHaveLength(1);
      expect(hooks(c)).toEqual(onCard);
      const why = whyOf(key);
      expect(hooks(why)).toEqual(behind[key]);
      expect(why.querySelectorAll("[data-portfolio-dot] [data-status-pill]")).toHaveLength(4);
    }
    // The Why? lines are the server's, verbatim.
    expect([...whyOf("PROTECT_ASSET").querySelectorAll("[data-portfolio-card-fuel-line]")].map((n) => n.textContent)).toEqual(PROTECT_WITH_FUEL.fuel_lines);
    expect([...whyOf("ASSURE_PERFORMANCE").querySelectorAll("[data-portfolio-card-value-line]")].map((n) => n.textContent)).toEqual(ASSURE_WITH_VALUES.value_lines);
    expect(text(whyOf("GROW_REVENUE").querySelector("[data-portfolio-card-days]"))).toBe("Different days: Kobo: Complete readings on 5 of 7 days");
    // D-UQFI.7: the card figure is the one --text-figure (30 px) element.
    const css = readSrc("estate/estatePortfolio.css");
    expect(css).toMatch(/\.oc-pfcard \.value-number\.oc-pffig\{font-size:var\(--text-figure\)/);
    expect(readSrc("ui/tokens.css")).toContain("--text-figure: var(--font-size-800);");
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

  // 1a (spec §3.5, D-1A.3, D-1A.10 I2): the Optimize card's day and scope, server text, on the face in v70's
  // `oc-pfdays` slot (after the figure, before the sentence); every other card unchanged.
  const SCOPE = "Cost of Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their total";
  const faceHooks = (root: Element) =>
    [...new Set([...root.querySelectorAll("*")].flatMap((n) => [...n.attributes].map((a) => a.name)).filter((a) => a.startsWith("data-portfolio-")))].sort();
  const ON_CARD = ["data-portfolio-card-basis", "data-portfolio-card-detail", "data-portfolio-card-link", "data-portfolio-card-name", "data-portfolio-card-value"];
  const scoped = () => outcomeSummaryBody({ cards: serverCards({ OPTIMIZE_COST: { ...OPTIMIZE_ONE_SITE, scope_text: SCOPE } }) });

  it("f1OptimizeFaceStatesTheServerScopeBetweenTheFigureAndTheSentence", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: scoped() }));
    await settledScreen();
    const optimize = card("OPTIMIZE_COST");
    const scope = optimize.querySelectorAll("[data-portfolio-card-scope]");
    expect(scope).toHaveLength(1);
    expect(scope[0].textContent).toBe(SCOPE);
    expect(scope[0].tagName).toBe("SMALL");
    expect(scope[0].classList.contains("oc-pfdays")).toBe(true);
    const fig = optimize.querySelector("[data-portfolio-card-value]") as Element;
    const detail = optimize.querySelector("[data-portfolio-card-detail]") as Element;
    expect(fig.compareDocumentPosition(scope[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(scope[0].compareDocumentPosition(detail) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(fig.contains(scope[0])).toBe(false);
    expect(value("OPTIMIZE_COST")).toBe("3.31 USD possible extra fuel cost");
    expect(faceHooks(optimize)).toEqual([...ON_CARD, "data-portfolio-card-scope"].sort());
  });

  it("f2NoScopeLineWithoutServerScopeText", async () => {
    for (const optimize of [{ ...OPTIMIZE_ONE_SITE, scope_text: null }, OPTIMIZE_ONE_SITE]) {
      const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: outcomeSummaryBody({ cards: serverCards({ OPTIMIZE_COST: optimize }) }) }));
      await settledScreen();
      expect(document.querySelector("[data-portfolio-card-scope]")).toBeNull();
      expect(faceHooks(card("OPTIMIZE_COST"))).toEqual(ON_CARD);
      view.unmount();
    }
  });

  it("f3TheOtherThreeCardsNeverRenderAScopeLine", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: scoped() }));
    await settledScreen();
    expect(document.querySelectorAll("[data-portfolio-card-scope]")).toHaveLength(1);
    for (const key of ["GROW_REVENUE", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]) {
      expect(card(key).querySelector("[data-portfolio-card-scope]")).toBeNull();
      expect(card(key).querySelector(".oc-pfdays")).toBeNull();
      expect(text(card(key))).not.toContain(SCOPE);
      expect(faceHooks(card(key))).toEqual(ON_CARD);
    }
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

  it("pulseCountsSummaryWarningsAndCountsThemSeparatelyOnTheProtectCard", async () => {
    // IA-P P2: the warning list under the ranked table left with the table; the pulse and the Protect card stay.
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings(five(), 4) }));
    await settledScreen();
    // IA-P2 P3b (D-IAP.12): the pulse's "{n} warnings not yet priced" line left with the pulse; the Protect card's own
    // server line (below) is the one place the count shows.
    expect(document.querySelector("[data-portfolio-pulse]")).toBeNull();
    expect(protectDetail()).toBe("Service disruptions recorded as findings · 4 early warnings, counted separately · loss not priced");
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });

  it("oneWarningIsSingularAndZeroIsShownWithNoList", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings([planWarning()], 1) }));
    await settledScreen();
    expect(protectDetail()).toBe("Service disruptions recorded as findings · 1 early warning, counted separately · loss not priced");
    cleanup();
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: withWarnings([], 0) }));
    await settledScreen();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(protectDetail()).toBe("Service disruptions recorded as findings · 0 early warnings, counted separately · loss not priced");
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });

  it("summaryNotLoadedReadsUnknownAndTheProtectCardHasNoServerText", async () => {
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }));
    await settledScreen();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
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
    const client = withOutcomeSummary(portfolioClient(loadedPortfolio(body)), { status: "loaded", value: outcomeSummaryBody({ coverage_line: COVERAGE_INCOMPLETE }) });
    // IA-P2 P3b: the context row stays on the tabs; the coverage line and the scope drawer are the Evidence section's.
    renderAt(ENTRY, client);
    await settledScreen();
    const context = document.querySelector("[data-portfolio-context]") as HTMLElement;
    expect(context.getAttribute("data-portfolio-context")).toBe("PARTIAL");
    expect(text(context.querySelector(".portfolio-badge"))).toBe("Some days incomplete");
    expect(text(context.querySelector("[data-portfolio-sentence]"))).toBe("Portfolio: Some sites have incomplete days");
    expect(context.querySelector("[data-portfolio-partial]")).toBeNull(); // R620's per-Site notes are gone
    cleanup();
    renderScope(client);
    await settledScreen();
    const line = await coverageLine();
    expect(line.getAttribute("data-portfolio-coverage")).toBe("INCOMPLETE");
    expect(text(line.querySelector("[data-portfolio-coverage-lead]"))).toBe("Some days have incomplete readings · 1 site with incomplete days");
    expect(Array.from(line.querySelectorAll("[data-portfolio-coverage-site]")).map(text)).toEqual([
      "Kobo: complete readings on 5 of 7 days · 1 with partial readings · 11 Oct: no readings · 12 Oct: not analysed yet",
      "GreenHarvest: complete readings on 7 of 7 days",
    ]);
    // IA-P2 P3b: the scope section is Evidence & records' (renderScope), not a tab.
    const drawer = document.querySelector("[data-portfolio-drawer='scope']") as HTMLElement;
    const cell = drawer.querySelector("[data-portfolio-scope-site='KOBO-001'] [data-portfolio-scope-coverage]");
    // review L1: the incomplete days sit on their own line under the coverage words
    const beforeBreak = Array.from(cell?.childNodes ?? []);
    expect(beforeBreak.slice(0, beforeBreak.findIndex((n) => n.nodeName === "BR")).map((n) => n.textContent).join("")).toBe(
      "Mini-grid · Incomplete days",
    );
    expect(cell?.querySelector("br + [data-portfolio-scope-gaps]")).not.toBeNull();
    expect(text(cell?.querySelector("[data-portfolio-scope-gaps]") ?? null)).toBe("Incomplete days: 11 Oct: no readings · 12 Oct: not analysed yet");
    // IA-P P2: the row value moved to the Decisions list's At stake cell, built by the same consequenceFirst.
    expect(consequenceFirst(body.rows.find((r) => r.finding_id.startsWith("f1f1f1f1"))!, body.coverage.sites[0])).toBe("Value not shown while this site has incomplete days");
    // the coverage line stays above the tabs on every tab
    expect(document.querySelectorAll("[data-portfolio-coverage]")).toHaveLength(1);
    // no state code on screen, in a title or in an aria-label; no "checked" for data anywhere on the page
    const page = document.body.textContent ?? "";
    expect(page).not.toMatch(/PARTIAL|UNASSESSED|NO_ASSESSED_SELECTION|NO_READINGS|NOT_ANALYSED|estate-coverage/);
    expect(page).not.toMatch(/days? checked|partly checked|not checked yet/i);
    const attrs = Array.from(document.querySelectorAll("[title],[aria-label]")).map((e) => `${e.getAttribute("title") ?? ""} ${e.getAttribute("aria-label") ?? ""}`);
    expect(attrs.join(" ")).not.toMatch(/PARTIAL|UNASSESSED|checked/i);
  });

  // PARTIAL-MONEY (D-E5.45 owner option 2; label D-E5.46): a Finding on an analysed day shows its amount, named as
  // the analysed days' only, and its gap clause is the coverage line's, from the same `days` block.
  it.each([
    ["NO_READINGS", "4 Nov: no readings"],
    ["READINGS_CONFLICT", "4 Nov: conflicting readings"],
    ["NOT_ENOUGH_READINGS", "4 Nov: not enough readings"],
  ])("partialSiteShowsTheAnalysedDaysAmountWithItsLabel %s", async (reason, clause) => {
    const body = partialBody(["2026-11-04"]);
    const kobo = body.coverage.sites[0].days!;
    kobo.gaps = [{ day: "2026-11-04", state: "UNASSESSED", reason }];
    body.rows = [COLD_ROW, row()]; // the analysed-day row carries its stored amount
    renderScope(withOutcomeSummary(portfolioClient(loadedPortfolio(body)), { status: "loaded", value: outcomeSummaryBody({ coverage_line: COVERAGE_INCOMPLETE }) }));
    await settledScreen();
    const line = await coverageLine();
    // IA-P P2: the row value is the Decisions list's At stake cell, built by the same consequenceFirst.
    const value = consequenceFirst(body.rows[1], body.coverage.sites[0]);
    expect(value).toBe(`$3.31–$3.97 for 6 of 7 days analysed · ${clause}`);
    // one day set: the coverage line names the same gap day with the same words, and the count excludes it
    expect(text(line.querySelector("[data-portfolio-coverage-site]"))).toBe(
      `Kobo: complete readings on 5 of 7 days · 1 with partial readings · ${clause}`,
    );
    expect(value).not.toMatch(/estimate|NO_READINGS|READINGS_CONFLICT|NOT_ENOUGH/);
  });

  it("partialSiteMoreThanThreeGapDaysReadAsACountInTheMoneyLabel", async () => {
    const body = partialBody(["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"], 14);
    body.rows = [COLD_ROW, row()];
    renderScope(withOutcomeSummary(portfolioClient(loadedPortfolio(body)), { status: "loaded", value: outcomeSummaryBody({ coverage_line: COVERAGE_INCOMPLETE }) }));
    await settledScreen();
    expect(consequenceFirst(body.rows[1], body.coverage.sites[0])).toBe(
      "$3.31–$3.97 for 10 of 14 days analysed · 4 days without a usable result",
    );
  });

  // D-E5.46: days sharing a reason are grouped; more than 3 gap days read as one count (the deep tab lists all).
  it("incompleteSiteWithManyGapsReadsACountAndTheScopeTabListsThem", async () => {
    const gaps = ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"];
    renderScope(withOutcomeSummary(portfolioClient(loadedPortfolio(partialBody(gaps, 14))), { status: "loaded", value: outcomeSummaryBody({ coverage_line: COVERAGE_INCOMPLETE }) }));
    await settledScreen();
    const line = await coverageLine();
    expect(text(line.querySelector("[data-portfolio-coverage-site]"))).toBe(
      "Kobo: complete readings on 5 of 7 days · 1 with partial readings · 4 days without a usable result",
    );
    // IA-P2 P3b: the scope section is Evidence & records' (renderScope), not a tab.
    // an older body's reason (NO_ASSESSED_SELECTION) reads as system work, never as a code
    expect(text(document.querySelector("[data-portfolio-scope-gaps]"))).toBe("Incomplete days: 1, 2, 3, 4 Oct: not analysed yet");
  });

  it("coverageLineCollapsesWhenEveryDayIsCompleteAndExplainsItsWords", async () => {
    const complete = { ...COVERAGE_INCOMPLETE, state: "COMPLETE" as const, lead: "Complete readings on every day" };
    renderScope(withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody())), { status: "loaded", value: outcomeSummaryBody({ coverage_line: complete }) }));
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
    expect(line.querySelector("[data-portfolio-coverage-link]")?.getAttribute("href")).toContain("/evidence");  // IA-P2 P3b: the scope link goes to Evidence & records (spec §2.4)
    // IA-P2 P3b placement: the coverage line leads the scope section (it was after the context row, before the tabs),
    // ahead of the scope drawer and the context footer.
    const order = ["[data-portfolio-coverage]", "[data-portfolio-drawer='scope']", "[data-portfolio-footer]"].map((sel) => document.querySelector(sel)!);
    expect(order[0].compareDocumentPosition(order[1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(order[1].compareDocumentPosition(order[2]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("coverageLineSaysNotKnownUntilTheSummaryLoads", async () => {
    renderScope(portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const line = document.querySelector("[data-portfolio-coverage]") as HTMLElement;
    expect(line.getAttribute("data-portfolio-coverage")).toBe("LOADING");
    expect(text(line.querySelector("[data-portfolio-coverage-lead]"))).toBe("Day readings are not known yet");
  });

  it("nonPartialBodiesShowNoGapLine", async () => {
    for (const body of [portfolioBody(), STATUS_BODIES.UNKNOWN]) {
      // PF-T: on the Scope & coverage tab, where the scope drawer (and its gap lines) render.
      const view = renderScope(portfolioClient(loadedPortfolio(body)));
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
  type Summary = ReturnType<typeof portfolioBody>["summary"];
  const kobo: EstateCheckedDays = { site_id: "s-kobo", site_name: "Kobo", checked: 5, requested: 7 };
  const harbour: EstateCheckedDays = { site_id: "s-harbour", site_name: "Harbour", checked: 6, requested: 7 };
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
  const dayText = (key: string) => text(whyOf(key).querySelector("[data-portfolio-card-days]"));
  const noteText = (key: string) => text(whyOf(key).querySelector("[data-portfolio-card-note]"));

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
    expect(whyOf("PROTECT_ASSET").querySelector("[data-portfolio-card-days]")?.className).toContain("oc-pfdays");
    // CH6b2-R Q1: the Portfolio-body clause is its own line; the detail is the server's detail, not joined with it.
    expect(noteText("PROTECT_ASSET")).toBe("Findings next to unchecked days are not shown yet");
    expect(detail("PROTECT_ASSET")).not.toContain("not shown yet");
    expect(detail("ASSURE_PERFORMANCE")).toBe("No verified result yet · no targets declared · no evidence gaps on the days assessed");
    expect(whyOf("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-note]")).toBeNull();
    // CH5d1-R: Optimize is the server cost card; a stored consequence has no days line, and no body note.
    expect(detail("OPTIMIZE_COST")).toBe("At Kobo · not added across sites");
    expect(whyOf("OPTIMIZE_COST").querySelector("[data-portfolio-card-days]")).toBeNull();
    expect(whyOf("OPTIMIZE_COST").querySelector("[data-portfolio-card-note]")).toBeNull();
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
    expect(scanCards()).toBe("");
  });

  it("completeBasisHasNoDaysLineAndNoNote", async () => {
    renderServer({ PROTECT_ASSET: serverCard({ value: { text: "No sites disrupted", small: null } }) }, {}, { count_basis: "COMPLETE", checked_days: [kobo] });
    await settledScreen();
    expect(value("PROTECT_ASSET")).toBe("No sites disrupted");
    expect(whyOf("PROTECT_ASSET").querySelector("[data-portfolio-card-days]")).toBeNull();
    expect(whyOf("PROTECT_ASSET").querySelector("[data-portfolio-card-note]")).toBeNull();
  });

  it("pv1AssureCardRendersEachValueLineThenItsClauseAndTheBodyNoteAlone", async () => {
    // PV-1-R §2/§4: one server line per verified result (never a total), then the card's clause, then the body note.
    renderServer({ ASSURE_PERFORMANCE: ASSURE_WITH_VALUES }, { ASSURE_PERFORMANCE: "evidence gap at 1 site" });
    await settledScreen();
    // UQ-FI-3: the detail is the card's one sentence; the value lines, their note and the body note sit behind "Why?".
    expect(detail("ASSURE_PERFORMANCE")).toBe(ASSURE_WITH_VALUES.detail);
    const assure = whyOf("ASSURE_PERFORMANCE");
    const lines = [...assure.querySelectorAll("[data-portfolio-card-value-line]")];
    expect(lines.map((n) => n.textContent)).toEqual(ASSURE_WITH_VALUES.value_lines);
    expect(lines.every((n) => n.className === "oc-pfnote")).toBe(true);
    expect(text(assure.querySelector("[data-portfolio-card-value-note]"))).toBe(ASSURE_WITH_VALUES.value_note);
    expect(text(assure.querySelector("[data-portfolio-card-note]"))).toBe("evidence gap at 1 site");
    // Render order behind "Why?": value lines, value note, body note.
    const order = [...assure.querySelectorAll("[data-portfolio-card-detail], [data-portfolio-card-value-line], [data-portfolio-card-value-note], [data-portfolio-card-note]")]
      .map((n) => [...n.attributes].map((a) => a.name).find((a) => a.startsWith("data-portfolio-card-")));
    expect(order).toEqual(["data-portfolio-card-value-line", "data-portfolio-card-value-line", "data-portfolio-card-value-note", "data-portfolio-card-note"]);
    // No other card carries value lines.
    for (const key of ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET"]) {
      expect(whyOf(key).querySelector("[data-portfolio-card-value-line], [data-portfolio-card-value-note]")).toBeNull();
    }
    expect(scanCards()).toBe("");
  });

  it("k4bProtectCardRendersEachFuelLineThenItsClauseAfterTheDetail", async () => {
    // DIESEL-1-R3j: one server line per unexplained-fuel Finding (never a total), then its clause.
    renderServer({ PROTECT_ASSET: PROTECT_WITH_FUEL });
    await settledScreen();
    // UQ-FI-3: the detail is the card's one sentence; the fuel lines and their clause sit behind "Why?".
    expect(detail("PROTECT_ASSET")).toBe(PROTECT_WITH_FUEL.detail);
    const protect = whyOf("PROTECT_ASSET");
    const lines = [...protect.querySelectorAll("[data-portfolio-card-fuel-line]")];
    expect(lines.map((n) => n.textContent)).toEqual(PROTECT_WITH_FUEL.fuel_lines);
    expect(lines.every((n) => n.className === "oc-pfnote")).toBe(true);
    expect(text(protect.querySelector("[data-portfolio-card-fuel-note]"))).toBe(PROTECT_WITH_FUEL.fuel_note);
    const order = [...protect.querySelectorAll("[data-portfolio-card-detail], [data-portfolio-card-fuel-line], [data-portfolio-card-fuel-note]")]
      .map((n) => [...n.attributes].map((a) => a.name).find((a) => a.startsWith("data-portfolio-card-")));
    expect(order).toEqual(["data-portfolio-card-fuel-line", "data-portfolio-card-fuel-line", "data-portfolio-card-fuel-note"]);
    for (const key of ["GROW_REVENUE", "OPTIMIZE_COST", "ASSURE_PERFORMANCE"]) {
      expect(whyOf(key).querySelector("[data-portfolio-card-fuel-line], [data-portfolio-card-fuel-note]")).toBeNull();
    }
    expect(scanCards()).toBe("");
  });

  it("k4bProtectCardWithoutOrWithEmptyKeysRendersNoFuelLine", async () => {
    renderServer({ PROTECT_ASSET: serverCard({ detail: "Service disruptions recorded as findings · loss not priced", fuel_lines: [], fuel_note: null }) });
    await settledScreen();
    expect(whyOf("PROTECT_ASSET").querySelector("[data-portfolio-card-fuel-line], [data-portfolio-card-fuel-note]")).toBeNull();
  });

  it("pv1AssureCardWithoutTheKeysRendersNeitherLinesNorClause", async () => {
    renderServer({ ASSURE_PERFORMANCE: serverCard({ detail: "no targets declared" }) });
    await settledScreen();
    expect(whyOf("ASSURE_PERFORMANCE").querySelector("[data-portfolio-card-value-line], [data-portfolio-card-value-note]")).toBeNull();
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
    expect(whyOf("PROTECT_ASSET").querySelector("[data-portfolio-card-days], [data-portfolio-card-note]")).toBeNull();
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

  // IA-P2 P3b (D-IAP.12): `ch4_strip_counts_opportunities_from_the_opportunity_read_with_their_labels` pinned the pulse
  // strip's opportunity count; the strip left with the pulse, so the test is retired (the Demand & capacity panel's own
  // opportunity read is pinned by the ch4_opportunity_panel_* tests above).

  it("walk1_6_d4_card_dots_say_no_target_for_this_outcome", async () => {
    // WALK1-6 D4 (R697): the fixture's Kobo Protect row is NO_OBJECTIVE; its card dot reads per outcome.
    renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    const dot = whyOf("PROTECT_ASSET").querySelector('[data-portfolio-dot^="KOBO-001|"]') as HTMLElement;
    expect(dot.getAttribute("title")).toBe("Kobo: No target for this outcome");
    expect(text(dot.querySelector("[data-status-pill]"))).toBe("No target for this outcome");
    expect(text(card("PROTECT_ASSET"))).not.toContain("No objective declared");
    // Other states keep the server word.
    const other = whyOf("PROTECT_ASSET").querySelector('[data-portfolio-dot^="COLD-001|"]') as HTMLElement;
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
  const part = (name: string) => text(whyOf("GROW_REVENUE").querySelector(`[data-portfolio-grow-part='${name}']`));

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
    const parts = whyOf("GROW_REVENUE").querySelector("dl.oc-pfgrow") as HTMLElement;
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
    expect(whyOf("GROW_REVENUE").querySelector("[data-portfolio-grow-parts]")).toBeNull();
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
    const grow = whyOf("GROW_REVENUE");
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
    expect(card("GROW_REVENUE").querySelector(".oc-chip")).toBeNull();
  });

  it("growIncomeNoteIsOmittedWhenTheServerSendsNone", async () => {
    renderServer({ GROW_REVENUE: serverCard({ value: { text: "18–20 kW", small: "unused" }, parts: growParts() }) });
    await settledScreen();
    expect(whyOf("GROW_REVENUE").querySelector("[data-portfolio-grow-parts]")).not.toBeNull();
    expect(whyOf("GROW_REVENUE").querySelector("dd.oc-pfnote")).toBeNull();
  });

  it("growMissingKeepsTheGapAndNoPartsAndNoSummaryReadsNotKnown", async () => {
    const view = renderAt(ENTRY, withOutcomeSummary(portfolioClient(loadedPortfolio(portfolioBody()))));
    await settledScreen();
    expect(value("GROW_REVENUE")).toBe("Not available yet");
    expect(basis("GROW_REVENUE")).toBe("Opportunities · revenue not measured yet");
    expect(whyOf("GROW_REVENUE").querySelector("[data-portfolio-grow-parts]")).toBeNull();
    view.unmount();
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(value("GROW_REVENUE")).toBe("Not known yet");
  });
});

/**
 * PF-T: Portfolio section tabs (`archive/agent-history/architect-proposal-portfolio-layout-2026-11-10.md` §6, §11; layout
 * `frontend/mockups/v71/portfolio-tabs.html`). One assertion per card rule.
 */
describe("PF-T Portfolio section tabs", () => {
  const WINDOW_QUERY = "from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z&known_at=2026-10-07T00:05:00Z";
  // IA-P2 P3b (spec §2.2, D-IAP.4): three tabs, Overview, Outcomes and Demand & capacity, drawn by SectionTabs (no counts;
  // PortfolioTabs.tsx). The Overview page is E2's (`portfolioHub.test.tsx`); this file mounts the Outcomes tab.
  const TAB_NAMES = ["Overview", "Outcomes", "Demand & capacity"];
  const OUTCOMES = `/portfolio/outcomes?${WINDOW_QUERY}`;

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
  const tabLink = (name: string) => tabLinks().find((a) => text(a) === name)!;
  const paramsOf = (a: Element) => new URL(a.getAttribute("href")!, "http://x").searchParams;
  const pathOf = (a: Element) => new URL(a.getAttribute("href")!, "http://x").pathname;

  it("renders a Portfolio sections nav of links, the current tab marked aria-current", async () => {
    renderTabs(OUTCOMES, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(tabRow().tagName).toBe("NAV");
    expect(tabLinks().map((a) => text(a))).toEqual(TAB_NAMES);
    expect(tabLinks().filter((a) => a.getAttribute("aria-current") === "page")).toEqual([tabLink("Outcomes")]);
  });

  it("every tab link carries from, to and known_at", async () => {
    renderTabs(OUTCOMES, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    for (const a of tabLinks()) {
      const p = paramsOf(a);
      expect([p.get("from"), p.get("to"), p.get("known_at")]).toEqual(["2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z", "2026-10-07T00:05:00Z"]);
    }
    expect(tabLinks().map(pathOf)).toEqual(["/portfolio", "/portfolio/outcomes", "/portfolio/demand-and-capacity"]);
  });

  it("no tab shows a count badge, whether the counts are unknown or known (the Opportunity and What changed tabs left)", async () => {
    const base = portfolioBody();
    for (const body of [
      portfolioBody({ total_count: null, summary: { ...base.summary, opportunity_count: null, accepted_action_count: null } }),
      portfolioBody({ total_count: 6, summary: { ...base.summary, opportunity_count: 1, accepted_action_count: 3 } }),
    ]) {
      const view = renderTabs(OUTCOMES, portfolioClient(loadedPortfolio(body)));
      await settledScreen();
      expect(tabRow().querySelectorAll("[data-pf-tab-count]").length).toBe(0);
      expect(text(tabRow())).not.toMatch(/\d/);
      view.unmount();
    }
  });

  it("a tab change keeps the page mounted, reads nothing again and moves focus to the panel heading", async () => {
    const client = portfolioClient(loadedPortfolio(portfolioBody()));
    renderTabs(OUTCOMES, client);
    await settledScreen();
    const h1 = screen.getByRole("heading", { level: 1 });
    fireEvent.click(tabLink("Demand & capacity"));
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(`/portfolio/demand-and-capacity?${new URLSearchParams(WINDOW_QUERY).toString()}`);
    expect(client.calls.length).toBe(1);
    expect(screen.getByRole("heading", { level: 1 })).toBe(h1);
    expect(document.activeElement).toBe(screen.getByRole("heading", { level: 2, name: OPPORTUNITY_PANEL }));
  });

  it("Outcomes shows the four cards and no pulse, counts strip or top three (D-IAP.12)", async () => {
    const rows = [1, 2, 3, 4].map((n) => row({ finding_id: `f-${n}`, finding_revision_id: `r-${n}`, title: `Finding ${n}` }));
    const base = portfolioBody();
    renderTabs(OUTCOMES, portfolioClient(loadedPortfolio(portfolioBody({ rows, total_count: 4, summary: { ...base.summary, opportunity_count: 1 } }))));
    await settledScreen();
    expect(document.querySelectorAll(".oc-pfcard").length).toBe(4);
    expect(document.querySelector("[data-portfolio-pulse]")).toBeNull();
    expect(screen.queryByRole("region", { name: PRIORITY_PANEL })).toBeNull();
    expect(screen.queryByRole("group", { name: "Finding lens" })).toBeNull();
  });

  it("SR-1: the page has no date form of its own; the cutoff line sits under the title, above the tabs", async () => {
    renderTabs(OUTCOMES, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    expect(document.querySelector("[data-estate-date-bar]")).toBeNull();
    expect(document.querySelector('.estate-portfolio input[type="date"]')).toBeNull();
    const line = document.querySelector("[data-estate-cutoff-line]")!;
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(h1.compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(line.compareDocumentPosition(tabRow()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("the tab row wraps at 760 px and below", async () => {
    // jsdom has no layout: the wrap rule is asserted on the stylesheet (read from disk, as estateRoots does).
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const css = fs.readFileSync(`${cwd}/src/estate/estatePortfolio.css`, "utf8");
    expect(css).toMatch(/@media \(max-width: ?760px\)\s*\{[^@]*\.pf-tabs \.site-tabs__list\s*\{[^}]*flex-wrap: ?wrap/s);
  });
});
