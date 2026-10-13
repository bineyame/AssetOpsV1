/**
 * The T028 vocabulary guard over its five surfaces (D-2026-10-04-plain-language-analysis-views,
 * section 4): Finding detail, Performance > Dispatch, the Site Overview
 * Dispatch card, the global and Site Findings indexes and Site > Evidence, in
 * their Overview, Analysis, Evidence, Alternatives and drawer states and their
 * empty, not-found and unavailable states. The product journey runs with the
 * Simulator Lab disabled.
 *
 * Every screen's text comes through the same client seam the backend serves,
 * so text the backend delivers is scanned exactly as a person would read it.
 * The live populated journey is scanned again in a browser by
 * `tools/layout-evidence.mjs` ("T028 product vocabulary"), against the
 * running backend's own text.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import {
  CANDIDATE_ASSESSMENT,
  CANDIDATE_ID,
  CANDIDATE_SUMMARY,
  EMPTY_ANALYTICS_CLIENT,
  NECESSARY_ID,
  NONE_READINESS,
  analyticsClient,
  declaration,
} from "../../sites/__tests__/analyticsFixtures";
import {
  EMPTY_EVIDENCE_CLIENT,
  POPULATED_EVIDENCE,
  RECORD_DETAIL,
  evidenceClient,
} from "../../sites/__tests__/evidenceFixtures";
import {
  emptyOverview,
  overviewClient,
  populatedOverview,
} from "../../sites/__tests__/overviewFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import type { SiteAnalyticsClient } from "../../sites/siteAnalyticsClient";
import type { SiteEvidenceClient } from "../../sites/siteEvidenceClient";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type { SiteOverviewClient } from "../../sites/siteOverviewClient";
import {
  VOCABULARY_VERSION,
  describeViolations,
  forbiddenPhrases,
  scanProductVocabulary,
  type VocabularyViolation,
} from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};
const UNAVAILABLE = { status: "unavailable", message: null } as const;

interface Clients {
  analytics?: SiteAnalyticsClient;
  evidence?: SiteEvidenceClient;
  overview?: SiteOverviewClient;
  /** The Simulator Lab gate; the product journey is checked with it off. */
  lab?: boolean;
}

function renderAt(path: string, clients: Clients = {}) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(clients.lab ?? false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={clients.evidence ?? evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteOverview={clients.overview ?? overviewClient({ status: "loaded", value: populatedOverview(SITE_ID) })}
        siteAnalytics={clients.analytics ?? analyticsClient(SITE_ID)}
      />
    </MemoryRouter>,
  );
}

/** Render one state, settle it, optionally act, and scan the whole document. */
async function scanState(
  page: string,
  path: string,
  clients: Clients = {},
  act?: () => Promise<void>,
): Promise<{ violations: VocabularyViolation[]; scanned: number }> {
  renderAt(path, clients);
  await settledScreen();
  if (act !== undefined) {
    await act();
    await settledScreen();
  }
  const result = scanProductVocabulary(document.body, `${page} (${path})`);
  cleanup();
  return result;
}

const unavailableAnalytics: SiteAnalyticsClient = {
  getDeclaration: () => Promise.resolve(UNAVAILABLE),
  getDispatch: () => Promise.resolve(UNAVAILABLE),
  getSiteFindings: () => Promise.resolve(UNAVAILABLE),
  getAssessment: () => Promise.resolve(UNAVAILABLE),
  getFindings: () => Promise.resolve(UNAVAILABLE),
};

async function openFirstClaimRecord() {
  fireEvent.click(screen.getAllByRole("button", { name: /GEN-1 \/ output_kw/ })[0]);
}

