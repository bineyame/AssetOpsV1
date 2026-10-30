/**
 * S4-04 phase 2: Site > Findings over the scoped Site Finding index for an
 * imported Site (`sitefindings:1#a` assessed empty, `#b` positive rows), with
 * the scope in the address and every non-current or refused read showing no
 * rows, no count and no "no Findings" claim.
 */
import { expectUnavailableEntry, rowLabels, UNAVAILABLE_STATUS } from "../../test/unavailableEntry";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { sitePerformanceHref } from "../operatorSiteRoutes";
import type { FindingIndexClient, FindingIndexResult } from "../../sites/findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { analyticsClient } from "../../sites/__tests__/analyticsFixtures";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import {
  FID_A,
  FID_B,
  RID_A,
  RID_B,
  TOKEN,
  indexBody,
  indexClient,
  indexRow,
  notCurrent,
} from "../../sites/__tests__/findingIndexFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { F104 } from "../../sites/__tests__/outcomeFixtures";
import { boardBody, fakeOutcomeBoard, planWarning } from "../../test/outcomeBoardFixture";
import type { OutcomeBoardClient } from "../../sites/outcomeBoardClient";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};
const WINDOW = "from=2026-10-25T00%3A00%3A00Z&to=2026-10-26T00%3A00%3A00Z&domain=mini-grid-dispatch";
const PATH = `/sites/${SITE_ID}/findings?${WINDOW}`;

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
}

