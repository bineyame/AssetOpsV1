import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import type { RunHistory } from "../runHistory";
import type { RunExecution, RunSetupClient, RunSummary } from "../runSetupClient";
import { NOT_RECORDED, NOT_STARTED, executionMethods } from "./executionFixtures";
import executionPrefix from "./kobo-policy-execution-prefix.json";
import historyPrefix from "./kobo-policy-history-prefix.json";

/**
 * T025e AC9-AC10: the run screen is an organised cockpit.
 *
 * The control strip on the execution clock comes first, then the record at
 * the history cursor (drawing beside inspection, the cursor, the curves, the
 * Applied timeline), and everything else is in closed disclosures below -
 * still on the page, with every hook and heading it had. jsdom has no layout,
 * so the geometry itself is measured by `tools/layout-evidence.mjs`; this
 * asserts the order, the closed state and that nothing was lost.
 */
const HISTORY = historyPrefix as unknown as RunHistory;
const EXECUTION = executionPrefix as unknown as RunExecution;
const RUN_ID = HISTORY.run_id;

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-mini-grid-stop-60",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

function client(recorded: boolean): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: recorded ? EXECUTION : { ...NOT_STARTED, run_id: RUN_ID } },
      undefined,
      { status: "loaded", history: recorded ? HISTORY : { ...NOT_RECORDED, run_id: RUN_ID } },
    ),
  };
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[`/simulator-lab/runs/${RUN_ID}`]}>
      <App
        flags={featureFlagsWith(true)}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function one(selector: string): HTMLElement {
  const found = document.querySelector<HTMLElement>(selector);
  if (found === null) {
    throw new Error(`nothing matches ${selector}`);
  }
  return found;
}

