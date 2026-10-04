/**
 * T028 phase 3: Site > Evidence part B (AC20) - the capability table above
 * T027 source health - and the AC18 rules for Evidence capability rows, with
 * rule 3 (a gap only from backend state) tested here.
 */
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import {
  LIMITED_READINESS,
  analyticsClient,
  declaration,
} from "../../sites/__tests__/analyticsFixtures";
import {
  POPULATED_EVIDENCE,
  evidenceClient,
} from "../../sites/__tests__/evidenceFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { presentationProfileFor } from "../../sites/presentationProfile";
import type {
  CapabilityReadiness,
  SiteAnalytics,
  SiteAnalyticsClient,
} from "../../sites/siteAnalyticsClient";
import type { EvidenceRead } from "../../sites/siteEvidenceClient";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const EVIDENCE_URL = `/sites/${SITE_ID}/evidence`;
const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function withDeclaration(read: EvidenceRead<SiteAnalytics>): SiteAnalyticsClient {
  return { ...analyticsClient(SITE_ID), getDeclaration: () => Promise.resolve(read) };
}

function served(
  analytics: { analytic_id: string; display_name: string; readiness?: CapabilityReadiness }[],
): SiteAnalyticsClient {
  return withDeclaration({ status: "loaded", value: declaration(SITE_ID, analytics) });
}

async function renderEvidence(analytics: SiteAnalyticsClient) {
  render(
    <MemoryRouter initialEntries={[EVIDENCE_URL]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteAnalytics={analytics}
      />
    </MemoryRouter>,
  );
  await settledScreen();
}

function rows(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>("[data-capability]"));
}

const DISPATCH_LIMITED = {
  analytic_id: "dispatch",
  display_name: "Dispatch",
  readiness: LIMITED_READINESS,
};

