import { fireEvent, render, screen as rtl } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { niceTicks, valueTicks } from "../HistoryCharts";
import { chartModel, plotted, readingAt, reportedRuns } from "../historyChartModel";
import type { RunHistory, RunHistoryResult } from "../runHistory";
import type {
  RunExecution,
  RunSetupClient,
  RunStageResult,
  RunSummary,
} from "../runSetupClient";
import { executionMethods } from "./executionFixtures";
import executionPrefix from "./kobo-policy-execution-prefix.json";
import historyPrefix from "./kobo-policy-history-prefix.json";

/**
 * The recorded day curves and the run header (T025c phase 2).
 *
 * Both fixtures are real payloads, written by `host/tests/make_history_fixtures.py`:
 * the policy-varied Kobo recipe (stop threshold 60 %, mini-grid v2, publication
 * profile 4, 5-minute step) with the generator controller's status silenced
 * for 30 minutes from offset 60, stepped live to offset 150 and serialized by
 * the backend's own `history_payload` and `execution_payload`. Nothing in them
 * is hand-edited. The prefix holds a generator start (a boundary transition at
 * 40 and 45), a reporting gap (status suppressed at 60 and 75), a drawn
 * dropout (status at 135), unserved mill load, and the battery both
 * discharging and charging.
 */

const HISTORY = historyPrefix as unknown as RunHistory;
const EXECUTION = executionPrefix as unknown as RunExecution;
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
  scenario_id: "kobo-mini-grid-stop-60",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

function client(
  history: RunHistoryResult = { status: "loaded", history: HISTORY },
  stage?: RunStageResult,
): RunSetupClient {
  return {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: EXECUTION },
      stage,
      history,
    ),
  };
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App
        flags={featureFlagsWith(true)}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function all(selector: string, scope: ParentNode = document): HTMLElement[] {
  return Array.from(scope.querySelectorAll<HTMLElement>(selector));
}

function panel(id: string): HTMLElement {
  const found = document.querySelector<HTMLElement>(`[data-chart-panel="${id}"]`);
  if (found === null) {
    throw new Error(`no chart panel ${id}`);
  }
  return found;
}

function cursorTo(offset: number): void {
  const index = HISTORY.boundaries.findIndex((b) => b.offset_minutes === offset);
  const range = document.getElementById("history-cursor-range") as HTMLInputElement;
  fireEvent.change(range, { target: { value: String(index) } });
}

function valueRow(key: string): HTMLElement {
  const row = document.querySelector<HTMLElement>(`[data-value-row="${key}"]`);
  if (row === null) {
    throw new Error(`no value row ${key}`);
  }
  return row;
}

