/**
 * W3-02 commit 4 named frontend tests (`.agent/W3-02-build-spec.md` "Proof and builder handoff"): the estate
 * Financials root under a local MemoryRouter (Lane A mounts the shell route), against the v6.9 `globalfinancials`
 * panel structure, with every column, chip, link, note and grouping result asserted. Bodies are shaped as the
 * reviewed `estate-financials-1` wire; IDs are synthetic, and no mock Site, value or basis survives.
 */
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { EstateCoverageSite } from "../estateClient";
import {
  AGGREGATION_PANEL,
  AGGREGATION_PROSE,
  BASIS_UNRESOLVED,
  ESTATE_FINANCIALS_PATH,
  EstateFinancialsPage,
  FINANCIALS_NOTICE,
  NO_ACCESSIBLE_SITES,
  NO_COMPARABLE_TOTAL,
  NO_CONSEQUENCE_LINES,
  PRIOR_MINI_GRID_UNAVAILABLE,
  REGISTER_PANEL,
  REGISTER_SUBTITLE,
  SOURCE_UNAVAILABLE,
  STILL_ASSESSED,
} from "../EstateFinancials";
import {
  EVIDENCE_REFUSAL_COPY,
  createEstateFinancialsClient,
  type EstateFinancialsBody,
  type EstateFinancialsClient,
  type EvidenceResult,
  type FinancialGroup,
  type FinancialRow,
} from "../estateEvidenceMoneyClient";
import { NOT_DISPLAYABLE, diagnosticText, moneyText, roundDecimal } from "../estateFinancialsWords";

const FROM = "2026-10-13T00:00:00Z";
const TO = "2026-10-20T00:00:00Z";
const KNOWN = "2026-10-20T09:30:00Z";
const MINI = "10000000-0000-4000-8000-000000000011";
const COLD = "10000000-0000-4000-8000-000000000012";
const EV = "10000000-0000-4000-8000-000000000013";
const EV2 = "10000000-0000-4000-8000-000000000014";
const WINDOW = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const COLD_QUERY = "from=2026-10-14T08%3A00%3A00.000000Z&to=2026-10-14T16%3A00%3A00.000000Z&known_at=2026-10-20T09%3A00%3A00.000000Z";
const COLD_EVIDENCE = `/sites/COLD-LAB-001/evidence?${COLD_QUERY}`;
const EV_BRIDGE = `/sites/EV-LAB-001/ev/financials?${COLD_QUERY}`;
const KEY = (n: number) => `sha256:${String(n).repeat(64).slice(0, 64)}`;

function coverageSite(siteId: string, state: EstateCoverageSite["state"] = "CURRENT"): EstateCoverageSite {
  return { site_id: siteId, state, committed_watermark: null, selection_id: null, match_state: "COMPLETE", job_state: "SETTLED", source_freshness: "RECENT" };
}

function line(over: Partial<FinancialRow> & Pick<FinancialRow, "line_key">): FinancialRow {
  return {
    domain: "mini_grid",
    site_id: MINI,
    site_code: "KOBO-001",
    site_name: "Kobo Mini-grid",
    category: "CANDIDATE_OPERATING_COST_EXPOSURE",
    finding_id: null,
    finding_revision_id: null,
    consequence_revision_id: over.line_key.split(":")[1],
    window_start: "2026-10-14T08:00:00.000000Z",
    window_end: "2026-10-14T09:00:00.000000Z",
    quantity: { low: "0", high: "2.970000", unit: "L" },
    amount: { low: "0", high: "3.9612", currency: "USD" },
    period_kind: "OBSERVED_WINDOW",
    assumption_revision_ids: ["a0000000-0000-4000-8000-000000000001"],
    assumption_fingerprint: KEY(9),
    basis_evidence_ids: ["e0000000-0000-4000-8000-000000000001"],
    technical_interval_ids: ["p0000000-0000-4000-8000-000000000001"],
    overlap_group: "og-1",
    eligibility: "ELIGIBLE",
    reason_codes: [],
    limit: "Generator fuel quantity is modelled from accepted power readings",
    source_provenance: { state: "CURRENT" },
    links: { site: "/sites/KOBO-001", bridge: "/sites/KOBO-001/financials", evidence: "/sites/KOBO-001/evidence", current_view_label: "Opens current Site view" },
    disclosure: { pinned_amount: null },
    group_key: KEY(1),
    ...over,
  };
}

