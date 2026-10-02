import { fireEvent, render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { chartModel } from "../historyChartModel";
import { intervalTimeline, runTimeline } from "../historyTimelineModel";
import { appendHistory, type AppendResult } from "../liveHistory";
import {
  isRunHistory,
  type RunHistory,
  type RunHistoryDeltaEnvelope,
} from "../runHistory";
import type {
  RunSetupClient,
  RunStage,
  RunStagedEnvelope,
  RunSummary,
} from "../runSetupClient";
import {
  RUNNING_IN_THE_GAP,
  STAGED_IN_THE_GAP,
  executionMethods,
} from "./executionFixtures";
import wire from "./kobo-degraded-evidence-deltas.json";

/**
 * T026 on the screen: records, a held publication and a sensor gap (AC10,
 * AC13 screen side, T025d C2).
 *
 * `kobo-degraded-evidence-deltas.json` is written by
 * `host/tests/make_history_fixtures.py` (`degraded_evidence_deltas`): the
 * degraded-evidence recipe (publication profile 5) - its state of charge
 * sampled at 240 is held by a publication delay and released at 250, its
 * discharge capability is silenced over [180, 240), its override record at
 * 120 is suppressed - as the backend's full read after start, one delta to
 * 235, single-step deltas through 255 and the full read. Nothing is edited
 * after serialization.
 */

interface DeltaRead {
  history: RunHistory;
  delta: RunHistoryDeltaEnvelope;
}

const fixture = wire as unknown as {
  base: RunHistory;
  deltas: DeltaRead[];
  full: RunHistory;
};
const FULL = fixture.full;
const SOC = { device_id: "battery-pcs-controller", signal_id: "state-of-charge" };

function copy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function accepted(result: AppendResult): RunHistory {
  if ("refused" in result) {
    throw new Error(`refused: ${result.refused.reason} ${result.refused.statement}`);
  }
  return result.ok;
}

/** The base folded with the first `count` deltas. */
function foldedThrough(count: number): RunHistory {
  let held = copy(fixture.base);
  for (const read of fixture.deltas.slice(0, count)) {
    held = accepted(appendHistory(held, copy(read.history), read.delta));
  }
  return held;
}

describe("history schema 3 on the live-follow wire (AC13)", () => {
  it("the fixture holds both new families, and every read is a history", () => {
    expect(FULL.history_schema_version).toBe(3);
    expect(FULL.records.length).toBeGreaterThan(0);
    expect(FULL.publications).toHaveLength(1);
    for (const read of [fixture.base, ...fixture.deltas.map((d) => d.history), FULL]) {
      expect(isRunHistory(read)).toBe(true);
    }
  });

  it("folds records and the held publication as appended rows equal to the full read", () => {
    const folded = foldedThrough(fixture.deltas.length);
    expect(folded.records).toEqual(FULL.records);
    expect(folded.publications).toEqual(FULL.publications);
    expect(folded.attempts).toEqual(FULL.attempts);
    expect(folded.coverage).toEqual(FULL.coverage);
  });

  it("carries the release once, in the delta of the boundary that released it", () => {
    const carrying = fixture.deltas.filter((d) => d.history.publications.length > 0);
    expect(carrying).toHaveLength(1);
    const [read] = carrying;
    const release = read.history.boundaries[read.history.boundaries.length - 1];
    expect(release.offset_minutes).toBe(250);
    expect(read.history.publications[0].released_offset_minutes).toBe(250);
    // Still held at 245: no row yet, so nothing can be read as published.
    expect(foldedThrough(fixture.deltas.indexOf(read)).publications).toEqual([]);
  });

  it("refuses a delta whose publication row is keyed before what is held", () => {
    const held = foldedThrough(fixture.deltas.length - 1);
    const last = fixture.deltas[fixture.deltas.length - 1];
    const forged = copy(last.history);
    forged.publications = [{ ...FULL.publications[0], released_offset_minutes: 240 }];
    const result = appendHistory(held, forged, last.delta);
    expect("refused" in result && result.refused.reason).toBe("ROW_NOT_AFTER_RECORDED");
  });
});

describe("the applied timeline (AC13 markers, T025d C2)", () => {
  it("shows a declared gap only as far as the run has recorded", () => {
    const gap = FULL.reporting_gaps[0];
    expect([gap.start_offset_minutes, gap.end_offset_minutes]).toEqual([180, 240]);
    const kinds = (history: RunHistory) =>
      runTimeline(history).filter((e) => e.kind === "Reporting condition");

    // At start the gap is declared but unreached: not shown as applied.
    expect(fixture.base.reporting_gaps).toHaveLength(1);
    expect(kinds(fixture.base)).toEqual([]);
    // Part way in it has begun: clipped to the recorded extent.
    const partWay = foldedThrough(1);
    const through = partWay.recorded_through_offset_minutes ?? 0;
    expect(through).toBeGreaterThan(180);
    expect(through).toBeLessThan(240);
    expect(kinds(partWay).map((e) => e.span)).toEqual([[180, through]]);
    expect(kinds(partWay)[0].applies).toContain(
      `through the recorded extent at ${through} min`,
    );
    // Once passed, it is its whole window.
    expect(kinds(FULL).map((e) => e.span)).toEqual([[180, 240]]);
  });

  it("puts the held publication at its source boundary and at its release", () => {
    const delay = (offset: number) =>
      intervalTimeline(FULL, offset).filter((e) => e.kind === "Publication delay");
    expect(delay(240)).toHaveLength(1);
    expect(delay(250)).toHaveLength(1);
    expect(delay(245)).toHaveLength(0);
    const [entry] = delay(250);
    expect(entry.span).toEqual([240, 250]);
    expect(entry.applies).toBe(
      "source time 2026-09-22T07:00:00Z; published 2026-09-22T07:10:03Z",
    );
    expect(entry.detail).toContain("Held 10 min");
    expect(entry.detail).toContain("Not a sensor gap");
  });

  it("marks records at their occurrence, and a suppressed one as none observed", () => {
    const policies = intervalTimeline(FULL, 0).filter((e) => e.kind === "Policy record");
    expect(policies.length).toBe(
      FULL.records.filter((r) => r.family === "POLICY").length,
    );
    expect(policies.every((e) => e.origin === "REPORTED")).toBe(true);
    expect(policies[0].applies).toMatch(/^occurred .*; effective from /);
    const [override] = intervalTimeline(FULL, 120).filter(
      (e) => e.kind === "Operational record",
    );
    expect(override.origin).toBe("SUPPRESSED_BY_GAP");
    expect(override.detail).toContain("None observed");
    expect(override.detail).toContain("never establishes that nothing was commanded");
  });
});

describe("the day curves (AC15)", () => {
  it("joins the capability tracks to the PV and battery curves", () => {
    const model = chartModel(FULL, 5);
    const panel = (id: string) => model.panels.find((p) => p.id === id);
    expect(panel("battery-power")?.reported.map((t) => t.signal_id)).toContain(
      "discharge-capability",
    );
    expect(
      model.panels
        .find((p) => p.reported.some((t) => t.signal_id === "available-power"))
        ?.reported.map((t) => t.signal_id),
    ).toContain("ac-power");
    expect(model.unpaired.map((t) => t.signal_id)).not.toContain("available-power");
    expect(model.unpaired.map((t) => t.signal_id)).not.toContain("discharge-capability");
  });
});

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const RUN: RunSummary = {
  run_id: FULL.run_id,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-mini-grid-degraded-evidence",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
  template_lineage: { state: "RECORDED", template_id: "hybrid-mini-grid-100kw", template_version: 3 },
};

function renderReloaded(history: RunHistory, stage: RunStage = STAGED_IN_THE_GAP) {
  const runSetup: RunSetupClient = {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: RUN }),
    ...executionMethods(
      { status: "loaded", execution: RUNNING_IN_THE_GAP },
      { status: "loaded", stage },
      { status: "loaded", history },
    ),
  };
  return render(
    <MemoryRouter initialEntries={[`/simulator-lab/runs/${FULL.run_id}`]}>
      <App flags={featureFlagsWith(true)} siteDirectory={EMPTY_SITE_DIRECTORY} runSetup={runSetup} />
    </MemoryRouter>,
  );
}

