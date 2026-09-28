import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import type {
  RunDetailResult,
  RunExecutionResult,
  RunSetupClient,
  RunSummary,
} from "../runSetupClient";
import {
  COMPLETED,
  INTERRUPTED,
  NOT_STARTED,
  RUNNING_IN_THE_GAP,
  executionMethods,
} from "./executionFixtures";

/**
 * Executing a draft, and telling three things apart on one screen.
 *
 * The risk these are written against is the one this milestone has paid for five
 * times: an assertion satisfied by adjacent text. Private truth, a reported value
 * and a retained reading sit inches apart here by construction, so every claim
 * below is pinned to its own CELL through a `data-` attribute on the row rather
 * than to the page's text. A screen that merged the three columns would render
 * every word these tests look for and fail every one of them.
 *
 * Every value is injected. Nothing here depends on a store, a kernel or a
 * network.
 */

const READY_ID = "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const BLOCKED_ID = "run-99aa88bb77cc66dd55ee44ff33221100";
const READY_URL = `/simulator-lab/runs/${READY_ID}`;
const ENABLED = featureFlagsWith(true);

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const READY_RUN: RunSummary = {
  run_id: READY_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure:
    "READY means every required executable input resolved and the selected " +
    "model profile declares it can consume them.",
  created_at: "2026-09-22T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: [
    {
      identity_field: "site",
      field: "Site",
      value: "MG-001",
      answered_by: "SITE_FOUNDATION",
      answered_by_detail: "site MG-001 foundation version 1",
      blocking_statement: null,
    },
  ],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

const BLOCKED_RUN: RunSummary = {
  ...READY_RUN,
  run_id: BLOCKED_ID,
  execution_status: "BLOCKED",
  readiness_disclosure: null,
  blocking_reasons: [
    {
      kind: "STATE_NOT_SUPPORTED",
      subject: "site-load-demand",
      statement:
        "Model profile minimal-fuel-tank version 1 does not model " +
        "site-load-demand at all.",
    },
  ],
};

function client(
  execution: RunExecutionResult = {
    status: "loaded",
    execution: RUNNING_IN_THE_GAP,
  },
  detail: RunDetailResult = { status: "loaded", run: READY_RUN },
): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve(detail),
    ...executionMethods(execution),
  };
}

function renderAt(path: string, runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={ENABLED}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function observationRow(signal: string): HTMLElement {
  const row = document.querySelector(
    `[data-observation="${signal}"]`,
  ) as HTMLElement | null;
  if (row === null) {
    throw new Error(`no observation row for ${signal}`);
  }
  return row;
}

function cell(row: HTMLElement, attribute: string): string {
  const found = row.querySelector(`[${attribute}]`);
  if (found === null) {
    throw new Error(`no ${attribute} cell on this row`);
  }
  return (found.textContent ?? "").trim();
}

function executionPanel(): HTMLElement {
  return screen
    .getByRole("heading", { name: "Executing this run" })
    .closest("section") as HTMLElement;
}

describe("the execution panel", () => {
  it("shows the simulated clock and the reading digest while a run is in flight", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const panel = executionPanel();

    expect(within(panel).getByText("RUNNING")).toBeInTheDocument();
    expect(within(panel).getByText("2026-09-22T01:45:00Z")).toBeInTheDocument();
    expect(within(panel).getByText("1545 minutes")).toBeInTheDocument();
    expect(within(panel).getByText("104 of 165")).toBeInTheDocument();
    // The reading digest is present and the trajectory digest is not, because a
    // digest over a prefix would be an identity for something that is not yet a
    // thing.
    expect(within(panel).getByText("c".repeat(64))).toBeInTheDocument();
    expect(
      within(panel).getByText(
        /not computed until this run reaches an outcome/,
      ),
    ).toBeInTheDocument();
  });

  it("places the contract's own statement rather than composing one", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const statement = document.querySelector(
      "[data-execution-statement]",
    ) as HTMLElement;

    expect(statement.textContent).toBe(RUNNING_IN_THE_GAP.statement);
  });

  it("shows a refused control on its own, never as a blocking reason", async () => {
    renderAt(
      READY_URL,
      client({
        status: "refused",
        code: "EXECUTION_ALREADY_TERMINAL",
        refusalKind: "ALREADY_TERMINAL",
        message: "This execution has already completed or failed.",
      }),
    );
    await settledScreen();

    const refusal = document.querySelector(
      "[data-control-refusal]",
    ) as HTMLElement;
    expect(refusal).not.toBeNull();
    expect(refusal.textContent).toContain("ALREADY_TERMINAL");

    // A refused control is not a blocked draft. A READY draft has no
    // blocking-reason table at all, so the two cannot be read as one fact.
    expect(
      screen.queryByRole("table", {
        name: "Why this draft cannot be executed",
      }),
    ).toBeNull();
  });

  it("says an execution failed, with the failure's own reason", async () => {
    renderAt(
      READY_URL,
      client({
        status: "loaded",
        execution: {
          ...RUNNING_IN_THE_GAP,
          status: "FAILED",
          statement: "This execution stopped before the end of its interval.",
          content_digest: "e".repeat(64),
          failure: {
            kind: "INTEGRATION_BOUND_FAILURE",
            subject: "fuel-tank-volume@fuel-tank",
            statement:
              "A cause would take a stock past a bound whose policy is to " +
              "fail the run.",
            at_offset_minutes: 1500,
            detail: [],
          },
        },
      }),
    );
    await settledScreen();

    const failure = document.querySelector(
      "[data-execution-failure]",
    ) as HTMLElement;
    expect(failure).not.toBeNull();
    expect(failure.textContent).toContain("INTEGRATION_BOUND_FAILURE");
    expect(failure.textContent).toContain("fuel-tank-volume@fuel-tank");
  });
});

