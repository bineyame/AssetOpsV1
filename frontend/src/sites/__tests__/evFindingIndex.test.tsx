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

function mount(type: string, list: EvRead<EvFindingsRead>, path = `/sites/${CODE}/findings?from=${FROM}&to=${TO}`) {
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
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evAssessment={client} siteFindingIndex={findingIndex as never} />
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
    expect(link.getAttribute("href")).toBe(`/sites/${CODE}/findings/${FID}?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`);
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
    expect(document.body.textContent).toContain("Showing the first 0 Findings; paging is not available on this page.");
  });

  it("refuses a window with the shared sentence and keeps the strip", async () => {
    mount("EV_CHARGING", refused(422, "EV_WINDOW_TOO_LONG"));
    await screen.findByText("The selected window is longer than 31 days.");
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
});
