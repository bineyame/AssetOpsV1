/**
 * S5-02 (`mini:3#a/b`): the imported Site Overview's selected-day Finding list over the S4-04 Site Finding index.
 *
 * The index is read with the Overview's served day as its exact half-open window; only a CURRENT, is_current read
 * with a count lists rows or says "no Findings"; every other read and every refusal shows no rows and no count.
 * Parity with the Overview's own Finding card follows `D-2026-10-16-s502-parity` (positive, retained pin,
 * differing basis, same-basis ID mismatch).
 */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { FindingIndexBody, FindingIndexClient, FindingIndexResult, FindingIndexScope } from "../../sites/findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { OverviewSelection, SiteOverviewClient, SiteWindowSummary } from "../../sites/siteOverviewClient";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import { indexBody, indexRow, notCurrent } from "../../sites/__tests__/findingIndexFixtures";
import { overviewClient, populatedOverview } from "../../sites/__tests__/overviewFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { OVERVIEW_FINDING_PREVIEW_LIMIT } from "../../sites/OverviewFindingList";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { FID, RID, WA, summary } from "./s5WindowFixtures";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };
const OTHER_FID = "0c0c0c0c-0000-4000-8000-00000000000c";
const OTHER_RID = "1c1c1c1c-0000-4000-8000-00000000001c";
const DAY = "2026-10-15";
const RUN = "9a9a9a9a-0000-4000-8000-00000000009a";

