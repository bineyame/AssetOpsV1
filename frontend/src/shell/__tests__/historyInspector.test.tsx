import { fireEvent, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import {
  fetchRunHistory,
  isRunHistory,
  type RunHistory,
  type RunHistoryResult,
} from "../runHistory";
import type { RunSetupClient, RunSummary } from "../runSetupClient";
import { RUNNING_IN_THE_GAP, executionMethods } from "./executionFixtures";
import prefix from "./kobo-mini-grid-history-prefix.json";

/**
 * The recorded-history inspector (T025c phase 1).
 *
 * `kobo-mini-grid-history-prefix.json` is a real payload: the host's history
 * read of the Kobo prolonged mini-grid recipe (mini-grid v2, 5-minute step)
 * after seven boundaries, serialized by the backend's own `history_payload`.
 * Nothing in it is hand-edited, so every value asserted here is one the
 * backend produces.
 */

const HISTORY = prefix as unknown as RunHistory;
const RUN_ID = HISTORY.run_id;
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
  site_id: "KOBO-001",
  scenario_id: "kobo-mini-grid-prolonged",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: { state: "RECORDED", template_id: "hybrid-mini-grid-100kw", template_version: 2 },
};

function client(history?: RunHistoryResult): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: RUNNING_IN_THE_GAP },
      undefined,
      history,
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

function all(selector: string): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>(selector));
}

function select(offset: number): void {
  // T025e: the one history cursor; the raw records have no select of their own.
  const index = HISTORY.boundaries.findIndex((b) => b.offset_minutes === offset);
  const range = document.getElementById("history-cursor-range") as HTMLInputElement;
  fireEvent.change(range, { target: { value: String(index) } });
}

