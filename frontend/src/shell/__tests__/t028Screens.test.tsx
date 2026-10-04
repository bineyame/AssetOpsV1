/**
 * T028 phase 2: Performance > Dispatch, Finding detail and its claim drawer,
 * the Findings rail root and Site > Findings (AC8, AC12, AC15, AC21), and the
 * AC18 rules for Performance subtabs and Finding types.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import {
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
  return (
    <output data-testid="location">{`${location.pathname}${location.search}`}</output>
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
  it("lists every assessed interval; a Necessary one raises no Finding", async () => {
    renderAt(`/sites/${SITE_ID}/performance`);
    await settledScreen();
    expect(linkLabels("Performance sections")).toEqual(["Dispatch assessment"]);
    const tabs = screen.getByRole("navigation", { name: "Site sections" });
    expect(within(tabs).getByRole("link", { name: "Performance" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    const candidate = document.querySelector(`[data-dispatch-interval="${CANDIDATE_ID}"]`);
    const necessary = document.querySelector(`[data-dispatch-interval="${NECESSARY_ID}"]`);
    expect(candidate).toHaveAttribute("data-claim-level", "CANDIDATE_AVOIDABLE");
    expect(necessary).toHaveAttribute("data-claim-level", "NECESSARY");
    expect(
      within(candidate as HTMLElement).getByRole("link", { name: "Open Finding" }),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(within(necessary as HTMLElement).queryByRole("link", { name: "Open Finding" })).toBeNull();
    expect(necessary).toHaveTextContent("Battery at reserve");
    expect(necessary).toHaveTextContent("No Finding (Necessary)");
    // The operational question leads; method and version sit behind a disclosure.
    const question = document.querySelector("[data-dispatch-question]") as HTMLElement;
    expect(question).toHaveTextContent("For each period the generator ran");
    expect(question.textContent).not.toMatch(/dispatch-2/);
    const method = document.querySelector('[data-disclosure="dispatch-method-details"]') as HTMLDetailsElement;
    expect(method.open).toBe(false);
    expect(method).toHaveTextContent("model dispatch-2");
    expect(
      question.compareDocumentPosition(method) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(candidate).toHaveTextContent("22 Sep 2026, 03:10 to 07:10 UTC");
  });

  it("selecting an interval shows its constraint and the inputs at its own time", async () => {
    renderAt(`/sites/${SITE_ID}/performance/dispatch`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "22 Sep 2026, 08:00 to 10:00 UTC" }));
    const selected = document.querySelector(`[data-dispatch-selected="${NECESSARY_ID}"]`) as HTMLElement;
    expect(selected).toHaveTextContent("Battery at reserve");
    expect(selected).toHaveTextContent("reserve 30 % (policy)");
    expect(selected).toHaveTextContent("discharge capability 40 kW");
    expect(selected.querySelector("[data-dispatch-meaning]")).toHaveTextContent("Needed runtime");
    expect(selected.querySelector('[data-next-step="CHECK_CONSTRAINT_IF_UNEXPECTED"]')).not.toBeNull();
    expect(location()).toBe(`/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}`);
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

describe("Finding detail (AC8, AC12, AC15, AC21)", () => {
  it("renders Overview | Evidence | Alternatives and the recommendation's hierarchy", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
    await settledScreen();
    expect(linkLabels("Finding sections")).toEqual(["Overview", "Evidence", "Alternatives"]);
    expect(screen.queryByText("Recommendation")).toBeNull();
    expect(screen.queryByText("History")).toBeNull();
    expect(railCurrent()).toBe("Findings");
    // Practitioner-first hierarchy: the accepted six-part order, in plain headings
    // (D-2026-10-04-practitioner-first-finding-presentation).
    expect(
      screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent),
    ).toEqual([
      "1. What the evidence suggests",
      "2. What was observed, and what is inferred",
      "3. How confident, and how much was measured",
      "4. What limits this conclusion",
      "5. Estimated fuel associated with this runtime",
      "6. What to check next",
    ]);
    const page = document.querySelector(`[data-finding="${CANDIDATE_ID}"]`) as HTMLElement;
    // Context: site, generator and the period, readable with its timezone (AC15).
    expect(page.querySelector("[data-finding-window]")).toHaveTextContent(
      "22 Sep 2026, 03:00 to 11:00 UTC",
    );
    expect(page.querySelector("[data-finding-type]")).toHaveTextContent("Generator dispatch interval");
    // The classification is explained, and its limit stays with it.
    expect(page.querySelector("[data-finding-meaning]")).toHaveTextContent(
      "Potentially avoidable runtime",
    );
    expect(page.querySelector("[data-finding-meaning]")).toHaveTextContent("not proven waste");
    // Provenance is behind a closed disclosure, not in the lead.
    const details = page.querySelector('[data-disclosure="finding-assessment-details"]') as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.querySelector("[data-finding-assessment-id]")).toHaveTextContent(CANDIDATE_ID);
    expect(details).toHaveTextContent("basis digest abc123");
    expect(details).toHaveTextContent("dispatch-2");
    expect(details.querySelector("[data-finding-revisions]")).not.toBeNull();
    // The disclosure is usable: its summary opens it.
    fireEvent.click(within(details).getByText("Assessment details"));
    expect(details.open).toBe(true);
    // Confidence and its basis stay visible, apart from coverage.
    expect(page.querySelector("[data-finding-confidence]")).toHaveTextContent("Medium");
    expect(page.querySelector("[data-confidence-basis]")).toHaveTextContent(
      "An Indeterminate portion lies inside the interval.",
    );
    expect(page.querySelector("[data-finding-coverage-summary]")).toHaveTextContent(
      "Not usable in every segment: Battery SOC (15 of 16 segments).",
    );
    // The full per-input coverage is one click away.
    const coverage = page.querySelector('[data-disclosure="finding-coverage-details"]') as HTMLDetailsElement;
    expect(coverage.open).toBe(false);
    expect(coverage.querySelector("[data-finding-coverage]")).toHaveTextContent(
      "15 of 16 segments had every required input.",
    );
    // Rule 3: the gap shown is the backend's, not the profile's; it stays visible.
    const gaps = page.querySelector("[data-finding-gaps]") as HTMLElement;
    expect(gaps).toHaveTextContent("Battery discharge capability: no record 05:00 to 05:15");
    expect(gaps.closest("details")).toBeNull();
    // Bounded fuel, modelled, with its duration and uncertainty visible; inputs behind a disclosure; no money.
    const fuel = page.querySelector('[data-finding-fuel="BOUNDED"]') as HTMLElement;
    expect(fuel).toHaveTextContent("21.6 to 29.3 L, modelled");
    expect(fuel.closest("details")).toBeNull();
    expect(fuel.parentElement).toHaveTextContent("for 3.5 to 4 h of candidate runtime, with ±10 %");
    const fuelDetails = page.querySelector('[data-disclosure="finding-fuel-details"]') as HTMLDetailsElement;
    expect(fuelDetails.open).toBe(false);
    expect(fuelDetails).toHaveTextContent("0.3 L/kWh ±10 %");
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
    expect(page.textContent ?? "").not.toMatch(/\$|USD|saving of/i);
  });

  it("the Evidence tab's claim drawer reuses the record inspector and keeps the root", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/evidence`);
    await settledScreen();
    const claims = document.querySelectorAll("[data-claim-segment]");
    expect(claims).toHaveLength(1);
    fireEvent.click(screen.getAllByRole("button", { name: /GEN-1 \/ output_kw at/ })[0]);
    await settledScreen();
    const drawer = screen.getByRole("complementary", { name: "Claim evidence" });
    expect(drawer).toHaveAttribute("data-claim-drawer", RECORD_DETAIL.message_id);
    expect(drawer.querySelector(`[data-evidence-record-detail="${RECORD_DETAIL.message_id}"]`)).not.toBeNull();
    expect(drawer).toHaveTextContent("dispatch-2");
    expect(location().startsWith(`/findings/${SITE_ID}/${CANDIDATE_ID}/evidence?`)).toBe(true);
    expect(railCurrent()).toBe("Findings");
    fireEvent.click(within(drawer).getByRole("button", { name: "Close evidence" }));
    expect(screen.queryByRole("complementary", { name: "Claim evidence" })).toBeNull();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}/evidence`);
  });

  it("the Alternatives tab lists each explanation with its status and challengeable evidence", async () => {
    renderAt(`/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives`);
    await settledScreen();
    const pcs = document.querySelector('[data-alternative="PCS_CAPABILITY_UNAVAILABLE"]') as HTMLElement;
    expect(pcs.querySelector("[data-alternative-status]")).toHaveTextContent("Not excluded");
    expect(pcs.querySelector("[data-alternative-gaps]")).toHaveTextContent("(15 min)");
    expect(within(pcs).getAllByRole("button", { name: /GEN-1 \/ output_kw/ })).toHaveLength(1);
    const override = document.querySelector('[data-alternative="UNOBSERVED_OVERRIDE"]') as HTMLElement;
    expect(override).toHaveTextContent("not proof none existed");
    expect(within(override).getByText("No accepted record referenced.")).toBeInTheDocument();
  });

  it("an unknown assessment id is said not to exist", async () => {
    renderAt(`/findings/${SITE_ID}/dispatch-nope`);
    await settledScreen();
    expect(screen.getByRole("heading", { name: "No such assessment" })).toBeInTheDocument();
  });
});

describe("the Findings rail root and Site > Findings (AC21)", () => {
  it("the global index lists the same Finding with its site; a row click opens it", async () => {
    renderAt("/findings");
    await settledScreen();
    expect(railCurrent()).toBe("Findings");
    const row = document.querySelector(`[data-finding-row="${CANDIDATE_ID}"]`) as HTMLElement;
    expect(row).toHaveTextContent(SITE_ID);
    expect(row).toHaveTextContent("Generator dispatch interval");
    // The index leads with the reason and period; revision lives on the Finding.
    expect(row).toHaveTextContent(CANDIDATE_SUMMARY.summary);
    expect(row).toHaveTextContent("22 Sep 2026, 03:10 to 07:10 UTC");
    expect(screen.queryByRole("columnheader", { name: "Revision" })).toBeNull();
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
    fireEvent.change(index.querySelector("[data-findings-filter]") as HTMLSelectElement, {
      target: { value: "INDETERMINATE" },
    });
    expect(index.querySelectorAll("[data-finding-row]")).toHaveLength(0);
    expect(index).toHaveTextContent("No Finding matches this filter.");
    fireEvent.change(index.querySelector("[data-findings-filter]") as HTMLSelectElement, {
      target: { value: "" },
    });
    fireEvent.click(index.querySelector(`[data-finding-row="${CANDIDATE_ID}"]`) as HTMLElement);
    await settledScreen();
    expect(location()).toBe(`/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(railCurrent()).toBe("Findings");
  });
});

describe("the Overview links to the Finding instead of recomputing it (AC12)", () => {
  function overviewWith(lead: string, findings: unknown[]): SiteOverviewReadModel {
    const overview = populatedOverview(SITE_ID);
    return {
      ...overview,
      findings,
      cards: overview.cards.map((card) =>
        card.domain_id === "Dispatch"
          ? {
              ...card,
              assessment: {
                status: "CANDIDATE_AVOIDABLE",
                label: "Candidate avoidable",
                reason: CANDIDATE_SUMMARY.summary,
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

  it("the Dispatch card and the Findings panel open the same Finding", async () => {
    renderAt(`/sites/${SITE_ID}`, { overview: overviewWith(CANDIDATE_ID, [CANDIDATE_SUMMARY]) });
    await settledScreen();
    expect(
      document.querySelector(`[data-overview-card-finding="${CANDIDATE_ID}"]`),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}`);
    expect(
      document.querySelector(`[data-overview-finding-link="${CANDIDATE_ID}"]`),
    ).toHaveAttribute("href", `/findings/${SITE_ID}/${CANDIDATE_ID}`);
  });

  it("a lead with no Finding links to its interval on Performance > Dispatch", async () => {
    renderAt(`/sites/${SITE_ID}`, { overview: overviewWith(NECESSARY_ID, []) });
    await settledScreen();
    expect(document.querySelector("[data-overview-card-finding]")).toBeNull();
    expect(
      document.querySelector(`[data-overview-card-dispatch="${NECESSARY_ID}"]`),
    ).toHaveAttribute("href", `/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}`);
  });
});
