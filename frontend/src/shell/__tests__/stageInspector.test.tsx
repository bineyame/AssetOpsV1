import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";
import {
  createRunSetupClient,
  isRunStage,
  type RunSetupClient,
  type RunStageResult,
  type RunSummary,
} from "../runSetupClient";
import {
  COMPLETED,
  NOT_STAGED,
  RUNNING_IN_THE_GAP,
  STAGED_IN_THE_GAP,
  STAGE_UNREADABLE,
  executionMethods,
} from "./executionFixtures";

/**
 * The stage inspector: exact staged envelopes, their metadata, and nothing more.
 *
 * Pinned to cells through `data-` attributes for the reason the execution tests
 * are: source time and publication time are three seconds apart and sit side by
 * side, and an assertion satisfied by adjacent text would pass with the two
 * columns swapped.
 */

const RUN_ID = "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const URL = `/simulator-lab/runs/${RUN_ID}`;

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

function client(stage: RunStageResult): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: RUNNING_IN_THE_GAP },
      stage,
    ),
  };
}

function renderAt(runSetup: RunSetupClient, enabled = true) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App
        flags={featureFlagsWith(enabled)}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function stageRow(messageId: string): HTMLElement {
  const row = document.querySelector(
    `[data-staged-envelope="${messageId}"]`,
  ) as HTMLElement | null;
  if (row === null) {
    throw new Error(`no staged envelope row for ${messageId}`);
  }
  return row;
}

describe("the stage inspector shows exact staged envelopes", () => {
  it("renders every staged envelope, and the set is not empty", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    const rows = document.querySelectorAll("[data-staged-envelope]");
    expect(rows.length).toBe(3);
    expect(
      document
        .querySelector("[data-stage-statement]")
        ?.getAttribute("data-stage-count"),
    ).toBe("3");
  });

  it("keeps source time and publication time in separate cells", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    const newest = STAGED_IN_THE_GAP.envelopes[2];
    const row = stageRow(newest.message_id);

    expect(
      row.querySelector("[data-staged-source-time]")?.textContent,
    ).toBe("2026-09-22T00:45:00Z");
    expect(
      row.querySelector("[data-staged-published-at]")?.textContent,
    ).toBe("2026-09-22T00:45:03Z");
    expect(row.querySelector("[data-staged-value]")?.textContent).toBe(
      "373.52 L",
    );
  });

  it("shows the selected envelope's canonical text byte for byte", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    const newest = STAGED_IN_THE_GAP.envelopes[2];
    const pre = document.querySelector(
      `[data-stage-canonical="${newest.message_id}"]`,
    );
    // Exact, not "contains": the inspector's job is to show what is persisted
    // without reformatting it.
    expect(pre?.textContent).toBe(newest.canonical);
    expect(
      document.querySelector("[data-stage-selected-source-time]")?.textContent,
    ).toBe(newest.source_time);
    expect(
      document.querySelector("[data-stage-selected-published-at]")
        ?.textContent,
    ).toBe(newest.published_at);
  });

  it("selects another envelope and shows its exact text instead", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    const first = STAGED_IN_THE_GAP.envelopes[0];
    fireEvent.click(screen.getByRole("button", { name: "Show envelope 89" }));

    const pre = document.querySelector("pre.canonical-text");
    expect(pre?.getAttribute("data-stage-canonical")).toBe(first.message_id);
    expect(pre?.textContent).toBe(first.canonical);
  });

  it("names the frozen mapping, the schema versions and the allowlist", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    const words = spacedText(screen.getByRole("main"));
    expect(words).toMatch(/Frozen mapping simulator-lab-gateway-fuel v1/);
    expect(words).toMatch(/Envelope schema assetops\.source-envelope v1/);
    const allowlist = screen
      .getByRole("heading", { name: "The allowlist this stage froze" })
      .closest("section") as HTMLElement;
    expect(within(allowlist).getAllByRole("row")).toHaveLength(2);
    expect(spacedText(allowlist)).toMatch(/fuel-level-sensor \/ fuel-level/);
  });

  it("says a running stage is not eligible, and why", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    expect(
      document
        .querySelector("[data-stage-release]")
        ?.getAttribute("data-stage-release"),
    ).toBe("NOT_ELIGIBLE");
    expect(
      document.querySelector('[data-stage-blocker="EXECUTION_NOT_COMPLETED"]'),
    ).not.toBeNull();
  });
});

describe("a control re-reads the persisted stage", () => {
  it("shows what stepping staged, read back rather than patched", async () => {
    let reads = 0;
    const runSetup: RunSetupClient = {
      ...client({ status: "loaded", stage: NOT_STAGED }),
      getStage: () => {
        reads += 1;
        return Promise.resolve({
          status: "loaded",
          stage: reads === 1 ? NOT_STAGED : STAGED_IN_THE_GAP,
        });
      },
    };
    renderAt(runSetup);
    await settledScreen();
    expect(document.querySelectorAll("[data-staged-envelope]")).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Step" }));

    await screen.findByRole("heading", { name: "Every staged envelope" });
    expect(reads).toBe(2);
    expect(document.querySelectorAll("[data-staged-envelope]")).toHaveLength(3);
  });
});

