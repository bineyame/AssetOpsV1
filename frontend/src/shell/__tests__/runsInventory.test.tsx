import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText, textNodes } from "../../test/text";
import type {
  RunDetailResult,
  RunInventoryRow,
  RunListResult,
  RunSetupClient,
  RunSummary,
} from "../runSetupClient";

/**
 * The Runs inventory and the Draft shell.
 *
 * Both screens are written against one risk, and these tests are mostly that
 * risk: a run inventory, a run detail, a frozen-identity panel and a Run
 * button can read as a product that nearly works, in a build where no run has
 * ever executed and none can. So the assertions are as much about what is
 * absent as about what renders - and the absences are checked as absences of
 * CONTROLS and CLAIMS rather than of words, because both screens have to be
 * able to say what has not happened.
 *
 * Every value is injected. Nothing here depends on a store or a network.
 */

const ENABLED = featureFlagsWith(true);
const DISABLED = featureFlagsWith(false);

const RUNS_URL = "/simulator-lab/runs";
const READY_ID = "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const BLOCKED_ID = "run-99aa88bb77cc66dd55ee44ff33221100";

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const ROWS: RunInventoryRow[] = [
  {
    run_id: READY_ID,
    lifecycle_status: "DRAFT",
    execution_status: "READY",
    created_at: "2026-09-22T09:00:00Z",
    site_id: "MG-001",
    foundation_version: 1,
    scenario_id: "fuel-loss-event",
    scenario_version: 1,
    interval: {
      start_time: "2026-09-21T00:00:00Z",
      end_time: "2026-09-22T17:00:00Z",
      duration_minutes: 2460,
    },
    blocking_reason_count: 0,
  },
  {
    run_id: BLOCKED_ID,
    lifecycle_status: "DRAFT",
    execution_status: "BLOCKED",
    created_at: "2026-09-22T08:00:00Z",
    site_id: "MG-001",
    foundation_version: 1,
    scenario_id: "fuel-loss-event",
    scenario_version: 1,
    interval: {
      start_time: "2026-09-21T00:00:00Z",
      end_time: "2026-09-22T17:00:00Z",
      duration_minutes: 2460,
    },
    blocking_reason_count: 3,
  },
];

const FROZEN_INPUTS = [
  {
    identity_field: "site",
    field: "Site",
    value: "MG-001",
    answered_by: "SITE_FOUNDATION",
    answered_by_detail: "site MG-001 foundation version 1",
  },
  {
    identity_field: "observation_bindings",
    field: "Cadence for fuel-level-sensor-reading",
    value: "15 minutes",
    answered_by: "PUBLICATION_PROFILE",
    answered_by_detail:
      "publication profile simulator-lab-publication version 1",
  },
  {
    identity_field: "profiles",
    field: "Model profile",
    value: "minimal-fuel-tank v1",
    answered_by: "RUN_INPUT",
    answered_by_detail: "supplied by this run setup request",
  },
];

const DISCLOSURE =
  "READY means every required executable input resolved and the selected " +
  "model profile declares it can consume them. It does not mean the model " +
  "can: nothing has verified that profile's supported states against an " +
  "executable model, because no causal runtime exists in this build.";

const READY_RUN: RunSummary = {
  run_id: READY_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: DISCLOSURE,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: FROZEN_INPUTS,
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
        "site-load-demand at all, which this scenario needs it to.",
    },
  ],
};

function runClient(
  list: RunListResult = { status: "loaded", runs: ROWS },
  detail: RunDetailResult = { status: "loaded", run: READY_RUN },
): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () =>
      Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve(list),
    getRun: () => Promise.resolve(detail),
  };
}

function renderAt(path: string, client: RunSetupClient, flags = ENABLED) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={client}
      />
    </MemoryRouter>,
  );
}

