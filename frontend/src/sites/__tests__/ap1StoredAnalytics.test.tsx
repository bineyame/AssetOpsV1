/**
 * AP-1 (D-SR.75, D-SR.77): a stored Site's `/analytics` now answers 200.
 * - Site > Evidence renders the capability table from it (existing component, stored fixture: no record count).
 * - Performance branches on the Site's store, not on the 409: a POSTGRES Site takes the durable Dispatch reads
 *   and never the file-era declaration path, even though `/analytics` would answer 200.
 */
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";
import { SitePerformance } from "../SitePerformance";
import type { PerformanceDispatchClient } from "../performanceDispatchClient";
import type { SiteAnalytics, SiteAnalyticsClient } from "../siteAnalyticsClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import { LIMITED_READINESS, analyticsClient, declaration } from "./analyticsFixtures";
import { POPULATED_EVIDENCE, evidenceClient } from "./evidenceFixtures";
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

describe("AP-1 stored-Site analytics readiness", () => {
  it("Site > Evidence renders the stored 200 as the capability table, with presence and no count", async () => {
    const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
    const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: STORED_SITE }) };
    const analytics = client();
    render(
      <MemoryRouter initialEntries={[`/sites/${SITE_ID}/evidence?view=analysis`]}>
        <App
          flags={featureFlagsWith(false)}
          siteDirectory={directory}
          siteDetail={detail}
          siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
          siteAnalytics={analytics}
        />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(analytics.getDeclaration).toHaveBeenCalled();
    expect(document.body.textContent).not.toContain("is not available yet for this site");
    const required = document.querySelector('[data-requirement-available="true"]');
    expect(required).toHaveTextContent(
      "Available solar power: Usable records received, latest 2026-10-08T08:30:00Z (reference pv-inverter-controller / available-power)",
    );
    expect(required?.textContent).not.toMatch(/null usable record/);
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