const MINI_LINE = line({ line_key: "mini_grid:c1000000-0000-4000-8000-000000000001" });
const COLD_LINE = line({
  line_key: "cold_chain:c2000000-0000-4000-8000-000000000002",
  domain: "cold_chain",
  site_id: COLD,
  site_code: "COLD-LAB-001",
  site_name: "Cold replay lab",
  category: "POTENTIAL_PRODUCT_EXPOSURE",
  window_start: "2026-10-14T08:00:00.000000Z",
  window_end: "2026-10-14T16:00:00.000000Z",
  quantity: { low: "25", high: "35", unit: "degC_min" },
  amount: null,
  assumption_revision_ids: [],
  assumption_fingerprint: null,
  technical_interval_ids: [],
  eligibility: "UNPRICED",
  reason_codes: ["UNPRICED"],
  limit: "Stock value is not declared, so product exposure stays unpriced.",
  links: { site: "/sites/COLD-LAB-001", bridge: `/sites/COLD-LAB-001/financials?${COLD_QUERY}`, evidence: COLD_EVIDENCE, current_view_label: null },
  group_key: KEY(2),
});
const EV_LINE = line({
  line_key: "ev_charging:c3000000-0000-4000-8000-000000000003",
  domain: "ev_charging",
  site_id: EV,
  site_code: "EV-LAB-001",
  site_name: "EV charging lab",
  category: "GROSS_TARIFF_SCENARIO",
  window_start: "2026-10-14T08:00:00.000000Z",
  window_end: "2026-10-15T08:00:00.000000Z",
  quantity: { low: "12.5", high: "12.5", unit: "kWh" },
  amount: { low: "36.005", high: "36.005", currency: "USD" },
  period_kind: "SCENARIO_WINDOW",
  limit: "Gross scenario only; not cash collected.",
  links: { site: "/sites/EV-LAB-001/ev", bridge: EV_BRIDGE, evidence: `/sites/EV-LAB-001/ev/evidence?${COLD_QUERY}`, current_view_label: null },
  group_key: KEY(3),
});

function group(over: Partial<FinancialGroup> & Pick<FinancialGroup, "category" | "state">): FinancialGroup {
  return {
    group_key: KEY(1),
    currency: "USD",
    window_start: "2026-10-14T08:00:00.000000Z",
    window_end: "2026-10-14T09:00:00.000000Z",
    period_kind: "OBSERVED_WINDOW",
    assumption_fingerprint: KEY(9),
    line_keys: [],
    amount: null,
    reason_codes: [],
    ...over,
  };
}

const STOCKED_GROUPS: FinancialGroup[] = [
  group({ category: "CANDIDATE_OPERATING_COST_EXPOSURE", state: "SINGLE_LINE", line_keys: [MINI_LINE.line_key] }),
  group({ group_key: KEY(2), category: "POTENTIAL_PRODUCT_EXPOSURE", state: "INELIGIBLE", currency: null, assumption_fingerprint: null, line_keys: [COLD_LINE.line_key], reason_codes: ["UNPRICED"] }),
  group({ group_key: KEY(3), category: "GROSS_TARIFF_SCENARIO", state: "SINGLE_LINE", period_kind: "SCENARIO_WINDOW", line_keys: [EV_LINE.line_key] }),
];

function body(over: Partial<EstateFinancialsBody> = {}): EstateFinancialsBody {
  const rows = over.rows ?? [MINI_LINE, COLD_LINE, EV_LINE];
  return {
    schema_version: "estate-financials-1",
    scope: { tenant_id: "t", authorized_site_count: 3, covered_site_count: 3, access_basis: `sha256:${"b".repeat(64)}` },
    window: { from: FROM, to: TO, bounds: "[from, to)", known_at: KNOWN },
    status: "CURRENT",
    coverage: { state: "COMPLETE", sites: [coverageSite(MINI), coverageSite(COLD), coverageSite(EV)] },
    summary: { eligible_line_count: 2, unpriced_line_count: 1, withheld_line_count: 0, estate_total: null, estate_total_state: "NO_ESTATE_TOTAL" },
    order: "window_start desc nulls last, site_code_key asc, site_id asc, category asc, line_key asc",
    total_count: rows.length,
    rows,
    groups: STOCKED_GROUPS,
    exclusions: [{ line_key: COLD_LINE.line_key, group_key: KEY(2), reason_codes: ["UNPRICED"] }],
    diagnostics: [],
    next_cursor: null,
    selection_token: `sha256:${"c".repeat(64)}`,
    ...over,
  };
}

function fake(result: EvidenceResult<EstateFinancialsBody>): EstateFinancialsClient & { calls: unknown[] } {
  const calls: unknown[] = [];
  return {
    calls,
    financials: (query) => {
      calls.push(query);
      return Promise.resolve(result);
    },
  };
}

const loaded = (value: EstateFinancialsBody): EvidenceResult<EstateFinancialsBody> => ({ status: "loaded", value });

function renderAt(entry: string, client: EstateFinancialsClient) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <main>
        <Routes>
          <Route path={ESTATE_FINANCIALS_PATH} element={<EstateFinancialsPage client={client} />} />
        </Routes>
      </main>
    </MemoryRouter>,
  );
}

function main(): HTMLElement {
  return document.querySelector("main") as HTMLElement;
}

function headers(panel: HTMLElement): string[] {
  return within(panel).getAllByRole("columnheader").map((h) => h.textContent ?? "");
}

function registerRows(): HTMLElement[] {
  return within(panelTitled(REGISTER_PANEL)).getAllByRole("row").slice(1);
}

function cells(row: HTMLElement): HTMLElement[] {
  return within(row).getAllByRole("cell");
}

