/**
 * IDX-GAPS U3: the Site Findings page, the Overview day list and the outcome board on a PARTIAL index
 * (`finding-index/2`): rows from the checked days, the days not checked yet named, never a zero or proved-empty claim.
 */
import { render, screen } from "@testing-library/react";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { FindingIndexBody, FindingIndexClient } from "../../sites/findingIndexClient";
import { gapDays, listsRows } from "../../sites/findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { analyticsClient } from "../../sites/__tests__/analyticsFixtures";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import {
  FID_A,
  FID_B,
  RID_A,
  RID_B,
  indexBody,
  indexClient,
  indexRow,
  partialBody,
} from "../../sites/__tests__/findingIndexFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { OverviewFindingList } from "../../sites/OverviewFindingList";
import { OutcomeBoard } from "../../sites/OutcomeBoard";
import { boardBody, fakeOutcomeBoard } from "../../test/outcomeBoardFixture";
import { panelTitled } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { summary } from "./s5WindowFixtures";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };
const WINDOW = "from=2026-10-25T00%3A00%3A00Z&to=2026-10-28T00%3A00%3A00Z&domain=mini-grid-dispatch";
const PATH = `/sites/${SITE_ID}/findings?${WINDOW}`;
const ROW = indexRow(FID_A, RID_A, "2026-10-25T08:00:00Z", "2026-10-25T09:00:00Z");