describe("the chart model reads the record and adds nothing", () => {
  const model = chartModel(HISTORY, EXECUTION.timestep_minutes);

  it("keeps kW, % and L apart and each load addressed", () => {
    expect(model.panels.map((p) => `${p.id}:${p.unit}`)).toEqual([
      "pv:kW",
      "load-load-clinic:kW",
      "load-load-res:kW",
      "load-load-mill:kW",
      "soc-battery:%",
      "battery-power:kW",
      "generator-output:kW",
      "fuel-fuel-tank:L",
    ]);
    expect(model.states.map((s) => s.address)).toEqual([
      "generator-state@generator",
    ]);
    // Every reported signal pairs with the quantity it measures.
    expect(model.unpaired).toEqual([]);
  });

  it("draws PV and the battery from the history's own flows, one curve per flow (T025e, C3)", () => {
    // No execution step reaches a chart: every PV and battery point is one
    // recorded flow's mean power, exactly as the history holds it.
    const series = (panel: string, id: string) => {
      const found = model.panels
        .find((p) => p.id === panel)
        ?.series.find((s) => s.id === id);
      if (found === undefined || found.kind === "instant") {
        throw new Error(`no interval series ${panel}/${id}`);
      }
      return found;
    };
    const pairs: [string, string, string][] = [
      ["pv", "pv-potential", "pv_potential"],
      ["pv", "pv-to-load", "pv_to_load"],
      ["pv", "pv-to-battery", "pv_to_battery"],
      ["pv", "pv-curtailed", "curtailed_pv"],
      ["pv", "pv-clipped", "inverter_clipping"],
      ["battery-power", "battery-to-load", "battery_to_load"],
      ["battery-power", "pv-to-battery", "pv_to_battery"],
    ];
    let compared = 0;
    for (const [panel, id, flowId] of pairs) {
      const values = series(panel, id).values;
      expect(values).toHaveLength(HISTORY.intervals.length);
      HISTORY.intervals.forEach((interval, i) => {
        const flow = interval.flows.find((f) => f.flow_id === flowId);
        expect(values[i].from).toBe(interval.from_offset);
        expect(values[i].exact).toBe(flow?.mean_power);
        compared += 1;
      });
    }
    expect(compared).toBeGreaterThan(7 * 12);
  });

  it("builds nothing from a history with no recorded interval", () => {
    const empty = chartModel({ ...HISTORY, intervals: [] }, EXECUTION.timestep_minutes);
    expect(empty.panels.map((p) => p.id)).not.toContain("pv");
    expect(empty.panels.map((p) => p.id)).not.toContain("battery-power");
  });

  it("plots each report once, at its own source time", () => {
    for (const panel of [...model.panels, ...model.states]) {
      for (const track of panel.reported) {
        const plottedOffsets = reportedRuns(track).flat().map((a) => a.at_offset_minutes);
        const reported = track.attempts
          .filter((a) => a.outcome === "REPORTED")
          .map((a) => a.at_offset_minutes);
        expect(plottedOffsets).toEqual(reported);
        expect(new Set(plottedOffsets).size).toBe(plottedOffsets.length);
      }
    }
  });

  it("breaks the reported trace at a due attempt with no reading, not at a not-due instant", () => {
    const status = model.states[0].reported[0];
    expect(
      reportedRuns(status).map((run) => [
        run[0].at_offset_minutes,
        run[run.length - 1].at_offset_minutes,
      ]),
    ).toEqual([
      [0, 45],
      [90, 120],
      [150, 150],
    ]);
    // The SOC signal is due every 15 minutes and every attempt reported, so
    // the eleven sparse readings are one unbroken trace.
    const soc = model.panels.find((p) => p.id === "soc-battery")!.reported[0];
    expect(soc.cadence_minutes).toBe(15);
    expect(reportedRuns(soc)).toHaveLength(1);
    expect(reportedRuns(soc)[0]).toHaveLength(11);
  });

  it("holds a stale reading with its original time and never restamps it", () => {
    const status = model.states[0].reported[0];
    const suppressed = readingAt(status, 75);
    expect(suppressed.kind).toBe("missing");
    expect(suppressed.kind === "missing" && suppressed.last?.at_offset_minutes).toBe(45);
    const notDue = readingAt(status, 80);
    expect(notDue.kind).toBe("not_due");
    expect(notDue.kind === "not_due" && notDue.last?.source_sample_time).toBe(
      "2026-09-22T03:45:00Z",
    );
  });
});

describe("the value axis contains every value it draws", () => {
  it("ends at a tick at or above the largest value, and starts at or below the smallest", () => {
    for (const [min, max] of [
      [0, 5],
      [0, 33],
      [0, 62.4],
      [-30, 20],
      [0, 1],
    ]) {
      const ticks = niceTicks(min, max);
      expect(ticks[0]).toBeLessThanOrEqual(min);
      expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(max);
    }
  });

  it("holds for every panel of the recorded run", () => {
    const model = chartModel(HISTORY, EXECUTION.timestep_minutes);
    for (const panel of model.panels) {
      const values = panel.series.flatMap((s) =>
        s.kind === "instant" ? s.points.map((p) => p.value) : s.values.map((v) => v.value),
      );
      values.push(
        ...panel.reported.flatMap((t) =>
          t.attempts.filter((a) => a.reported_value !== null).map((a) => plotted(a.reported_value!)),
        ),
      );
      const ticks = valueTicks(panel, values);
      expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(Math.max(...values));
      expect(ticks[0]).toBeLessThanOrEqual(Math.min(...values));
    }
  });
});