function next(day: string): string {
  const d = new Date(`${day}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

/** The Overview's served day as the server builds it: `[day 00:00Z, next day 00:00Z)`. */
function day(d: string, over: Partial<SiteWindowSummary> = {}): SiteWindowSummary {
  const base = summary(d);
  return {
    ...base,
    assessment: { ...base.assessment, run_id: RUN },
    window: { start: `${d}T00:00:00Z`, end: `${next(d)}T00:00:00Z`, utc_date: d, bounds: "[start, end)" },
    ...over,
  };
}

/** An index body on the same basis as `day(d)`: same Site, window, S3 selection and S4 matching pass. */
function aligned(d: string, over: Partial<FindingIndexBody> = {}): FindingIndexBody {
  return indexBody({
    site_id: "site-uuid",
    window: { from: `${d}T00:00:00Z`, to: `${next(d)}T00:00:00Z`, bounds: "[from, to)", intersection: "x" },
    discovery: { days: [d], requested_days: [d], continuity_tolerance_minutes: 20, limit_days: 62 },
    watermarks: {
      matcher: { match_pass_id: "mp", matched_through_selection_seq: 4 },
      days: [
        {
          day: d,
          status: "CURRENT",
          reasons: [],
          s3: {
            status: "CURRENT",
            selection_seq: 4,
            run_id: RUN,
            window_assessment_revision_id: WA,
            model_version: "dispatch-3.1",
            input_sha256: "def",
            configuration_sha256: "ghi",
            knowledge_cutoff: `${d}T12:00:00Z`,
            selected_at: `${d}T12:00:00Z`,
          },
          s4: { matched: true, matcher_version: "m" },
        },
      ],
    },
    ...over,
  });
}

const rowsOf = (d: string, firstId = FID, firstRev = RID) => [
  indexRow(firstId, firstRev, `${d}T06:00:00Z`, `${d}T08:00:00Z`),
  indexRow(OTHER_FID, OTHER_RID, `${d}T02:00:00Z`, `${d}T03:00:00Z`, { lifecycle: "NO_LONGER_SUPPORTED" }),
];

function positive(d: string, over: Partial<FindingIndexBody> = {}): FindingIndexBody {
  return aligned(d, { rows: rowsOf(d), total_count: 3, next_cursor: "cursor-2", ...over });
}

function overviewOf(answer: (selection: OverviewSelection) => SiteWindowSummary) {
  const getOverview = vi.fn((_s: string, _w: unknown, selection: OverviewSelection = {}) =>
    Promise.resolve({ status: "loaded" as const, value: answer(selection) }),
  );
  return { client: { getOverview } as unknown as SiteOverviewClient, getOverview };
}

function indexOf(answer: (scope: FindingIndexScope) => FindingIndexResult) {
  const getFindingIndex = vi.fn((_site: string, scope: FindingIndexScope) => Promise.resolve(answer(scope)));
  return { client: { getFindingIndex } as FindingIndexClient, getFindingIndex };
}

function Probe() {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output data-location>{`${location.pathname}${location.search}`}</output>
      <button type="button" data-back onClick={() => navigate(-1)}>
        back
      </button>
    </>
  );
}

function renderAt(path: string, overview: SiteOverviewClient, index: FindingIndexClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteOverview={overview}
        siteFindingIndex={index}
      />
      <Probe />
    </MemoryRouter>,
  );
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";
const listState = () =>
  document.querySelector("[data-overview-finding-list]")?.getAttribute("data-overview-finding-list") ?? null;
const rowIds = () =>
  Array.from(document.querySelectorAll("[data-overview-finding-row]")).map((r) => r.getAttribute("data-overview-finding-row"));
const parity = () =>
  document.querySelector("[data-overview-finding-parity]")?.getAttribute("data-overview-finding-parity") ?? null;

function noClaim() {
  expect(document.querySelector("[data-overview-finding-row]")).toBeNull();
  expect(document.querySelector("[data-overview-finding-parity]")).toBeNull();
  expect(screen.queryByText(/No Findings for this day/)).toBeNull();
  expect(screen.queryByText(/\d+ Findings? overlap this day/)).toBeNull();
}

function fullListQuery(): URLSearchParams {
  const href = document.querySelector("[data-overview-finding-full-list]")?.getAttribute("href") ?? "";
  expect(href.startsWith(`/sites/${SITE_ID}/findings?`)).toBe(true);
  return new URLSearchParams(href.split("?")[1]);
}

describe("S5-02 Overview Finding list: request scope", () => {
  it("reads the index with the Overview's served day, the supported domain and the preview limit", async () => {
    const overview = overviewOf(() => day("2026-10-25"));
    const index = indexOf(() => ({ status: "loaded", value: aligned("2026-10-25") }));
    renderAt(`/sites/${SITE_ID}`, overview.client, index.client);
    await settledScreen();
    expect(index.getFindingIndex).toHaveBeenCalledTimes(1);
    expect(index.getFindingIndex.mock.calls[0]).toEqual([
      "KOBO-001",
      {
        domain: "mini-grid-dispatch",
        from: "2026-10-25T00:00:00Z",
        to: "2026-10-26T00:00:00Z",
        limit: OVERVIEW_FINDING_PREVIEW_LIMIT,
        cursor: null,
      },
    ]);
    // The served day, not the browser clock, is the window; the address keeps S5-01's keys.
    expect(where()).toBe(`/sites/${SITE_ID}?date=2026-10-25&finding_id=${FID}&finding_revision_id=${RID}`);
  });

  it("a legacy (not imported) Overview issues no index request and shows no list", async () => {
    const index = indexOf(() => ({ status: "loaded", value: aligned(DAY) }));
    renderAt(
      `/sites/${SITE_ID}`,
      overviewClient({ status: "loaded", value: populatedOverview(SITE_ID) }),
      index.client,
    );
    await settledScreen();
    expect(index.getFindingIndex).not.toHaveBeenCalled();
    expect(document.querySelector("[data-overview-finding-list]")).toBeNull();
  });
});

describe("S5-02 Overview Finding list: assessed zero and Unknown (mini:3#a)", () => {
  it("states the assessed zero with its basis and links the full list for the identical window", async () => {
    const overview = overviewOf(() => day("2026-10-25", { known_finding: null }));
    const body = aligned("2026-10-25", {
      discovery: { days: ["2026-10-24", "2026-10-25"], requested_days: ["2026-10-25"], continuity_tolerance_minutes: 20, limit_days: 62 },
    });
    renderAt(`/sites/${SITE_ID}?date=2026-10-25`, overview.client, indexOf(() => ({ status: "loaded", value: body })).client);
    await settledScreen();
    expect(listState()).toBe("current-empty");
    const list = document.querySelector('[data-overview-finding-list="current-empty"]') as HTMLElement;
    expect(list.textContent).toContain("No Findings for this day.");
    expect(list.textContent).toContain("2026-10-24, 2026-10-25");
    expect(list.querySelector("[data-finding-index-token]")?.textContent).toBe(body.selection_token);
    const q = fullListQuery();
    expect([q.get("domain"), q.get("from"), q.get("to"), q.get("limit")]).toEqual([
      "mini-grid-dispatch",
      "2026-10-25T00:00:00Z",
      "2026-10-26T00:00:00Z",
      null,
    ]);
  });

  it.each([
    ["UNASSESSED", "S3_UNASSESSED"],
    ["STALE_PROJECTION", "S3_DIRTY"],
    ["FAILED", "S3_FAILED"],
    ["PENDING", "S4_MATCH_DEFERRED_WINDOW"],
  ] as const)("a %s index reads Unknown with its reasons and makes no zero claim", async (status, reason) => {
    const overview = overviewOf(() => day(DAY));
    const body = { ...notCurrent(status, reason), window: aligned(DAY).window };
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overview.client, indexOf(() => ({ status: "loaded", value: body })).client);
    await settledScreen();
    expect(listState()).toBe(status);
    expect(document.querySelector("[data-finding-index-reasons]")?.textContent).toContain(reason);
    noClaim();
    // The Overview's own Finding card stays under its own read.
    expect(document.querySelector(`[data-known-finding="${FID}"]`)).not.toBeNull();
  });

  it("a CURRENT status that is not is_current (a deferred matched window) makes no empty claim", async () => {
    const body = aligned(DAY, { is_current: false, total_count: null });
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => day(DAY)).client, indexOf(() => ({ status: "loaded", value: body })).client);
    await settledScreen();
    expect(listState()).toBe("CURRENT");
    noClaim();
  });

  it.each([
    [{ status: "closed", message: "Performance source closed.", note: null }, "closed"],
    [{ status: "continuity_limit", message: "Too long.", limitDays: 62, inspectedFrom: null, inspectedTo: null }, "continuity_limit"],
    [{ status: "basis_changed", message: null, reason: "TOKEN" }, "basis_changed"],
    [{ status: "unauthenticated", message: null }, "unauthenticated"],
    [{ status: "forbidden", message: null }, "forbidden"],
    [{ status: "invalid", message: null, code: "X", field: "from" }, "invalid"],
    [{ status: "unavailable", message: null }, "unavailable"],
  ] as [FindingIndexResult, string][])("a refused read (%#) shows no rows, no count and keeps the Overview", async (result, state) => {
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => day(DAY)).client, indexOf(() => result).client);
    await settledScreen();
    expect(listState()).toBe(state);
    noClaim();
    expect(document.querySelector("[data-money-state]")).not.toBeNull();
    expect(document.querySelector("[data-freshness-state]")).not.toBeNull();
  });
});

describe("S5-02 Overview Finding list: positive rows and parity (mini:3#b)", () => {
  it("lists persisted rows in index order with exact revision links, the first-page state and same-basis parity", async () => {
    const body = positive(DAY);
    const { container } = renderAt(
      `/sites/${SITE_ID}?date=${DAY}`,
      overviewOf(() => day(DAY)).client,
      indexOf(() => ({ status: "loaded", value: body })).client,
    );
    await settledScreen();
    expect(listState()).toBe("current-rows");
    expect(rowIds()).toEqual([FID, OTHER_FID]);
    const links = Array.from(document.querySelectorAll("[data-overview-finding-link]")).map((a) => a.getAttribute("href"));
    expect(links).toEqual([
      `/sites/${SITE_ID}/findings/${FID}?revision_id=${RID}`,
      `/sites/${SITE_ID}/findings/${OTHER_FID}?revision_id=${OTHER_RID}`,
    ]);
    expect(screen.getByText("3 Findings overlap this day.")).toBeInTheDocument();
    expect(document.querySelector('[data-overview-finding-shown="first-page"]')?.textContent).toBe(
      "Showing the first 2 of 3. This is not the whole list.",
    );
    expect(fullListQuery().get("from")).toBe(`${DAY}T00:00:00Z`);
    expect(parity()).toBe("same");
    expect(document.querySelector("[data-overview-finding-reload]")).toBeNull();
    expect(document.querySelector("[data-finding-index-token]")?.textContent).toBe(body.selection_token);
    // No amount, priority or action is invented on the list.
    const list = document.querySelector('[data-overview-finding-list="current-rows"]') as HTMLElement;
    expect(list.textContent).not.toMatch(/\$|USD|priority|action/i);
    const { violations } = scanProductVocabulary(container, "overview finding list");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("a retained address pin is not compared; both bases and a reload are shown and rows stay", async () => {
    const overview = overviewOf(() =>
      day(DAY, { known_finding: { ...day(DAY).known_finding!, selected_by: "PINNED_RETAINED_WHILE_BASIS_INCOMPLETE" } }),
    );
    renderAt(`/sites/${SITE_ID}?date=${DAY}&finding_id=${FID}&finding_revision_id=${RID}`, overview.client,
      indexOf(() => ({ status: "loaded", value: positive(DAY) })).client);
    await settledScreen();
    expect(parity()).toBe("not-compared");
    expect(rowIds()).toEqual([FID, OTHER_FID]);
    expect(document.querySelector("[data-overview-finding-parity]")?.textContent).toContain("kept address pin");
    expect(document.querySelector("[data-overview-finding-reload]")).not.toBeNull();
    expect(screen.queryByText(/is the same Finding version/)).toBeNull();
  });

  it("a non-current Overview with otherwise matching reads makes no same claim", async () => {
    const stale = day(DAY);
    stale.freshness = { ...stale.freshness, state: "STALE_PROJECTION", reasons: ["SCHEDULE_STOPPED"] };
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => stale).client, indexOf(() => ({ status: "loaded", value: positive(DAY) })).client);
    await settledScreen();
    expect(parity()).toBe("not-compared");
    expect(document.querySelector("[data-overview-finding-parity]")?.textContent).toContain("The Overview itself is not current");
    expect(document.querySelector("[data-overview-finding-reload]")).not.toBeNull();
    expect(screen.queryByText(/is the same Finding version/)).toBeNull();
    expect(rowIds()).toEqual([FID, OTHER_FID]);
  });

  it("a current read with a count but an empty first page makes no count claim and offers a reload", async () => {
    const body = positive(DAY, { rows: [], total_count: 3, next_cursor: "cursor-2" });
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => day(DAY)).client, indexOf(() => ({ status: "loaded", value: body })).client);
    await settledScreen();
    expect(listState()).toBe("unavailable");
    expect(screen.queryByText(/Showing the first 0/)).toBeNull();
    expect(document.querySelector("[data-overview-finding-reload]")).not.toBeNull();
  });

  it("a differing basis (another assessment selection) is not compared", async () => {
    const body = positive(DAY);
    body.watermarks.days[0].s3.selection_seq = 5;
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => day(DAY)).client, indexOf(() => ({ status: "loaded", value: body })).client);
    await settledScreen();
    expect(parity()).toBe("not-compared");
    expect(document.querySelector("[data-overview-finding-parity]")?.textContent).toContain(
      "The assessment selection differs between the two reads.",
    );
    expect(rowIds()).toEqual([FID, OTHER_FID]);
  });

  it("on the same basis, different IDs are named as a disagreement with no equality claim", async () => {
    const body = positive(DAY, { rows: rowsOf(DAY, OTHER_FID, OTHER_RID).slice(0, 1), total_count: 1, next_cursor: null });
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => day(DAY)).client, indexOf(() => ({ status: "loaded", value: body })).client);
    await settledScreen();
    expect(parity()).toBe("different");
    expect(screen.queryByText(/is the same Finding version/)).toBeNull();
    expect(document.querySelector('[data-overview-finding-shown="all"]')?.textContent).toBe("Showing all 1.");
    expect(document.querySelector(`[data-known-finding="${FID}"]`)).not.toBeNull();
  });

  it("the reload reads the Overview and the list again", async () => {
    const overview = overviewOf(() =>
      day(DAY, { known_finding: { ...day(DAY).known_finding!, selected_by: "PINNED_RETAINED_WHILE_BASIS_INCOMPLETE" } }),
    );
    const index = indexOf(() => ({ status: "loaded", value: positive(DAY) }));
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overview.client, index.client);
    await settledScreen();
    expect(overview.getOverview).toHaveBeenCalledTimes(1);
    fireEvent.click(document.querySelector("[data-overview-finding-reload]") as HTMLElement);
    await settledScreen();
    expect(overview.getOverview).toHaveBeenCalledTimes(2);
    expect(index.getFindingIndex).toHaveBeenCalledTimes(2);
  });
});

describe("S5-02 Overview Finding list: date change, late answers and navigation", () => {
  it("a date change re-reads the new day and an older day's late answer never appears", async () => {
    const pending = new Map<string, (r: FindingIndexResult) => void>();
    const getFindingIndex = vi.fn(
      (_s: string, scope: FindingIndexScope) =>
        new Promise<FindingIndexResult>((resolve) => pending.set(scope.from.slice(0, 10), resolve)),
    );
    const overview = overviewOf((sel) => day(sel.date ?? DAY));
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overview.client, { getFindingIndex });
    await screen.findByText(/Loading the findings for this day/);
    fireEvent.click(document.querySelector('[data-window-day-link="next"]') as HTMLElement);
    await screen.findByText(/Findings for 2026-10-16/);
    // The old day answers last, after the new day.
    await act(async () => {
      pending.get("2026-10-16")!({ status: "loaded", value: aligned("2026-10-16") });
    });
    await act(async () => {
      pending.get(DAY)!({ status: "loaded", value: positive(DAY) });
    });
    await settledScreen();
    expect(listState()).toBe("current-empty");
    expect(rowIds()).toEqual([]);
    expect(where()).toContain("date=2026-10-16");
    // The date change dropped the old day's Finding pin from the request.
    expect(overview.getOverview.mock.calls[1][2]).toMatchObject({ date: "2026-10-16", finding_id: null });
  });

  it("a row link opens the exact revision and Back returns to the selected Overview day", async () => {
    renderAt(`/sites/${SITE_ID}?date=${DAY}`, overviewOf(() => day(DAY)).client,
      indexOf(() => ({ status: "loaded", value: positive(DAY) })).client);
    await settledScreen();
    const before = where();
    const row = document.querySelector(`[data-overview-finding-row="${OTHER_FID}"]`) as HTMLElement;
    const link = within(row).getByRole("link");
    link.focus();
    expect(document.activeElement).toBe(link);
    fireEvent.click(link);
    expect(where()).toBe(`/sites/${SITE_ID}/findings/${OTHER_FID}?revision_id=${OTHER_RID}`);
    fireEvent.click(document.querySelector("[data-back]") as HTMLElement);
    await settledScreen();
    expect(where()).toBe(before);
    expect(where()).toContain(`date=${DAY}`);
  });
});