describe("private truth beside what was reported", () => {
  it("separates the true value, the reported value and the reading's own time", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const row = observationRow("fuel-level-sensor:fuel-level");

    // Five cells, five claims. The tank holds 254.02 L; the newest reading says
    // 373.52 L; that reading was taken an hour earlier; the quality says it is
    // retained; and the outcome names the gap.
    expect(cell(row, "data-observation-true")).toBe("254.02 L");
    expect(cell(row, "data-observation-reported")).toBe("373.52 L");
    expect(cell(row, "data-observation-source-time")).toBe(
      "2026-09-22T00:45:00Z",
    );
    expect(cell(row, "data-observation-quality")).toBe("STALE");
    expect(cell(row, "data-observation-outcome")).toContain(
      "SUPPRESSED_BY_GAP",
    );

    // And the two numbers disagree, which is the whole demonstration. An
    // assertion that only checked both were present would pass over a screen
    // showing one number twice.
    expect(cell(row, "data-observation-true")).not.toBe(
      cell(row, "data-observation-reported"),
    );
  });

  it("shows the retained reading's source time, not this instant's", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const row = observationRow("fuel-level-sensor:fuel-level");

    // The run is at 01:45 and the reading was taken at 00:45. A screen that
    // restamped a retained reading would show the first in both cells.
    expect(cell(row, "data-observation-source-time")).not.toBe(
      RUNNING_IN_THE_GAP.simulation_time,
    );
  });

  it("keeps two reporting paths apart, including the one nothing measured", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const fuel = observationRow("fuel-level-sensor:fuel-level");
    const generator = observationRow("generator-controller:ac-power");

    expect(cell(fuel, "data-observation-true")).toBe("254.02 L");
    // The generator's interval measurement does not exist at this instant. That
    // is a different fact from a reading not arriving, and each row states its
    // own rather than sharing one.
    expect(cell(generator, "data-observation-true")).toBe("not measured here");
    expect(cell(generator, "data-observation-reported")).toBe("45 kW");
    expect(cell(generator, "data-observation-outcome")).toBe("not due");
  });

  it("shows the private stock as its own row", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const row = document.querySelector(
      '[data-private-state="fuel-tank-volume@fuel-tank"]',
    ) as HTMLElement;

    expect(row).not.toBeNull();
    expect(row.textContent).toContain("254.02");
  });

  it("names the declared reporting gap, its shape and which signal it silences", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const row = document.querySelector(
      '[data-reporting-gap="fuel-level-reporting-gap"]',
    ) as HTMLElement;

    expect(row).not.toBeNull();
    expect(row.textContent).toContain("fuel-level-sensor / fuel-level");
    expect(row.textContent).toContain("1490");
    expect(row.textContent).toContain("1580");
    // The SHAPE, in its own cell. A POINT covering one step and a WINDOW
    // covering ninety minutes are different declarations, and a table showing
    // only the resolved offsets would render them the same way - which is how
    // an instant became a run-long outage before this was carried.
    const shape = row.querySelector("[data-reporting-gap-shape]");
    expect(shape?.getAttribute("data-reporting-gap-shape")).toBe("WINDOW");
    expect((shape?.textContent ?? "").trim()).toBe("WINDOW");
  });

  it("shows a point condition as a point, not as the span it resolves to", async () => {
    renderAt(
      READY_URL,
      client({
        status: "loaded",
        execution: {
          ...RUNNING_IN_THE_GAP,
          reporting_gaps: [
            {
              ...RUNNING_IN_THE_GAP.reporting_gaps[0],
              timing_shape: "POINT",
              offset_minutes: 1485,
              end_offset_minutes: 1500,
            },
          ],
        },
      }),
    );
    await settledScreen();

    const row = document.querySelector(
      '[data-reporting-gap="fuel-level-reporting-gap"]',
    ) as HTMLElement;

    expect(
      row.querySelector("[data-reporting-gap-shape]")?.textContent?.trim(),
    ).toBe("POINT");
    expect(row.textContent).toContain("1485");
    expect(row.textContent).toContain("1500");
  });

  it("lists each configured path with its own cadence, bias and dropout", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const fuel = document.querySelector(
      '[data-signal="fuel-level-sensor:fuel-level"]',
    ) as HTMLElement;
    const generator = document.querySelector(
      '[data-signal="generator-controller:ac-power"]',
    ) as HTMLElement;

    expect(fuel.textContent).toContain("15 minutes");
    expect(fuel.textContent).toContain("-0.5 L");
    expect(fuel.textContent).toContain("40");
    // The two paths differ in every parameter, which is what makes a change to
    // one visible as a change to one.
    expect(generator.textContent).toContain("60 minutes");
    expect(generator.textContent).toContain("0 kW");
  });

  it("shows a suppressed attempt in the newest attempts, with its reason", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    const suppressed = document.querySelector(
      '[data-sample-attempt="fuel-level-sensor:fuel-level:1545"]',
    ) as HTMLElement;
    const published = document.querySelector(
      '[data-sample-attempt="fuel-level-sensor:fuel-level:1485"]',
    ) as HTMLElement;

    expect(suppressed.textContent).toContain("SUPPRESSED_BY_GAP");
    expect(suppressed.textContent).toContain("nothing published");
    expect(published.textContent).toContain("373.52 L");
  });
});