describe("the value axis is declared or ratchets, never shrinks (T025e AC8)", () => {
  it("uses the declared 0-100 % for a state of charge and the held generator rating", () => {
    const model = chartModel(HISTORY, EXECUTION.timestep_minutes);
    const soc = model.panels.find((p) => p.id === "soc-battery")!;
    expect(soc.bound).toEqual({ min: 0, max: 100 });
    const ticks = valueTicks(soc, [37.5]);
    expect(ticks[0]).toBe(0);
    expect(ticks[ticks.length - 1]).toBe(100);
    const generator = model.panels.find((p) => p.id === "generator-output")!;
    expect(generator.bound?.max).toBeGreaterThan(0);
    // A load has no declared range: it ratchets.
    expect(model.panels.find((p) => p.id === "load-load-mill")!.bound).toBeUndefined();
  });

  it("is the same axis at every boundary of a live run until a value outgrows it", () => {
    const model = chartModel(HISTORY, EXECUTION.timestep_minutes);
    for (const panel of model.panels) {
      let top = -Infinity;
      let bottom = Infinity;
      let widened = 0;
      for (let k = 1; k <= HISTORY.boundaries.length; k += 1) {
        const through = HISTORY.boundaries[k - 1].offset_minutes;
        const values = panel.series.flatMap((s) =>
          s.kind === "instant"
            ? s.points.filter((p) => p.offset <= through).map((p) => p.value)
            : s.values.filter((v) => v.from <= through).map((v) => v.value),
        );
        const ticks = valueTicks(panel, values);
        const [lo, hi] = [ticks[0], ticks[ticks.length - 1]];
        if (k > 1) {
          expect(hi).toBeGreaterThanOrEqual(top);
          expect(lo).toBeLessThanOrEqual(bottom);
          if (hi !== top || lo !== bottom) {
            widened += 1;
          }
        }
        top = hi;
        bottom = lo;
      }
      expect(widened, panel.id).toBeLessThanOrEqual(3);
    }
  });

  it("never lowers its top as a series grows", () => {
    let top = 0;
    const values: number[] = [];
    for (let v = 0; v < 500; v += 0.37) {
      values.push(v);
      const ticks = valueTicks({}, values);
      expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(top);
      top = ticks[ticks.length - 1];
    }
  });
});