function before(a: Element, b: Element): boolean {
  return (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
}

describe("the organised run cockpit (T025e AC9)", () => {
  it("puts the control strip first, then the record at the history cursor, in reading order", async () => {
    renderAt(client(true));
    await settledScreen();

    const order = [
      "[data-control-strip]",
      "[data-execution-clock]",
      "[data-playback-statement]",
      "[data-cockpit-record]",
      "[data-drawing-boundary]",
      "[data-interval-span]",
      "[data-history-cursor]",
      '[data-chart-panel="pv"]',
      "[data-timeline-scope]",
      "[data-run-not-line]",
    ].map(one);
    for (let i = 1; i < order.length; i += 1) {
      expect(before(order[i - 1], order[i]), `${i}`).toBe(true);
    }
    // The drawing and the inspection share one row; the cursor is not the clock.
    expect(one(".run-cockpit__stage").contains(one("[data-drawing-boundary]"))).toBe(true);
    expect(one(".run-cockpit__stage").contains(one("[data-interval-span]"))).toBe(true);
    expect(one("[data-execution-clock]").textContent).toBe(
      `Execution clock: boundary ${EXECUTION.boundaries_completed} of ${EXECUTION.boundaries_total}, ${EXECUTION.simulation_time}`,
    );
    expect(one("label[for='history-cursor-range']").textContent).toBe("History cursor");
  });

  it("has nothing above the cockpit that grows with the run: every table is inside or below it", async () => {
    renderAt(client(true));
    await settledScreen();

    const cockpit = one("[data-cockpit]");
    const tables = Array.from(document.querySelectorAll("table"));
    expect(tables.length).toBeGreaterThan(10);
    for (const table of tables) {
      expect(cockpit.contains(table) || before(cockpit, table)).toBe(true);
    }
    // The per-step tables and the newest attempts are in the closed latest-step
    // disclosure, below the cockpit.
    const latest = one('[data-disclosure="latest-step"]');
    expect(before(cockpit, latest)).toBe(true);
    expect(latest.querySelectorAll("[data-sample-attempt]").length).toBeGreaterThan(0);
  });

  it("reads the balance as one verdict line, with the identities one click away", async () => {
    renderAt(client(true));
    await settledScreen();

    const verdict = one("[data-balance-verdict]");
    expect(verdict.getAttribute("data-balance-verdict")).toBe("holds");
    const identities = Array.from(document.querySelectorAll("[data-interval-balance]"));
    expect(identities.length).toBeGreaterThan(0);
    for (const row of identities) {
      expect(row.closest('details[data-disclosure="interval-balance"]')).not.toBeNull();
    }
  });

  it("reserves every cockpit region before the first boundary is recorded", async () => {
    renderAt(client(false));
    await settledScreen();

    const range = one("#history-cursor-range") as HTMLInputElement;
    expect(range.disabled).toBe(true);
    for (const selector of [
      "[data-return-to-live-slot]",
      "[data-history-lag]",
      "[data-drawing-empty]",
      "[data-interval-empty]",
      "[data-charts-empty]",
      ".run-cockpit__timeline",
    ]) {
      expect(one("[data-cockpit-record]").contains(one(selector)), selector).toBe(true);
    }
  });
});

describe("everything else on demand, nothing lost (T025e AC10)", () => {
  it("keeps every secondary section in a closed disclosure below the cockpit", async () => {
    renderAt(client(true));
    await settledScreen();

    const cockpit = one("[data-cockpit]");
    const disclosures = Array.from(
      document.querySelectorAll<HTMLDetailsElement>("details[data-disclosure]"),
    );
    const names = disclosures.map((d) => d.getAttribute("data-disclosure"));
    for (const name of [
      "run-identity",
      "execution-provenance",
      "latest-step",
      "reporting-paths",
      "history-facts",
      "raw-records",
      "stage",
      "run-not",
      "how-playback-works",
    ]) {
      expect(names, name).toContain(name);
    }
    for (const details of disclosures) {
      expect(details.open, details.getAttribute("data-disclosure") ?? "").toBe(false);
      if (!cockpit.contains(details)) {
        expect(before(cockpit, details)).toBe(true);
      }
    }
  });

  it("keeps every hook and heading id the earlier slices and the evidence read", async () => {
    renderAt(client(true));
    await settledScreen();

    for (const selector of [
      "[data-history-cursor]",
      "[data-return-to-live-slot]",
      "[data-history-lag]",
      "#history-cursor-range",
      "[data-timeline-go]",
      "[data-cursor-offset]",
      "[data-drawing-boundary]",
      "[data-interval-span]",
      "[data-interval-control]",
      "[data-interval-load]",
      "[data-execution-statement]",
      "[data-execution-status]",
      "[data-playback-state]",
      "[data-playback-statement]",
      "[data-header-run]",
      "[data-header-boundaries]",
      "[data-header-history]",
      "[data-header-stage]",
      "[data-history-source]",
      "[data-history-recorded]",
      "[data-history-family]",
      "[data-history-selected]",
      "[data-history-sample]",
      "[data-signal]",
      "[data-sample-attempt]",
      "[data-private-state]",
      "[data-stage-statement]",
      "[data-chart-panel]",
      "[data-value-row]",
      "#run-heading",
      "#run-execution-heading",
      "#run-playback-heading",
      "#run-header-heading",
      "#run-identity-heading",
      "#run-frozen-heading",
      "#run-drawing-heading",
      "#run-interval-control-heading",
      "#run-interval-effective-heading",
      "#run-interval-loads-heading",
      "#run-interval-balance-heading",
      "#run-history-charts-heading",
      "#run-history-values-heading",
      "#run-timeline-heading",
      "#run-history-heading",
      "#run-history-coverage-heading",
      "#run-history-boundary-heading",
      "#run-private-heading",
      "#run-observations-heading",
      "#run-signals-heading",
      "#run-reports-heading",
      "#run-stage-heading",
      "#run-not-heading",
    ]) {
      expect(document.querySelector(selector), selector).not.toBeNull();
    }
    // Duplicates went: the trajectory digest is stated once, in provenance.
    const digest = EXECUTION.content_digest ?? "not computed until this run reaches an outcome";
    const mentions = Array.from(document.querySelectorAll("dd, code, span")).filter(
      (el) => el.children.length === 0 && el.textContent === digest,
    );
    expect(mentions.length).toBeLessThanOrEqual(1);
  });
});