const STATES: Array<[string, string, Clients?, (() => Promise<void>)?]> = [
  ["Site Overview, Dispatch card", `/sites/${SITE_ID}`],
  ["Site Overview, no evidence", `/sites/${SITE_ID}`, { overview: overviewClient({ status: "loaded", value: emptyOverview(SITE_ID) }) }],
  ["Site Overview, unavailable", `/sites/${SITE_ID}`, { overview: overviewClient(UNAVAILABLE) }],
  // With the Lab on, its entries (workspace link, Site quick actions) keep the
  // Lab's vocabulary and are the only text exempted as `lab`.
  ["Site Overview, Lab on", `/sites/${SITE_ID}`, { lab: true }],
  ["Finding Overview, Lab on", `/findings/${SITE_ID}/${CANDIDATE_ID}`, { lab: true }],
  ["Dispatch Overview", `/sites/${SITE_ID}/performance/dispatch`],
  ["Dispatch Overview, a period selected", `/sites/${SITE_ID}/performance/dispatch?interval=${CANDIDATE_ID}`],
  ["Dispatch Analysis, Needed period", `/sites/${SITE_ID}/performance/dispatch?interval=${NECESSARY_ID}&view=analysis`],
  ["Dispatch Analysis, possibly avoidable period", `/sites/${SITE_ID}/performance/dispatch?interval=${CANDIDATE_ID}&view=analysis`],
  ["Dispatch Analysis, unknown period", `/sites/${SITE_ID}/performance/dispatch?interval=dispatch-gone&view=analysis`],
  ["Dispatch, nothing assessed", `/sites/${SITE_ID}/performance/dispatch`, { analytics: EMPTY_ANALYTICS_CLIENT }],
  ["Dispatch, loaded and empty", `/sites/${SITE_ID}/performance/dispatch`, { analytics: analyticsClient(SITE_ID, { emptyDispatch: true }) }],
  ["Site Evidence, None readiness", `/sites/${SITE_ID}/evidence`, {
    analytics: analyticsClient(SITE_ID, {
      declaration: declaration(SITE_ID, [{ analytic_id: "dispatch", display_name: "Dispatch", readiness: NONE_READINESS }]),
    }),
  }],
  ["Dispatch, unavailable", `/sites/${SITE_ID}/performance/dispatch`, { analytics: unavailableAnalytics }],
  ["Finding Overview", `/findings/${SITE_ID}/${CANDIDATE_ID}`],
  ["Finding Analysis", `/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`],
  ["Finding Evidence", `/findings/${SITE_ID}/${CANDIDATE_ID}/evidence`],
  // S4-03: the old Evidence tab resolves to the saved Finding's Evidence view; its record drawer is gone.
  ["Finding Alternatives, record drawer open", `/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives`, {}, openFirstClaimRecord],
  ["Finding Alternatives", `/findings/${SITE_ID}/${CANDIDATE_ID}/alternatives`],
  ["Finding, unknown assessment", `/findings/${SITE_ID}/dispatch-nope/analysis`],
  ["Finding, unavailable", `/findings/${SITE_ID}/${CANDIDATE_ID}`, { analytics: unavailableAnalytics }],
  ["Findings index", "/findings"],
  ["Findings index, none", "/findings", { analytics: EMPTY_ANALYTICS_CLIENT }],
  ["Findings index, unavailable", "/findings", { analytics: unavailableAnalytics }],
  ["Site Findings", `/sites/${SITE_ID}/findings`],
  ["Site Findings, none", `/sites/${SITE_ID}/findings`, { analytics: EMPTY_ANALYTICS_CLIENT }],
  ["Site Evidence Overview", `/sites/${SITE_ID}/evidence`],
  ["Site Evidence Analysis", `/sites/${SITE_ID}/evidence?view=analysis`],
  ["Site Evidence Analysis, one assessed period", `/sites/${SITE_ID}/evidence?view=analysis&assessment=${CANDIDATE_ID}`],
  ["Site Evidence Analysis, unknown period", `/sites/${SITE_ID}/evidence?view=analysis&assessment=dispatch-gone`],
  ["Site Evidence, record drawer", `/sites/${SITE_ID}/evidence?signal=GEN-1/active_power&record=${RECORD_DETAIL.message_id}`],
  ["Site Evidence, no evidence", `/sites/${SITE_ID}/evidence`, { evidence: EMPTY_EVIDENCE_CLIENT, analytics: EMPTY_ANALYTICS_CLIENT }],
  ["Site Evidence, unavailable", `/sites/${SITE_ID}/evidence`, { evidence: evidenceClient(UNAVAILABLE, UNAVAILABLE), analytics: unavailableAnalytics }],
];

afterEach(cleanup);

describe("T028 product vocabulary guard (section 4)", () => {
  it("the list is versioned and matches on word boundaries", () => {
    expect(VOCABULARY_VERSION).toBeGreaterThanOrEqual(1);
    expect(forbiddenPhrases("The generator was running.")).toEqual(["running"]);
    expect(forbiddenPhrases("Truncated, rerouted, brand-new")).toEqual([]);
    expect(forbiddenPhrases("Reported solar power (PV) and battery charge (SOC)")).toEqual([]);
    expect(forbiddenPhrases("Reported PV and SOC")).toEqual(["PV", "SOC"]);
    expect(forbiddenPhrases("Battery soc")).toEqual([]);
  });

  it("every T028 surface and state, with Lab off, says nothing on the list", async () => {
    const violations: VocabularyViolation[] = [];
    for (const [page, path, clients, act] of STATES) {
      const result = await scanState(page, path, clients, act);
      // A scan of an empty or loading screen would pass for the wrong reason.
      expect(result.scanned, `${page} scanned nothing`).toBeGreaterThan(5);
      violations.push(...result.violations);
    }
    expect(describeViolations(violations)).toBe("");
  }, 60000);
});