function select(offset: number): void {
  const index = FULL.boundaries.findIndex((b) => b.offset_minutes === offset);
  const range = document.getElementById("history-cursor-range") as HTMLInputElement;
  fireEvent.change(range, { target: { value: String(index) } });
}

function attemptRow(signal: string): HTMLElement | null {
  return Array.from(
    document.querySelectorAll<HTMLElement>("[data-history-attempt]"),
  ).find((row) => row.querySelector("th")?.textContent?.endsWith(` ${signal}`)) ?? null;
}

describe("the inspector after reload tells a sensor gap from a publication delay (AC10)", () => {
  it("shows the held reading's source time, publication time and host-recorded hold", async () => {
    renderReloaded(FULL);
    await settledScreen();
    select(240);
    await settledScreen();

    const row = attemptRow(SOC.signal_id);
    expect(row?.dataset.outcome).toBe("REPORTED");
    const cell = row?.querySelector("[data-history-publication]");
    expect(cell?.getAttribute("data-history-publication")).toBe("DELAYED");
    expect(cell?.textContent).toBe(
      "Publication delay: source 2026-09-22T07:00:00Z, published 2026-09-22T07:10:03Z, held 10 min. Not a sensor gap.",
    );
  });

  it("shows a silenced reading as a sensor gap, not a delay", async () => {
    const silenced = FULL.attempts.find(
      (a) => a.signal_id === "discharge-capability" && a.outcome === "SUPPRESSED_BY_GAP",
    );
    expect(silenced).toBeDefined();
    renderReloaded(FULL);
    await settledScreen();
    select(silenced!.at_offset_minutes);
    await settledScreen();

    const row = attemptRow("discharge-capability");
    expect(row?.dataset.outcome).toBe("SUPPRESSED_BY_GAP");
    const cell = row?.querySelector("[data-history-publication]");
    expect(cell?.getAttribute("data-history-publication")).toBe("SENSOR_GAP");
    expect(cell?.textContent).not.toContain("delay:");
    // A reading published on time says no delay, rather than nothing.
    const onTime = Array.from(
      document.querySelectorAll('[data-history-attempt] [data-history-publication]'),
    ).map((cell) => cell.getAttribute("data-history-publication"));
    expect(onTime).toContain("NOT_HELD");
  });

  it("lists the release at the boundary that released it, and the records where they occurred", async () => {
    renderReloaded(FULL);
    await settledScreen();
    select(250);
    await settledScreen();
    const released = document.querySelector(
      `[data-history-released="${SOC.device_id}:${SOC.signal_id}"]`,
    );
    expect(released?.textContent).toContain("held 10 min by soc-publication-delay");

    select(120);
    await settledScreen();
    const record = document.querySelector("[data-history-record]");
    expect(record?.getAttribute("data-outcome")).toBe("SUPPRESSED_BY_GAP");
    expect(record?.textContent).toContain("none observed");
  });
});

