/**
 * T028 phase 3: Site > Evidence part B (AC20) - the capability table above
 * T027 source health - and the AC18 rules for Evidence capability rows, with
 * rule 3 (a gap only from backend state) tested here. Presentation checkpoint
 * 1 (D-2026-10-04-plain-language-analysis-views): local Overview | Analysis
 * views, plain readiness words, site-wide scope labelled apart from the
 * selected window.
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

async function renderEvidence(analytics: SiteAnalyticsClient, url: string = EVIDENCE_URL) {
  render(
    <MemoryRouter initialEntries={[url]}>
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

function linkLabels(name: string): string[] {
  return within(screen.getByRole("navigation", { name }))
    .getAllByRole("link")
    .map((link) => link.textContent ?? "");
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
  it("Overview: one dispatch row above the source summary, in plain words, scope labelled", async () => {
    await renderEvidence(served([DISPATCH_LIMITED]));

    expect(linkLabels("Evidence views")).toEqual(["Overview", "Analysis"]);
    const capability = screen.getByRole("heading", { name: "What can we assess from this site's records?" });
    const sources = screen.getByRole("heading", { name: "Where the records come from" });
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
    expect(text).toContain("Possibly avoidable operation can be identified only where the required records exist");
    const missing = row.querySelector('[data-capability-missing="COVERAGE_GAP"]') as HTMLElement;
    expect(missing).toHaveAttribute("data-capability-limits", "yes");
    expect(missing).toHaveTextContent("Available battery output: no usable record for 5 of 13 assessed parts");
    // Optional absence is stated as not received, never as proof (AC7).
    expect(row.querySelector("[data-capability-not-observed]")).toHaveTextContent(
      "Not received: Operator instruction. Absence is not proof that none existed.",
    );
    // Site-wide scope, labelled apart from the selected window.
    expect(document.querySelector("[data-capability-question]")).toHaveTextContent(
      "Scope: whole site. Based on all of this site's accepted records, not only the selected window.",
    );
    expect(document.querySelector("[data-evidence-window]")).toHaveTextContent("Selected window:");
    expect(row.querySelector("[data-capability-meaning]")).toHaveTextContent(
      "Assessments are possible but limited",
    );
    expect(document.querySelector("[data-evidence-source-summary]")).toHaveTextContent(
      "Demonstration data",
    );
    // Method, versions and the detailed tables belong to Analysis.
    expect(document.querySelector("details")).toBeNull();
    expect(document.querySelector("[data-capability-versions]")).toBeNull();
    expect(screen.queryByRole("heading", { name: "Source status" })).toBeNull();
    expect(text).not.toMatch(/dispatch-2|readiness-3|segment|Indeterminate|Candidate avoidable/);
  });

  it("Analysis: method, versions, required records and gap references; window kept", async () => {
    await renderEvidence(served([DISPATCH_LIMITED]), `${EVIDENCE_URL}?view=analysis&from=2026-09-22T00:00:00Z`);
    const views = screen.getByRole("navigation", { name: "Evidence views" });
    expect(within(views).getByRole("link", { name: "Analysis" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("heading", { name: "How readiness is scored" })).toBeInTheDocument();
    expect(document.querySelector("[data-capability-statement]")).toHaveTextContent("How this is scored:");
    expect(document.querySelector("[data-capability-versions]")).toHaveTextContent(
      "Dispatch assessment: assessment method dispatch-2, readiness scoring readiness-3",
    );
    expect(document.querySelector("[data-capability-gap-detail]")).toHaveTextContent(
      "Assessed periods: dispatch-cand0001.",
    );
    expect(screen.getByRole("heading", { name: "Source status" })).toBeInTheDocument();
    // Switching back to Overview keeps the window parameter.
    expect(within(views).getByRole("link", { name: "Overview" })).toHaveAttribute(
      "href",
      `${EVIDENCE_URL}?from=2026-09-22T00%3A00%3A00Z`,
    );
  });

  it("a Full row says no gap limited an assessed period", async () => {
    await renderEvidence(
      served([
        {
          ...DISPATCH_LIMITED,
          readiness: {
            ...LIMITED_READINESS,
            level: "FULL",
            label: "Full",
            missing_evidence: [],
            gaps: [],
            optional_not_observed: [],
          },
        },
      ]),
    );
    const [row] = rows();
    expect(row).toHaveAttribute("data-capability-readiness", "FULL");
    expect(within(row).getByText("Full")).toBeInTheDocument();
    expect(row.querySelector('[data-capability-missing="none"]')).toHaveTextContent(
      "Every required input has usable records; no gap limited an assessed period.",
    );
    expect(row.querySelector("[data-capability-assessed]")).toHaveTextContent("1 assessed period.");
    expect(row.querySelector("[data-capability-not-observed]")).toBeNull();
  });

  it("a generator-operation gap is a limiting row, never a Full 'no gaps' claim (R5)", async () => {
    // The row as the backend scores the AC1 gap fixture under readiness-3.
    await renderEvidence(
      served([
        {
          ...DISPATCH_LIMITED,
          readiness: {
            ...LIMITED_READINESS,
            missing_evidence: [
              {
                kind: "COVERAGE_GAP",
                role: "Generator state",
                device_id: null,
                signal_id: null,
                statement:
                  "Generator state: not observed for 60 min in 1 assessed interval (1 span(s)); that time is Indeterminate.",
                limits_claim: true,
                assessment_ids: ["dispatch-a"],
              },
            ],
            gaps: [
              "Generator operation: not recorded for 60 min in 1 assessed period; that time cannot be determined.",
            ],
          },
        },
      ]),
    );
    const [row] = rows();
    expect(row).toHaveAttribute("data-capability-readiness", "LIMITED");
    const gap = row.querySelector('[data-capability-missing="COVERAGE_GAP"]') as HTMLElement;
    expect(gap).toHaveAttribute("data-capability-limits", "yes");
    expect(gap).toHaveTextContent("Generator operation: not recorded for 60 min");
    expect(row.querySelector('[data-capability-missing="none"]')).toBeNull();
    expect(spacedText(row)).not.toContain("no gap limited");
  });

  it("zero assessed periods say coverage is not yet checked, never bare completeness", async () => {
    await renderEvidence(
      served([
        {
          ...DISPATCH_LIMITED,
          readiness: {
            ...LIMITED_READINESS,
            level: "FULL",
            label: "Full",
            missing_evidence: [],
            gaps: [],
            optional_not_observed: [],
            assessed_intervals: 0,
          },
        },
      ]),
    );
    const [row] = rows();
    expect(row.querySelector("[data-capability-assessed]")).toHaveTextContent(
      "No period has been assessed yet: records exist, but whether they cover each period has not been checked.",
    );
    expect(row.querySelector('[data-capability-missing="none"]')).toHaveTextContent(
      "Every required input has usable records.",
    );
    expect(row.textContent).not.toContain("no gap limited");
  });

  it("nothing appears when the site has no declared assessment", async () => {
    await renderEvidence(served([]));
    expect(screen.queryByRole("heading", { name: "What can we assess from this site's records?" })).toBeNull();
    expect(rows()).toHaveLength(0);
    expect(spacedText(screen.getByRole("main"))).not.toMatch(/readiness|claim ceiling/i);
    expect(screen.getByRole("heading", { name: "Where the records come from" })).toBeInTheDocument();
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
      "No readiness was given for this assessment, so none is shown.",
    );
    expect(row.querySelector("[data-capability-missing]")).toBeNull();
    expect(spacedText(row)).not.toMatch(/Full|Limited|Battery/);
  });

  it("rule 3: the missing information listed is exactly the backend's, in its plain words", async () => {
    await renderEvidence(served([DISPATCH_LIMITED]));
    const listed = Array.from(
      rows()[0].querySelectorAll("[data-capability-missing]"),
      (item) => item.textContent,
    );
    expect(listed).toEqual(LIMITED_READINESS.gaps);
    expect(LIMITED_READINESS.gaps).toHaveLength(LIMITED_READINESS.missing_evidence.length);
  });
});