describe("the recorded-history inspector", () => {
  it("states the source, the recorded extent and every family's coverage", async () => {
    renderAt(client({ status: "loaded", history: HISTORY }));
    await settledScreen();

    expect(
      document.querySelector("[data-history-source]")?.getAttribute(
        "data-history-source",
      ),
    ).toBe("LIVE_SESSION");
    expect(document.querySelector("[data-history-recorded]")?.textContent).toBe(
      `7 of ${HISTORY.boundaries_total}`,
    );
    const families = all("[data-history-family]");
    expect(families.map((row) => row.dataset.historyFamily)).toEqual([
      "state_samples",
      "intervals",
      "observation_attempts",
      "timeline",
      "drawing",
      "records",
      "publications",
    ]);
    // T026: a profile-4 run's mapping has no record channel, so records are
    // not applicable rather than missing; publications are recorded (none held).
    expect(families.map((row) => row.dataset.availability)).toEqual([
      "RECORDED",
      "RECORDED",
      "RECORDED",
      "RECORDED",
      "RECORDED",
      "NOT_APPLICABLE",
      "RECORDED",
    ]);
  });

  it("opens at the last recorded boundary and shows its exact values", async () => {
    renderAt(client({ status: "loaded", history: HISTORY }));
    await settledScreen();

    expect(
      document.querySelector("[data-history-selected]")?.getAttribute(
        "data-history-selected",
      ),
    ).toBe("30");
    const soc = all("[data-history-attempt]").find(
      (row) => row.dataset.historyAttempt === "battery-state-of-charge@battery",
    );
    // A non-terminating exact value is shown as the ratio it is.
    expect(soc?.textContent).toContain("685/19");
  });

  it("keeps a missing reading apart from a reported zero", async () => {
    renderAt(client({ status: "loaded", history: HISTORY }));
    await settledScreen();

    select(0);
    const first = all("[data-history-attempt]");
    const pv = first.find(
      (row) => row.dataset.historyAttempt === "pv-ac-power@pv-inverter",
    );
    expect(pv?.dataset.outcome).toBe("NO_PRECEDING_INTERVAL");
    expect(pv?.querySelector("[data-history-no-reading]")).not.toBeNull();
    expect(pv?.querySelector("[data-exact]")).toBeNull();

    select(15);
    const later = all("[data-history-attempt]").find(
      (row) => row.dataset.historyAttempt === "pv-ac-power@pv-inverter",
    );
    expect(later?.dataset.outcome).toBe("REPORTED");
    expect(later?.querySelector("[data-exact]")?.getAttribute("data-exact")).toBe(
      "0",
    );
    expect(later?.querySelector("[data-history-no-reading]")).toBeNull();
  });

  it("shows no interval measurement at the first boundary, and says why", async () => {
    renderAt(client({ status: "loaded", history: HISTORY }));
    await settledScreen();

    select(0);
    const phases = all("[data-history-sample]").map((row) => row.dataset.phase);
    expect(phases).toContain("POST_EVENT");
    expect(phases).not.toContain("PRECEDING_INTERVAL");
    expect(
      document.querySelector("[data-history-selected]")?.textContent,
    ).toContain("No step ended at this boundary");

    select(5);
    expect(
      all("[data-history-sample]").map((row) => row.dataset.phase),
    ).toContain("PRECEDING_INTERVAL");
  });

  it("says a boundary with no due signal is cadence, not dropout", async () => {
    renderAt(client({ status: "loaded", history: HISTORY }));
    await settledScreen();

    select(5);
    expect(all("[data-history-attempt]")).toHaveLength(0);
    expect(
      document.querySelector("[data-history-no-attempts]")?.textContent,
    ).toContain("not a dropout");
  });

  it("keeps each load addressed in the interval decided at a boundary", async () => {
    renderAt(client({ status: "loaded", history: HISTORY }));
    await settledScreen();

    select(5);
    expect(
      document
        .querySelector("[data-history-interval]")
        ?.getAttribute("data-history-interval"),
    ).toBe("5-10");
    const loads = all("[data-history-load]").map(
      (row) => row.dataset.historyLoad,
    );
    expect(new Set(loads)).toEqual(
      new Set([
        "load-demand@load-clinic",
        "load-demand@load-res",
        "load-demand@load-mill",
      ]),
    );
    expect(all("[data-history-load]")).toHaveLength(3);
  });

  it("shows a run with no history as stated absence, with no boundary records", async () => {
    renderAt(client());
    await settledScreen();

    expect(
      document.querySelector("[data-history-source]")?.getAttribute(
        "data-history-source",
      ),
    ).toBe("NOT_RECORDED");
    const families = all("[data-history-family]");
    // T026: history schema 3 adds `records` and `publications`.
    expect(families).toHaveLength(7);
    expect(
      families.every((row) => row.dataset.availability === "UNAVAILABLE"),
    ).toBe(true);
    expect(document.querySelector("[data-history-boundary-select]")).toBeNull();
  });

  it("says when the history could not be read", async () => {
    renderAt(client({ status: "unavailable", message: "store offline" }));
    await settledScreen();

    expect(
      document.querySelector("[data-history-unavailable]")?.textContent,
    ).toContain("store offline");
  });

  it("is never read while the Lab gate is closed", async () => {
    const runSetup = client({ status: "loaded", history: HISTORY });
    const read = vi.spyOn(runSetup, "getExecutionHistory");
    renderAt(runSetup, false);
    await settledScreen();

    expect(read).not.toHaveBeenCalled();
    expect(document.querySelector("[data-history-source]")).toBeNull();
  });
});

describe("the history read", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reads the run's own history path and nothing else", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ history: HISTORY }), { status: 200 }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchRunHistory("/api/runs", RUN_ID);

    expect(result.status).toBe("loaded");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]).toEqual([
      `/api/runs/${RUN_ID}/execution/history`,
    ]);
  });

  it("refuses a sample whose value is not exact text", () => {
    const damaged = {
      ...HISTORY,
      samples: [{ ...HISTORY.samples[0], value: 40 }],
    };
    expect(isRunHistory(HISTORY)).toBe(true);
    expect(isRunHistory(damaged)).toBe(false);
  });
});