describe("the recorded day curves on the run screen", () => {
  it("draws every panel with separate unit axes and a cursor on each", async () => {
    renderAt(client());
    await settledScreen();

    const figures = all("[data-chart-panel]");
    expect(figures.map((f) => f.dataset.chartPanel)).toEqual([
      "pv",
      "load-load-clinic",
      "load-load-res",
      "load-load-mill",
      "soc-battery",
      "battery-power",
      "generator-output",
      "fuel-fuel-tank",
      "state-generator",
    ]);
    // Every panel holds a drawing, and every drawing sits in its own region.
    expect(all(".history-chart__scroll svg")).toHaveLength(figures.length);
    // The mill's panel draws each recorded step once for each of its series.
    for (const id of ["demand", "served", "unserved"]) {
      const path = panel("load-load-mill").querySelector<SVGElement>(
        `[data-chart-series="${id}"]`,
      );
      expect(path?.getAttribute("data-points")).toBe(String(HISTORY.intervals.length));
    }
    // It opens at the last recorded boundary, on every chart at once.
    expect(
      new Set(all("[data-chart-cursor]").map((c) => c.getAttribute("data-chart-cursor"))),
    ).toEqual(new Set(["150"]));
  });

  it("shows gaps with a glyph and an outcome in words, not by colour", async () => {
    renderAt(client());
    await settledScreen();

    const status = panel("state-generator");
    expect(
      all("[data-chart-missing]", status).map(
        (g) => `${g.getAttribute("data-offset")}:${g.getAttribute("data-chart-missing")}`,
      ),
    ).toEqual(["60:SUPPRESSED_BY_GAP", "75:SUPPRESSED_BY_GAP", "135:DROPPED"]);
    expect(all("[data-chart-reported-run]", status).map((r) => r.getAttribute("data-chart-reported-run"))).toEqual([
      "0-45",
      "90-120",
      "150-150",
    ]);
    expect(
      all("[data-legend-outcome]", status).map((l) => l.textContent),
    ).toEqual(["□Due, no reading: SUPPRESSED_BY_GAP", "×Due, no reading: DROPPED"]);
    // The first boundary's interval signals have no reading, stated as such.
    expect(
      all("[data-chart-missing]", panel("pv")).map((g) => g.getAttribute("data-chart-missing")),
    ).toEqual(["NO_PRECEDING_INTERVAL"]);
  });

  it("moves one shared selection by keyboard-operable control, and executes nothing", async () => {
    const runSetup = client();
    const step = vi.spyOn(runSetup, "stepExecution");
    const toEnd = vi.spyOn(runSetup, "runExecutionToEnd");
    const start = vi.spyOn(runSetup, "startExecution");
    renderAt(runSetup);
    await settledScreen();

    cursorTo(80);
    expect(
      new Set(all("[data-chart-cursor]").map((c) => c.getAttribute("data-chart-cursor"))),
    ).toEqual(new Set(["80"]));
    // The boundary inspector below follows the same selection.
    expect(
      document.querySelector("[data-history-selected]")?.getAttribute("data-history-selected"),
    ).toBe("80");
    expect(document.querySelector("[data-cursor-offset]")?.textContent).toContain(
      "2026-09-22T04:20:00Z",
    );
    // T025e: one cursor - the raw records have no boundary select of their
    // own; the Applied timeline drives the charts the other way.
    expect(document.querySelector("[data-history-boundary-select]")).toBeNull();
    fireEvent.click(rtl.getByLabelText("The whole recorded run"));
    fireEvent.click(
      document.querySelector('[data-timeline-go="40"]') as HTMLButtonElement,
    );
    expect(
      new Set(all("[data-chart-cursor]").map((c) => c.getAttribute("data-chart-cursor"))),
    ).toEqual(new Set(["40"]));
    expect(step).not.toHaveBeenCalled();
    expect(toEnd).not.toHaveBeenCalled();
    expect(start).not.toHaveBeenCalled();
  });

  it("states what each exact value describes at the selected boundary", async () => {
    renderAt(client());
    await settledScreen();

    cursorTo(80);
    const ended = HISTORY.intervals.find((i) => i.to_offset === 80)!;
    const mill = ended.loads.find((l) => l.address === "load-demand@load-mill")!;
    // The chart's value is the recorded one, for the step that ended here.
    const unserved = valueRow("load-load-mill-unserved");
    expect(unserved.textContent).toContain("step [75, 80) that ended here");
    expect(unserved.querySelector("[data-exact]")?.getAttribute("data-exact")).toBe(
      mill.unserved_power,
    );
    expect(mill.unserved_power).not.toBe("0");
    // A control accepted here governs the step that begins here.
    expect(valueRow("soc-battery-stop-threshold").textContent).toContain(
      "step [80, 85) that begins here",
    );
    expect(
      valueRow("soc-battery-stop-threshold").querySelector("[data-exact]")?.getAttribute("data-exact"),
    ).toBe("60");
    // A stale reading keeps its source time, and a not-due instant is cadence.
    const status = valueRow("state-generator-generator-controller-status");
    expect(status.querySelector("[data-reading-not-due]")?.textContent).toContain(
      "from source time 2026-09-22T03:45:00Z (STALE)",
    );
  });

  it("keeps state at T apart from state over the step, at a transition", async () => {
    renderAt(client());
    await settledScreen();

    cursorTo(40);
    expect(
      valueRow("state-generator-at").querySelector("[data-discrete]")?.textContent,
    ).toBe("STOPPED");
    expect(
      valueRow("state-generator-for-step").querySelector("[data-discrete]")?.textContent,
    ).toBe("STARTING");
  });

  it("leaves the first interval absent and keeps a reported zero apart from no reading", async () => {
    renderAt(client());
    await settledScreen();

    cursorTo(0);
    const accepted = valueRow("pv-pv-to-load");
    expect(accepted.textContent).toContain("absent: no interval has completed yet");
    expect(accepted.querySelector("[data-exact]")).toBeNull();
    const reportedAtZero = valueRow("pv-pv-inverter-controller-ac-power");
    expect(reportedAtZero.querySelector("[data-reading-missing]")?.getAttribute(
      "data-reading-missing",
    )).toBe("NO_PRECEDING_INTERVAL");

    cursorTo(15);
    const reportedZero = valueRow("pv-pv-inverter-controller-ac-power");
    expect(reportedZero.querySelector("[data-reading-quality]")?.getAttribute(
      "data-reading-quality",
    )).toBe("GOOD");
    expect(reportedZero.querySelector("[data-exact]")?.getAttribute("data-exact")).toBe("0");
  });

  it("says a family was not recorded and draws nothing from it", async () => {
    const legacy: RunHistory = {
      ...HISTORY,
      source: "LEGACY_ARTIFACT",
      samples: [],
      intervals: [],
      attempts: [],
      coverage: HISTORY.coverage.map((c) => ({
        ...c,
        availability: "UNAVAILABLE",
        availability_statement: "This artifact was written before history was recorded.",
      })),
    };
    renderAt(client({ status: "loaded", history: legacy }));
    await settledScreen();

    const notes = document.querySelector("[data-charts-unavailable]")?.textContent ?? "";
    expect(notes).toContain("state_samples is UNAVAILABLE");
    expect(notes).toContain("intervals is UNAVAILABLE");
    expect(document.querySelector('[data-chart-panel="load-load-mill"]')).toBeNull();
    expect(document.querySelector('[data-chart-panel="soc-battery"]')).toBeNull();
  });
});

