/**
 * post-W6 W2-cold unit 4 (R253, rulings Q1-Q3): a COLDCHAIN Site's Findings page renders the cold index from the
 * selected `ColdFindingsRead`, never the mini index or its "not released" reason; a mini Site keeps the mini index.
 */
import { cleanup, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { ColdAssessmentClient, ColdEnvelope, ColdFindingItem, ColdFindingsRead, ColdRead } from "../coldAssessmentClient";
import type { FindingIndexClient } from "../findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

afterEach(cleanup);

const FROM = "2026-10-06T19:00:00Z";
const TO = "2026-10-06T20:05:00Z";
const KNOWN = "2026-10-06T20:06:00Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const Q = `?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;

const envelope = (selected = true): ColdEnvelope =>
  ({
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN },
    currentness: { state: "CURRENT", watermark: { decided_at: KNOWN, assessment_revision_ids: selected ? [id(50)] : [] }, latest_relevant_evidence_at: null, pending_since: null },
    source_provenance: null,
    selected_source_provenance: null,
    pending_source_provenance: null,
    limitations: [],
  }) as unknown as ColdEnvelope;

const item = (n: number, kind: string, over: Partial<ColdFindingItem> = {}): ColdFindingItem => ({
  finding_id: id(n),
  kind,
  subject_asset_id: null,
  revision_id: id(n + 100),
  lifecycle: "SUPPORTED",
  claim_level: "BOUNDED",
  title: kind === "EXCURSION" ? "Chamber above policy" : "Automatic start failed",
  claim: kind === "EXCURSION" ? { direction: "HIGH", duration_bounds: { low: "25", high: "35" }, peak_observed: "8.2" } : { result: "OBSERVED_FAILURE" },
  episode_bounds: { start: { earliest: "2026-10-06T19:10:00Z", latest: "2026-10-06T19:15:00Z" }, end: { earliest: null, latest: null } },
  limitations: [],
  assessment_revision_id: id(50),
  evidence_ids: [],
  as_of: KNOWN,
  limitation: null,
  ...over,
});

const ok = <T,>(value: T): ColdRead<T> => ({ status: "loaded", value });
const STOCKED: ColdFindingsRead = {
  ...envelope(),
  items: [item(901, "EXCURSION"), item(902, "START_RESPONSE"), item(903, "OTHER_KIND", { lifecycle: "RESOLVED" })],
  next_cursor: null,
};

const site = (type: string) =>
  ({
    site_id: "COLD-001",
    display_name: "Kobo vaccine cold store",
    site_type: type,
    timezone: "Africa/Addis_Ababa",
    source: { mode: "SIMULATED" },
    location: { country: "Ethiopia", locality: "Kobo" },
    lifecycle_status: "PLANNED",
    origin: "USER",
    template: null,
    configuration_store: "POSTGRES",
  }) as unknown as SiteDetailReadModel;
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };

function renderIndex(read: ColdRead<ColdFindingsRead>, path = `/sites/COLD-001/findings${Q}`, type = "COLDCHAIN") {
  const cold = {
    getTemperature: vi.fn(),
    getBackupChain: vi.fn(),
    listFindings: vi.fn(() => Promise.resolve(read)),
    getFinding: vi.fn(),
  } as unknown as ColdAssessmentClient;
  const findingIndex = { getFindingIndex: vi.fn(() => new Promise(() => undefined)) } as unknown as FindingIndexClient;
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: site(type) }) };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
        coldAssessment={cold}
        siteFindingIndex={findingIndex}
      />
    </MemoryRouter>,
  );
  return { cold, findingIndex };
}

const panel = () => panelTitled("Findings at this site");
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ");
const strip = () => document.querySelector('[aria-label="Findings state"]') as HTMLElement;