describe("the stage says how far it was published", () => {
  it("shows the publication watermark and the blocker it produces", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    expect(
      document.querySelector("[data-stage-published-through]")?.textContent,
    ).toBe("boundary 104 of 165");
    const blocker = document.querySelector(
      '[data-stage-blocker="STAGING_INCOMPLETE"]',
    );
    expect(blocker).not.toBeNull();
    // A healthy run part way through is incomplete, not failed (review R4).
    expect(blocker?.textContent).toMatch(/expected while the run is still executing/);
    expect(blocker?.textContent).not.toMatch(/A stage write failed/);
  });
});

describe("an unreadable stage is shown as a failure, not as content", () => {
  it("names the integrity failure and presents no envelope", async () => {
    renderAt(client({ status: "loaded", stage: STAGE_UNREADABLE }));
    await settledScreen();

    expect(
      document
        .querySelector("[data-stage-statement]")
        ?.getAttribute("data-stage-status"),
    ).toBe("STAGE_UNREADABLE");
    expect(document.querySelector("[data-stage-unreadable]")?.textContent).toMatch(
      /integrity digest does not match/,
    );
    expect(
      document.querySelector('[data-stage-blocker="INTEGRITY_FAILURE"]'),
    ).not.toBeNull();
    expect(document.querySelectorAll("[data-staged-envelope]")).toHaveLength(0);
    expect(document.querySelector("pre.canonical-text")).toBeNull();
  });
});

describe("the inspector cannot edit what it shows", () => {
  it("offers no input, and no control but choosing which envelope to read", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }));
    await settledScreen();

    const stagePanels = [
      "Staged source envelopes",
      "The allowlist this stage froze",
      "The selected envelope, exactly as staged",
      "Every staged envelope",
    ].map(
      (name) =>
        screen.getByRole("heading", { name }).closest("section") as HTMLElement,
    );

    for (const panel of stagePanels) {
      expect(panel.querySelectorAll("input, textarea, select")).toHaveLength(0);
      for (const button of Array.from(panel.querySelectorAll("button"))) {
        expect(button.textContent).toMatch(/^Show envelope \d+$/);
      }
    }
  });
});

describe("the stage is read from the stage route, and only behind the gate", () => {
  it("reads the stage path under the runs path, with GET", async () => {
    const calls: [string, RequestInit | undefined][] = [];
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      calls.push([String(input), init]);
      return Promise.resolve(
        new Response(JSON.stringify({ stage: STAGED_IN_THE_GAP }), {
          status: 200,
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      const result = await createRunSetupClient(
        "/profiles",
        "/runs",
      ).getStage(RUN_ID);
      expect(result.status).toBe("loaded");
      expect(calls).toHaveLength(1);
      expect(calls[0][0]).toBe(`/runs/${RUN_ID}/stage`);
      expect(calls[0][1]?.method ?? "GET").toBe("GET");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("refuses to render half a stage", () => {
    expect(isRunStage(STAGED_IN_THE_GAP)).toBe(true);
    const broken = {
      ...STAGED_IN_THE_GAP,
      envelopes: [{ ...STAGED_IN_THE_GAP.envelopes[0], canonical: 7 }],
    };
    expect(isRunStage(broken)).toBe(false);
  });

  it("serves no run screen at all, and so no inspector, when the Lab is off", async () => {
    renderAt(client({ status: "loaded", stage: STAGED_IN_THE_GAP }), false);
    await settledScreen();

    expect(
      screen.queryByRole("heading", { name: "Staged source envelopes" }),
    ).toBeNull();
    expect(document.querySelector("[data-staged-envelope]")).toBeNull();
  });

  it("a completed, verified stage says eligible and that nothing releases it", async () => {
    const eligible: RunStageResult = {
      status: "loaded",
      stage: {
        ...STAGED_IN_THE_GAP,
        execution_status: "COMPLETED",
        release_eligible: true,
        release_blockers: [],
        published_through: 165,
      },
    };
    const runSetup: RunSetupClient = {
      ...client(eligible),
      ...executionMethods({ status: "loaded", execution: COMPLETED }, eligible),
    };
    renderAt(runSetup);
    await settledScreen();

    const release = document.querySelector("[data-stage-release]");
    expect(release?.getAttribute("data-stage-release")).toBe("ELIGIBLE");
    expect(release?.textContent).toMatch(/Nothing in this build releases it/);
  });

  it("a draft nothing executed has an empty stage and says so", async () => {
    renderAt(client({ status: "loaded", stage: NOT_STAGED }));
    await settledScreen();

    expect(
      document
        .querySelector("[data-stage-statement]")
        ?.getAttribute("data-stage-status"),
    ).toBe("NOT_STAGED");
    expect(document.querySelectorAll("[data-staged-envelope]")).toHaveLength(0);
  });
});