describe("the execution controls", () => {
  it("offers Start and not Step before a run has begun", async () => {
    renderAt(READY_URL, client({ status: "loaded", execution: NOT_STARTED }));
    await settledScreen();

    expect(
      screen.getByRole("button", { name: "Start this run" }),
    ).toBeEnabled();
    expect(screen.getByRole("button", { name: "Step" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Run to the end" }),
    ).toBeDisabled();
  });

  it("offers Step and not Start once a run is in flight", async () => {
    renderAt(READY_URL, client());
    await settledScreen();

    expect(
      screen.getByRole("button", { name: "Start this run" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Step" })).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Run to the end" }),
    ).toBeEnabled();
  });

  it("sends the boundary it is advancing from, so a repeat advances once", async () => {
    const requests: Array<{ boundaries: number; fromBoundary: number }> = [];
    const stepping: RunSetupClient = {
      ...client(),
      stepExecution: (_runId, request) => {
        requests.push({
          boundaries: request.boundaries,
          fromBoundary: request.fromBoundary,
        });
        return Promise.resolve({
          status: "loaded",
          execution: RUNNING_IN_THE_GAP,
        });
      },
    };

    renderAt(READY_URL, stepping);
    await settledScreen();

    const step = screen.getByRole("button", { name: "Step" });
    fireEvent.click(step);
    await settledScreen();
    fireEvent.click(step);
    await settledScreen();

    // Both requests name the boundary the projection says the run is at, so the
    // second is a repeat the port refuses rather than a second step. The screen
    // is not what decides that, which is why the assertion is about what it sent.
    expect(requests).toEqual([
      { boundaries: 1, fromBoundary: 104 },
      { boundaries: 1, fromBoundary: 104 },
    ]);
  });

  it("sends the batch size a reader asked for", async () => {
    const requests: number[] = [];
    const stepping: RunSetupClient = {
      ...client(),
      stepExecution: (_runId, request) => {
        requests.push(request.boundaries);
        return Promise.resolve({
          status: "loaded",
          execution: RUNNING_IN_THE_GAP,
        });
      },
    };

    renderAt(READY_URL, stepping);
    await settledScreen();

    fireEvent.change(screen.getByLabelText("Boundaries to advance"), {
      target: { value: "16" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Step" }));
    await settledScreen();

    expect(requests).toEqual([16]);
  });

  it("offers no execution control at all for a blocked draft", async () => {
    renderAt(`/simulator-lab/runs/${BLOCKED_ID}`, {
      ...client(),
      getRun: () => Promise.resolve({ status: "loaded", run: BLOCKED_RUN }),
    });
    await settledScreen();

    expect(
      screen.queryByRole("button", { name: "Start this run" }),
    ).toBeNull();
    expect(screen.queryByRole("button", { name: "Step" })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Run to the end" }),
    ).toBeNull();
    // And the reasons it cannot be executed are still the setup ones, in their
    // own table.
    expect(
      screen.getByRole("table", { name: "Why this draft cannot be executed" }),
    ).toBeInTheDocument();
  });

  it("offers no control once a run is terminal, and shows both digests", async () => {
    renderAt(READY_URL, client({ status: "loaded", execution: COMPLETED }));
    await settledScreen();

    expect(
      screen.getByRole("button", { name: "Start this run" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Step" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Run to the end" }),
    ).toBeDisabled();
    expect(screen.getByText("d".repeat(64))).toBeInTheDocument();
    expect(screen.getByText("165 of 165")).toBeInTheDocument();
  });

  it("says an execution was interrupted rather than showing a prefix", async () => {
    renderAt(READY_URL, client({ status: "loaded", execution: INTERRUPTED }));
    await settledScreen();

    expect(within(executionPanel()).getByText("INTERRUPTED")).toBeInTheDocument();
    // No world and no reading, because there are none: what the interrupted run
    // produced lived in a process that has ended.
    expect(
      screen.queryByRole("table", { name: "What the world holds" }),
    ).toBeNull();
    expect(
      screen.queryByRole("table", { name: "What each device reported" }),
    ).toBeNull();
  });

  it("says the execution surface could not be reached, without inventing a state", async () => {
    renderAt(
      READY_URL,
      client({
        status: "unavailable",
        message: "This build serves the Simulator Lab without an execution "
          + "port composed behind it.",
      }),
    );
    await settledScreen();

    const unavailable = document.querySelector(
      "[data-execution-unavailable]",
    ) as HTMLElement;
    expect(unavailable).not.toBeNull();
    expect(unavailable.textContent).toContain("without an execution port");
    expect(screen.queryByRole("button", { name: "Step" })).toBeNull();
  });
});

describe("what executing a draft still is not", () => {
  it("states that nothing was staged, committed or written to a site", async () => {
    renderAt(READY_URL, client({ status: "loaded", execution: COMPLETED }));
    await settledScreen();

    const panel = screen
      .getByRole("heading", { name: "What this run is not" })
      .closest("section") as HTMLElement;

    expect(spacedText(panel)).toMatch(
      /nothing has been staged for a gateway/i,
    );
    expect(spacedText(panel)).toMatch(/it cannot be committed/i);
    expect(spacedText(panel)).toMatch(/writes to no site/i);
  });

  it("offers no commit, stage, release, replay or reset control anywhere", async () => {
    renderAt(READY_URL, client({ status: "loaded", execution: COMPLETED }));
    await settledScreen();

    const controls = Array.from(
      screen.getByRole("main").querySelectorAll("button, a"),
    ).map((node) => (node.textContent ?? "").trim());

    // A closed list rather than a word ban. A new control has to be added here
    // deliberately, which is the lesson a word ban learnt the hard way when
    // "Execute this run now" walked past one.
    expect(controls).toEqual([
      "Start this run",
      "Step",
      "Run to the end",
      "Back to Runs",
      "Back to the Simulator Lab",
    ]);
  });
});