describe("W2-cold unit 4: cold Site Findings index", () => {
  it("r253_selected_rows_columns_and_windowed_links", async () => {
    const { cold, findingIndex } = renderIndex(ok(STOCKED));
    await settledScreen();
    expect(cold.listFindings).toHaveBeenCalledWith("COLD-001", { from: FROM, to: TO, known_at: KNOWN });
    expect(findingIndex.getFindingIndex).not.toHaveBeenCalled();
    expect(document.querySelector("[data-site-findings-lenses]")).not.toBeNull();
    expect(text(strip())).toContain("Scoped to Kobo vaccine cold store · 2 open");
    expect(text(strip())).toContain("Cold-chain Findings are not in the global Findings list");
    expect(text(strip())).toContain("Manage in Findings");
    expect(strip().querySelector("a")).toBeNull();
    expect(Array.from(panel().querySelectorAll("thead th")).map((h) => h.textContent)).toEqual([
      "Finding",
      "Domain",
      "Priority",
      "Confidence",
      "State",
      "Main consequence",
      "Lens",
    ]);
    const rows = Array.from(panel().querySelectorAll("[data-cold-finding-row]"));
    expect(rows).toHaveLength(3);
    const cells = (r: Element) => Array.from(r.querySelectorAll("td")).map((c) => text(c));
    expect(cells(rows[0]).slice(1)).toEqual(["Temperature", "Not assessed", "Bounded", expect.any(String), "25–35 min above the limit · peak 8.2 °C", "Not assessed"]);
    expect(cells(rows[1])[5]).toBe("Start failed");
    expect(cells(rows[2])[1]).not.toMatch(/Temperature|Backup/);
    expect(cells(rows[2])[5]).toBe("Not in this list");
    expect(rows[0].querySelector("[data-cold-finding-link]")?.getAttribute("href")).toBe(`/sites/COLD-001/findings/${id(901)}${Q}`);
    expect(rows[0].querySelector('[data-cold-domain-link="temperature"]')?.getAttribute("href")).toBe(`/sites/COLD-001/performance/temperature${Q}`);
    expect(rows[1].querySelector('[data-cold-domain-link="backup"]')?.getAttribute("href")).toBe(`/sites/COLD-001/performance/backup${Q}`);
    expect(rows[0].querySelector("small")?.textContent).toMatch(/^Began /);
    expect(text(document.querySelector("main"))).not.toMatch(/not released/i);
    expect(document.querySelector("[data-cold-findings-cursor]")).toBeNull();
    expectV69Panels("sitefindings");
    // Ruling 3 (B14-10): the main tabs keep the selected window.
    const tabs = Array.from(document.querySelectorAll("nav.site-tabs:not(.site-subtabs) a.site-tabs__link"));
    expect(tabs.length).toBeGreaterThan(4);
    for (const a of tabs) expect(a.getAttribute("href")?.endsWith(Q)).toBe(true);
    const scan = scanProductVocabulary(document.querySelector("main") as HTMLElement, "sitefindings", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(5);
    expect(describeViolations(scan.violations)).toBe("");
  });

  it("r253_empty_selected_window", async () => {
    renderIndex(ok({ ...envelope(), items: [], next_cursor: null }));
    await settledScreen();
    expect(text(panel())).toContain("No Findings at this site in the selected window.");
    expect(text(strip())).toContain("0 open");
  });

  it("r253_no_selected_assessment", async () => {
    renderIndex(ok({ ...envelope(false), items: [], next_cursor: null }));
    await settledScreen();
    expect(text(panel())).toContain("No cold assessment for this window");
    expect(text(panel())).not.toContain("No Findings at this site");
  });

  it("r253_cursor_note", async () => {
    renderIndex(ok({ ...STOCKED, next_cursor: "c1" }));
    await settledScreen();
    expect(document.querySelector("[data-cold-findings-cursor]")?.textContent).toBe("Showing the first 3 Findings; paging is not available on this page.");
  });

  it.each([
    [{ status: "refused", httpStatus: 422, code: "COLD_WINDOW_INVALID", message: "x" }, "Window cannot be read", "The selected window needs both a start and an end, with the start before the end.", false],
    [{ status: "refused", httpStatus: 403, code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: "x" }, "Source permission refused", "may not be shown to you", true],
    [{ status: "refused", httpStatus: 503, code: "COLD_READ_UNAVAILABLE", message: "x" }, "Assessment unavailable", "could not be read", true],
  ] as const)("r253_refusal %#", async (read, title, sentence, windowLine) => {
    renderIndex(read as unknown as ColdRead<ColdFindingsRead>);
    await settledScreen();
    expect(text(strip())).toContain(title);
    if (title !== "Window cannot be read") expect(text(strip())).not.toContain("Window cannot be read");
    expect(text(panel())).toContain(sentence);
    expect(document.querySelector("[data-cold-date-bar]") !== null).toBe(windowLine);
    expect(panel().querySelector('[data-disclosure="cold-refusal-references"]')).not.toBeNull();
    expect(panel().querySelector("[data-cold-finding-row]")).toBeNull();
  });

  it("r253_mini_site_keeps_the_mini_index", async () => {
    const { cold, findingIndex } = renderIndex(ok(STOCKED), `/sites/COLD-001/findings${Q}`, "MINIGRID");
    await waitFor(() => expect(findingIndex.getFindingIndex).toHaveBeenCalled(), { timeout: 5000 });
    expect(cold.listFindings).not.toHaveBeenCalled();
    // A mini Site's main tabs carry no cold window query.
    for (const a of Array.from(document.querySelectorAll("nav.site-tabs:not(.site-subtabs) a.site-tabs__link"))) expect(a.getAttribute("href")).not.toContain("known_at");
    expect(document.querySelector("[data-cold-finding-row]")).toBeNull();
  });
});
