/**
 * T028 phase 2: Performance > Dispatch, Finding detail and its record drawer,
 * the Findings rail root and Site > Findings (AC8, AC12, AC15, AC21), and the
 * AC18 rules for Performance subtabs and Finding types. Presentation
 * checkpoint 1 (D-2026-10-04-plain-language-analysis-views): plain default
 * views, the Finding Analysis tab, Dispatch Overview | Analysis, and the
 * card and index links into Analysis.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import {
  CANDIDATE_ASSESSMENT,
  CANDIDATE_ID,
  CANDIDATE_SUMMARY,
  NECESSARY_ID,
  analyticsClient,
  declaration,
} from "../../sites/__tests__/analyticsFixtures";
import {
  POPULATED_EVIDENCE,
  RECORD_DETAIL,
  evidenceClient,
} from "../../sites/__tests__/evidenceFixtures";
import {
  overviewClient,
  populatedOverview,
} from "../../sites/__tests__/overviewFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import {
  DEFAULT_CAPABILITY_ORDER,
  findingTypeLabel,
  orphanFindingTypeIds,
  performanceSubtabs,
  presentationProfileFor,
} from "../../sites/presentationProfile";
import type { SiteAnalyticsClient } from "../../sites/siteAnalyticsClient";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type { SiteOverviewReadModel } from "../../sites/siteOverviewClient";
import { settledScreen } from "../../test/settled";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function Location() {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output data-testid="location">{`${location.pathname}${location.search}`}</output>
      <button type="button" onClick={() => navigate(-1)}>
        Back
      </button>
    </>
  );
}

function renderAt(
  path: string,
  options: { analytics?: SiteAnalyticsClient; overview?: SiteOverviewReadModel } = {},
) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteOverview={overviewClient({
          status: "loaded",
          value: options.overview ?? populatedOverview(SITE_ID),
        })}
        siteAnalytics={options.analytics ?? analyticsClient(SITE_ID)}
      />
      <Location />
    </MemoryRouter>,
  );
}

function location(): string {
  return screen.getByTestId("location").textContent ?? "";
}

function railCurrent(): string | null {
  const rail = screen.getByRole("navigation", { name: "Operator routes" });
  return rail.querySelector('[aria-current="page"]')?.textContent ?? null;
}

function linkLabels(name: string): string[] {
  return within(screen.getByRole("navigation", { name }))
    .getAllByRole("link")
    .map((link) => link.textContent ?? "");
}

describe("Performance renders Dispatch as its only subtab (AC21)", () => {
  it("lists every assessed period in plain words; a Needed one has no Finding", async () => {
    renderAt(`/sites/${SITE_ID}/performance`);
    await settledScreen();
    expect(linkLabels("Performance sections")).toEqual(["Dispatch assessment"]);
    // Contextual views inside Dispatch, not capabilities (D-2026-10-04-plain-language-analysis-views).
    expect(linkLabels("Dispatch views")).toEqual(["Overview", "Analysis"]);
    const tabs = screen.getByRole("navigation", { name: "Site sections" });
    expect(within(tabs).getByRole("link", { name: "Performance" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    const candidate = document.querySelector(`[data-dispatch-interval="${CANDIDATE_ID}"]`);
    const necessary = document.querySelector(`[data-dispatch-interval="${NECESSARY_ID}"]`);
    expect(candidate).toHaveAttribute("data-claim-level", "CANDIDATE_AVOIDABLE");
    expect(necessary).toHaveAttribute("data-claim-level", "NECESSARY");
    expect(candidate).toHaveTextContent("Possibly avoidable");
    expect(necessary).toHaveTextContent("Needed");
    expect(
      within(candidate as HTMLElement).getByRole("link", { name: "Open Finding" }),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(within(necessary as HTMLElement).queryByRole("link", { name: "Open Finding" })).toBeNull();
    expect(necessary).toHaveTextContent("Battery charge was at or below its minimum reserve.");
    expect(necessary).toHaveTextContent("No Finding (needed)");
    expect(candidate).toHaveTextContent("3 h 45 min to 4 h 15 min");
    // The operational question leads; no method version or development words on the default view.
    const question = document.querySelector("[data-dispatch-question]") as HTMLElement;
    expect(question).toHaveTextContent("For each period the generator operated");
    const view = document.querySelector(".dispatch-view") as HTMLElement;
    expect(view.textContent).not.toMatch(/dispatch-2|\bruntime\b|\bran\b|binding|Candidate avoidable|Indeterminate/);
    expect(document.querySelector("details")).toBeNull();
    expect(candidate).toHaveTextContent("22 Sep 2026, 03:10 to 07:10 UTC");
  });

  it("each period row draws its own assessment's compact timeline (checkpoint 2a)", async () => {
    renderAt(`/sites/${SITE_ID}/performance/dispatch`);
    await settledScreen();
    const rows = Array.from(document.querySelectorAll("[data-dispatch-interval]"));
    expect(rows.length).toBeGreaterThan(1);
    for (const row of rows) {
      expect(row.querySelector('[data-graphic="assessed-period-timeline"]')).toHaveAttribute(
        "data-graphic-assessment",
        row.getAttribute("data-dispatch-interval"),
      );
    }
  });

  it("selecting a period shows its concise explanation and leads to its Analysis", async () => {
    renderAt(`/sites/${SITE_ID}/performance/dispatch`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "22 Sep 2026, 08:00 to 10:00 UTC" }));
    const selected = document.querySelector(`[data-dispatch-selected="${NECESSARY_ID}"]`) as HTMLElement;
    expect(selected).toHaveTextContent("The generator was needed during this period.");
    expect(selected.querySelector("[data-dispatch-meaning]")).toHaveTextContent("Needed means");
    expect(selected.querySelector('[data-next-step="CHECK_CONSTRAINT_IF_UNEXPECTED"]')).not.toBeNull();
    expect(location()).toBe(`/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}`);
    fireEvent.click(within(selected).getByRole("link", { name: "View the analysis of this period" }));
    await settledScreen();
    expect(location()).toBe(
      `/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}&view=analysis`,
    );
  });

  it("Analysis explains a Needed period that has no Finding, with its values and records", async () => {
    renderAt(`/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}&view=analysis`);
    await settledScreen();
    const views = screen.getByRole("navigation", { name: "Dispatch views" });
    expect(within(views).getByRole("link", { name: "Analysis" })).toHaveAttribute("aria-current", "page");
    const analysis = document.querySelector(`[data-analysis="${NECESSARY_ID}"]`) as HTMLElement;
    expect(analysis).toHaveTextContent("Reasons the generator was needed: Battery at minimum reserve.");
    const values = analysis.querySelector("[data-segment-values]") as HTMLElement;
    expect(values.querySelector('[data-value-row="load_kw"]')).toHaveTextContent("Site demand18 kW");
    expect(values.querySelector('[data-value-row="discharge_capability_kw"]')).toHaveTextContent(
      "Available battery output40 kW",
    );
    expect(values.querySelector('[data-value-row="reserve_pct"]')).toHaveTextContent(
      "Minimum battery reserve30 % (site setting)",
    );
    expect(analysis).toHaveTextContent("Assessment methoddispatch-2");
    expect(analysis).toHaveTextContent("dispatch-2");
    expect(analysis).toHaveTextContent("(an assessed period without a Finding)");
    // Record links open the Site Evidence inspector, not the Lab.
    expect(analysis.querySelector("[data-analysis-record]")).toHaveAttribute(
      "href",
      `/sites/${SITE_ID}/evidence?signal=GEN-1/output_kw&record=${RECORD_DETAIL.message_id}`,
    );
    // Overview keeps the selection; switching views keeps `interval`.
    fireEvent.click(within(views).getByRole("link", { name: "Overview" }));
    await settledScreen();
    expect(location()).toBe(`/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}`);
    expect(document.querySelector(`[data-dispatch-selected="${NECESSARY_ID}"]`)).not.toBeNull();
  });

  it("a selected period that is not among the current results is said so, not substituted", async () => {
    renderAt(`/sites/${SITE_ID}/performance/dispatch?interval=dispatch-gone&view=analysis`);
    await settledScreen();
    expect(document.querySelector("[data-dispatch-selected-missing]")).toHaveTextContent(
      "not among the current results",
    );
    expect(document.querySelector("[data-dispatch-analysis]")).toHaveAttribute(
      "data-dispatch-analysis",
      "none",
    );
    expect(document.querySelector("[data-analysis]")).toBeNull();
  });
});

describe("AC18 rules for Performance subtabs", () => {
  const profile = presentationProfileFor("MINIGRID");

  it("rule 1: a served id the profile does not know renders by its backend name, after known ids", () => {
    const subtabs = performanceSubtabs(profile, [
      { id: "renewable", display_name: "Renewable headroom" },
      { id: "dispatch", display_name: "Dispatch" },
    ]);
    expect(subtabs.map((s) => [s.id, s.label, s.known])).toEqual([
      ["dispatch", "Dispatch assessment", true],
      ["renewable", "Renewable headroom", false],
    ]);
    expect(subtabs[1].order).toBe(DEFAULT_CAPABILITY_ORDER);
  });

  it("rule 1 on screen: an unknown served analytic still gets a subtab", async () => {
    renderAt(`/sites/${SITE_ID}/performance`, {
      analytics: {
        ...analyticsClient(SITE_ID),
        getDeclaration: () =>
          Promise.resolve({
            status: "loaded",
            value: declaration(SITE_ID, [
              { analytic_id: "dispatch", display_name: "Dispatch" },
              { analytic_id: "renewable", display_name: "Renewable headroom" },
            ]),
          }),
      },
    });
    await settledScreen();
    expect(linkLabels("Performance sections")).toEqual([
      "Dispatch assessment",
      "Renewable headroom",
    ]);
  });

  it("rule 2: a profile id the backend does not serve renders nothing", async () => {
    renderAt(`/sites/${SITE_ID}/performance`, {
      analytics: {
        ...analyticsClient(SITE_ID),
        getDeclaration: () =>
          Promise.resolve({ status: "loaded", value: declaration(SITE_ID, []) }),
      },
    });
    await settledScreen();
    expect(screen.queryByRole("navigation", { name: "Performance sections" })).toBeNull();
    expect(screen.queryByText("Dispatch assessment")).toBeNull();
  });
});

describe("AC18 rules for Finding types", () => {
  const profile = presentationProfileFor("MINIGRID");

  it("rule 1: a known type takes the profile label; an unknown one renders by its backend name", () => {
    expect(findingTypeLabel(profile, "generator-dispatch-interval")).toEqual({
      id: "generator-dispatch-interval",
      label: "Generator dispatch interval",
      known: true,
    });
    expect(findingTypeLabel(profile, "fuel-residual", "Fuel residual")).toEqual({
      id: "fuel-residual",
      label: "Fuel residual",
      known: false,
    });
    expect(findingTypeLabel(null, "fuel-residual").label).toBe("fuel-residual");
  });

  it("rule 2: a profile Finding type no served analytic emits is flagged", () => {
    expect(orphanFindingTypeIds(profile, ["generator-dispatch-interval"])).toEqual([]);
    expect(orphanFindingTypeIds(profile, [])).toEqual(["generator-dispatch-interval"]);
  });
});

describe("Finding detail (AC8, AC12, AC15, AC21 as amended 2026-10-04)", () => {
  it("renders Overview | Analysis | Evidence | Alternatives with a plain default reading", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
    await settledScreen();
    expect(linkLabels("Finding sections")).toEqual(["Overview", "Analysis", "Evidence", "Alternatives"]);
    expect(screen.queryByText("Recommendation")).toBeNull();
    expect(screen.queryByText("History")).toBeNull();
    expect(railCurrent()).toBe("Findings");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Finding: Possibly avoidable");
    expect(
      screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent),
    ).toEqual([
      "What happened",
      "When, and for how long",
      "How confident, and what limits it",
      "Estimated fuel",
      "What to check next",
    ]);
    const page = document.querySelector(`[data-finding="${CANDIDATE_ID}"]`) as HTMLElement;
    // Context: site, equipment and the period, readable with its timezone (AC15).
    expect(page.querySelector("[data-finding-window]")).toHaveTextContent(
      "22 Sep 2026, 03:00 to 11:00 UTC",
    );
    expect(page).toHaveTextContent(HYBRID_MINI_GRID_SITE.display_name);
    expect(page.querySelector("[data-finding-type]")).toHaveTextContent("Generator dispatch interval");
    // One bounded conclusion and its main reason, then its meaning.
    expect(page.querySelector("[data-finding-claim]")).toHaveTextContent(
      "The generator may have operated longer than needed.",
    );
    expect(page.querySelector("[data-finding-meaning]")).toHaveTextContent("not proof of wasted fuel");
    // Observed, assessed and estimated are labelled apart; portions are separate values.
    expect(page).toHaveTextContent("Recorded: generator operating");
    expect(page).toHaveTextContent("Assessed: possibly avoidable3 h 30 min to 4 h");
    expect(page).toHaveTextContent("Assessed: cannot determine15 min");
    // Confidence in words with its principal limitation; limits and gaps stay on the default view.
    expect(page.querySelector("[data-finding-confidence]")).toHaveTextContent("Confidence: Medium.");
    expect(page).toHaveTextContent("15 min of the period cannot be determined, which lowers confidence.");
    expect(page.querySelector("[data-finding-gaps]")).toHaveTextContent(
      "Available battery output: no record received",
    );
    expect(page.querySelector("[data-claim-limits]")).toHaveTextContent(
      "not part of the possibly avoidable time",
    );
    expect(page.querySelector("[data-finding-open-alternatives]")).toHaveTextContent(
      "Unrecorded operator instruction, Battery output not reported",
    );
    // Estimated fuel: a range with its unit, called an estimate, not savings; no money.
    const fuel = page.querySelector('[data-finding-fuel="BOUNDED"]') as HTMLElement;
    expect(fuel).toHaveTextContent("Estimated fuel associated with possibly avoidable operation");
    expect(fuel).toHaveTextContent("Low 21.6 litres to high 29.3 litres");
    expect(page).toHaveTextContent("This is an estimate, not confirmed fuel savings");
    // Method detail moved to Analysis: no disclosures, no method version, no record identifiers.
    expect(page.querySelector("details")).toBeNull();
    expect(page.textContent ?? "").not.toMatch(/dispatch-2|abc123|digest/);
    expect(page.textContent ?? "").not.toMatch(
      /\bruntime\b|\brunning\b|\bran\b|binding|Candidate avoidable|Indeterminate|\bPV\b|\bSOC\b|\bload\b|segment/i,
    );
    // Next steps are the backend's, linked to what they concern, framed as checks.
    const confirm = page.querySelector('[data-next-step="CONFIRM_OPERATOR_INSTRUCTION"]') as HTMLElement;
    expect(within(confirm).getByRole("link")).toHaveAttribute(
      "href",
      `/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives#alternative-UNOBSERVED_OVERRIDE`,
    );
    expect(
      within(page.querySelector('[data-next-step="CHECK_BATTERY_CAPABILITY"]') as HTMLElement).getByRole("link"),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives#alternative-PCS_CAPABILITY_UNAVAILABLE`);
    expect(page.querySelector("[data-next-step-framing]")).toHaveTextContent(
      "not an instruction to stop the generator",
    );
    expect(within(page).getByRole("link", { name: "See how this conclusion was reached" })).toHaveAttribute(
      "href",
      `/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`,
    );
    expect(page.textContent ?? "").not.toMatch(/\$|USD|saving of/i);
  });

  it("Analysis holds the inputs, confidence, coverage, calculation and references", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`);
    await settledScreen();
    expect(
      within(screen.getByRole("navigation", { name: "Finding sections" })).getByRole("link", {
        name: "Analysis",
      }),
    ).toHaveAttribute("aria-current", "page");
    const analysis = document.querySelector(`[data-analysis="${CANDIDATE_ID}"]`) as HTMLElement;
    expect(analysis.querySelectorAll("[data-analysis-segment]")).toHaveLength(1);
    // Values used at each end; plain names; a missing value is never zero.
    // A zero is a value with a zero-width bar, not "Not reported".
    const solar = analysis.querySelector('[data-segment-values] [data-value-row="pv_available_kw"]') as HTMLElement;
    expect(solar).toHaveTextContent("Available solar power0 kW");
    expect(solar.querySelector("[data-bar-width]")).toHaveAttribute("data-bar-width", "0.000000");
    expect(analysis.querySelector("[data-analysis-confidence-explanation]")).toHaveTextContent(
      "15 min of the period cannot be determined",
    );
    expect(analysis.querySelector('[data-coverage-input="soc"]')).toHaveTextContent(
      "Battery charge15 of 16",
    );
    expect(analysis.querySelector('[data-analysis-fuel="BOUNDED"]')).toHaveTextContent(
      "Low 21.6 litres to high 29.3 litres",
    );
    expect(analysis).toHaveTextContent("0.3 L/kWh, ±10 %");
    // References: method version, assessment reference, verification reference, revisions.
    expect(analysis).toHaveTextContent("dispatch-2");
    expect(analysis.querySelector("[data-finding-assessment-id]")).toHaveTextContent(CANDIDATE_ID);
    expect(analysis).toHaveTextContent("verification reference abc123");
    // Links to Evidence and Alternatives instead of copying their lists.
    expect(within(analysis).getByRole("link", { name: "Other possible explanations (Alternatives)" })).toHaveAttribute(
      "href",
      `/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives`,
    );
    expect(analysis.querySelectorAll("[data-alternative]")).toHaveLength(0);
    expect(analysis.textContent ?? "").not.toMatch(/\bruntime\b|\brunning\b|binding|Indeterminate|segment|digest/i);
  });

  it("the Evidence tab's record drawer reuses the record inspector and keeps the root", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/evidence`);
    await settledScreen();
    const parts = document.querySelectorAll("[data-claim-segment]");
    expect(parts).toHaveLength(1);
    expect(parts[0]).toHaveTextContent("Possibly avoidable");
    fireEvent.click(screen.getAllByRole("button", { name: /GEN-1 \/ output_kw, 22 Sep 2026/ })[0]);
    await settledScreen();
    const drawer = screen.getByRole("complementary", { name: "Supporting record" });
    expect(drawer).toHaveAttribute("data-claim-drawer", RECORD_DETAIL.message_id);
    expect(drawer.querySelector(`[data-evidence-record-detail="${RECORD_DETAIL.message_id}"]`)).not.toBeNull();
    expect(drawer).toHaveTextContent("Assessment methoddispatch-2");
    expect(location().startsWith(`/findings/${SITE_ID}/${CANDIDATE_ID}/evidence?`)).toBe(true);
    expect(railCurrent()).toBe("Findings");
    fireEvent.click(within(drawer).getByRole("button", { name: "Close record" }));
    expect(screen.queryByRole("complementary", { name: "Supporting record" })).toBeNull();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}/evidence`);
  });

  it("the Alternatives tab lists other possible explanations with plain status and their records", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives`);
    await settledScreen();
    expect(screen.getByRole("heading", { name: "Other possible explanations" })).toBeInTheDocument();
    const pcs = document.querySelector('[data-alternative="PCS_CAPABILITY_UNAVAILABLE"]') as HTMLElement;
    expect(pcs).toHaveTextContent("Battery output not reported");
    expect(pcs.querySelector("[data-alternative-status]")).toHaveTextContent("Still possible");
    expect(pcs.querySelector("[data-alternative-gaps]")).toHaveTextContent("(15 min)");
    expect(within(pcs).getAllByRole("button", { name: /GEN-1 \/ output_kw/ })).toHaveLength(1);
    const override = document.querySelector('[data-alternative="UNOBSERVED_OVERRIDE"]') as HTMLElement;
    expect(override).toHaveTextContent("That does not prove none was given.");
    expect(within(override).getByText("No accepted record referenced.")).toBeInTheDocument();
  });

  it("direct links, Back and reload keep each tab; old tab links still open", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
    await settledScreen();
    fireEvent.click(
      within(screen.getByRole("navigation", { name: "Finding sections" })).getByRole("link", {
        name: "Analysis",
      }),
    );
    await settledScreen();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`);
    expect(document.querySelector(`[data-analysis="${CANDIDATE_ID}"]`)).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    await settledScreen();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(document.querySelector("[data-finding-claim]")).not.toBeNull();
    cleanup();
    // Reload is a fresh render at the address; an unknown tab falls back to Overview.
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`);
    await settledScreen();
    expect(document.querySelector(`[data-analysis="${CANDIDATE_ID}"]`)).not.toBeNull();
    cleanup();
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/recommendation`);
    await settledScreen();
    expect(document.querySelector("[data-finding-claim]")).not.toBeNull();
  });

  it("an unknown assessment id is said not to exist, with the current results offered", async () => {
    renderAt(`/findings/${SITE_ID}/dispatch-nope/analysis`);
    await settledScreen();
    expect(screen.getByRole("heading", { name: "No such assessment" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /See the current results/ })).toHaveAttribute(
      "href",
      `/sites/${SITE_ID}/performance/dispatch`,
    );
  });
});

describe("the Findings rail root and Site > Findings (AC21)", () => {
  it("the global index leads with the plain outcome; a row opens Overview, a link opens Analysis", async () => {
    renderAt("/findings");
    await settledScreen();
    expect(railCurrent()).toBe("Findings");
    const row = document.querySelector(`[data-finding-row="${CANDIDATE_ID}"]`) as HTMLElement;
    expect(row).toHaveTextContent(SITE_ID);
    expect(row).toHaveTextContent("Generator dispatch interval");
    expect(row).toHaveTextContent("The generator may have operated longer than needed.");
    expect(row).toHaveTextContent("Possibly avoidable");
    expect(row).toHaveTextContent("Medium 15 min of the period cannot be determined");
    expect(row).toHaveTextContent("22 Sep 2026, 03:10 to 07:10 UTC");
    expect(row.textContent ?? "").not.toMatch(/Candidate avoidable|runtime/);
    expect(screen.queryByRole("columnheader", { name: "Revision" })).toBeNull();
    expect(row.querySelector(`[data-finding-row-analysis="${CANDIDATE_ID}"]`)).toHaveAttribute(
      "href",
      `/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`,
    );
    fireEvent.click(row);
    await settledScreen();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
  });

  it("Site > Findings is a scoped, filterable index whose row click changes the root", async () => {
    renderAt(`/sites/${SITE_ID}/findings`);
    await settledScreen();
    expect(railCurrent()).toBe("Sites");
    const index = document.querySelector('[data-findings-index="site"]') as HTMLElement;
    expect(index.querySelectorAll("[data-finding-row]")).toHaveLength(1);
    expect(index.querySelector(".kpi-strip, [data-kpi]")).toBeNull();
    expect(within(index).getByRole("option", { name: "Cannot determine" })).toBeInTheDocument();
    fireEvent.change(index.querySelector("[data-findings-filter]") as HTMLSelectElement, {
      target: { value: "INDETERMINATE" },
    });
    expect(index.querySelectorAll("[data-finding-row]")).toHaveLength(0);
    expect(index).toHaveTextContent("No Finding matches this filter.");
    fireEvent.change(index.querySelector("[data-findings-filter]") as HTMLSelectElement, {
      target: { value: "" },
    });
    expect(
      index.querySelector(`[data-finding-row-analysis="${CANDIDATE_ID}"]`),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`);
    fireEvent.click(index.querySelector(`[data-finding-row="${CANDIDATE_ID}"]`) as HTMLElement);
    await settledScreen();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(railCurrent()).toBe("Findings");
  });
});

describe("the Overview links to the Finding instead of recomputing it (AC12)", () => {
  function overviewWith(lead: string, findings: unknown[], necessary = false): SiteOverviewReadModel {
    const overview = populatedOverview(SITE_ID);
    return {
      ...overview,
      findings,
      cards: overview.cards.map((card) =>
        card.domain_id === "Dispatch"
          ? {
              ...card,
              assessment: {
                status: necessary ? "NECESSARY" : "CANDIDATE_AVOIDABLE",
                label: necessary ? "Needed" : "Possibly avoidable",
                reason: necessary
                  ? "The generator was needed during this period. Battery charge was at or below its minimum reserve."
                  : "The generator may have operated longer than needed.",
                capability_id: "dispatch",
                capability_display_name: "Dispatch",
                assessment_ids: [lead],
                lead_assessment_id: lead,
              },
            }
          : card,
      ),
    };
  }

  it("the Dispatch card and the Findings panel open the same Finding; the card links its Analysis", async () => {
    renderAt(`/sites/${SITE_ID}`, { overview: overviewWith(CANDIDATE_ID, [CANDIDATE_SUMMARY]) });
    await settledScreen();
    expect(
      document.querySelector(`[data-overview-card-finding="${CANDIDATE_ID}"]`),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(
      document.querySelector(`[data-overview-card-analysis="${CANDIDATE_ID}"]`),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`);
    const panelLink = document.querySelector(`[data-overview-finding-link="${CANDIDATE_ID}"]`);
    expect(panelLink).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(panelLink).toHaveTextContent(
      "Possibly avoidable: The generator may have operated longer than needed.",
    );
  });

  it("the card's compact timeline draws the lead period it links to (checkpoint 2a)", async () => {
    const base = overviewWith(CANDIDATE_ID, [CANDIDATE_SUMMARY]);
    const a = CANDIDATE_ASSESSMENT;
    const overview: SiteOverviewReadModel = {
      ...base,
      cards: base.cards.map((card) =>
        card.domain_id === "Dispatch"
          ? {
              ...card,
              assessment: {
                ...card.assessment,
                lead_revision: 1,
                lead_timeline: {
                  assessed_window: a.assessed_window,
                  interval: a.interval,
                  segments: a.segments.map((s) => ({ ...s, outcome: "Possibly avoidable" })),
                  fuel: {
                    status: "BOUNDED",
                    low_litres: "21.6",
                    high_litres: "29.3",
                    label: "Estimated fuel associated with possibly avoidable operation",
                    text: "21.6 to 29.3 litres",
                    note: "This is an estimate, not confirmed fuel savings.",
                  },
                },
              },
            }
          : card,
      ),
    };
    renderAt(`/sites/${SITE_ID}`, { overview });
    await settledScreen();
    const slot = document.querySelector(`[data-overview-card-timeline="${CANDIDATE_ID}"]`) as HTMLElement;
    const timeline = slot.querySelector('[data-graphic="assessed-period-timeline"]') as HTMLElement;
    expect(timeline).toHaveAttribute("data-graphic-assessment", CANDIDATE_ID);
    expect(timeline).toHaveAttribute("data-compact", "true");
    expect(document.querySelector(`[data-overview-card-analysis="${CANDIDATE_ID}"]`)).not.toBeNull();
    expect(within(slot).getByRole("img").getAttribute("aria-label")).toContain(
      "03:10 UTC to 07:10 UTC, Possibly avoidable",
    );
    expect(slot.querySelector("[data-fuel-text]")).toHaveTextContent("Low 21.6 litres to high 29.3 litres");
  });

  it("a Needed lead with no Finding links to its period on Dispatch and to Dispatch's Analysis", async () => {
    renderAt(`/sites/${SITE_ID}`, { overview: overviewWith(NECESSARY_ID, [], true) });
    await settledScreen();
    expect(document.querySelector("[data-overview-card-finding]")).toBeNull();
    expect(
      document.querySelector(`[data-overview-card-dispatch="${NECESSARY_ID}"]`),
    ).toHaveAttribute("href", `/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}`);
    const analysis = document.querySelector(`[data-overview-card-analysis="${NECESSARY_ID}"]`) as HTMLElement;
    expect(analysis).toHaveAttribute(
      "href",
      `/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}&view=analysis`,
    );
    fireEvent.click(analysis);
    await settledScreen();
    expect(document.querySelector(`[data-analysis="${NECESSARY_ID}"]`)).not.toBeNull();
  });
});