function renderPage(index: FindingIndexClient) {
  return render(
    <MemoryRouter initialEntries={[PATH]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteAnalytics={analyticsClient(SITE_ID)}
        siteFindingIndex={index}
      />
    </MemoryRouter>,
  );
}

async function page(body: FindingIndexBody) {
  const { client } = indexClient(() => ({ status: "loaded", value: body }));
  renderPage(client);
  await settledScreen();
  return panelTitled("Findings at this site");
}

const claim = () => document.querySelector("[data-site-findings-claim]")?.textContent ?? null;
const state = () => document.querySelector("[data-finding-index-state]")?.getAttribute("data-finding-index-state");
const NEVER = [/No Findings in this window/, /Every day in this window was assessed/, /\d+ Findings? in this window/];

describe("IDX-GAPS client helpers", () => {
  it("lists rows on a current CURRENT or a PARTIAL body, and counts only requested days not checked", () => {
    expect(listsRows(indexBody())).toBe(true);
    expect(listsRows(indexBody({ is_current: false }))).toBe(false);
    expect(listsRows(partialBody([]))).toBe(true);
    expect(listsRows(indexBody({ status: "UNASSESSED", is_current: false }))).toBe(false);
    const body = partialBody([ROW], {
      gaps: [
        { day: "2026-10-24", state: "PENDING", reason: "NOT_CURRENT" },
        { day: "2026-10-25", state: "CURRENT", reason: "WITHHELD_FINDING" },
        { day: "2026-10-26", state: "UNASSESSED", reason: "NOT_CURRENT" },
      ],
    });
    expect(gapDays(body).map((g) => g.day)).toEqual(["2026-10-26"]);
  });
});

describe("IDX-GAPS Site Findings page on a PARTIAL index", () => {
  it("lists the row, names the gap day in the paragraph and the day strip", async () => {
    const card = await page(partialBody([ROW]));
    expect(state()).toBe("partial");
    expect(document.querySelector("[data-site-findings='partial']")).not.toBeNull();
    expect(claim()).toBe("1 Finding on the assessed days");
    expect(card.querySelector(`[data-finding-index-row='${FID_A}']`)).not.toBeNull();
    expect(card.querySelector("[data-site-findings-gap-days]")?.textContent).toBe(
      "1 of 3 days in this window is not analysed yet, so nothing is concluded about it.",
    );
    expect(screen.getAllByText("Some days are incomplete").length).toBeGreaterThan(0);
    const steps = Array.from(card.querySelectorAll<HTMLElement>("[data-step-strip] [data-step]"));
    expect(steps.length).toBe(3);
    expect(steps[1]?.textContent).toContain("This period has not been analysed");
    expect(card.textContent).not.toContain("A Finding that reaches into one of the incomplete days");
    for (const never of NEVER) expect(document.body.textContent).not.toMatch(never);
    for (const set of [undefined, "w1"] as const) {
      const { violations } = scanProductVocabulary(document.body, "sitefindings partial", set ? { set } : {});
      expect(violations, describeViolations(violations)).toEqual([]);
    }
  });

  it("uses the zero form with no rows, never the proved-empty words, and says when a Finding is held back", async () => {
    const card = await page(partialBody([], { withheld: true }));
    expect(claim()).toBe("No Findings on the assessed days");
    expect(card.querySelector("[data-finding-index-row]")).toBeNull();
    expect(card.textContent).toContain(
      "A Finding that reaches into one of the incomplete days is not shown until that day is analysed.",
    );
    for (const never of NEVER) expect(document.body.textContent).not.toMatch(never);
    expect(document.body.textContent).not.toContain("No Findings are listed and no count is given");
  });

  it("names no count when no requested day is a gap, and keeps the neighbouring-day sentence", async () => {
    const card = await page(
      partialBody([ROW], { gaps: [{ day: "2026-10-28", state: "PENDING", reason: "NOT_CURRENT" }] }),
    );
    expect(card.querySelector("[data-site-findings-gap-days]")).toBeNull();
    expect(card.textContent).toContain("A Finding that reaches into a neighbouring day not analysed yet is not shown.");
  });

  it("keeps the CURRENT rows view unchanged", async () => {
    const rows = indexBody({
      rows: [indexRow(FID_B, RID_B, "2026-10-25T18:00:00Z", "2026-10-25T19:00:00Z"), ROW],
      total_count: 2,
    });
    await page(rows);
    expect(state()).toBe("current-rows");
    expect(claim()).toBe("2 Findings in this window");
    expect(document.querySelector("[data-site-findings='partial']")).toBeNull();
  });
});

describe("IDX-GAPS Overview day list on a PARTIAL index", () => {
  const links = { finding: (f: string, r: string) => `/f/${f}?r=${r}`, findingList: () => "/list" };
  const day = "2026-10-25";
  const oneDay = (rows: FindingIndexBody["rows"], over: Partial<FindingIndexBody> = {}) =>
    partialBody(rows, {
      window: { from: `${day}T00:00:00Z`, to: "2026-10-26T00:00:00Z", bounds: "[from, to)", intersection: "x" },
      discovery: { days: [day, "2026-10-26"], requested_days: [day], continuity_tolerance_minutes: 20, limit_days: 62 },
      gaps: [
        { day, state: "CURRENT", reason: "WITHHELD_FINDING" },
        { day: "2026-10-26", state: "UNASSESSED", reason: "NOT_CURRENT" },
      ],
      withheld: true,
      ...over,
    });

  async function overview(body: FindingIndexBody) {
    const { client } = indexClient(() => ({ status: "loaded", value: body }));
    render(
      <MemoryRouter>
        <OverviewFindingList summary={summary(day)} client={client} links={links} onReload={() => undefined} />
      </MemoryRouter>,
    );
    await settledScreen();
  }

  it("lists the row and the note after the count", async () => {
    await overview(oneDay([ROW]));
    expect(document.querySelector("[data-overview-finding-list]")?.getAttribute("data-overview-finding-list")).toBe(
      "current-rows",
    );
    expect(document.querySelector(`[data-overview-finding-row='${FID_A}']`)).not.toBeNull();
    expect(document.querySelector("[data-overview-finding-partial]")?.textContent).toBe(
      "A Finding that reaches into a neighbouring day not analysed yet is not shown.",
    );
  });

  it("never says the day has no Findings when the only Finding was held back", async () => {
    await overview(oneDay([]));
    expect(document.querySelector("[data-overview-finding-list]")?.getAttribute("data-overview-finding-list")).toBe(
      "partial-empty",
    );
    expect(document.body.textContent).toContain("No Findings on the assessed days.");
    expect(document.body.textContent).not.toContain("No Findings for this day");
  });
});

describe("IDX-GAPS outcome board gap line", () => {
  async function board(body = boardBody()) {
    const fake = fakeOutcomeBoard({ status: "loaded", value: body });
    render(
      <MemoryRouter>
        <OutcomeBoard client={fake.client} siteCode="KOBO-001" query={{ date: "2026-10-06" }} />
      </MemoryRouter>,
    );
    await settledScreen();
  }

  it("renders the backend line under the rows only when present", async () => {
    const text = "23 of the last 31 days have no checked readings yet";
    await board(boardBody({ finding_gaps: { text, days: ["2026-10-01"] } }));
    const line = document.querySelector("[data-outcome-finding-gaps]");
    expect(line?.textContent).toBe(text);
    expect(line?.className).toBe("v69-chart-note");
  });

  it("renders nothing without it", async () => {
    await board(boardBody({ finding_gaps: null }));
    expect(document.querySelector("[data-outcome-finding-gaps]")).toBeNull();
  });
});