describe("the run header", () => {
  it("keeps identity, position, outcome, recorded coverage and stage apart", async () => {
    renderAt(client());
    await settledScreen();

    const header = document.querySelector('[aria-labelledby="run-header-heading"]') as HTMLElement;
    expect(header.querySelector("[data-header-run]")?.textContent).toBe(
      `${RUN_ID} on Site KOBO-001`,
    );
    expect(header.querySelector("[data-header-window]")?.textContent).toBe(
      "2026-09-22T03:00:00Z to 2026-09-22T11:00:00Z",
    );
    expect(header.querySelector("[data-header-timestep]")?.getAttribute("data-header-timestep")).toBe("5");
    // The port's counts, not a count of samples.
    expect(header.querySelector("[data-header-boundaries]")?.textContent).toBe(
      `${EXECUTION.boundaries_completed} of ${EXECUTION.boundaries_total} completed`,
    );
    expect(header.querySelector("[data-header-execution]")?.getAttribute("data-header-execution")).toBe("RUNNING");
    expect(header.querySelector("[data-header-history]")?.textContent).toContain(
      "LIVE_SESSION: 31 of 97 boundaries recorded through offset 150 min; families recorded 5 of 5; read from the live session, so no persisted digest is claimed",
    );
    expect(header.querySelector("[data-header-stage]")?.getAttribute("data-header-stage")).toBe("NOT_STAGED");
    expect(header.textContent).toContain(String(EXECUTION.seed));
    expect(header.textContent).toContain("publication simulator-lab-publication v4");
  });
});