describe("Site > Evidence capability table (AC20)", () => {
  it("shows one dispatch row above source health with readiness, ceiling and missing evidence", async () => {
    await renderEvidence(served([DISPATCH_LIMITED]));

    const capability = screen.getByRole("heading", { name: "Capability readiness" });
    const sources = screen.getByRole("heading", { name: "Source health" });
    expect(
      capability.compareDocumentPosition(sources) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    const [row] = rows();
    expect(rows()).toHaveLength(1);
    expect(row).toHaveAttribute("data-capability", "dispatch");
    expect(row).toHaveAttribute("data-capability-readiness", "LIMITED");
    const text = spacedText(row);
    expect(text).toContain("Dispatch assessment");
    expect(text).toContain("Limited");
    expect(row.querySelector("[data-capability-ceiling]")).toHaveAttribute(
      "data-capability-ceiling",
      "CANDIDATE_AVOIDABLE",
    );
    expect(text).toContain("Candidate avoidable only for portions whose required inputs are evidenced");
    const missing = row.querySelector('[data-capability-missing="COVERAGE_GAP"]') as HTMLElement;
    expect(missing).toHaveAttribute("data-capability-limits", "yes");
    expect(missing).toHaveTextContent("Battery discharge capability");
    // Override absence is stated as not observed, never as proof (AC7).
    expect(row.querySelector("[data-capability-not-observed]")).toHaveTextContent(
      "Not observed: Operator override. Absence is not proof that none existed.",
    );
  });

  it("a Full row says no claim-limiting gap was identified in the assessed intervals", async () => {
    await renderEvidence(
      served([
        {
          ...DISPATCH_LIMITED,
          readiness: {
            ...LIMITED_READINESS,
            level: "FULL",
            label: "Full",
            missing_evidence: [],
            optional_not_observed: [],
          },
        },
      ]),
    );
    const [row] = rows();
    expect(row).toHaveAttribute("data-capability-readiness", "FULL");
    expect(within(row).getByText("Full")).toBeInTheDocument();
    expect(row.querySelector('[data-capability-missing="none"]')).toHaveTextContent(
      "All required signals have usable records; no claim-limiting gaps identified in assessed intervals.",
    );
    expect(row.querySelector("[data-capability-assessed]")).toHaveTextContent("1 interval assessed.");
    expect(row.querySelector("[data-capability-not-observed]")).toBeNull();
  });

  it("zero assessed intervals say signal availability only, never bare completeness", async () => {
    await renderEvidence(
      served([
        {
          ...DISPATCH_LIMITED,
          readiness: {
            ...LIMITED_READINESS,
            level: "FULL",
            label: "Full",
            missing_evidence: [],
            optional_not_observed: [],
            assessed_intervals: 0,
          },
        },
      ]),
    );
    const [row] = rows();
    expect(row.querySelector("[data-capability-assessed]")).toHaveTextContent(
      "No intervals assessed; signal availability only.",
    );
    expect(row.querySelector('[data-capability-missing="none"]')).toHaveTextContent(
      "no intervals assessed, so coverage is not yet checked.",
    );
    expect(row.textContent).not.toContain("no claim-limiting gaps identified");
  });

  it("nothing appears when the site has no declared analytic", async () => {
    await renderEvidence(served([]));
    expect(screen.queryByRole("heading", { name: "Capability readiness" })).toBeNull();
    expect(rows()).toHaveLength(0);
    expect(spacedText(screen.getByRole("main"))).not.toMatch(/readiness|claim ceiling/i);
    expect(screen.getByRole("heading", { name: "Source health" })).toBeInTheDocument();
  });

  it("an unreadable declaration is said so, with no row", async () => {
    await renderEvidence(
      withDeclaration({ status: "unavailable", message: "The analytics store is down." }),
    );
    expect(document.querySelector('[data-capability-state="unavailable"]')).toHaveTextContent(
      "The analytics store is down.",
    );
    expect(rows()).toHaveLength(0);
  });
});

describe("AC18 rules for Evidence capability rows", () => {
  it("rule 1: a served analytic the profile does not know renders by its backend name, after known rows", async () => {
    await renderEvidence(
      served([
        { analytic_id: "renewable", display_name: "Renewable headroom", readiness: LIMITED_READINESS },
        DISPATCH_LIMITED,
      ]),
    );
    expect(rows().map((row) => row.getAttribute("data-capability"))).toEqual([
      "dispatch",
      "renewable",
    ]);
    const unknown = rows()[1];
    expect(unknown).toHaveAttribute("data-capability-known", "no");
    expect(within(unknown).getByRole("rowheader")).toHaveTextContent("Renewable headroom");
  });

  it("rule 2: the profile's dispatch entry renders nothing when the backend does not serve it", async () => {
    expect(presentationProfileFor("MINIGRID")?.capabilities?.map((c) => c.id)).toContain(
      "dispatch",
    );
    await renderEvidence(
      served([
        { analytic_id: "renewable", display_name: "Renewable headroom", readiness: LIMITED_READINESS },
      ]),
    );
    expect(rows().map((row) => row.getAttribute("data-capability"))).toEqual(["renewable"]);
    expect(screen.queryByText(/Dispatch assessment/)).toBeNull();
  });

  it("rule 3: gaps come only from backend state, never from the profile", async () => {
    // The profile carries presentation keys only: no readiness, gap or ceiling.
    for (const entry of presentationProfileFor("MINIGRID")?.capabilities ?? []) {
      expect(Object.keys(entry).sort()).toEqual(["emphasis", "group", "id", "label", "order"]);
    }
    // A served analytic the backend did not score shows no readiness and no gap.
    await renderEvidence(served([{ analytic_id: "dispatch", display_name: "Dispatch" }]));
    const [row] = rows();
    expect(row).toHaveAttribute("data-capability-readiness", "NOT_SCORED");
    expect(row.querySelector("[data-capability-not-scored]")).toHaveTextContent(
      "The backend served no readiness for this analytic, so none is shown.",
    );
    expect(row.querySelector("[data-capability-missing]")).toBeNull();
    expect(spacedText(row)).not.toMatch(/Full|Limited|Battery/);
  });

  it("rule 3: the missing evidence listed is exactly the backend's, in its words", async () => {
    await renderEvidence(served([DISPATCH_LIMITED]));
    const listed = Array.from(
      rows()[0].querySelectorAll("[data-capability-missing]"),
      (item) => item.textContent,
    );
    expect(listed).toEqual(LIMITED_READINESS.missing_evidence.map((item) => item.statement));
  });
});