function note(panel: string, key: string): string | null {
  return panelTitled(panel).querySelector(`[data-estate-note='${key}']`)?.textContent ?? null;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("W3-02 estate Financials root", () => {
  it("rendersMockFinancialPanelsAndUnpricedRows", async () => {
    renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake(loaded(body())));
    await settledScreen();
    expectV69Panels("globalfinancials");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio financials");
    const header = screen.getByRole("heading", { level: 1 }).closest("header") as HTMLElement;
    expect(within(header).getByText("Financials", { selector: ".page-header__eyebrow" })).toBeTruthy();
    expect(header.textContent).toContain("Estate consequences with source-site ownership and bounded interpretation");
    expect(main().querySelector("[data-estate-window]")?.textContent).toBe("Window 2026-10-13 to 2026-10-19 (UTC days)");
    // Static status bar: blue chip and subcopy, no assessment enum.
    const status = screen.getByRole("status", { name: "Financial status" });
    expect(status.querySelector("[data-estate-status-chip]")?.textContent).toBe("Site-owned consequences");
    expect(status.querySelector("[data-estate-status-chip]")?.className).toContain("estate-tone--blue");
    expect(status.textContent).toContain("Values grouped by basis and period; no financial assessment");
    const register = panelTitled(REGISTER_PANEL);
    expect(register.textContent).toContain(REGISTER_SUBTITLE);
    expect(headers(register)).toEqual(["Site", "Category", "Window / quantity", "Value", "Basis / limit", "Source"]);
    const notice = main().querySelector("[data-estate-notice]");
    expect(notice?.textContent).toBe(FINANCIALS_NOTICE);
    expect(notice?.className).not.toContain("v69-notice--blue"); // amber
    expect(panelTitled(AGGREGATION_PANEL).querySelector(".prose")?.textContent).toBe(AGGREGATION_PROSE);

    const [mini, cold, ev] = registerRows().map(cells);
    expect(mini.map((c) => c.firstElementChild?.textContent ?? c.textContent)).toEqual([
      "Kobo Mini-grid",
      "Candidate operating-cost exposure",
      "14 Oct 2026 · 08:00–09:00 UTC",
      "$0.00–$3.97", // outward to the minor unit: high 3.9612 rounds up
      "Generator fuel quantity is modelled from accepted power readings",
      "Site bridge →",
    ]);
    expect(mini[2].textContent).toContain("0–2.97 L");
    // Cold: every selected head is a row, unpriced, in °C-min, its own limitation; no mock `backup excursion`.
    expect(cells(registerRows()[1])[1].textContent).toBe("Potential product exposure");
    expect(cold[2].textContent).toBe("14 Oct 2026 · 08:00–16:00 UTC25–35 °C-min");
    expect(cold[3].querySelector("[data-estate-eligibility='UNPRICED']")?.textContent).toBe("Unpriced");
    expect(cold[3].querySelector(".estate-chip")?.className).toContain("estate-tone--amber");
    expect(cold[4].textContent).toContain("Stock value is not declared");
    expect(cold[4].textContent).toContain("Basis details");
    // EV: half even to two places as its Site page; a two-day window shows both endpoints; one kWh value.
    expect(ev[2].textContent).toBe("14 Oct 2026 · 08:00 UTC – 15 Oct 2026 · 08:00 UTC12.5 kWh");
    expect(ev[3].textContent).toBe("$36.00");
    expect(ev[4].textContent).toContain("Gross scenario only; not cash collected.");
    expect(ev[4].textContent).toContain("Basis details");
    // Exact IDs live in the closed basis disclosure only.
    const details = ev[4].querySelector("details") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.textContent).toContain("a0000000-0000-4000-8000-000000000001");
    expect(details.textContent).toContain(EV_LINE.line_key);
    // No estate total, no mock value, Site, basis or destination name.
    for (const mock of ["GreenHarvest", "Depot", "Kobo ·", "$36.00 ·", "Modelled fuel + scenario accrual", "backup excursion", "Stock / product loss not established", "Scenario tariff; not collections", "120 kWh", "Estate total"]) {
      expect(main().textContent).not.toContain(mock);
    }
    expectPlantedPanelRejected("globalfinancials");
  });

  it("rendersComparableAndExcludedReasons", async () => {
    const evA = line({ ...EV_LINE, line_key: "ev_charging:c4000000-0000-4000-8000-000000000004", amount: { low: "18.0025", high: "18.0025", currency: "KES" }, group_key: KEY(4) });
    const evB = line({ ...EV_LINE, line_key: "ev_charging:c5000000-0000-4000-8000-000000000005", site_id: EV2, site_code: "EV-LAB-002", site_name: "Second EV lab", amount: { low: "18.0035", high: "18.0035", currency: "KES" }, group_key: KEY(4) });
    const evUsd = line({ ...EV_LINE, line_key: "ev_charging:c6000000-0000-4000-8000-000000000006", amount: { low: "9", high: "9", currency: "USD" }, group_key: KEY(6) });
    const pending = line({ ...MINI_LINE, line_key: "mini_grid:c7000000-0000-4000-8000-000000000007", eligibility: "PENDING", amount: null, reason_codes: ["PENDING"], disclosure: { pinned_amount: { low: "1", high: "2.001", currency: "USD" } } });
    const groups: FinancialGroup[] = [
      // Mixed eligible/pending partition (commit-3 L4): the eligible mate carries only PARTITION_INELIGIBLE.
      group({ category: "CANDIDATE_OPERATING_COST_EXPOSURE", state: "INELIGIBLE", line_keys: [MINI_LINE.line_key, pending.line_key], reason_codes: ["PENDING"] }),
      group({ group_key: KEY(4), category: "GROSS_TARIFF_SCENARIO", state: "COMPARABLE", currency: "KES", period_kind: "SCENARIO_WINDOW", line_keys: [evA.line_key, evB.line_key], amount: { low: "36.006", high: "36.006", currency: "KES" } }),
      group({ group_key: KEY(6), category: "GROSS_TARIFF_SCENARIO", state: "SINGLE_LINE", period_kind: "SCENARIO_WINDOW", line_keys: [evUsd.line_key] }),
      group({ group_key: null, category: "POTENTIAL_PRODUCT_EXPOSURE", state: "NO_LINES", currency: null, window_start: null, window_end: null, period_kind: null, assumption_fingerprint: null, reason_codes: ["NO_LINES"] }),
    ];
    const value = body({
      rows: [MINI_LINE, pending, evA, evB, evUsd],
      groups,
      exclusions: [
        { line_key: MINI_LINE.line_key, group_key: KEY(1), reason_codes: ["PARTITION_INELIGIBLE"] },
        { line_key: pending.line_key, group_key: KEY(1), reason_codes: ["PENDING"] },
      ],
      // Commit-3 L3: three lines in the category, two currency values.
      diagnostics: [{ category: "GROSS_TARIFF_SCENARIO", code: "MIXED_CURRENCY", line_keys: [evA.line_key, evB.line_key, evUsd.line_key] }],
    });
    renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake(loaded(value)));
    await settledScreen();
    expectV69Panels("globalfinancials");
    const aggregation = panelTitled(AGGREGATION_PANEL);
    const results = Array.from(aggregation.querySelectorAll("[data-estate-group]"));
    expect(results.map((r) => r.querySelector("[data-estate-group-state]")?.textContent)).toEqual(["Not totalled", "Comparable", "Single line", "No lines"]);
    // Only COMPARABLE has a number, outward to the KES minor unit; no estate total anywhere.
    expect(results[1].textContent).toContain("Gross tariff estimate · KES 36.00–KES 36.01 · 2 lines");
    expect(results[1].querySelector(".estate-chip")?.className).toContain("estate-tone--green");
    expect(results[2].textContent).not.toContain("$9");
    expect(results[0].querySelector("[data-estate-group-reasons]")?.textContent).toBe("New work is being assessed");
    expect(results[3].textContent).toContain("Potential product exposure");
    expect(results[3].querySelector("[data-estate-group-reasons]")?.textContent).toBe("No consequence lines in this category");
    expect(aggregation.querySelector("[data-estate-note='no-comparable']")).toBeNull();
    // Ruling c4: every result sits in one closed summary row; four groups plus one diagnostic, one comparable total.
    const resultsDisclosure = aggregation.querySelector<HTMLDetailsElement>("[data-disclosure='estate-financials-results']");
    expect(resultsDisclosure?.open).toBe(false);
    expect(resultsDisclosure?.querySelector("[data-estate-summary-text]")?.textContent).toBe("Results (5) · 1 comparable total");
    expect(resultsDisclosure?.querySelector("summary")?.textContent).toContain("5 grouping results. 1 comparable total by basis; no estate total.");
    expect(resultsDisclosure?.querySelector("[data-estate-results]")).not.toBeNull();
    // L4 in plain words: the eligible mate is grouped with a line that cannot be totalled; the pending line is pending.
    expect(results[0].querySelector(`[data-estate-exclusion='${MINI_LINE.line_key}']`)?.textContent).toBe(
      "Kobo Mini-grid · Candidate operating-cost exposure: Grouped with a line that cannot be totalled",
    );
    expect(results[0].querySelector(`[data-estate-exclusion='${pending.line_key}']`)?.textContent).toBe(
      "Kobo Mini-grid · Candidate operating-cost exposure: New work is being assessed",
    );
    expect(aggregation.textContent).not.toContain("PARTITION_INELIGIBLE");
    // L3: the diagnostic names the category with more than one value, never a pairwise difference.
    const diagnostic = aggregation.querySelector("[data-estate-diagnostic='MIXED_CURRENCY']");
    expect(diagnostic?.textContent).toBe("Different valuesGross tariff estimate: more than one currency · 3 lines in the differing-value category");
    expect(aggregation.textContent).not.toMatch(/differ(s)? from|each other|MIXED_CURRENCY/);
    expect(diagnosticText("GROSS_TARIFF_SCENARIO", "DIFFERENT_WINDOW", 1)).toBe("Gross tariff estimate: more than one window · 1 line in the differing-value category");
    // A pending line shows no current value; its pinned value stays in the disclosure as not current.
    const pendingRow = registerRows()[1];
    expect(cells(pendingRow)[3].textContent).toBe("Pending");
    expect(cells(pendingRow)[4].textContent).toContain("Stored value, not current$1.00–$2.01");
    expect(main().textContent).not.toContain("Estate total");
  });

  it("rendersFinancialEmptyPendingAndRefusals", async () => {
    // Complete empty scope: headers kept, the note outside the table, no total.
    let view = renderAt(
      `${ESTATE_FINANCIALS_PATH}?${WINDOW}`,
      fake(loaded(body({ status: "EMPTY_SCOPE", scope: { tenant_id: "t", authorized_site_count: 0, covered_site_count: 0, access_basis: "x" }, coverage: { state: "EMPTY", sites: [] }, rows: [], total_count: 0, groups: [], exclusions: [], diagnostics: [] }))),
    );
    await settledScreen();
    expectV69Panels("globalfinancials");
    expect(headers(panelTitled(REGISTER_PANEL))).toHaveLength(6);
    expect(note(REGISTER_PANEL, "empty-scope")).toBe(NO_ACCESSIBLE_SITES);
    expect(panelTitled(REGISTER_PANEL).textContent).not.toContain(NO_CONSEQUENCE_LINES);
    expect(note(AGGREGATION_PANEL, "no-comparable")).toBe(NO_COMPARABLE_TOTAL);
    expect(panelTitled(AGGREGATION_PANEL).querySelector("[data-estate-results]")).toBeNull();
    // Ruling c4: the no-total meaning is the summary's accessible name and lives in the closed details, not a default paragraph.
    const emptySummary = panelTitled(AGGREGATION_PANEL).querySelector("[data-disclosure='estate-financials-results'] > summary");
    expect(emptySummary?.querySelector("[data-estate-summary-text]")?.textContent).toBe("Results (0) · No comparable total");
    expect(emptySummary?.textContent).toContain(`0 grouping results. ${NO_COMPARABLE_TOTAL}.`);
    expect(panelTitled(AGGREGATION_PANEL).querySelector("[data-estate-note='no-comparable']")?.closest("details")?.open).toBe(false);
    view.unmount();

    // Scope with no selected line.
    view = renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake(loaded(body({ rows: [], total_count: 0, groups: [], exclusions: [] }))));
    await settledScreen();
    expectV69Panels("globalfinancials");
    expect(note(REGISTER_PANEL, "no-selection")).toBe(NO_CONSEQUENCE_LINES);
    view.unmount();

    // Commit-3 L5: a pending/stale mini-grid selection has no register line; its category coverage is unknown and
    // the prior amount is unavailable in this selection (never "no consequence").
    const sentinel = group({ group_key: null, category: "CANDIDATE_OPERATING_COST_EXPOSURE", state: "UNKNOWN_COVERAGE", currency: null, window_start: null, window_end: null, period_kind: null, assumption_fingerprint: null, reason_codes: ["NO_LINES", "UNKNOWN_COVERAGE"] });
    for (const state of ["PENDING_RECOMPUTE", "STALE_SOURCE"] as const) {
      view = renderAt(
        `${ESTATE_FINANCIALS_PATH}?${WINDOW}`,
        fake(loaded(body({ status: state, coverage: { state: "PARTIAL", sites: [coverageSite(MINI, state), coverageSite(COLD), coverageSite(EV)] }, rows: [COLD_LINE, EV_LINE], total_count: 2, groups: [sentinel, ...STOCKED_GROUPS.slice(1)] }))),
      );
      await settledScreen();
      expectV69Panels("globalfinancials");
      expect(registerRows()).toHaveLength(2);
      expect(main().querySelector("[data-estate-money-row^='mini_grid:']")).toBeNull();
      expect(note(REGISTER_PANEL, "partial")).toBe(STILL_ASSESSED);
      expect(note(REGISTER_PANEL, "prior-mini-grid")).toBe(PRIOR_MINI_GRID_UNAVAILABLE);
      const unknown = panelTitled(AGGREGATION_PANEL).querySelector("[data-estate-group-state='UNKNOWN_COVERAGE']");
      expect(unknown?.textContent).toBe("Coverage incomplete");
      expect(panelTitled(AGGREGATION_PANEL).textContent).toContain("No consequence lines in this category; some Sites have no complete selection");
      expect(main().textContent).not.toMatch(/no prior|no mini-grid consequence/i);
      view.unmount();
    }

    // Historical: every affected value carries the as-of instant; a conflict says the basis is unresolved.
    const historical = line({ ...EV_LINE, eligibility: "HISTORICAL", amount: null, reason_codes: ["HISTORICAL"] });
    const conflict = line({ ...MINI_LINE, eligibility: "CONFLICT", amount: null, reason_codes: ["OVERLAPPING_BASIS"] });
    view = renderAt(
      `${ESTATE_FINANCIALS_PATH}?${WINDOW}`,
      fake(loaded(body({ status: "HISTORICAL", summary: { eligible_line_count: 0, unpriced_line_count: 0, withheld_line_count: 2, estate_total: null, estate_total_state: "NO_ESTATE_TOTAL", as_of: "2026-10-18T00:00:00Z" }, rows: [conflict, historical], total_count: 2, groups: [] }))),
    );
    await settledScreen();
    expectV69Panels("globalfinancials");
    expect(note(REGISTER_PANEL, "historical")).toBe("Historical as of 2026-10-18 00:00:00 UTC");
    expect(note(REGISTER_PANEL, "conflict")).toBe(BASIS_UNRESOLVED);
    const [conflictRow, historicalRow] = registerRows();
    expect(cells(historicalRow)[3].textContent).toBe("Historical as of 2026-10-18 00:00:00 UTC");
    expect(cells(historicalRow)[3].querySelector(".estate-chip")?.className).toContain("estate-tone--blue");
    expect(cells(conflictRow)[3].textContent).toBe("Not comparable");
    expect(cells(conflictRow)[3].querySelector(".estate-chip")?.className).toContain("estate-tone--red");
    view.unmount();

    // Refusals: the exact copy, prior rows removed, no table.
    for (const [code, status] of [["UNAUTHENTICATED", 401], ["ESTATE_SCOPE_FORBIDDEN", 403], ["ESTATE_SITE_NOT_FOUND", 404], ["ESTATE_STORE_UNAVAILABLE", 503], ["ESTATE_BASIS_CHANGED", 409], ["INVALID_WINDOW", 422], ["INVALID_CURSOR", 422]] as const) {
      view = renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake({ status: "refused", httpStatus: status, code, copy: EVIDENCE_REFUSAL_COPY[code] }));
      await settledScreen();
      expect(main().querySelector(`[data-page-refusal="${code}"]`)?.textContent).toContain(EVIDENCE_REFUSAL_COPY[code]);
      expect(main().querySelector("table")).toBeNull();
      expect(main().textContent).not.toContain("Kobo Mini-grid");
      view.unmount();
    }
  });

  it("preservesSupportedSiteLinksAndCurrentViewLabel", async () => {
    const unlinked = line({ ...MINI_LINE, line_key: "mini_grid:c8000000-0000-4000-8000-000000000008", site_name: "", links: { site: "/sites/KOBO-001", bridge: null, evidence: null, current_view_label: null } });
    renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake(loaded(body({ rows: [MINI_LINE, COLD_LINE, EV_LINE, unlinked], total_count: 4 }))));
    await settledScreen();
    const rows = registerRows();
    const site = (r: HTMLElement) => r.querySelector("[data-estate-site-link]")?.getAttribute("href");
    const source = (r: HTMLElement) => r.querySelector("[data-estate-source-link]");
    expect(rows.map(site)).toEqual(["/sites/KOBO-001", "/sites/COLD-LAB-001", "/sites/EV-LAB-001/ev", "/sites/KOBO-001"]);
    // Mini-grid: the server's current-view bridge, labelled as such (no estate cutoff carried).
    expect(source(rows[0])?.getAttribute("href")).toBe("/sites/KOBO-001/financials");
    expect(rows[0].querySelector("[data-estate-current-view]")?.textContent).toBe("Opens current Site view");
    // Cold: Site evidence with the row's own window and cutoff; EV: the Site bridge with its own query.
    expect(source(rows[1])?.textContent).toBe("Site evidence →");
    expect(source(rows[1])?.getAttribute("href")).toBe(COLD_EVIDENCE);
    expect(rows[1].querySelector("[data-estate-current-view]")).toBeNull();
    expect(source(rows[2])?.textContent).toBe("Site bridge →");
    expect(source(rows[2])?.getAttribute("href")).toBe(EV_BRIDGE);
    // No server link: plain text, never a built path; an empty stored name shows the stored code.
    expect(source(rows[3])).toBeNull();
    expect(rows[3].querySelector("[data-estate-source='unavailable']")?.textContent).toBe(SOURCE_UNAVAILABLE);
    expect(rows[3].querySelector("[data-estate-site-link]")?.textContent).toBe("KOBO-001");
    for (const link of main().querySelectorAll("a")) expect(link.getAttribute("href")).not.toContain(FROM);
  });

  it("readsTheFinancialsWireAndMapsRefusals", async () => {
    const fetched: string[] = [];
    const responses: [number, unknown][] = [
      [200, body()],
      [409, { detail: { code: "ESTATE_BASIS_CHANGED", message: "x", rows: null, total_count: null, groups: null, exclusions: null, diagnostics: null } }],
      [200, { ...body(), schema_version: "estate-evidence-1" }],
      [418, { detail: { code: "SOMETHING_ELSE" } }],
    ];
    vi.stubGlobal("fetch", (url: string) => {
      fetched.push(url);
      const [status, json] = responses.shift() as [number, unknown];
      return Promise.resolve(new Response(JSON.stringify(json), { status }));
    });
    const client = createEstateFinancialsClient();
    const query = { from: FROM, to: TO, known_at: KNOWN, limit: 50, cursor: "abc" };
    expect((await client.financials(query)).status).toBe("loaded");
    expect(await client.financials(query)).toEqual({ status: "refused", httpStatus: 409, code: "ESTATE_BASIS_CHANGED", copy: EVIDENCE_REFUSAL_COPY.ESTATE_BASIS_CHANGED });
    expect((await client.financials(query)) as { code: string }).toMatchObject({ code: "ESTATE_STORE_UNAVAILABLE" });
    expect(await client.financials(query)).toEqual({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "Estate data is temporarily unavailable. Try again." });
    expect(decodeURIComponent(fetched[0])).toBe(`/api/estate/financials?from=${FROM}&to=${TO}&known_at=${KNOWN}&limit=50&cursor=abc`);
  });

  it("roundsStoredMoneyForDisplayWithoutFloats", async () => {
    expect(roundDecimal("3.9612", 2, "ceil")).toBe("3.97");
    expect(roundDecimal("3.9612", 2, "floor")).toBe("3.96");
    expect(roundDecimal("-0.001", 2, "floor")).toBe("-0.01");
    expect(roundDecimal("-0.001", 2, "ceil")).toBe("0.00");
    expect(roundDecimal("2.345", 2, "even")).toBe("2.34");
    expect(roundDecimal("2.355", 2, "even")).toBe("2.36");
    expect(roundDecimal("1000.5", 0, "ceil")).toBe("1001");
    expect(roundDecimal("12.3456", 3, "floor")).toBe("12.345");
    expect(roundDecimal("not a number", 2, "floor")).toBeNull();
    expect(moneyText({ low: "0", high: "3.9612", currency: "USD" }, "outward")).toBe("$0.00–$3.97");
    expect(moneyText({ low: "120.4", high: "120.4", currency: "UGX" }, "outward")).toBe("UGX 120–UGX 121");
    expect(moneyText({ low: "1", high: "1", currency: "XYZ" }, "outward")).toBeNull();
    // An eligible line in a currency without a known minor unit withholds its numeric display.
    const odd = line({ ...MINI_LINE, amount: { low: "1", high: "2", currency: "XYZ" } });
    renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake(loaded(body({ rows: [odd], total_count: 1 }))));
    await settledScreen();
    expect(cells(registerRows()[0])[3].textContent).toBe(NOT_DISPLAYABLE);
  });
});

