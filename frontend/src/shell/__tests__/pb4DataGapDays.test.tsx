/**
 * PB-4 (D-E5.46): a day whose selected run could not be analysed for a data fact (conflicting readings, or not
 * enough readings) makes the Site Findings list and the Overview day list PARTIAL with the data-fact words. It is
 * never "Checked: nothing to report", and "not analysed yet" stays for system work only.
 */
import { render } from "@testing-library/react";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { FindingIndexBody } from "../../sites/findingIndexClient";
import { gapDays } from "../../sites/findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { analyticsClient } from "../../sites/__tests__/analyticsFixtures";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import { FID_A, RID_A, indexBody, indexClient, indexRow, partialBody } from "../../sites/__tests__/findingIndexFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { OverviewFindingList } from "../../sites/OverviewFindingList";
import { dayGapWords } from "../../ui/productWords";
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
const CONFLICT = "Readings for this day conflict (duplicate or overlapping reports), so it can't be analysed";
const TOO_FEW = "Not enough readings received to analyse this day";
const NEVER = [/(Checked|Analysed): nothing to report/, /not analysed yet/i, /not checked yet/, /No Findings in this window/];

/** Every day CURRENT in S3; the named day is a data gap. */
function dataGapBody(rows: FindingIndexBody["rows"], reason: string, over: Partial<FindingIndexBody> = {}) {
  const day = indexBody().watermarks.days[0];
  const days = ["2026-10-25", "2026-10-26", "2026-10-27"];
  return partialBody(rows, {
    watermarks: { matcher: indexBody().watermarks.matcher, days: days.map((d) => ({ ...day, day: d })) },
    status_reasons: [],
    gaps: [{ day: "2026-10-26", state: "CURRENT", reason }],
    ...over,
  });
}

async function page(body: FindingIndexBody) {
  const { client } = indexClient(() => ({ status: "loaded", value: body }));
  render(
    <MemoryRouter initialEntries={[PATH]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteAnalytics={analyticsClient(SITE_ID)}
        siteFindingIndex={client}
      />
    </MemoryRouter>,
  );
  await settledScreen();
  return panelTitled("Findings at this site");
}

describe("PB-4 shared day-gap words", () => {
  it("states the data fact in full and short form, and keeps 'not analysed yet' for system work", () => {
    expect(dayGapWords("READINGS_CONFLICT")).toMatchObject({ label: CONFLICT, short: "conflicting readings" });
    expect(dayGapWords("NOT_ENOUGH_READINGS")).toMatchObject({ label: TOO_FEW, short: "not enough readings" });
    expect(dayGapWords("NO_READINGS")).toMatchObject({ label: "No readings received for this day", short: "no readings" });
    expect(dayGapWords("NOT_ANALYSED")).toMatchObject({ label: "Not analysed yet", short: "not analysed yet" });
    expect(dayGapWords("SOMETHING_ELSE")).toBeNull();
  });

  it("counts a data-gap day as a gap day of the window", () => {
    expect(gapDays(dataGapBody([ROW], "READINGS_CONFLICT")).map((g) => g.day)).toEqual(["2026-10-26"]);
  });
});

describe("PB-4 Site Findings page with a conflicting-readings day", () => {
  it("is partial, names the day with the data fact, and never claims the window was checked", async () => {
    const card = await page(dataGapBody([ROW], "READINGS_CONFLICT"));
    expect(document.querySelector("[data-site-findings='partial']")).not.toBeNull();
    expect(card.querySelector(`[data-finding-index-row='${FID_A}']`)).not.toBeNull();
    expect(card.querySelector("[data-site-findings-data-gap='2026-10-26']")?.textContent).toContain(`${CONFLICT}.`);
    expect(document.body.textContent).toContain("Some days could not be analysed");
    const steps = Array.from(card.querySelectorAll<HTMLElement>("[data-step-strip] [data-step]"));
    expect(steps[1]?.textContent).toContain("Conflicting readings");
    expect(steps[1]?.textContent).not.toContain("Checked");
    for (const never of NEVER) expect(document.body.textContent).not.toMatch(never);
    for (const set of [undefined, "w1"] as const) {
      const { violations } = scanProductVocabulary(document.body, "pb4 partial", set ? { set } : {});
      expect(violations, describeViolations(violations)).toEqual([]);
    }
  });

  it("names a not-enough-readings day", async () => {
    const card = await page(dataGapBody([], "NOT_ENOUGH_READINGS"));
    expect(card.querySelector("[data-site-findings-data-gap='2026-10-26']")?.textContent).toContain(`${TOO_FEW}.`);
    for (const never of NEVER) expect(document.body.textContent).not.toMatch(never);
  });
});

describe("PB-4 Overview day list on a day that could not be analysed", () => {
  const links = { finding: (f: string, r: string) => `/f/${f}?r=${r}`, findingList: () => "/list" };
  const day = "2026-10-25";

  async function overview(reason: string) {
    const body = dataGapBody([], reason, {
      window: { from: `${day}T00:00:00Z`, to: "2026-10-26T00:00:00Z", bounds: "[from, to)", intersection: "x" },
      discovery: { days: [day], requested_days: [day], continuity_tolerance_minutes: 20, limit_days: 62 },
      watermarks: { matcher: indexBody().watermarks.matcher, days: [{ ...indexBody().watermarks.days[0], day }] },
      gaps: [{ day, state: "CURRENT", reason }],
      total_count: 0,
    });
    const { client } = indexClient(() => ({ status: "loaded", value: body }));
    render(
      <MemoryRouter>
        <OverviewFindingList summary={summary(day)} client={client} links={links} onReload={() => undefined} />
      </MemoryRouter>,
    );
    await settledScreen();
  }

  it("states the conflicting readings, never the proved-empty words", async () => {
    await overview("READINGS_CONFLICT");
    const list = document.querySelector("[data-overview-finding-list]");
    expect(list?.getAttribute("data-overview-finding-list")).toBe("data-gap");
    expect(list?.textContent).toContain(CONFLICT);
    expect(document.body.textContent).not.toContain("No Findings on the assessed days");
    for (const never of NEVER) expect(document.body.textContent).not.toMatch(never);
  });

  it("states not enough readings", async () => {
    await overview("NOT_ENOUGH_READINGS");
    expect(document.querySelector("[data-overview-finding-list]")?.textContent).toContain(TOO_FEW);
    for (const never of NEVER) expect(document.body.textContent).not.toMatch(never);
  });
});