function renderAt(path: string, index: FindingIndexClient, outcomeBoard?: OutcomeBoardClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteAnalytics={analyticsClient(SITE_ID)}
        siteFindingIndex={index}
        {...(outcomeBoard === undefined ? {} : { outcomeBoard })}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";
const state = () => document.querySelector("[data-finding-index-state]")?.getAttribute("data-finding-index-state");
const query = () => new URLSearchParams(where().split("?")[1] ?? "");
/** The single v69 panel "Findings at this site" (W1-F3; formerly the answer card). */
const card = () => panelTitled("Findings at this site");
/** The v69 statusbar before the panel: the claim and the shared state line (W1-F3). */
const statusBar = () => document.querySelector("[data-site-findings-status]") as HTMLElement;
const claim = () => statusBar()?.querySelector("[data-site-findings-claim]")?.textContent ?? null;

/** The exact value under a labelled row of the closed exact-reference disclosure. */
function exactValue(label: string): string | null {
  const disclosure = card().querySelector("details[data-exact-references]");
  expect(disclosure, "an exact-reference disclosure").not.toBeNull();
  for (const row of Array.from(disclosure!.querySelectorAll(".exact-references__row"))) {
    if (row.querySelector("dt")?.textContent === label) return row.querySelector("dd code")?.textContent ?? null;
  }
  return null;
}

/** The day strip step for one plain day. */
function dayStep(day: string): HTMLElement | null {
  return (
    Array.from(card().querySelectorAll<HTMLElement>("[data-step-strip] [data-step]")).find(
      (step) => step.querySelector(".step-strip__label")?.textContent === day,
    ) ?? null
  );
}

function noClaim() {
  expect(document.querySelector("[data-finding-index-row]")).toBeNull();
  expect(document.querySelector("table[aria-labelledby='site-finding-index-heading']")).toBeNull();
  expect(screen.queryByText(/No Findings in this window/)).toBeNull();
  expect(screen.queryByText(/\d+ Findings? in this window/)).toBeNull();
}

const ROWS = indexBody({
  rows: [
    indexRow(FID_B, RID_B, "2026-10-25T18:00:00Z", "2026-10-25T19:00:00Z", {
      relations: { merged_from: [], recurs_after: FID_A, recurred_by: [], split_from: null, split_parts: [] },
    }),
    indexRow(FID_A, RID_A, "2026-10-25T06:00:00Z", "2026-10-25T07:00:00Z", { lifecycle: "NO_LONGER_SUPPORTED" }),
  ],
  total_count: 3,
  next_cursor: "cursor-page-2",
});

describe("S4-04 Site Findings index: assessed empty (sitefindings:1#a)", () => {
  it("reads the address scope and states an assessed empty window with its basis", async () => {
    const { client, getFindingIndex } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    renderAt(PATH, client);
    await settledScreen();
    expect(getFindingIndex).toHaveBeenCalledTimes(1);
    expect(getFindingIndex.mock.calls[0]).toEqual([
      SITE_ID,
      { domain: "mini-grid-dispatch", from: "2026-10-25T00:00:00Z", to: "2026-10-26T00:00:00Z", limit: null, cursor: null },
    ]);
    expect(state()).toBe("current-empty");
    expect(claim()).toBe("No Findings in this window");
    // W1-UX-02: the list reference moved into the labelled exact-reference disclosure, and the
    // per-day basis into the day strip (checked and matched).
    expect(exactValue("List reference")).toBe(TOKEN);
    expect(dayStep("25 Oct 2026")?.getAttribute("data-step")).toBe("done");
    expect(dayStep("25 Oct 2026")?.textContent).toContain("Checked, and Findings matched");
    expect(document.querySelector("[data-finding-index-row]")).toBeNull();
    const { violations } = scanProductVocabulary(document.body, "site findings empty");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("defaults to today's UTC day and the supported domain when the address names none", async () => {
    const { client, getFindingIndex } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    renderAt(`/sites/${SITE_ID}/findings`, client);
    await settledScreen();
    const scope = getFindingIndex.mock.calls[0][1];
    const today = new Date().toISOString().slice(0, 10);
    expect(scope.domain).toBe("mini-grid-dispatch");
    expect(scope.from).toBe(`${today}T00:00:00Z`);
    expect(new Date(scope.to).getTime() - new Date(scope.from).getTime()).toBe(86400000);
  });

  it("changing the dates writes a new window to the address and reads again", async () => {
    const { client, getFindingIndex } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    renderAt(PATH, client);
    await settledScreen();
    fireEvent.change(screen.getByLabelText(/From \(UTC day\)/), { target: { value: "2026-10-20" } });
    fireEvent.change(screen.getByLabelText(/To \(UTC day, included\)/), { target: { value: "2026-10-21" } });
    expect(screen.getByLabelText(/From \(UTC day\)/)).toHaveValue("2026-10-20");
    fireEvent.click(screen.getByRole("button", { name: "Show Findings" }));
    await waitFor(() => expect(query().get("from")).toBe("2026-10-20T00:00:00Z"));
    await settledScreen();
    expect(query().get("to")).toBe("2026-10-22T00:00:00Z");
    expect(query().get("cursor")).toBeNull();
    expect(getFindingIndex).toHaveBeenCalledTimes(2);
    expect(getFindingIndex.mock.calls[1][1].from).toBe("2026-10-20T00:00:00Z");
  });
});

describe("S4-04 Site Findings index: positive rows (sitefindings:1#b)", () => {
  it("lists rows in the read's order with exact revision links, relations and no amount", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: ROWS }));
    renderAt(PATH, client);
    await settledScreen();
    expect(state()).toBe("current-rows");
    expect(claim()).toBe("3 Findings in this window");
    const rows = Array.from(document.querySelectorAll("[data-finding-index-row]"));
    expect(rows.map((r) => r.getAttribute("data-finding-index-row"))).toEqual([FID_B, FID_A]);
    const links = Array.from(document.querySelectorAll("[data-finding-index-link]"));
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      `/sites/${SITE_ID}/findings/${FID_B}?revision_id=${RID_B}`,
      `/sites/${SITE_ID}/findings/${FID_A}?revision_id=${RID_A}`,
    ]);
    // W1-UX-02: the related-Finding link reads in words; it still opens the exact related Finding.
    const related = within(rows[0] as HTMLElement).getByRole("link", { name: "Recurs after an earlier Finding" });
    expect(related).toHaveAttribute("href", `/sites/${SITE_ID}/findings/${FID_A}`);
    expect(related.getAttribute("data-finding-index-related")).toBe(FID_A);
    expect(within(rows[1] as HTMLElement).getByText("No longer supported")).toBeInTheDocument();
    for (const cell of document.querySelectorAll("[data-finding-index-amount]")) {
      expect(cell.getAttribute("data-finding-index-amount")).toBe("UNAVAILABLE");
      expect(cell.textContent).not.toMatch(/\d/);
    }
    expect(screen.getByText("Showing 2 of 3.")).toBeInTheDocument();
    const { violations } = scanProductVocabulary(document.body, "site findings rows");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("the next page keeps the cursor in the address, so reload reads the same page", async () => {
    const { client, getFindingIndex } = indexClient((scope) =>
      scope.cursor
        ? { status: "loaded", value: indexBody({ rows: [indexRow(FID_A, RID_A, "2026-10-25T01:00:00Z", "2026-10-25T02:00:00Z")], total_count: 3 }) }
        : { status: "loaded", value: ROWS },
    );
    renderAt(PATH, client);
    await settledScreen();
    fireEvent.click(screen.getByRole("link", { name: "Next page" }));
    await settledScreen();
    expect(query().get("cursor")).toBe("cursor-page-2");
    expect(query().get("from")).toBe("2026-10-25T00:00:00Z");
    expect(getFindingIndex.mock.calls[1][1].cursor).toBe("cursor-page-2");
    expect(screen.getByRole("link", { name: "First page" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Next page" })).toBeNull();
  });
});

describe("OUT-A A4 Site Findings index: category pills", () => {
  it("a mini row shows solid Optimize and outlined Protect under its title; a row without the key shows none", async () => {
    const body = indexBody({
      rows: [
        indexRow(FID_B, RID_B, "2026-10-25T18:00:00Z", "2026-10-25T19:00:00Z", { categories: F104 }),
        indexRow(FID_A, RID_A, "2026-10-25T06:00:00Z", "2026-10-25T07:00:00Z"),
      ],
      total_count: 2,
      next_cursor: null,
    });
    const { client } = indexClient(() => ({ status: "loaded", value: body }));
    renderAt(PATH, client);
    await settledScreen();
    const rows = Array.from(document.querySelectorAll("[data-finding-index-row]"));
    expect(rows).toHaveLength(2);
    const tags = Array.from(rows[0].querySelectorAll("td:first-child .oc-affects")).map((el) => [el.textContent, el.classList.contains("quiet")]);
    expect(tags).toEqual([
      ["Affects Optimize cost and efficiency", false],
      ["Also checked under Protect asset and capital", true],
    ]);
    expect(rows[1].querySelector("[data-outcome-tags]")).toBeNull();
    const scan = scanProductVocabulary(rows[0] as HTMLElement, "sitefindings", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(2);
    expect(describeViolations(scan.violations)).toBe("");
  });
});

describe("S4-04 Site Findings index: no rows, no count, no empty claim", () => {
  const cases: [string, FindingIndexResult, string][] = [
    ["pending", { status: "loaded", value: notCurrent("PENDING", "MATCH_PENDING") }, "PENDING"],
    ["unassessed", { status: "loaded", value: notCurrent("UNASSESSED", "no selection") }, "UNASSESSED"],
    ["stale", { status: "loaded", value: notCurrent("STALE_PROJECTION", "late evidence") }, "STALE_PROJECTION"],
    ["failed", { status: "loaded", value: notCurrent("FAILED", "RECOMPUTE_FAILED") }, "FAILED"],
    ["closed gate", { status: "closed", message: "Performance comparison has not passed", note: "n" }, "closed"],
    [
      "continuity limit",
      { status: "continuity_limit", message: "Episode continuity reaches beyond 62 UTC days.", limitDays: 62, inspectedFrom: "2026-08-01", inspectedTo: "2026-10-01" },
      "continuity-limit",
    ],
    ["invalid window", { status: "invalid", message: "The window may span at most 31 UTC days.", code: "INVALID_WINDOW", field: "to" }, "invalid"],
    ["unavailable", { status: "unavailable", message: null }, "unavailable"],
  ];
  it.each(cases)("%s", async (_name, result, expected) => {
    const { client } = indexClient(() => result);
    renderAt(PATH, client);
    await settledScreen();
    expect(state()).toBe(expected);
    noClaim();
    if (result.status === "loaded") {
      expect(screen.getByText(/This is not a statement that the window has no Findings/)).toBeInTheDocument();
      // W1-UX-02: the raw recorded reason moved into the labelled exact-reference disclosure.
      expect(exactValue("Reason recorded 1")).toMatch(/^2026-10-25: /);
    }
  });

  it("a changed basis under an old cursor restarts from the first page", async () => {
    const { client, getFindingIndex } = indexClient((scope) =>
      scope.cursor
        ? { status: "basis_changed", message: "changed", reason: "SELECTION_CHANGED" }
        : { status: "loaded", value: ROWS },
    );
    renderAt(`${PATH}&cursor=old-cursor`, client);
    await settledScreen();
    expect(state()).toBe("basis-changed");
    noClaim();
    fireEvent.click(screen.getByRole("link", { name: "Start again from the first page" }));
    await settledScreen();
    expect(query().get("cursor")).toBeNull();
    expect(getFindingIndex.mock.calls.at(-1)?.[1].cursor).toBeNull();
    expect(state()).toBe("current-rows");
  });
});

describe("S4-04 Site Findings index: a Site with no imported record", () => {
  it("keeps the older Site Findings summary rather than relabelling it as the index", async () => {
    const { client } = indexClient(() => ({ status: "not_imported", message: null }));
    renderAt(`/sites/${SITE_ID}/findings`, client);
    await settledScreen();
    expect(document.querySelector('[data-findings-index="site"]')).not.toBeNull();
    expect(document.querySelector('[data-findings-index="site-window"]')).toBeNull();
    expect(state()).toBeUndefined();
  });
});

describe("W1-UX-02: Site Findings index (sitefindings) answer card", () => {
  const AS_OF = /^As of \d{1,2} \w{3} \d{4}, \d{2}:\d{2} UTC$/;

  function w1Scans(page: string) {
    const main = document.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, `${page} (W1)`, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(8);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const t028 = scanProductVocabulary(main, page);
    expect(t028.violations, describeViolations(t028.violations)).toEqual([]);
  }

  function disclosureScan(page: string) {
    const disclosure = scanDisclosureVocabulary(card(), `${page} disclosure`);
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.scanned).toBeGreaterThan(0);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
  }

  function outsideDisclosure(): string {
    const details = card().querySelector("details[data-exact-references]");
    return (card().textContent ?? "").replace(details?.textContent ?? "", "");
  }

  it("populated: leads with the question, the count, a current state line and the rows; references stay closed", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: ROWS }));
    renderAt(PATH, client);
    await settledScreen();
    expect(card().textContent).toContain("Domain links back to the Performance view that produced the finding.");
    expect(expectStateLineVisible(statusBar())).toBe("Using the latest checked readings");
    expect(statusBar().querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 30 Oct 2026, 08:00 UTC");
    expect(statusBar().querySelector("[data-product-status-scope]")?.textContent).toContain("25 Oct 2026");
    expect(card().querySelectorAll("[data-finding-index-row]")).toHaveLength(2);
    // W1-F3 review M4: a one-day window is named by every row's Period cell, so no day strip repeats it beside rows.
    expect(card().querySelectorAll("[data-step-strip]")).toHaveLength(0);
    expect(card().querySelector("[data-finding-index-row] .finding-index-period")?.textContent).toContain("25 Oct 2026");
    // W1-F3 review H2: the mock's Domain, Priority and Confidence columns; the unsupported two are honest unknowns.
    expect(Array.from(card().querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Finding", "Domain", "Priority", "Confidence", "State", "Main consequence", "Lens", "Period",
    ]);
    for (const row of Array.from(card().querySelectorAll("[data-finding-index-row]"))) {
      expect(row.querySelector("[data-finding-index-domain]")?.textContent).toBe("Dispatch");
      expect(row.querySelector("[data-finding-index-priority]")?.textContent).toBe("Not assessed");
      expect(row.querySelector("[data-finding-index-confidence]")?.textContent).toBe("Not assessed");
      expect(row.querySelector("[data-finding-index-lens]")?.textContent).toBe("Not assessed");
    }
    expect(within(card()).getByRole("link", { name: "Open the newest Finding" })).toHaveAttribute(
      "href",
      `/sites/${SITE_ID}/findings/${FID_B}?revision_id=${RID_B}`,
    );
    // Opaque page and list references live only in the closed disclosure, not in the default reading.
    expect(exactValue("Next page reference")).toBe("cursor-page-2");
    expect(exactValue("List reference")).toBe(TOKEN);
    const details = card().querySelector("details[data-exact-references]") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.querySelector("summary")?.textContent).toBe("How this was worked out");
    const outside = outsideDisclosure();
    for (const raw of ["cursor-page-2", TOKEN, FID_A, FID_B, RID_A, RID_B, FID_A.slice(0, 8), "CURRENT", "SUPPORTED"]) {
      expect(outside).not.toContain(raw);
    }
    // The exact references come last in the panel.
    expect((card().querySelector(".panel__body") as HTMLElement).lastElementChild).toBe(details);
    w1Scans("site findings rows");
    disclosureScan("site findings rows");
  });

  it("proved zero: a current empty window says so with a plain As of beside the claim", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    renderAt(PATH, client);
    await settledScreen();
    expect(state()).toBe("current-empty");
    expect(claim()).toBe("No Findings in this window");
    expect(expectStateLineVisible(statusBar())).toBe("Checked: nothing to report");
    expect(statusBar().querySelector("[data-product-status-as-of]")?.textContent).toMatch(AS_OF);
    expect(statusBar().querySelector("[data-product-status-as-of]")?.textContent).toBe("As of 30 Oct 2026, 08:00 UTC");
    w1Scans("site findings empty");
    disclosureScan("site findings empty");
  });

  const notCurrentCases: [string, Parameters<typeof notCurrent>[0], string, string, string][] = [
    ["pending", "PENDING", "MATCH_PENDING", "Not checked yet", "waiting"],
    ["unassessed", "UNASSESSED", "no selection", "We have not checked this period", "not-known"],
    ["stale (late readings)", "STALE_PROJECTION", "late evidence", "This result may miss newer readings", "waiting"],
    ["failed", "FAILED", "RECOMPUTE_FAILED", "The latest check could not be completed", "problem"],
  ];
  it.each(notCurrentCases)("%s: a non-positive state line, no count, no rows, no zero claim", async (_n, status, reason, label, step) => {
    const body = notCurrent(status, reason);
    body.watermarks.days[0] = { ...body.watermarks.days[0], status };
    const { client } = indexClient(() => ({ status: "loaded", value: body }));
    renderAt(PATH, client);
    await settledScreen();
    noClaim();
    expect(expectStateLineVisible(statusBar())).toBe(label);
    expect(statusBar().querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(statusBar().querySelector("[data-product-status-as-of]")?.textContent).toMatch(AS_OF);
    expect(claim()).toBe("The Findings for this window are not known");
    expect(screen.getByText(/This is not a statement that the window has no Findings/)).toBeInTheDocument();
    expect(dayStep("25 Oct 2026")?.getAttribute("data-step")).toBe(step);
    expect(exactValue("Recorded list state")).toBe(status);
    expect(exactValue("Reason recorded 1")).toBe(`2026-10-25: ${reason}`);
    const outside = outsideDisclosure();
    expect(outside).not.toContain(status);
    expect(outside).not.toContain(reason);
    w1Scans(`site findings ${status}`);
    disclosureScan(`site findings ${status}`);
  });

  it("an unrecognised list state falls back non-positively", async () => {
    const body = notCurrent("PENDING", "x");
    (body as { status: string }).status = "SOMETHING_NEW";
    const { client } = indexClient(() => ({ status: "loaded", value: body }));
    renderAt(PATH, client);
    await settledScreen();
    noClaim();
    expect(expectStateLineVisible(statusBar())).toBe("We cannot judge this yet");
    expect(statusBar().querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
  });

  /** A refused or unavailable read records no time: explicit checks instead of the timed helper. */
  function expectUntimedStateLine(label: string) {
    const status = statusBar().querySelector("[data-product-status]") as HTMLElement;
    expect(status).not.toBeNull();
    expect(status.getAttribute("data-product-status")).not.toBe("positive");
    expect(status.closest("details")).toBeNull();
    expect(status.querySelector("[data-product-status-label]")?.textContent).toBe(label);
    expect((status.querySelector(".product-status__sentence")?.textContent ?? "").length).toBeGreaterThan(10);
    expect(status.querySelector("[data-product-status-scope]")?.textContent).toContain("25 Oct 2026");
    expect(status.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
    for (const details of Array.from(card().querySelectorAll<HTMLDetailsElement>("details"))) {
      expect(details.open).toBe(false);
    }
  }

  const refusedCases: [string, FindingIndexResult, string, string][] = [
    ["refused (no access)", { status: "forbidden", message: null }, "forbidden", "This cannot be shown to you"],
    ["unavailable", { status: "unavailable", message: null }, "unavailable", "This could not be read right now"],
    ["closed", { status: "closed", message: "Performance comparison has not passed", note: "n" }, "closed", "Not released for this Site"],
    [
      "continuity limit",
      { status: "continuity_limit", message: null, limitDays: 62, inspectedFrom: "2026-08-01", inspectedTo: "2026-10-01" },
      "continuity-limit",
      "The list cannot be completed",
    ],
    ["unauthenticated", { status: "unauthenticated", message: null }, "unauthenticated", "Sign in needed"],
    ["invalid", { status: "invalid", message: null, code: "INVALID_WINDOW", field: "to" }, "invalid", "This window is not valid"],
  ];
  it.each(refusedCases)("%s: a distinct non-positive state line with no time, no count and no zero claim", async (_n, result, expected, label) => {
    const { client } = indexClient(() => result);
    renderAt(PATH, client);
    await settledScreen();
    expect(state()).toBe(expected);
    noClaim();
    expectUntimedStateLine(label);
    expect(card().textContent).toContain("Domain links back to the Performance view that produced the finding.");
    const main = document.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, `site findings ${expected} (W1)`, { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    if (result.status === "invalid") {
      expect(exactValue("Recorded reason")).toBe("INVALID_WINDOW");
      expect(outsideDisclosure()).not.toContain("INVALID_WINDOW");
      disclosureScan("site findings invalid");
    }
  });

  it("a changed list keeps its raw reason and old page reference only in exact detail", async () => {
    const { client } = indexClient(() => ({ status: "basis_changed", message: "changed", reason: "SELECTION_CHANGED" }));
    renderAt(`${PATH}&cursor=old-cursor`, client);
    await settledScreen();
    expectUntimedStateLine("The list changed while you were reading it");
    expect(exactValue("Recorded reason")).toBe("SELECTION_CHANGED");
    expect(exactValue("Old page reference")).toBe("old-cursor");
    expect(outsideDisclosure()).not.toContain("SELECTION_CHANGED");
    w1Scans("site findings basis changed");
    disclosureScan("site findings basis changed");
  });
});

describe("W1-F3: Site Findings index renders exactly the v69 panel (sitefindings)", () => {
  const variants: [string, FindingIndexResult, string][] = [
    ["stocked", { status: "loaded", value: ROWS }, "current-rows"],
    ["empty (assessed)", { status: "loaded", value: indexBody() }, "current-empty"],
    ["pending (not current)", { status: "loaded", value: notCurrent("PENDING", "MATCH_PENDING") }, "PENDING"],
    ["refused (no access)", { status: "forbidden", message: null }, "forbidden"],
    ["refused (closed)", { status: "closed", message: "Performance comparison has not passed", note: "n" }, "closed"],
    ["refused (basis changed)", { status: "basis_changed", message: "changed", reason: "SELECTION_CHANGED" }, "basis-changed"],
  ];
  it.each(variants)("%s: one panel 'Findings at this site' holding the window, the state and its gap", async (_n, result, expected) => {
    const { client } = indexClient(() => result);
    renderAt(PATH, client);
    await settledScreen();
    expectV69Panels("sitefindings");
    const panel = card();
    expect(state()).toBe(expected);
    // post-W6 W1-a Q18 / R196: the mock's lens chips (All live and selected, the rest unbuilt) sit above the scope
    // strip; the strip carries "Manage in Findings"; the panel holds the compact window control under its heading.
    expect(statusBar().compareDocumentPosition(panel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const controls = panel.querySelector("[data-site-findings-controls]") as HTMLElement;
    expect(controls, "the window control row is in the panel").not.toBeNull();
    const lenses = screen.getByRole("list", { name: "Finding lenses" });
    expect(panel.contains(lenses), "the lens row is outside the panel").toBe(false);
    expect(lenses.compareDocumentPosition(statusBar()) & Node.DOCUMENT_POSITION_FOLLOWING, "lenses above the strip").toBeTruthy();
    const manage = statusBar().querySelector("[data-site-findings-manage]") as HTMLAnchorElement;
    expect(manage.textContent).toBe("Manage in Findings →");
    expect(manage.getAttribute("href")).toBe("/findings");
    expect(rowLabels(lenses)).toEqual([
      "All",
      `Cost (${UNAVAILABLE_STATUS})`,
      `Risks (${UNAVAILABLE_STATUS})`,
      `Opportunities (${UNAVAILABLE_STATUS})`,
    ]);
    expect(lenses.querySelector("[data-lens='all']")).toHaveAttribute("aria-current", "true");
    for (const lens of ["Cost", "Risks", "Opportunities"]) expectUnavailableEntry(lenses, lens);
    const windowRow = document.querySelector("[data-finding-index-window]") as HTMLElement;
    expect(windowRow.classList.contains("v69-chips"), "the window form is the mock's chips row").toBe(true);
    expect(controls.contains(windowRow)).toBe(true);
    expect(lenses.compareDocumentPosition(windowRow) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const heading = within(panel).getByRole("heading", { name: "Findings at this site" });
    expect(heading.compareDocumentPosition(controls) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(statusBar().querySelector("[data-product-status]"), "the shared state line is in the statusbar").not.toBeNull();
    expect(document.querySelector("[data-headline-card]"), "no lead card").toBeNull();
    expect(panel.querySelector("h3"), "no answer-card blocks or headline inside the panel").toBeNull();
    if (expected === "current-rows") {
      expect(panel.querySelectorAll("[data-finding-index-row]").length).toBeGreaterThan(0);
    } else {
      // The precise gap is stated inside the panel; no rows and no count.
      const gap = panel.querySelector("[data-site-findings-gap]") as HTMLElement;
      expect(gap, "an in-panel gap").not.toBeNull();
      expect((gap.textContent ?? "").length).toBeGreaterThan(20);
      expect(panel.querySelector("[data-finding-index-row]")).toBeNull();
      expect(panel.textContent).not.toMatch(/\d+ Findings? in this window/);
    }
  });
});

describe("W1-F3 height phase: Site Findings index shows the mock's three rows", () => {
  it("shows the first 3 rows of the page; the rest stay reachable, in the read's order, behind 'Show all N'; no repeated amount note", async () => {
    const ids = [1, 2, 3, 4, 5].map((n) => `f-${n}`);
    const five = indexBody({
      rows: ids.map((id, i) => indexRow(id, `r-${i + 1}`, `2026-10-25T1${5 - i}:00:00Z`, `2026-10-25T1${5 - i}:30:00Z`)),
      total_count: 5,
      next_cursor: null,
    });
    const { client } = indexClient(() => ({ status: "loaded", value: five }));
    renderAt(PATH, client);
    await settledScreen();
    const rows = Array.from(document.querySelectorAll("[data-finding-index-row]"));
    expect(rows.map((r) => r.getAttribute("data-finding-index-row"))).toEqual(ids);
    expect(rows.filter((r) => visibleOutsideClosedDisclosure(r)).map((r) => r.getAttribute("data-finding-index-row"))).toEqual(ids.slice(0, 3));
    const showAll = document.querySelector("details[data-show-all='finding-index-rows']") as HTMLDetailsElement;
    expect(showAll.open).toBe(false);
    expect(showAll.querySelector("summary")).toHaveTextContent("Show all 5 Findings on this page");
    // W1-F3 review M4: the in-panel amount note is gone; every visible row's cell and the notice still say no amount.
    expect(document.querySelectorAll("[data-finding-index-amount-note]")).toHaveLength(0);
    for (const row of rows.filter((r) => visibleOutsideClosedDisclosure(r))) {
      expect(row.querySelector("[data-finding-index-amount]")?.textContent).toBe("Not in this list");
    }
    expect(document.querySelector("[data-site-findings-notice], .notice")?.textContent).toMatch(/No amount is shown in this list/);
    // All five rows are on this page, so no "Showing 5 of 5." line repeats the count.
    expect(document.body.textContent).not.toMatch(/Showing 5 of 5/);
  });

  it("W1-F3 review M4: a window of more than one day keeps its day strip beside the rows", async () => {
    const twoDays = indexBody({ rows: ROWS.rows, total_count: 3 });
    twoDays.watermarks.days = [twoDays.watermarks.days[0], { ...twoDays.watermarks.days[0], day: "2026-10-26" }];
    const { client } = indexClient(() => ({ status: "loaded", value: twoDays }));
    renderAt(PATH, client);
    await settledScreen();
    expect(document.querySelectorAll("[data-step-strip] [data-step]")).toHaveLength(2);
  });
});

// --- post-W6 W1-b Q19/Q20 (R197) -----------------------------------------------------------------------------------

describe("post-W6 W1-b: Site Findings index Domain and renewable links (Q19/Q20)", () => {
  const dispatch = sitePerformanceHref(SITE_ID, "dispatch");
  const interval = (id: string) => ({
    assessment_revision_id: id,
    analytic_run_id: "run",
    model_version: "dispatch-3.1",
    matcher_version: "finding-episode-1",
    cohort_sha256: null,
  });
  const BODY = indexBody({
    rows: [
      // A proved 15-minute interval revision: the link selects it.
      indexRow(FID_B, RID_B, "2026-10-25T18:00:00Z", "2026-10-25T19:00:00Z", {
        assessment: { ...interval("iv-1"), interval_assessment_revision_ids: ["iv-1"] },
      }),
      // A whole-window primary (not in the interval list): day only.
      indexRow(FID_A, RID_A, "2026-10-25T23:30:00+03:00", "2026-10-25T23:45:00+03:00", {
        assessment: { ...interval("win-1"), interval_assessment_revision_ids: ["iv-9"] },
      }),
      // No interval list at all: day only.
      indexRow("f-missing-list", "r-missing-list", "2026-10-24T06:00:00Z", "2026-10-24T07:00:00Z", { assessment: interval("ar") }),
      // An invalid episode start: plain Domain text, no invented day.
      indexRow("f-invalid", "r-invalid", "not-a-time", "2026-10-24T07:00:00Z", { assessment: interval("ar") }),
    ],
    total_count: 4,
  });
  const domain = (fid: string) =>
    card().querySelector(`[data-finding-index-row="${fid}"] [data-finding-index-domain]`) as HTMLElement;

  it("links Dispatch to the row's UTC day, adding a revision only when the row proves it is an interval revision", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: BODY }));
    renderAt(PATH, client);
    await settledScreen();
    expect(within(domain(FID_B)).getByRole("link", { name: "Dispatch" })).toHaveAttribute("href", `${dispatch}?day=2026-10-25&revision=iv-1`);
    // 23:30 at +03:00 is 20:30 UTC on the same day; the whole-window primary is never selected.
    expect(within(domain(FID_A)).getByRole("link", { name: "Dispatch" })).toHaveAttribute("href", `${dispatch}?day=2026-10-25`);
    expect(within(domain("f-missing-list")).getByRole("link", { name: "Dispatch" })).toHaveAttribute("href", `${dispatch}?day=2026-10-24`);
    expect(domain("f-invalid").querySelector("a")).toBeNull();
    expect(domain("f-invalid").textContent).toBe("Dispatch");
    expect(card().textContent).toContain("Domain links back to the Performance view that produced the finding.");
  });

  it("links 'open the renewable evaluation' to the Site's Performance Renewable view, with no Opportunity address", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: BODY }));
    renderAt(PATH, client);
    await settledScreen();
    const helper = document.querySelector("[data-opportunity-index-helper]") as HTMLElement;
    expect(helper.textContent).toBe("Opportunity index unavailable; open the renewable evaluation for this site's five-day study.");
    const link = within(helper).getByRole("link", { name: "open the renewable evaluation" });
    expect(link).toHaveAttribute("href", sitePerformanceHref(SITE_ID, "renewable"));
    expect(link.getAttribute("href")).not.toMatch(/opportunit/i);
  });
});

