/**
 * W3-02 commit 2 named frontend tests (`.agent/W3-02-build-spec.md` "Proof and builder handoff"): the estate
 * Evidence root under a local MemoryRouter (Lane A mounts the shell route), against the v6.9 `globalevidence`
 * panel structure, with every card, column, chip, link, inert example and state-table string asserted. Bodies are
 * shaped as the reviewed `estate-evidence-1` wire; IDs are synthetic, and no mock count, Site or Action survives.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { EstateCoverageSite } from "../estateClient";
import {
  COVERAGE_PANEL,
  COVERAGE_SUBTITLE,
  ESTATE_EVIDENCE_PATH,
  EVIDENCE_EYEBROW,
  EVIDENCE_NOTICE,
  EVIDENCE_SUBTITLE,
  EstateEvidencePage,
  GAPS_PANEL,
  NO_ACCESSIBLE_SITES,
  NO_GAPS,
  NO_NEXT_STEP,
  NO_SELECTED_EVIDENCE,
  NO_UNLOCKS,
  STILL_ASSESSED,
  unlocksText,
} from "../EstateEvidence";
import {
  EVIDENCE_REFUSAL_COPY,
  createEstateEvidenceMoneyClient,
  type EstateEvidenceBody,
  type EstateEvidenceMoneyClient,
  type EvidenceGap,
  type EvidenceResult,
  type EvidenceRow,
} from "../estateEvidenceMoneyClient";

const FROM = "2026-10-13T00:00:00Z";
const TO = "2026-10-20T00:00:00Z";
const KNOWN = "2026-10-20T09:30:00Z";
const MINI = "10000000-0000-4000-8000-000000000011";
const COLD = "10000000-0000-4000-8000-000000000012";
const EV = "10000000-0000-4000-8000-000000000013";
const WINDOW = `from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`;
const COLD_LINK = "/sites/COLD-LAB-001/evidence?from=2026-10-14T08%3A00%3A00.000000Z&to=2026-10-14T16%3A00%3A00.000000Z&known_at=2026-10-20T09%3A00%3A00.000000Z";

function coverageSite(siteId: string, state: EstateCoverageSite["state"] = "CURRENT"): EstateCoverageSite {
  return { site_id: siteId, state, committed_watermark: null, selection_id: null, match_state: "COMPLETE", job_state: "SETTLED", source_freshness: "RECENT" };
}

function row(over: Partial<EvidenceRow> & Pick<EvidenceRow, "capability_key" | "capability_label">): EvidenceRow {
  return {
    site_id: MINI,
    site_code: "KOBO-001",
    site_name: "Kobo Mini-grid",
    domain: "mini_grid",
    domain_label: "mini-grid",
    window_start: "2026-10-14T00:00:00Z",
    window_end: "2026-10-15T00:00:00Z",
    raw_state: "LIMITED",
    readiness: "LIMITED",
    current_ceiling: null,
    ceiling: null,
    ceiling_source: "NONE",
    next_evidence: null,
    gap_codes: [],
    selected_revision_ids: ["10000000-0000-4000-8000-000000000501"],
    source_provenance: { state: "UNKNOWN" },
    links: { site: "/sites/KOBO-001", site_readiness: "/sites/KOBO-001", site_readiness_label: "Opens current Site view" },
    disclosure: { capability_key: over.capability_key, constituents: [], reasons: [], historical: null },
    ...over,
  };
}

const MINI_ROW = row({
  capability_key: "GENERATOR_SUPPORT@2026-10-14",
  capability_label: "Generator support",
  current_ceiling: "Candidate in supported intervals",
  ceiling_source: "W1_CLAIM_LIMIT",
  next_evidence: "Record Feeder demand",
  gap_codes: ["GENERATOR_UNOBSERVED"],
});
const COLD_ROW = row({
  site_id: COLD,
  site_code: "COLD-LAB-001",
  site_name: "Cold replay lab",
  domain: "cold_chain",
  domain_label: "cold-chain",
  capability_key: "temperature@2026-10-14T08:00:00.000000Z/2026-10-14T16:00:00.000000Z",
  capability_label: "Temperature compliance",
  window_start: "2026-10-14T08:00:00Z",
  window_end: "2026-10-14T16:00:00Z",
  raw_state: "FULL",
  readiness: "FULL",
  links: { site: "/sites/COLD-LAB-001", site_readiness: COLD_LINK, site_readiness_label: null },
});
const EV_ROW = row({
  site_id: EV,
  site_code: "EV-LAB-001",
  site_name: "EV charging lab",
  domain: "ev_charging",
  domain_label: "EV charging",
  capability_key: "sessions",
  capability_label: "Session outcomes",
  window_start: null,
  window_end: null,
  raw_state: "UNASSESSED",
  readiness: "UNKNOWN",
  selected_revision_ids: [],
  links: { site: "/sites/EV-LAB-001", site_readiness: "/sites/EV-LAB-001", site_readiness_label: "Opens current Site view" },
});

const GAPS: EvidenceGap[] = [
  {
    domain: "mini_grid",
    gap_code: "GENERATOR_UNOBSERVED",
    missing_role: "feeder_demand",
    label: "Feeder demand not observed",
    site_ids: [MINI],
    site_codes: ["KOBO-001"],
    site_names: ["Kobo Mini-grid"],
    unlocks: ["GENERATOR_SUPPORT@2026-10-15", "GENERATOR_SUPPORT@2026-10-14"],
    next_step: "Record Feeder demand",
    link: null,
  },
  {
    domain: "ev_charging",
    gap_code: "TARIFF_GAP",
    missing_role: null,
    label: "Missing EV tariff",
    site_ids: [COLD, EV],
    site_codes: ["COLD-LAB-001", "EV-LAB-001"],
    site_names: ["Cold replay lab", "EV charging lab"],
    unlocks: [],
    next_step: null,
    link: null,
  },
];

function body(over: Partial<EstateEvidenceBody> = {}): EstateEvidenceBody {
  const rows = over.rows ?? [MINI_ROW, COLD_ROW, EV_ROW];
  return {
    schema_version: "estate-evidence-1",
    scope: { tenant_id: "t", authorized_site_count: 3, covered_site_count: 3, access_basis: `sha256:${"b".repeat(64)}` },
    window: { from: FROM, to: TO, bounds: "[from, to)", known_at: KNOWN },
    status: "CURRENT",
    coverage: { state: "COMPLETE", sites: [coverageSite(MINI), coverageSite(COLD), coverageSite(EV)] },
    summary: {
      limited_site_count: 1,
      priority_gap_count: null,
      unsupported_claim_count: null,
      capability_count: rows.length,
      full_count: 1,
      limited_count: 1,
      none_count: 0,
      unknown_count: 1,
    },
    order: "site_code_key asc, site_id asc, capability_key asc",
    total_count: rows.length,
    rows,
    gaps: GAPS,
    next_cursor: null,
    selection_token: `sha256:${"c".repeat(64)}`,
    ...over,
  };
}

function fake(result: EvidenceResult<EstateEvidenceBody>): EstateEvidenceMoneyClient & { calls: unknown[] } {
  const calls: unknown[] = [];
  return {
    calls,
    evidence: (query) => {
      calls.push(query);
      return Promise.resolve(result);
    },
  };
}

const loaded = (value: EstateEvidenceBody): EvidenceResult<EstateEvidenceBody> => ({ status: "loaded", value });

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{`${location.pathname}${location.search}`}</output>;
}

function renderAt(entry: string, client: EstateEvidenceMoneyClient) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <main>
        <Routes>
          <Route path={ESTATE_EVIDENCE_PATH} element={<EstateEvidencePage client={client} />} />
        </Routes>
      </main>
      <LocationProbe />
    </MemoryRouter>,
  );
}

function main(): HTMLElement {
  return document.querySelector("main") as HTMLElement;
}

function headers(panel: HTMLElement): string[] {
  return within(panel).getAllByRole("columnheader").map((h) => h.textContent ?? "");
}

function cards(): { label: string; value: string; note: string }[] {
  return within(screen.getByRole("list", { name: "Evidence summary" }))
    .getAllByRole("listitem")
    .map((card) => ({
      label: card.querySelector(".v69-metric__label")?.textContent ?? "",
      value: card.querySelector(".v69-metric__value")?.textContent ?? "",
      note: card.querySelector(".v69-metric__note")?.textContent ?? "",
    }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("W3-02 estate Evidence root", () => {
  it("rendersMockEvidencePanelsAndHonestCards", async () => {
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body())));
    await settledScreen();
    expectV69Panels("globalevidence");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio evidence");
    expect(main().textContent).toContain("Cross-site claim readiness, recurring gaps and instrumentation priorities");
    expect(main().querySelector("[data-estate-window]")?.textContent).toBe("Window 2026-10-13 to 2026-10-19 (UTC days)");
    expect(cards()).toEqual([
      { label: "Sites with limited claims", value: "1 of 3", note: "Sites with a selected limited capability" },
      { label: "Priority evidence actions", value: "Not assessed", note: "Priority is not recorded for estate evidence gaps" },
      { label: "Unsupported claims", value: "Not assessed", note: "No cross-domain unsupported-claim count is recorded" },
    ]);
    // Neutral tone on all three cards (closure 4: `MetricTone` neutral is `muted`), never a mock number.
    for (const card of main().querySelectorAll("[data-estate-card]")) expect(card.className).toContain("v69-metric--muted");
    const coverage = panelTitled(COVERAGE_PANEL);
    expect(coverage.textContent).toContain(COVERAGE_SUBTITLE);
    expect(headers(coverage)).toEqual(["Site / domain", "Operational capability", "Readiness", "Current ceiling", "Next evidence"]);
    expect(headers(panelTitled(GAPS_PANEL))).toEqual(["Gap", "Sites", "Unlocks", "Next step"]);
    const notice = main().querySelector("[data-estate-notice]");
    expect(notice?.textContent).toBe(EVIDENCE_NOTICE);
    expect(notice?.className).toContain("v69-notice--blue");
    for (const mock of ["GreenHarvest", "Depot", "Kobo · mini-grid", "Restore 14:50 PCS", "battery condition", "Excluded", "PCS, loading"]) {
      expect(main().textContent).not.toContain(mock);
    }
    expectPlantedPanelRejected("globalevidence");
  });

  it("rendersGroupedCapabilitiesAndTypedGaps", async () => {
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body())));
    await settledScreen();
    const rows = within(panelTitled(COVERAGE_PANEL)).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(3);
    const cells = rows.map((r) => within(r).getAllByRole("cell"));
    // Site / domain is the stored name and the domain word, never a renamed mock Site.
    expect(cells.map((c) => c[0].querySelector("a")?.textContent)).toEqual([
      "Kobo Mini-grid · mini-grid",
      "Cold replay lab · cold-chain",
      "EV charging lab · EV charging",
    ]);
    const capability = (cell: HTMLElement) => [cell.querySelector(".estate-evidence-label")?.textContent, cell.querySelector(".estate-evidence-meta")?.textContent];
    expect(capability(cells[0][1])).toEqual(["Generator support", "2026-10-14 00:00 – 2026-10-15 00:00 UTC"]);
    expect(capability(cells[1][1])).toEqual(["Temperature compliance", "2026-10-14 08:00–16:00 UTC"]);
    expect(cells.map((c) => c[2].querySelector("[data-estate-readiness]")?.textContent)).toEqual(["Limited", "Full", "Unknown"]);
    expect(cells[0][2].querySelector("[data-estate-readiness]")?.className).toContain("estate-tone--amber");
    expect(cells[1][2].querySelector("[data-estate-readiness]")?.className).toContain("estate-tone--green");
    expect(cells[2][2].querySelector("[data-estate-readiness]")?.className).toContain("estate-tone--gray");
    expect(cells[2][2].querySelector("[data-estate-row-context]")?.textContent).toBe("Not assessed");
    expect(cells.map((c) => c[3].textContent)).toEqual(["Candidate in supported intervals", "No current ceiling", "No current ceiling"]);
    expect(cells.map((c) => c[4].textContent)).toEqual(["Record Feeder demand", "Not recorded", "Not recorded"]);
    // The capability key, raw state and selected revisions sit in the closed disclosure.
    const details = cells[0][1].querySelector("details");
    expect(details?.open).toBe(false);
    expect(details?.textContent).toContain("GENERATOR_SUPPORT@2026-10-14");
    expect(details?.textContent).toContain("10000000-0000-4000-8000-000000000501");

    const gapRows = within(panelTitled(GAPS_PANEL)).getAllByRole("row").slice(1);
    expect(gapRows).toHaveLength(2);
    const gapCells = gapRows.map((r) => within(r).getAllByRole("cell"));
    expect(gapCells.map((c) => c[0].querySelector(".estate-cell__primary")?.textContent)).toEqual([
      "Feeder demand not observed",
      "Missing EV tariff",
    ]);
    expect(gapCells.map((c) => c[1].textContent)).toEqual(["Kobo Mini-grid", "Cold replay lab · EV charging lab"]);
    expect(gapCells[0][0].querySelector("details")?.textContent).toContain("feeder_demand");
    expect(gapCells.map((c) => c[2].textContent)).toEqual(["Generator support", NO_UNLOCKS]);
    expect(gapCells.map((c) => c[3].textContent)).toEqual(["Record Feeder demand · Not available yet", NO_NEXT_STEP]);
    expect(unlocksText(["energy@b", "temperature@a", "energy@a", "unknown@x"])).toBe("Delivered energy · Temperature compliance");
  });

  it("keepsInertMockActions", async () => {
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body())));
    await settledScreen();
    const gaps = panelTitled(GAPS_PANEL);
    const examples = gaps.querySelector("[data-estate-examples]") as HTMLElement;
    expect(examples.textContent).toContain("Example destinations");
    for (const label of ["ACT-049, ACT-061", "Map transfer switch", "Operational records", "Preventive plan"]) {
      const entry = within(examples).getByLabelText(`${label}, Not available yet`);
      expect(entry.textContent).toBe(`${label} · Not available yet`);
    }
    // No example is a control, and no gap row carries an invented Action link.
    expect(gaps.querySelectorAll("a, button, [href]")).toHaveLength(0);
    expect(within(gaps).getAllByRole("row")).toHaveLength(3);
  });

  it("rendersEvidenceEmptyPendingAndRefusals", async () => {
    // Complete empty authorized scope: `0 of 0`, the scope note, headers kept, no zero rows.
    let view = renderAt(
      `${ESTATE_EVIDENCE_PATH}?${WINDOW}`,
      fake(loaded(body({
        status: "EMPTY_SCOPE",
        scope: { tenant_id: "t", authorized_site_count: 0, covered_site_count: 0, access_basis: "x" },
        coverage: { state: "EMPTY", sites: [] },
        summary: { limited_site_count: 0, priority_gap_count: null, unsupported_claim_count: null, capability_count: 0, full_count: 0, limited_count: 0, none_count: 0, unknown_count: 0 },
        total_count: 0,
        rows: [],
        gaps: [],
      }))),
    );
    await settledScreen();
    expectV69Panels("globalevidence");
    expect(cards()[0]).toEqual({ label: "Sites with limited claims", value: "0 of 0", note: NO_ACCESSIBLE_SITES });
    expect(headers(panelTitled(COVERAGE_PANEL))).toHaveLength(5);
    expect(panelTitled(COVERAGE_PANEL).querySelector("[data-estate-note]")?.textContent).toBe(NO_ACCESSIBLE_SITES);
    expect(panelTitled(COVERAGE_PANEL).textContent).not.toContain(NO_SELECTED_EVIDENCE);
    expect(panelTitled(GAPS_PANEL).querySelector("[data-estate-note='no-gaps']")?.textContent).toBe(NO_GAPS);
    view.unmount();

    // Authorized scope, nothing selected.
    view = renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body({ rows: [], total_count: 0, gaps: [] }))));
    await settledScreen();
    expectV69Panels("globalevidence");
    expect(panelTitled(COVERAGE_PANEL).querySelector("[data-estate-note='no-selection']")?.textContent).toBe(NO_SELECTED_EVIDENCE);
    view.unmount();

    // Partial/pending: known rows kept, truth-dependent card unknown, the pending context chip.
    const pending = { ...EV_ROW, raw_state: "PENDING_RECOMPUTE" };
    view = renderAt(
      `${ESTATE_EVIDENCE_PATH}?${WINDOW}`,
      fake(loaded(body({
        status: "PENDING_RECOMPUTE",
        coverage: { state: "PARTIAL", sites: [coverageSite(MINI), coverageSite(COLD), coverageSite(EV, "PENDING_RECOMPUTE")] },
        summary: { limited_site_count: null, priority_gap_count: null, unsupported_claim_count: null, capability_count: 3, full_count: null, limited_count: null, none_count: null, unknown_count: null },
        rows: [MINI_ROW, COLD_ROW, pending],
      }))),
    );
    await settledScreen();
    expectV69Panels("globalevidence");
    expect(cards()[0]).toEqual({ label: "Sites with limited claims", value: "Not assessed", note: "Some Site evidence is unavailable" });
    expect(within(panelTitled(COVERAGE_PANEL)).getAllByRole("row")).toHaveLength(4);
    expect(panelTitled(COVERAGE_PANEL).querySelector("[data-estate-note='partial']")?.textContent).toBe(STILL_ASSESSED);
    expect(main().querySelector("[data-estate-row-context='PENDING_RECOMPUTE']")?.className).toContain("estate-tone--amber");
    expect(main().textContent).not.toMatch(/\b0 of 3\b/);
    view.unmount();

    // Historical: every affected value labelled, no current claim.
    const historical = { ...COLD_ROW, raw_state: "HISTORICAL", readiness: "UNKNOWN" as const };
    view = renderAt(
      `${ESTATE_EVIDENCE_PATH}?${WINDOW}&known_at=${encodeURIComponent("2026-10-18T00:00:00Z")}`,
      fake(loaded(body({
        status: "HISTORICAL",
        window: { from: FROM, to: TO, bounds: "[from, to)", known_at: "2026-10-18T00:00:00Z" },
        summary: { ...body().summary, limited_site_count: null, as_of: "2026-10-18T00:00:00Z" },
        rows: [historical],
        gaps: [],
      }))),
    );
    await settledScreen();
    expectV69Panels("globalevidence");
    expect(main().querySelector("[data-estate-row-context='HISTORICAL']")?.textContent).toBe("Historical as of 2026-10-18 00:00:00 UTC");
    expect(main().querySelector("[data-estate-row-context='HISTORICAL']")?.className).toContain("estate-tone--blue");
    expect(panelTitled(COVERAGE_PANEL).querySelector("[data-estate-note='historical']")?.textContent).toBe("Historical as of 2026-10-18 00:00:00 UTC");
    view.unmount();

    // Refusals: the exact copy, prior rows removed, no table.
    for (const [code, status] of [["UNAUTHENTICATED", 401], ["ESTATE_SCOPE_FORBIDDEN", 403], ["ESTATE_STORE_UNAVAILABLE", 503], ["ESTATE_BASIS_CHANGED", 409], ["INVALID_WINDOW", 422], ["INVALID_CURSOR", 422]] as const) {
      view = renderAt(
        `${ESTATE_EVIDENCE_PATH}?${WINDOW}`,
        fake({ status: "refused", httpStatus: status, code, copy: EVIDENCE_REFUSAL_COPY[code] }),
      );
      await settledScreen();
      const refusal = main().querySelector(`[data-page-refusal="${code}"]`);
      expect(refusal?.textContent).toContain(EVIDENCE_REFUSAL_COPY[code]);
      expect(main().querySelector("table")).toBeNull();
      expect(main().textContent).not.toContain("Kobo Mini-grid");
      view.unmount();
    }
    // c2-q2: the exhaustive literal table, aliases included, and nothing else.
    const RESET = "This selection cannot be read. Reset the filters.";
    expect(EVIDENCE_REFUSAL_COPY).toEqual({
      UNAUTHENTICATED: "Sign in to view estate evidence and financials.",
      ESTATE_SCOPE_FORBIDDEN: "You do not have access to this estate view.",
      ESTATE_SOURCE_DISCLOSURE_FORBIDDEN: "Source details for one or more Sites cannot be shown.",
      ESTATE_SITE_NOT_FOUND: "This Site is no longer in the selected estate.",
      ESTATE_STORE_UNAVAILABLE: "Estate data is temporarily unavailable. Try again.",
      ESTATE_READ_UNAVAILABLE: "Estate data is temporarily unavailable. Try again.",
      ESTATE_BASIS_CHANGED: "The selection changed. Refresh to see the latest basis.",
      ESTATE_SELECTION_INCONSISTENT: "The selection changed. Refresh to see the latest basis.",
      INVALID_WINDOW: "Choose a UTC window of up to 31 days with a start before its end.",
      INVALID_KNOWN_AT: RESET,
      INVALID_LIMIT: RESET,
      INVALID_CURSOR: RESET,
      ESTATE_PARAMETER_UNKNOWN: RESET,
      ESTATE_CURSOR_INVALID: RESET,
    });
    for (const copy of Object.values(EVIDENCE_REFUSAL_COPY)) expect(copy.toLowerCase()).not.toContain("cutoff");
  });

  it("namesGapSitesFromTheWireNotThePage", async () => {
    // c2-q1: the gap's Sites are on another page (only the Kobo row is here); names come from `site_names`, an
    // empty stored name shows its stored code, and every code stays in `Record details`.
    const offPage: EvidenceGap = { ...GAPS[1], site_names: ["Cold replay lab", ""] };
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body({ rows: [MINI_ROW], total_count: 3, gaps: [offPage] }))));
    await settledScreen();
    const cells = within(within(panelTitled(GAPS_PANEL)).getAllByRole("row")[1]).getAllByRole("cell");
    expect(cells[1].textContent).toBe("Cold replay lab · EV-LAB-001");
    expect(cells[0].querySelector("details")?.textContent).toContain("COLD-LAB-001, EV-LAB-001");
  });

  it("showsPlainReadinessAndContextWords", async () => {
    // c2-q4: readiness chip words, and a separate context chip only for pending/stale/unassessed/historical rows.
    const rows = [
      { ...COLD_ROW, capability_key: "a", raw_state: "CONTRADICTORY", readiness: "CONTRADICTORY" as const },
      { ...COLD_ROW, capability_key: "b", raw_state: "PENDING_RECOMPUTE", readiness: "UNKNOWN" as const },
      { ...COLD_ROW, capability_key: "c", raw_state: "STALE_SOURCE", readiness: "UNKNOWN" as const },
      { ...COLD_ROW, capability_key: "d", raw_state: "UNASSESSED", readiness: "UNKNOWN" as const },
      { ...COLD_ROW, capability_key: "e", raw_state: "NOT_APPLICABLE", readiness: "NOT_APPLICABLE" as const },
      { ...COLD_ROW, capability_key: "f", raw_state: "FULL", readiness: "FULL" as const },
    ];
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body({ rows, total_count: rows.length, gaps: [] }))));
    await settledScreen();
    const cells = within(panelTitled(COVERAGE_PANEL)).getAllByRole("row").slice(1).map((r) => within(r).getAllByRole("cell")[2]);
    const words = cells.map((c) => [...c.querySelectorAll(".estate-chip")].map((chip) => [chip.textContent, chip.className.replace(/.*estate-tone--/, "")]));
    expect(words).toEqual([
      [["Conflicting records", "red"]],
      [["Unknown", "gray"], ["New evidence is being assessed", "amber"]],
      [["Unknown", "gray"], ["May miss newer readings", "amber"]],
      [["Unknown", "gray"], ["Not assessed", "gray"]],
      [["N/A", "gray"]],
      [["Full", "green"]],
    ]);
    // Raw state IDs stay in `Record details` only.
    const visible = cells.map((c) => c.textContent).join(" ");
    for (const raw of ["PENDING_RECOMPUTE", "STALE_SOURCE", "UNASSESSED", "CONTRADICTORY", "Contradictory"]) expect(visible).not.toContain(raw);
  });

  it("preservesSupportedSiteLinksAndCurrentViewLabel", async () => {
    const client = fake(loaded(body({ next_cursor: "opaque-cursor" })));
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, client);
    await settledScreen();
    const links = Array.from(panelTitled(COVERAGE_PANEL).querySelectorAll("[data-estate-site-link]"));
    // The server owns `links.*`: the cold row opens its own window; the others open the current Site view.
    expect(links.map((a) => a.getAttribute("href"))).toEqual(["/sites/KOBO-001", COLD_LINK, "/sites/EV-LAB-001"]);
    const rows = within(panelTitled(COVERAGE_PANEL)).getAllByRole("row").slice(1);
    expect(rows.map((r) => r.querySelector("[data-estate-current-view]")?.textContent ?? null)).toEqual([
      "Opens current Site view",
      null,
      "Opens current Site view",
    ]);
    // The pager keeps the window and passes the opaque cursor back unchanged.
    const next = within(panelTitled(COVERAGE_PANEL)).getByRole("link", { name: "Next page" });
    expect(decodeURIComponent(next.getAttribute("href") ?? "")).toBe(`${ESTATE_EVIDENCE_PATH}?from=${FROM}&to=${TO}&cursor=opaque-cursor`);
    expect(client.calls[0]).toMatchObject({ from: FROM, to: TO, known_at: null, cursor: null });
    // Applying a new window restarts at page one.
    fireEvent.change(main().querySelector("input[type=date]") as HTMLInputElement, { target: { value: "2026-10-12" } });
    fireEvent.click(screen.getByRole("button", { name: "Show" }));
    await settledScreen();
    expect(decodeURIComponent(screen.getByTestId("location").textContent ?? "")).toBe(
      `${ESTATE_EVIDENCE_PATH}?from=2026-10-12T00:00:00Z&to=${TO}`,
    );
  });

  it("readsTheEvidenceWireAndMapsRefusals", async () => {
    const fetched: string[] = [];
    const responses: [number, unknown][] = [
      [200, body()],
      [409, { detail: { code: "ESTATE_BASIS_CHANGED", message: "server text", rows: null, total_count: null, gaps: null } }],
      [200, { schema_version: "estate-finding-index-2" }],
      [418, { detail: { code: "SOMETHING_ELSE" } }],
    ];
    vi.stubGlobal("fetch", (url: string) => {
      fetched.push(url);
      const [status, json] = responses.shift() as [number, unknown];
      return Promise.resolve(new Response(JSON.stringify(json), { status }));
    });
    const client = createEstateEvidenceMoneyClient();
    const query = { from: FROM, to: TO, known_at: KNOWN, limit: 50, cursor: "abc" };
    expect((await client.evidence(query)).status).toBe("loaded");
    expect(await client.evidence(query)).toEqual({ status: "refused", httpStatus: 409, code: "ESTATE_BASIS_CHANGED", copy: EVIDENCE_REFUSAL_COPY.ESTATE_BASIS_CHANGED });
    expect((await client.evidence(query)) as { code: string }).toMatchObject({ code: "ESTATE_STORE_UNAVAILABLE" });
    expect(await client.evidence(query)).toEqual({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "Estate data is temporarily unavailable. Try again." });
    expect(decodeURIComponent(fetched[0])).toBe(`/api/estate/evidence?from=${FROM}&to=${TO}&known_at=${KNOWN}&limit=50&cursor=abc`);
  });

  it("test_evidence_eyebrow_above_title_on_estate_root", async () => {
    renderAt(`${ESTATE_EVIDENCE_PATH}?${WINDOW}`, fake(loaded(body())));
    await settledScreen();
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(h1.textContent).toBe("Portfolio evidence");
    const header = h1.closest("header") as HTMLElement;
    expect(header).not.toBeNull();
    const eyebrow = within(header).getByText(EVIDENCE_EYEBROW, { selector: ".page-header__eyebrow" });
    expect(eyebrow.textContent).toBe("Evidence");
    // Eyebrow precedes the heading, which precedes the subtitle, all in the same header.
    expect(eyebrow.compareDocumentPosition(h1) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const subtitle = within(header).getByText(EVIDENCE_SUBTITLE);
    expect(h1.compareDocumentPosition(subtitle) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // Not a breadcrumb: the estate root draws none.
    expect(screen.queryByRole("navigation", { name: /breadcrumb/i })).toBeNull();
  });
});
