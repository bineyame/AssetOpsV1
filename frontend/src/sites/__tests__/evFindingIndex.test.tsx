import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvAssessmentClient, EvFindingsRead, EvRead } from "../evAssessmentClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { F130 } from "./outcomeFixtures";
import { boardBody, fakeOutcomeBoard, planWarning } from "../../test/outcomeBoardFixture";
import type { OutcomeBoardClient } from "../outcomeBoardClient";

/* post-W6 W2-EV U4 (B9-10/R253): an EV Site's Findings page lists the selected EV Findings read. */

const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:00:00.000000Z";
const FID = "00000000-0000-4000-8000-000000000900";
const BLOCK = { classification: "REGISTERED_SIMULATION", source_ids: [], evidence_ids: [], basis_sha256: null };
const LINKS = { self: null, evidence: null, analysis: null, finding: null, financials: null };

const findings = (items: EvFindingsRead["items"], next: string | null = null): EvFindingsRead => ({
  site_id: "s",
  window: { from: FROM, to: TO, known_at: TO },
  currentness: { state: "CURRENT", as_of: TO, limitation: null },
  source_provenance: BLOCK,
  limitations: [],
  items,
  next_cursor: next,
});
const item = { finding_id: FID, revision_id: "r1", revision_no: 1, basis_sha256: "b", session_id: null, title: "Charger fault stopped a session", claim_level: "OBSERVED", lifecycle: "SUPPORTED", as_of: TO, links: LINKS };
const ok = (v: EvFindingsRead): EvRead<EvFindingsRead> => ({ status: "loaded", value: v });
const refused = (httpStatus: number, code: string): EvRead<never> => ({ status: "refused", httpStatus, code, message: "x" });

const site = (type: string) =>
  ({
    site_id: CODE, display_name: "EV lab depot", site_type: type, location: { country: "Ethiopia", locality: "Addis" },
    timezone: "Africa/Addis_Ababa", lifecycle_status: "PLANNED", origin: "USER", source: { mode: "SIMULATED" }, template: null, configuration_store: "POSTGRES",
  }) as unknown as SiteDetailReadModel;

function mount(
  type: string,
  list: EvRead<EvFindingsRead>,
  path = `/sites/${CODE}/findings?from=${FROM}&to=${TO}`,
  outcomeBoard?: OutcomeBoardClient,
) {
  const s = site(type);
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: s }) };
  const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [s] }) };
  const client = {
    listSessions: vi.fn(), getSession: vi.fn(), getFinding: vi.fn(),
    listFindings: vi.fn(() => Promise.resolve(list)),
  } as unknown as EvAssessmentClient;
  const findingIndex = { getFindingIndex: vi.fn(() => Promise.resolve({ status: "not_imported" })) };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evAssessment={client} siteFindingIndex={findingIndex as never} {...(outcomeBoard === undefined ? {} : { outcomeBoard })} />
    </MemoryRouter>,
  );
  return { client, findingIndex };
}

afterEach(cleanup);