describe("OUT-C U5 mini Site Findings early warnings", () => {
  it("lists the board warnings under the list for the UTC day of to, without the Site name", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    const board = fakeOutcomeBoard({ status: "loaded", value: boardBody({ warnings: [planWarning({ title: "Battery at or near its reserve" })] }) });
    renderAt(PATH, client, board.client);
    await settledScreen();
    await waitFor(() => expect(document.querySelector("[data-early-warnings]")).not.toBeNull());
    expect(board.calls).toEqual([{ siteCode: SITE_ID, query: { date: "2026-10-25" } }]);
    const list = document.querySelector("[data-early-warnings]") as HTMLElement;
    expect(card().contains(list)).toBe(true);
    expect(list.querySelector("strong")?.textContent).toBe("Battery at or near its reserve");
    expect(list.querySelector("small")?.textContent).toBe("Protect asset and capital · Due 2 Nov");
    expect(describeViolations(scanProductVocabulary(list, "site-findings", { set: "w1" }).violations)).toBe("");
  });

  it("shows no list when the board has no warnings", async () => {
    const { client } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    const board = fakeOutcomeBoard({ status: "loaded", value: boardBody() });
    renderAt(PATH, client, board.client);
    await settledScreen();
    await waitFor(() => expect(board.calls).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(card()).not.toBeNull();
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });
});
