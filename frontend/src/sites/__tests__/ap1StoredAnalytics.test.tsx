/**
 * AP-1 (D-SR.75, D-SR.77): a stored Site's `/analytics` now answers 200.
 * - D-SR.79: a stored Site's Evidence page is the ledger shape; a 200 with rows fills the Overview's "What we can
 *   conclude now" with the capability table and the badge "Evidence · Overview"; 409, 422 and `[]` keep today's line.
 * - Performance branches on the Site's store, not on the 409: a POSTGRES Site takes the durable Dispatch reads
 *   and never the file-era declaration path, even though `/analytics` would answer 200.
 */
import { render, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";
import { CAPABILITY_HEADING_ID, CapabilityReadinessAnalysis } from "../CapabilityReadiness";
import type { EvidenceRead } from "../evidenceRead";
import { SitePerformance } from "../SitePerformance";
import type { PerformanceDispatchClient } from "../performanceDispatchClient";
import type { SiteAnalytics, SiteAnalyticsClient } from "../siteAnalyticsClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import { LIMITED_READINESS, analyticsClient, declaration } from "./analyticsFixtures";
import { LEDGER_EVIDENCE, ledgerClient } from "./ledgerEvidenceFixtures";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const STORED_SITE = { ...HYBRID_MINI_GRID_SITE, configuration_store: "POSTGRES" };

function storedDeclaration(): SiteAnalytics {
  const base = declaration(SITE_ID, [{ analytic_id: "dispatch", display_name: "Dispatch", readiness: LIMITED_READINESS }]);
  return {
    ...base,
    analytics: base.analytics.map((row) => ({
      ...row,
      model_version: "dispatch-2",
      required_evidence: [
        {
          device_id: "pv-inverter-controller",
          signal_id: "available-power",
          family: "MEASUREMENT",
          role: "PV capability",
          plain_role: "Available solar power",
          available: true,
          usable_records: null,
          last_source_time: "2026-10-08T08:30:00Z",
        },
      ],
    })),
  };
}

function client(): SiteAnalyticsClient {
  return { ...analyticsClient(SITE_ID), getDeclaration: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: storedDeclaration() })) };
}

/** D-SR.79: the real stored branch, the ledger evidence shape through `SiteEvidence` (Overview). */
function renderLedger(read: EvidenceRead<SiteAnalytics>) {
  const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: STORED_SITE }) };
  const analytics = { ...analyticsClient(SITE_ID), getDeclaration: vi.fn(() => Promise.resolve(read)) };
  render(
    <MemoryRouter initialEntries={[`/sites/${SITE_ID}/evidence`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail}
        siteEvidence={ledgerClient({ status: "loaded", value: LEDGER_EVIDENCE })} siteAnalytics={analytics} />
    </MemoryRouter>,
  );
  return analytics;
}

function conclude(): HTMLElement {
  return document.getElementById("site-evidence-state-heading")?.closest("section") as HTMLElement;
}

function badge(): string | null | undefined {
  return document.querySelector('[data-evidence-statusbar="overview"] .badge')?.textContent;
}

function expectTodayLine() {
  expect(document.querySelector('[data-evidence-store="POSTGRES"]')).not.toBeNull();
  expect(conclude().querySelector("[data-not-available='capability-conclusions']")).toHaveTextContent(
    "Not available yet: capability-by-capability conclusions",
  );
  expect(conclude().querySelector(`#${CAPABILITY_HEADING_ID}`)).toBeNull();
  expect(badge()).toBe("No capability conclusion yet");
}