describe("EV Site Findings", () => {
  it("lists the selected EV Findings, not the mini index", async () => {
    const { client, findingIndex } = mount("EV_CHARGING", ok(findings([item])));
    await settledScreen();
    const link = await screen.findByRole("link", { name: item.title });
    expect(link.getAttribute("href")).toBe(`/sites/${CODE}/findings/${FID}?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(TO)}`);
    const sessions = [...document.querySelectorAll("a")].find((a) => a.textContent === "Sessions" && a.closest("[data-ev-finding-row]"));
    expect(sessions?.getAttribute("href")).toBe(`/sites/${CODE}/performance/sessions?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(TO)}`);
    expect(document.querySelector("[data-ev-findings-index='loaded']")).not.toBeNull();
    expect(document.body.textContent).toContain("Scoped to EV lab depot · 1 open");
    expect(document.body.textContent).toContain("EV charging Findings are not in the global Findings list");
    expect(document.querySelectorAll("[data-ev-finding-row] td")).toHaveLength(7);
    // Q26 cap fallback: the mini index row class gives the title a readable column; the strip parts are separated.
    expect(document.querySelector("[data-ev-finding-row]")?.classList.contains("finding-index-row")).toBe(true);
    expect(document.querySelector("[data-ev-findings-global-note]")?.textContent).toBe(" · EV charging Findings are not in the global Findings list");
    expect(client.listFindings).toHaveBeenCalledWith(CODE, expect.objectContaining({ from: FROM, to: TO }));
    expect(findingIndex.getFindingIndex).not.toHaveBeenCalled();
    const tab = [...document.querySelectorAll("a")].find((a) => a.textContent === "Overview");
    expect(tab?.getAttribute("href")).toContain(`/sites/${CODE}/ev`);
  });

  it("states empty and cursor", async () => {
    mount("EV_CHARGING", ok(findings([], "next")));
    await screen.findByText("No Findings at this site in the selected window.");
    expect(document.querySelector("[data-ev-findings-cursor]")).toBeNull();
    expect(document.body.textContent).not.toContain("Showing the first 0");
  });

  it("keeps paging honesty when items exist and a cursor is set", async () => {
    mount("EV_CHARGING", ok(findings([item], "next")));
    await screen.findByText("Showing the first 1 Findings; paging is not available on this page.");
  });

  it("Q23: a no-window address opens rows with the read's own window and cutoff (inventory-check)", async () => {
    mount("EV_CHARGING", ok(findings([item])), `/sites/${CODE}/findings`);
    const link = await screen.findByRole("link", { name: item.title });
    expect(link.getAttribute("href")).toBe(`/sites/${CODE}/findings/${FID}?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(TO)}`);
  });

  it("refuses a window with the shared sentence and keeps the strip", async () => {
    mount("EV_CHARGING", refused(422, "EV_WINDOW_TOO_LONG"));
    await screen.findByText("The selected window is longer than 31 days.");
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(document.body.textContent).toContain("Window cannot be read");
    expect(document.querySelector("[data-ev-findings-index='refused']")).not.toBeNull();
  });

  it("does not call a 503 a window error", async () => {
    mount("EV_CHARGING", refused(503, "X"));
    await screen.findByText("EV evidence is temporarily unavailable. Retry.");
    expect(document.body.textContent).not.toContain("Window cannot be read");
  });

  it("leaves a mini Site on the mini index", async () => {
    const { client, findingIndex } = mount("MINIGRID", ok(findings([item])));
    await waitFor(() => expect(findingIndex.getFindingIndex).toHaveBeenCalled());
    await settledScreen();
    expect(client.listFindings).not.toHaveBeenCalled();
    expect(document.querySelector("[data-ev-findings-index]")).toBeNull();
  });

  it("OUT-A A4: the interruption row shows two solid pills, Protect then Grow, and no outlined pill", async () => {
    mount("EV_CHARGING", ok(findings([{ ...item, categories: F130 }])));
    await settledScreen();
    await screen.findByRole("link", { name: item.title });
    const tagsOf = (row: Element | null) =>
    Array.from(row?.querySelectorAll(".oc-affects") ?? []).map((el) => [el.textContent, el.classList.contains("quiet")]);
    expect(tagsOf(document.querySelector("[data-ev-finding-row] td:first-child"))).toEqual([
      ["Affects Protect asset and capital", false],
      ["Affects Grow revenue", false],
    ]);
    const scan = scanProductVocabulary(document.querySelector("[data-outcome-tags]") as HTMLElement, "sitefindings", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(0);
    expect(describeViolations(scan.violations)).toBe("");
  });
});

describe("OUT-C U5 EV Site Findings early warnings", () => {
  it("lists the board warnings under the list for the page window, with the Site name first (H1-1)", async () => {
    const warning = planWarning({ key: "CONNECTOR_OUT_OF_SERVICE:c1", badge: "RISK", title: "Connector c1 out of service", seen: "44 min out and 16 min unknown on 6 Oct", site_code: "EV-LAB-001", site_name: "Depot Charging" });
    const board = fakeOutcomeBoard({ status: "loaded", value: boardBody({ warnings: [warning] }) });
    mount("EV_CHARGING", ok(findings([item])), undefined, board.client);
    await settledScreen();
    await waitFor(() => expect(document.querySelector("[data-early-warnings]")).not.toBeNull());
    expect(board.calls).toEqual([{ siteCode: CODE, query: { from: FROM, to: TO, known_at: null } }]);
    const list = document.querySelector("[data-early-warnings]") as HTMLElement;
    expect(list.closest("[data-ev-findings-index='loaded']")).not.toBeNull();
    expect(list.querySelector(".oc-kind")?.className).toBe("oc-kind risk");
    expect(list.querySelector("small")?.textContent).toBe("Depot · Protect asset and capital · 44 min out and 16 min unknown on 6 Oct");
    expect(describeViolations(scanProductVocabulary(list, "site-findings", { set: "w1" }).violations)).toBe("");
  });

  it("shows no list when the board has no warnings", async () => {
    const board = fakeOutcomeBoard({ status: "loaded", value: boardBody() });
    mount("EV_CHARGING", ok(findings([item])), undefined, board.client);
    await settledScreen();
    await waitFor(() => expect(board.calls).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(document.querySelector("[data-ev-findings-index='loaded']")).not.toBeNull();
    expect(document.querySelector("[data-early-warnings]")).toBeNull();
  });
});