describe("the guard's failing-example proofs", () => {
  it("a forbidden phrase delivered by the backend is caught, with its page and phrase", async () => {
    const base = analyticsClient(SITE_ID);
    const leaking: SiteAnalyticsClient = {
      ...base,
      getAssessment: async (site, id) => {
        const read = await base.getAssessment(site, id);
        if (read.status !== "loaded") return read;
        return {
          status: "loaded",
          value: {
            ...read.value,
            reading: { ...read.value.reading!, reason: "The binding constraint held for this run." },
          },
        };
      },
    };
    const page = "Finding Overview";
    const path = `/findings/${SITE_ID}/${CANDIDATE_ID}`;
    const { violations } = await scanState(page, path, { analytics: leaking });
    const caught = violations.map((v) => `${v.page}|${v.phrase}`);
    expect(caught).toContain(`${page} (${path})|binding`);
    expect(caught).toContain(`${page} (${path})|run`);
  });

  it("with the Lab on, its entries render and are the only text exempted as lab", async () => {
    renderAt(`/sites/${SITE_ID}`, { lab: true });
    await settledScreen();
    const lab = Array.from(document.querySelectorAll('[data-vocabulary-exempt="lab"]')).map((el) => el.textContent);
    expect(lab).toContain("Open Simulator Lab");
    expect(lab).toContain("Open in Simulator Lab");
    expect(lab.length).toBeGreaterThanOrEqual(5);
    cleanup();
  });

  it("an accessible label is scanned, not only visible text", () => {
    document.body.innerHTML = `<main><p>${"Plain words. ".repeat(3)}</p><svg aria-label="Simulator run timeline"></svg></main>`;
    const { violations } = scanProductVocabulary(document.body, "proof");
    expect(violations.map((v) => `${v.where}|${v.phrase}`)).toEqual([
      "aria-label|run",
      "aria-label|simulator",
    ]);
    document.body.innerHTML = "";
  });

  it("a reference value inside authored text is skipped, the authored words still scanned, prose refused", () => {
    document.body.innerHTML = `<main>
      <li data-vocabulary-reference="generator-controller / policy-minimum-runtime">Minimum operating time setting (reference generator-controller / policy-minimum-runtime)</li>
      <button data-vocabulary-reference="simulator-lab-source" aria-label="Inspect records from simulator-lab-source">Inspect</button>
      <li data-vocabulary-reference="simulator-lab-source">The run came from simulator-lab-source</li>
      <li data-vocabulary-reference="the run was binding">x</li>
    </main>`;
    const { violations } = scanProductVocabulary(document.body, "proof");
    expect(document.body.textContent).toContain("policy-minimum-runtime");
    expect(violations.map((v) => `${v.where}|${v.phrase}`)).toEqual([
      "data-vocabulary-reference|a reference value is not an identifier",
      "text|run",
    ]);
    document.body.innerHTML = "";
  });

  it("a source reference keeps its exact value and is not flagged; an exemption cannot cover a panel", () => {
    const reference = "sim-run-0042";
    document.body.innerHTML = `<main>
      <p>Source reference <span data-vocabulary-exempt="source-reference">${reference}</span></p>
      <a data-vocabulary-exempt="lab" href="/lab">Simulator Lab</a>
      <section data-vocabulary-exempt="source-reference"><p>The run was binding.</p></section>
      <span data-vocabulary-exempt="whatever">x</span>
    </main>`;
    const { violations } = scanProductVocabulary(document.body, "proof");
    expect(document.body.textContent).toContain(reference);
    expect(violations.map((v) => v.phrase)).toEqual([
      "exemption wraps more than one value",
      'unknown exemption "whatever"',
    ]);
    document.body.innerHTML = "";
  });

  it("the candidate fixture is the one the backend projection shapes", () => {
    // Guards the proof above against a fixture with no reading to leak into.
    expect(CANDIDATE_SUMMARY.reading?.reason).toBeTruthy();
    expect(CANDIDATE_ASSESSMENT.claim_level).toBeTruthy();
    expect(CANDIDATE_SUMMARY.assessment_id).toBe(CANDIDATE_ID);
  });
});