async function readDisk(path: string): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
  const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
  return fs.readFileSync(`${cwd}/${path}`, "utf8");
}

describe("W3-02 commit 4 measured Financials layout", () => {
  it("showsFullLimitsInBasisDetailsAndEveryRowWithoutAVerticalCap", async () => {
    // Post-W6 W3-estate Q12 / Q20: five 160-character, two-sentence limits joined with a space by the server. The cell
    // shows the first sentence, the Basis details `Limits` line holds the whole text, no `.;` join appears, and
    // every row (both EV rows included) renders.
    const longLimit = (n: number) => {
      const first = `Limit ${n} first sentence states the bounded interpretation of this consequence line in full words.`;
      const text = `${first} Second sentence ${n} keeps the remaining caveat.`;
      return text.padEnd(160, "x").slice(0, 159) + ".";
    };
    const rows = [
      line({ ...MINI_LINE, line_key: "mini_grid:l1", limit: longLimit(1) }),
      line({ ...COLD_LINE, line_key: "cold_chain:l2", limit: longLimit(2) }),
      line({ ...EV_LINE, line_key: "ev_charging:l3", limit: longLimit(3) }),
      line({ ...EV_LINE, line_key: "ev_charging:l4", site_id: EV2, site_code: "EV-LAB-002", site_name: "Second EV lab", limit: longLimit(4) }),
      line({ ...MINI_LINE, line_key: "mini_grid:l5", limit: longLimit(5) }),
    ];
    for (const r of rows) expect(r.limit!.length).toBe(160);
    renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake(loaded(body({ rows }))));
    await settledScreen();
    const rendered = registerRows();
    expect(rendered).toHaveLength(5);
    expect(rendered.map((r) => r.getAttribute("data-estate-money-row"))).toEqual(rows.map((r) => r.line_key));
    const evRows = rendered.filter((r) => (r.getAttribute("data-estate-money-row") ?? "").startsWith("ev_charging:"));
    expect(evRows).toHaveLength(2);
    expect(evRows.map((r) => r.querySelector("[data-estate-site-link]")?.getAttribute("href"))).toEqual([
      "/sites/EV-LAB-001/ev",
      "/sites/EV-LAB-001/ev",
    ]);
    rendered.forEach((r, i) => {
      const limit = rows[i].limit!;
      expect(r.querySelector("[data-estate-limit]")?.textContent).toBe(limit.slice(0, limit.indexOf(".") + 1));
      expect(r.querySelector("[data-estate-limits]")?.textContent).toBe(limit);
      const dt = r.querySelector("[data-estate-limits]")?.previousElementSibling;
      expect(dt?.textContent).toBe("Limits");
    });
    expect(main().textContent).not.toContain(".;");
    // No vertical cap on the register at either width; horizontal scrolling stays.
    const css = await readDisk("src/estate/estateFinancials.css");
    expect(css).not.toMatch(/max-height/);
    expect(css).toMatch(/\.estate-financials-table \.data-table__scroll \{[^}]*overflow-x: auto/s);
  });

  it("meetsMeasuredNarrowLayoutWithoutDocumentOverflow", async () => {
    // jsdom has no layout: this reads the real-browser 390 px measurements of the mounted `/financials` page
    // (`.agent/W3-02-evidence/capture-financials.mjs`). Ruling c4: the closed results summary stays within its 24 px
    // allowance at 12 px; opened, the results list never scrolls internally, every group/diagnostic/exclusion is visible
    // and the page stays unclipped. Ruling c4b: the 12px/1.8 mock prose keeps the closed Aggregation panel within 123 (1440) / 187 (390).
    for (const state of ["positive", "partial"]) {
      const file = `../.agent/W3-02-evidence/app-financials-${state}.json`;
      const narrow = (JSON.parse(await readDisk(file)).results as Record<string, any>[]).find((r) => r.width === 390);
      expect(narrow, `${state} 390 measurement present`).toBeDefined();
      expect(narrow!.ready).toBe(true);
      expect(narrow!.main).toBe("Financials");
      expect(narrow!.docScrollW).toBeLessThanOrEqual(narrow!.docClientW);
      for (const piece of ["status", "register", "notice", "aggregation"]) {
        expect(narrow!.pieces[piece], `${state} ${piece} measured`).not.toBeNull();
      }
      for (const piece of ["status", "register", "notice", "aggregation"]) {
        expect(narrow!.pieces[piece].h, `${state} ${piece} within its 390 maximum`).toBeLessThanOrEqual(narrow!.maxima[piece]);
      }
      const t = narrow!.registerTable;
      expect(t, "register table scroll container measured").not.toBeNull();
      expect(t.client).toBeGreaterThan(0);
      expect(t.rows).toBeGreaterThan(0);
      expect(t.scroll).toBeGreaterThanOrEqual(t.client); // the table scrolls inside its own container
      // Final review H1: the mock's three-row baseline is visible at 390 before any vertical internal scroll, and a
      // register of up to three rows plus its notes stays within the 448 px cap.
      const cap = parseFloat(t.maxH);
      const threeRows = t.headH + 3 * Math.max(...t.rowHs);
      expect(threeRows, `${state} header + 3 rows fit the list cap`).toBeLessThanOrEqual(cap);
      expect(t.scrollH, `${state} register list does not scroll vertically at ${t.rows} rows`).toBeLessThanOrEqual(t.clientH);
      expect(narrow!.pieces.register.h - t.clientH + threeRows, `${state} three-row register within 448`).toBeLessThanOrEqual(448);
      expect(t.client).toBeLessThanOrEqual(narrow!.docClientW);
      const all = JSON.parse(await readDisk(file)).results as Record<string, any>[];
      for (const r of all) {
        expect(r.pieces.aggregation.h, `${state} ${r.width} aggregation within cap`).toBeLessThanOrEqual(r.width === 1440 ? 123 : 187);
        expect(r.aggParts.proseFs).toBe("12px");
        expect(r.aggParts.proseLh).toBe("21.6px");
      }
      const ap = narrow!.aggParts;
      expect(ap.proseFs).toBe("12px");
      expect(ap.proseLh).toBe("21.6px");
      expect(narrow!.aggSummary.lines).toBe(1);
      const s = narrow!.aggSummary;
      expect(s.open).toBe(false);
      expect(s.fontSize).toBe("12px");
      expect(s.wrapperH).toBeLessThanOrEqual(24);
      const o = narrow!.opened;
      expect(o.results.items).toBeGreaterThan(0);
      expect(o.results.scrollH).toBe(o.results.clientH);
      const { groups, diagnostics, exclusions, visible } = o.reach;
      expect(visible).toBeGreaterThanOrEqual(groups + diagnostics + exclusions);
      expect(o.docScrollW).toBeLessThanOrEqual(o.docClientW);
    }
  });
});

