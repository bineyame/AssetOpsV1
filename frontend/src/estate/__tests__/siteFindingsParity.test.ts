/**
 * IA-P P5, D-IAP.39 layer 2 (the client layer of the Findings alias parity proof), on D-IAP.42 and D-IAP.43.
 *
 * The bodies are the server layer's whole-month reads (`backend/tests/test_iap_site_findings_parity_postgres.py`,
 * written once under `IAP_WRITE_FIXTURES=1`, normalised: uuid tokens, times re-based to 2026-10-01), never by hand.
 * Per aliased vertical (COLD, EV): the Site body is parsed by the Site page's own client (`listFindings`), the estate
 * body runs through the Findings list path (`loadAllPages` -> `findingItems` -> `homeListModel(findingsDef(), items,
 * {show: "all"}, "site:{code}")`), and the shown row keys must hold every Site id. MINI has no alias and no body
 * (D-IAP.42: MD-IAP-15). Plant `parity` (the scope keyed on `site_id`) fails both cases.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { createColdAssessmentClient } from "../../sites/coldAssessmentClient";
import { createEvAssessmentClient } from "../../sites/evAssessmentClient";
import { homeListModel } from "../../ui/homeListModel";
import type { EstateFindingsBody } from "../estateClient";
import { loadAllPages } from "../estateReadCache";
import { findingItems, findingsDef } from "../homeLists";
import COLD_ESTATE from "./fixtures/iap/parity-cold-estate.json?raw";
import COLD_SITE from "./fixtures/iap/parity-cold-site.json?raw";
import EV_ESTATE from "./fixtures/iap/parity-ev-estate.json?raw";
import EV_SITE from "./fixtures/iap/parity-ev-site.json?raw";

afterEach(() => {
  vi.unstubAllGlobals();
});

function serve(text: string) {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(text, { status: 200, headers: { "content-type": "application/json" } }))));
}

async function siteIds(vertical: "cold" | "ev", code: string, text: string): Promise<string[]> {
  serve(text);
  const window = { from: null, to: null, known_at: null } as never;
  const client = vertical === "cold" ? createColdAssessmentClient() : createEvAssessmentClient();
  const read = await client.listFindings(code, window);
  expect(read.status).toBe("loaded");
  const items = (read as { value: { items: { finding_id: string }[] } }).value.items;
  return items.map((i) => i.finding_id);
}

async function shownKeys(code: string, text: string): Promise<string[]> {
  const body = JSON.parse(text) as EstateFindingsBody;
  // The pinned body is page one of a one-page read (the server layer reads every page; `next_cursor` is null).
  expect(body.next_cursor).toBeNull();
  const all = await loadAllPages<EstateFindingsBody, EstateFindingsBody["rows"][number]>(() => Promise.resolve({ status: "loaded", value: body } as never));
  expect(all.status).toBe("loaded");
  const { first, rows } = (all as { value: { first: EstateFindingsBody; rows: EstateFindingsBody["rows"] } }).value;
  const items = findingItems(rows, first.coverage?.sites ?? [], []);
  const def = findingsDef();
  return homeListModel(def, items, { show: "all" }, `site:${code}`).shown.map((i) => def.rowKey(i));
}

describe("IA-P P5: a Site's Findings are on the Findings list at scope site:{code} (D-IAP.39 layer 2)", () => {
  it.each([
    ["cold", "COLD-LAB-001", COLD_SITE, COLD_ESTATE],
    ["ev", "EV-LAB-001", EV_SITE, EV_ESTATE],
  ] as const)("%s: the shown row keys hold every Site id (plant parity)", async (vertical, code, site, estate) => {
    const ids = await siteIds(vertical, code, site);
    expect(ids.length).toBeGreaterThan(0); // a vacuous pass fails
    const shown = await shownKeys(code, estate);
    expect(shown.length).toBeGreaterThan(0);
    for (const id of ids) expect(shown).toContain(id);
  });
});