describe("AP-1 stored-Site analytics readiness", () => {
  it("a stored 200 fills 'What we can conclude now' on the ledger Overview, with the Evidence badge", async () => {
    const analytics = renderLedger({ status: "loaded", value: storedDeclaration() });
    await settledScreen();
    expect(analytics.getDeclaration).toHaveBeenCalled();
    expect(document.querySelector('[data-evidence-store="POSTGRES"]')).not.toBeNull();
    const panel = conclude();
    expect(panel.querySelector(`#${CAPABILITY_HEADING_ID}`)).not.toBeNull();
    expect(within(panel).getByRole("table")).toHaveTextContent("Dispatch");
    expect(panel.querySelector("[data-not-available='capability-conclusions']")).toBeNull();
    expect(badge()).toBe("Evidence · Overview");
  });

  it("a 409 (gate closed) keeps today's line and badge", async () => {
    renderLedger({ status: "unavailable", message: "Site KOBO-001 moved", transition: "AWAITING_EVIDENCE_MIGRATION" });
    await settledScreen();
    expectTodayLine();
    expect(document.body.textContent).not.toContain("is not available yet for this site");
  });

  it("a 422 keeps today's line and shows no revision UUID or model id", async () => {
    const uuid = "9b0c1d2e-0000-4000-8000-0000000000aa";
    renderLedger({ status: "unavailable", message: `Readiness maps dispatch-3.2 results only; revision ${uuid} is dispatch-3.1.` });
    await settledScreen();
    expectTodayLine();
    expect(document.body.textContent).not.toContain(uuid);
    expect(document.body.textContent).not.toContain("dispatch-3.1");
  });

  it("a cold or EV Site's analytics: [] keeps today's line and badge", async () => {
    renderLedger({ status: "loaded", value: declaration(SITE_ID, []) });
    await settledScreen();
    expectTodayLine();
  });

  it("the Analysis requirement list shows presence, no count, and the binding ids", () => {
    render(<MemoryRouter><CapabilityReadinessAnalysis declaration={{ status: "loaded", value: storedDeclaration() }} profile={null} /></MemoryRouter>);
    const required = document.querySelector('[data-requirement-available="true"]');
    expect(required).toHaveTextContent(
      "Available solar power: Usable records received, latest 2026-10-08T08:30:00Z (reference pv-inverter-controller / available-power)",
    );
    expect(required?.textContent).not.toMatch(/null usable record/);
  });

  it("an unbound role shows (Not bound) and no file-era id; a policy row shows no reference (D-SR.78 Q2, D-SR.79 N1)", () => {
    const base = storedDeclaration();
    const row = base.analytics[0];
    const stored: SiteAnalytics = {
      ...base,
      analytics: [
        {
          ...row,
          required_evidence: [
            { ...row.required_evidence[0], role: "Load", plain_role: "Site load", device_id: null, signal_id: null, unbound: true, available: false, last_source_time: null },
            { ...row.required_evidence[0], role: "Reserve policy", plain_role: "Reserve policy", device_id: null, signal_id: null, unbound: false, available: true, last_source_time: null },
          ],
        },
      ],
    };
    render(<MemoryRouter><CapabilityReadinessAnalysis declaration={{ status: "loaded", value: stored }} profile={null} /></MemoryRouter>);
    const items = Array.from(document.querySelectorAll("[data-capability-required] li"));
    const load = items.find((li) => li.textContent?.startsWith("Site load"));
    const policy = items.find((li) => li.textContent?.startsWith("Reserve policy"));
    expect(load?.textContent).toMatch(/\(Not bound\)$/);
    expect(load?.textContent).not.toContain("reference");
    expect(policy?.textContent).not.toContain("reference");
    expect(document.body.textContent).not.toContain("pv-inverter-controller");
  });

  it("Performance takes the durable reads for a POSTGRES Site without asking /analytics", async () => {
    const analytics = client();
    const performance: PerformanceDispatchClient = {
      getCutover: vi.fn(() => new Promise<never>(() => undefined)),
      getWindow: vi.fn(() => new Promise<never>(() => undefined)),
      getRevision: vi.fn(() => new Promise<never>(() => undefined)),
    };
    render(
      <MemoryRouter>
        <SitePerformance
          siteId={SITE_ID}
          client={analytics}
          profile={null}
          capabilityId={undefined}
          subtabHref={(id) => `/x/${id}`}
          findingHref={(id) => `/f/${id}`}
          findingAnalysisHref={(id) => `/f/${id}?view=analysis`}
          recordHref={() => "/r"}
          performance={performance}
          configurationStore="POSTGRES"
        />
      </MemoryRouter>,
    );
    expect(analytics.getDeclaration).not.toHaveBeenCalled();
    expect(performance.getCutover).toHaveBeenCalledWith(SITE_ID);
  });

  it("an unstated store keeps reading the declaration (older backend)", async () => {
    const analytics = client();
    render(
      <MemoryRouter>
        <SitePerformance
          siteId={SITE_ID}
          client={analytics}
          profile={null}
          capabilityId={undefined}
          subtabHref={(id) => `/x/${id}`}
          findingHref={(id) => `/f/${id}`}
          findingAnalysisHref={(id) => `/f/${id}?view=analysis`}
          recordHref={() => "/r"}
        />
      </MemoryRouter>,
    );
    expect(analytics.getDeclaration).toHaveBeenCalledWith(SITE_ID);
    await settledScreen();
  });
});