describe("post-W6 W3-estate refused window", () => {
  it("classifiesInvalidWindowFromThePageQueryAndHidesTheDates", async () => {
    const cases: [string, string][] = [
      ["from=2026-10-07T00:00:00Z&to=2026-10-05T00:00:00Z", "The selected window needs both a start and an end, with the start before the end."],
      ["from=2026-08-01T00:00:00Z&to=2026-10-01T00:00:00Z", "The selected window is longer than 31 days."],
      [WINDOW, "The selected window is invalid."],
    ];
    for (const [query, copy] of cases) {
      const view = renderAt(`${ESTATE_FINANCIALS_PATH}?${query}`, fake({ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", copy: "server copy" }));
      await settledScreen();
      expect(main().querySelector("[data-page-refusal='INVALID_WINDOW'] p")?.textContent).toBe(copy);
      expect(main().querySelector("[data-estate-window]")?.textContent).toBe("Window not valid");
      view.unmount();
    }
    const view = renderAt(`${ESTATE_FINANCIALS_PATH}?${WINDOW}`, fake({ status: "refused", httpStatus: 403, code: "ESTATE_SCOPE_FORBIDDEN", copy: EVIDENCE_REFUSAL_COPY.ESTATE_SCOPE_FORBIDDEN }));
    await settledScreen();
    expect(main().querySelector("[data-page-refusal] p")?.textContent).toBe(EVIDENCE_REFUSAL_COPY.ESTATE_SCOPE_FORBIDDEN);
    expect(main().querySelector("[data-estate-window]")?.textContent).toBe("Window 2026-10-13 to 2026-10-19 (UTC days)");
    view.unmount();
  });
});
