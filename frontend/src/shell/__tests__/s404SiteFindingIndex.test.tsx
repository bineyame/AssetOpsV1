/**
 * S4-04 phase 2: Site > Findings over the scoped Site Finding index for an
 * imported Site (`sitefindings:1#a` assessed empty, `#b` positive rows), with
 * the scope in the address and every non-current or refused read showing no
 * rows, no count and no "no Findings" claim.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
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
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

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

function renderAt(path: string, index: FindingIndexClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteAnalytics={analyticsClient(SITE_ID)}
        siteFindingIndex={index}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";
const state = () => document.querySelector("[data-finding-index-state]")?.getAttribute("data-finding-index-state");
const query = () => new URLSearchParams(where().split("?")[1] ?? "");

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
    expect(screen.getByRole("heading", { name: "No Findings in this window" })).toBeInTheDocument();
    expect(document.querySelector("[data-finding-index-token]")?.textContent).toBe(TOKEN);
    expect(document.querySelector('[data-finding-index-day="2026-10-25"]')?.textContent).toContain("Assessed");
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
    expect(screen.getByRole("heading", { name: "3 Findings in this window" })).toBeInTheDocument();
    const rows = Array.from(document.querySelectorAll("[data-finding-index-row]"));
    expect(rows.map((r) => r.getAttribute("data-finding-index-row"))).toEqual([FID_B, FID_A]);
    const links = Array.from(document.querySelectorAll("[data-finding-index-link]"));
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      `/sites/${SITE_ID}/findings/${FID_B}?revision_id=${RID_B}`,
      `/sites/${SITE_ID}/findings/${FID_A}?revision_id=${RID_A}`,
    ]);
    expect(within(rows[0] as HTMLElement).getByRole("link", { name: FID_A.slice(0, 8) })).toHaveAttribute(
      "href",
      `/sites/${SITE_ID}/findings/${FID_A}`,
    );
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
      expect(document.querySelector("[data-finding-index-reasons]")?.textContent).toContain("2026-10-25");
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