describe("the Runs inventory", () => {
  it("is not served when the gate is closed", async () => {
    renderAt(RUNS_URL, runClient(), DISABLED);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
  });

  it("lists a row per persisted draft, from the record", async () => {
    renderAt(RUNS_URL, runClient());
    await settledScreen();

    const table = screen.getByRole("table", { name: "Draft runs" });
    const rows = within(table).getAllByRole("row").slice(1);

    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain(READY_ID);
    expect(rows[0].textContent).toContain("MG-001");
    expect(rows[0].textContent).toContain("fuel-loss-event");
    expect(rows[0].textContent).toContain("READY");
    expect(rows[1].textContent).toContain("BLOCKED");
  });

  it("opens one run by its own identity", async () => {
    renderAt(RUNS_URL, runClient());
    await settledScreen();

    expect(screen.getByRole("link", { name: READY_ID })).toHaveAttribute(
      "href",
      `/simulator-lab/runs/${READY_ID}`,
    );
  });

  it("claims nothing about what a run has done", async () => {
    // A progress or evidence column would arrive as a zero, and a zero is a
    // measurement. Checked as column headings, because that is where a
    // column that should not exist would appear.
    renderAt(RUNS_URL, runClient());
    await settledScreen();

    const headings = within(screen.getByRole("table", { name: "Draft runs" }))
      .getAllByRole("columnheader")
      .map((cell) => cell.textContent ?? "");

    expect(headings.length).toBeGreaterThan(0);
    for (const banned of [
      /progress/i,
      /elapsed/i,
      /health/i,
      /evidence/i,
      /observation/i,
      /output/i,
      /result/i,
    ]) {
      expect(headings.join(" ")).not.toMatch(banned);
    }
  });

  it("says no run has been set up rather than showing an empty table", async () => {
    renderAt(RUNS_URL, runClient({ status: "loaded", runs: [] }));
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "No draft runs yet" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("does not report an unreadable store as an empty inventory", async () => {
    renderAt(RUNS_URL, runClient({ status: "unavailable" }));
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "Runs unavailable" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "No draft runs yet" })).toBeNull();
  });

  it("renders no digit that is not a record value", async () => {
    renderAt(RUNS_URL, runClient());
    await settledScreen();

    const expected = new Set<string>();
    for (const row of ROWS) {
      expected.add(row.run_id);
      expected.add(row.created_at);
      expected.add(row.site_id);
      expected.add(String(row.foundation_version));
      expected.add(row.scenario_id);
      expected.add(String(row.scenario_version));
      expected.add(row.interval.start_time);
      expected.add(row.interval.end_time);
    }

    const withDigits = textNodes(screen.getByRole("main")).filter((leaf) =>
      /\d/.test(leaf),
    );

    expect(withDigits.length).toBeGreaterThan(0);
    for (const leaf of withDigits) {
      expect(expected).toContain(leaf);
    }
  });
});