/** One staged envelope, in the shape the stage API serves since T026. */
function envelope(
  sequence: number,
  device_id: string,
  signal_id: string,
  source_time: string,
  published_at: string,
  extra: Partial<RunStagedEnvelope> = {},
): RunStagedEnvelope {
  return {
    ...STAGED_IN_THE_GAP.envelopes[0],
    message_id: `m-${sequence}`,
    sequence,
    device_id,
    signal_id,
    source_time,
    published_at,
    family: "MEASUREMENT",
    ...extra,
  };
}

describe("the stage detail tells a sensor gap from a publication delay (AC10, AC14)", () => {
  const STAGE: RunStage = {
    ...STAGED_IN_THE_GAP,
    envelopes: [
      envelope(1, SOC.device_id, SOC.signal_id, "2026-09-22T07:00:00Z", "2026-09-22T07:10:03Z", {
        measurement: "INSTANTANEOUS",
        value: "41.5",
        unit: "%",
        quality: "GOOD",
      }),
      envelope(2, "battery-pcs-controller", "discharge-capability", "2026-09-22T06:15:00Z", "2026-09-22T06:15:03Z", {
        value: null,
        quality: "UNAVAILABLE",
        unavailable_reason: "REPORTING_PATH_UNAVAILABLE",
      }),
      envelope(3, "site-controller", "policy-reserve-soc", "2026-09-22T03:00:00Z", "2026-09-22T03:00:03Z", {
        family: "POLICY",
        measurement: "POLICY",
        quality: "RECORDED",
      }),
    ],
  };

  function show(sequence: number): HTMLElement | null {
    const button = Array.from(document.querySelectorAll("button")).find(
      (item) => item.textContent === `Show envelope ${sequence}`,
    );
    fireEvent.click(button!);
    return document.querySelector<HTMLElement>("[data-stage-selected-arrival]");
  }

  it("reads the hold from the history row and names a gap as a gap", async () => {
    renderReloaded(FULL, STAGE);
    await settledScreen();

    const delayed = show(1);
    expect(delayed?.getAttribute("data-stage-selected-arrival")).toBe("DELAYED");
    expect(delayed?.textContent).toContain("held 10 min by soc-publication-delay");
    expect(document.querySelector("[data-stage-selected-source-time]")?.textContent).toBe(
      "2026-09-22T07:00:00Z",
    );
    expect(document.querySelector("[data-stage-selected-published-at]")?.textContent).toBe(
      "2026-09-22T07:10:03Z",
    );

    const gap = show(2);
    expect(gap?.getAttribute("data-stage-selected-arrival")).toBe("SENSOR_GAP");
    expect(gap?.textContent).toContain("Not a publication delay");

    expect(show(3)?.getAttribute("data-stage-selected-arrival")).toBe("ON_TIME");
  });

  it("shows a record as a record, not as a measurement of some quality", async () => {
    renderReloaded(FULL, STAGE);
    await settledScreen();
    const qualities = Array.from(
      document.querySelectorAll("[data-staged-quality]"),
      (cell) => cell.getAttribute("data-staged-quality"),
    );
    expect(qualities).toEqual(["GOOD", "UNAVAILABLE", "RECORD"]);
    expect(document.body.textContent).toContain("POLICY record");
  });
});
