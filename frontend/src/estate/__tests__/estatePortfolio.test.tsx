/**
 * W3-03 run 2: the estate Portfolio page under a local MemoryRouter (Lane A mounts the shell route), against the
 * v69 `portfolio` panels and `.agent/W3-03-build-spec.md` closures 1-5, r1a, r1b, r1b2 and r1b4 literals.
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { EstateClient, EstatePortfolioStatus } from "../estateClient";
import { EstatePortfolioPage } from "../EstatePortfolio";
import {
  COLD_ROW,
  coverageSite,
  loadedPortfolio,
  portfolioBody,
  portfolioClient,
  refused,
  row,
  SITES,
  STATUS_BODIES,
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
    const cards = Array.from(document.querySelectorAll("[data-portfolio-card]"));
    expect(cards.map((c) => c.getAttribute("data-portfolio-card"))).toEqual([
      "OPERATING_COST",
      "SERVICE_PRODUCT_RISK",
      "PRODUCTIVE_USE",
      "ASSET_LIFE",
      "VERIFIED_RECOVERY",
    ]);
    // R5: the Site-owned value is formatted from the exact selected line (outward to the minor unit).
    expect(text(cards[0].querySelector("[data-portfolio-card-value]"))).toBe("$3.31–$3.97");
    expect(text(cards[0])).toContain("Kobo · Candidate operating-cost exposure · 6 Oct 2026 · 14:20–15:20 UTC");
    expect(cards[0].tagName).toBe("A");
    expect(cards[0].getAttribute("href")).toBe("/financials?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z");
    // R6: no reviewed RISK producer, so the risk card is `Not assessed` and links to the risk root, not /findings.
    expect(text(cards[1].querySelector("[data-portfolio-card-value]"))).toBe("Not assessed");
    expect(cards[1].getAttribute("href")).toMatch(/^\/findings\/risks\?/);
    expect(cards[2].tagName).toBe("DIV");
    expect(cards[3].tagName).toBe("DIV");
    expect(cards[4].tagName).toBe("DIV");
    expect(within(cards[4] as HTMLElement).getByRole("link", { name: "Inspect financial basis" })).toBeTruthy();
    expect(text(document.body)).not.toMatch(/18–20|kW ×|\$2\.50|battery on watch|ACT-0/);
    const pulse = document.querySelector("[data-portfolio-pulse]") as HTMLElement;
    expect(text(pulse)).toContain("Not assessed priority sites");
    expect(text(pulse)).toContain("Distinct consequence categories · no combined savings total");
    const rows = Array.from(document.querySelectorAll("[data-portfolio-row]"));
    expect(rows).toHaveLength(2);
    expect(text(rows[0])).toContain("Unpriced");
  });

  it("rendersUnpricedCardAndEmptyRisksLensNotAssessed", async () => {
    const cards = portfolioBody().value_cards.map((c) =>
      c.key === "OPERATING_COST"
        ? { ...c, state: "UNPRICED" as const, line_keys: ["cold"], detail: "GreenHarvest · consequence recorded without a price", basis_text: "Price not established" }
        : c,
    );
    renderAt(`${ENTRY}&lens=risks`, portfolioClient(loadedPortfolio(portfolioBody({ value_cards: cards, rows: [], total_count: 0, lens: "risks" }))));
    await settledScreen();
    const first = document.querySelector("[data-portfolio-card='OPERATING_COST']") as HTMLElement;
    expect(text(first.querySelector("[data-portfolio-card-value]"))).toBe("Unpriced");
    expect(text(first)).toContain("GreenHarvest · consequence recorded without a price");
    expect(text(document.querySelector("[data-portfolio-card='SERVICE_PRODUCT_RISK'] [data-portfolio-card-value]"))).toBe("Not assessed");
    expect(text(document.querySelector("[data-portfolio-empty]"))).toBe("No matching supported Findings");
  });

  it("rendersEveryFindingColumnAndFourLensStates", async () => {
    const client = portfolioClient(
      loadedPortfolio(portfolioBody({ coverage: { ...portfolioBody().coverage, finding_state: "PARTIAL" } })),
    );
    renderAt(ENTRY, client);
    await settledScreen();
    const priority = panel("Where management should act first");
    expect(Array.from(priority.querySelectorAll("th")).map((th) => th.textContent)).toEqual([
      "Site",
      "Finding / operating mechanism",
      "Value / consequence",
      "Priority",
      "Confidence",
      "Action / next move",
    ]);
    expect(text(priority.querySelector("[data-portfolio-count]"))).toBe("2 selected Findings · coverage incomplete");
    const partialObjectives = document.querySelector("[data-portfolio-panel='objectives']") as HTMLElement;
    expect(text(partialObjectives)).toContain("Site detail is unavailable for these cells.");
    expect(text(partialObjectives)).not.toContain("Select a linked cell for context.");
    const w1 = priority.querySelector(`[data-portfolio-row^='f1f1f1f1']`) as HTMLElement;
    const cells = Array.from(w1.querySelectorAll("td")).map(lines);
    expect(cells[0]).toBe("Kobo Mini-grid Opens current Site view");
    expect(cells[1]).toBe("Extended generator support Finding KOBO-001 · f1f1f1f1-0000-4000-8000-000000000001 · Mechanism not recorded");
    expect(cells[2]).toBe("$3.31–$3.97 Basis not recorded 6 Oct 2026 · 14:20–15:20 UTC");
    expect(cells[3]).toBe("Not assessed");
    expect(cells[4]).toBe("Not assessed No reviewed confidence measure");
    expect(cells[5]).toBe("No accepted Action Next move not recorded Recommendation not accepted Review Finding");
    const cold = priority.querySelector(`[data-portfolio-row^='f2f2f2f2']`) as HTMLElement;
    expect(text(cold)).toContain("Finding detail unavailable");
    expect(cold.querySelector("[data-portfolio-finding-link]")).toBeNull();
    expect(text(priority)).toContain("Priority and confidence are not assessed for these records.");
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

  it("rendersFiveObjectiveRowsForEveryAuthorizedSite", async () => {
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody())));
    await settledScreen();
    const objectives = panel("Objectives across the estate");
    expect(Array.from(objectives.querySelectorAll("[data-portfolio-objective]")).map((r) => r.getAttribute("data-portfolio-objective"))).toEqual([
      "SERVICE_PRODUCT",
      "BACKUP",
      "ASSET_CONDITION",
      "COST_CONTROL",
      "EVIDENCE",
    ]);
    expect(Array.from(objectives.querySelectorAll("[data-portfolio-matrix-site]")).map((e) => `${e.firstChild?.textContent} ${text(e.querySelector("small"))}`)).toEqual([
      "Kobo KOBO-001",
      "GreenHarvest COLD-001",
      "Depot EV-LAB-001",
      "Harbour EV-LAB-002",
    ]);
    expect(objectives.querySelectorAll("[data-portfolio-cell]")).toHaveLength(20);
    const cell = (code: string, key: string) => objectives.querySelector(`[data-portfolio-cell^='${code}|${key}|']`) as HTMLElement;
    expect(text(cell("KOBO-001", "COST_CONTROL"))).toBe("ReviewSite detail unavailable");
    expect(text(cell("COLD-001", "COST_CONTROL"))).toBe("N/ASite detail unavailable");
    expect(text(cell("COLD-001", "EVIDENCE"))).toBe("LimitedSite detail unavailable");
    expect(text(cell("EV-LAB-001", "EVIDENCE"))).toBe("FullSite detail unavailable");
    expect(cell("KOBO-001", "SERVICE_PRODUCT").getAttribute("aria-description")).toBe("No reviewed objective assessment");
    expect(objectives.querySelector("a")).toBeNull();
    expect(text(objectives)).toContain(
      "Site-owned assessments · Unknown is not healthy. N/A means the objective is not configured. Site detail is unavailable for these cells.",
    );
    expect(text(objectives)).not.toContain("Select a linked cell for context.");
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
    const client = portfolioClient(loadedPortfolio(portfolioBody({ next_cursor: "c1" })), loadedPortfolio(pageTwo));
    renderAt(ENTRY, client);
    await settledScreen();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Load more Findings" }));
    });
    expect(document.querySelectorAll("[data-portfolio-row]")).toHaveLength(3);
    expect(document.querySelectorAll("[data-portfolio-card]")).toHaveLength(5);
    expect(document.querySelectorAll("[data-portfolio-cell]")).toHaveLength(20);
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
    expect(text(document.querySelector("[data-portfolio-card='OPERATING_COST'] [data-portfolio-card-value]"))).toBe("Not comparable for this selection");
  });

  it("noLineCardUsesExactShortLiteralFromApiAndFallback", async () => {
    // r3b: the API value and the missing-display_value fallback are both exactly "No supported value".
    const noLine = (display_value: string | null) => portfolioBody({
      value_cards: portfolioBody().value_cards.map((c) =>
        c.key === "OPERATING_COST" ? { ...c, state: "NO_LINE" as const, display_value, detail: "No selected operating-cost consequence", basis_text: "No value line", tone: "neutral" as const } : c,
      ),
    });
    const sel = "[data-portfolio-card='OPERATING_COST'] [data-portfolio-card-value]";
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
    expect(within(footer()).getByRole("link", { name: "Inspect energy basis →" }).getAttribute("href")).toBe("/sites/EV-LAB-001/evidence");
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
    renderAt(ENTRY, portfolioClient(loadedPortfolio(portfolioBody({ rows: [row(), twin] }))));
    await settledScreen();
    const labels = Array.from(document.querySelectorAll("[data-portfolio-row] td:nth-child(2) small:first-of-type")).map(text);
    expect(new Set(labels).size).toBe(2);
    expect(labels).toEqual([
      "Finding KOBO-001 · f1f1f1f1-0000-4000-8000-000000000001 · Mechanism not recorded",
      "Finding KOBO-001 · f1f1f1f1-0000-4000-8000-0000000000aa · Mechanism not recorded",
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
    expect(main.querySelector("[data-portfolio-scroll='objectives'] .objective-matrix")).not.toBeNull();
    expect(Array.from(main.querySelectorAll(".portfolio-bottom > section.panel")).map((p) => p.getAttribute("data-portfolio-panel"))).toEqual([
      "opportunity",
      "progress",
    ]);
    expect(COLD_ROW.links.finding).toBeNull();
  });
});