describe("one draft run", () => {
  const url = `/simulator-lab/runs/${READY_ID}`;

  it("renders the frozen identity with its answerers", async () => {
    renderAt(url, runClient());
    await settledScreen();

    const table = screen.getByRole("table", { name: "The frozen inputs" });

    for (const row of FROZEN_INPUTS) {
      expect(within(table).getByText(row.field)).toBeInTheDocument();
      expect(within(table).getByText(row.answered_by)).toBeInTheDocument();
    }
  });

  it("carries the disclosure from the record rather than composing one", async () => {
    renderAt(url, runClient());
    await settledScreen();

    expect(screen.getByText(DISCLOSURE)).toBeInTheDocument();
  });

  it("offers the run action disabled, with the prerequisite named", async () => {
    renderAt(url, runClient());
    await settledScreen();

    const control = screen.getByRole("button", { name: "Run this draft" });

    expect(control).toBeDisabled();
    const reason = document.getElementById(
      control.getAttribute("aria-describedby") ?? "",
    );
    expect(reason?.textContent).toMatch(/causal kernel/i);
  });

  it("offers no run action at all on a blocked draft", async () => {
    // A blocked draft cannot be run for a second, prior reason. The same
    // disabled button on both would say the two are the same distance from
    // working.
    renderAt(
      `/simulator-lab/runs/${BLOCKED_ID}`,
      runClient(undefined, { status: "loaded", run: BLOCKED_RUN }),
    );
    await settledScreen();

    expect(screen.queryByRole("button", { name: "Run this draft" })).toBeNull();
    const reasons = screen.getByRole("table", {
      name: "Why this draft cannot be executed",
    });
    expect(
      within(reasons).getByText("STATE_NOT_SUPPORTED"),
    ).toBeInTheDocument();
    expect(screen.queryByText(DISCLOSURE)).toBeNull();
  });

  it("offers no runtime control of any kind", async () => {
    // Absent rather than disabled: a disabled control says the capability
    // exists and is switched off, which is a different and false claim.
    renderAt(url, runClient());
    await settledScreen();

    const main = screen.getByRole("main");
    for (const banned of [
      /pause/i,
      /resume/i,
      /step/i,
      /reset/i,
      /rerun/i,
      /replay/i,
      /commit/i,
      /stage/i,
      /ingest/i,
      /open in assetops/i,
      /truth/i,
      // The three this list was missing. An enabled anchor reading "Execute
      // this run now" passed both guard suites until a reviewer added one:
      // the ban was written over a word list, and the next violation used a
      // word nobody had listed.
      /execute/i,
      /start/i,
      /launch/i,
    ]) {
      expect(within(main).queryByRole("button", { name: banned })).toBeNull();
      expect(within(main).queryByRole("link", { name: banned })).toBeNull();
    }

    // And the only button on the screen is the disabled one above.
    const buttons = within(main).getAllByRole("button");
    expect(buttons).toHaveLength(1);
    expect(buttons[0]).toBeDisabled();

    // The durable half: the links this screen carries are exactly the two
    // ways back, by href and by text. A word list can only ban what somebody
    // thought of; a closed set fails on a fifth link whatever it is called.
    const links = within(main)
      .getAllByRole("link")
      .map((link) => [link.getAttribute("href"), link.textContent]);
    expect(links).toEqual([
      ["/simulator-lab/runs", "Back to Runs"],
      ["/simulator-lab", "Back to the Simulator Lab"],
    ]);
  });

  it("reserves no plausible runtime value", async () => {
    // The trap this screen is built against: a shell that reads as a runtime
    // which happens to be stopped. A zeroed clock or an empty observation
    // count would be exactly that.
    renderAt(url, runClient());
    await settledScreen();

    const main = screen.getByRole("main");
    const words = spacedText(main);

    for (const banned of [
      /simulated time/i,
      /elapsed/i,
      /progress/i,
      /steps completed/i,
      /observations/i,
    ]) {
      expect(words).not.toMatch(banned);
    }

    // And no leaf reading as a meter: a bare clock or a percentage. Checked
    // per leaf rather than over the joined text, because a timestamp the
    // record supplies contains `00:00` inside it and banning that string
    // would be banning the record.
    const leaves = textNodes(main);
    expect(leaves.length).toBeGreaterThan(0);
    for (const leaf of leaves) {
      expect(leaf).not.toMatch(/^\d{1,2}:\d{2}(:\d{2})?$/);
      expect(leaf).not.toMatch(/^\d+(\.\d+)?\s*%$/);
    }
  });

  it("says what the draft is not", async () => {
    renderAt(url, runClient());
    await settledScreen();

    const words = spacedText(screen.getByRole("main"));

    expect(words).toMatch(/has not been executed/i);
    expect(words).toMatch(/Nothing has been staged for a gateway/i);
    expect(words).toMatch(/cannot be committed/i);
    expect(words).toMatch(/No evidence has been accepted/i);
    expect(words).toMatch(/No conclusion has been drawn/i);
  });

  it("carries no private scenario expectation", async () => {
    renderAt(url, runClient());
    await settledScreen();

    const words = spacedText(screen.getByRole("main"));

    expect(words).not.toMatch(/expectation/i);
    expect(words).not.toMatch(/oracle/i);
  });

  it("states a run that is not persisted rather than showing another", async () => {
    renderAt(url, runClient(undefined, { status: "not_found" }));
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "No such run" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("separates an unreadable store from a run that is not there", async () => {
    renderAt(url, runClient(undefined, { status: "unavailable" }));
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "Run unavailable" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "No such run" })).toBeNull();
  });
});
