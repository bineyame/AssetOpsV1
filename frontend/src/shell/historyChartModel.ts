/**
 * The chart model of one run's recorded Lab history (T025c phase 2).
 *
 * Every value here is a recorded one, read off the history alone (T025e: no
 * longer the execution projection's steps). Nothing is resolved, interpolated or filled:
 * this module decides only WHERE a recorded value is drawn and what it is
 * called, and it keeps the exact text beside the number it plots so an
 * inspector can show what was recorded rather than what was drawn.
 *
 * Three temporal kinds, kept apart because they mean different things:
 *
 * - an INSTANT value is state at a boundary, after that instant's events
 *   (a stock, a discrete state at T);
 * - an INTERVAL value describes one resolved step `[from, to)` - a mean power,
 *   a load's service - and is drawn across that step, never as a point;
 * - a GOVERNING value is a control accepted at T that holds over the step that
 *   begins at T (the effective reserve, a policy threshold).
 *
 * A reported value is drawn once, at its own source time. A due attempt that
 * produced no reading breaks the reported trace; an instant where the signal
 * was not due has no attempt at all and breaks nothing.
 */

import type {
  RunHistory,
  RunHistoryAttempt,
  RunHistorySignal,
} from "./runHistory";

/** A number for plotting only. The exact text always travels beside it. */
export function plotted(exact: string): number {
  const ratio = /^(-?\d+)\/(\d+)$/.exec(exact);
  if (ratio !== null) {
    return Number(ratio[1]) / Number(ratio[2]);
  }
  return Number(exact);
}

export interface InstantPoint {
  offset: number;
  value: number;
  exact: string;
}

export interface IntervalValue {
  from: number;
  to: number;
  value: number;
  exact: string;
}

/** Which categorical slot and dash pattern a series wears: never colour alone. */
export interface SeriesStyle {
  slot: 1 | 2 | 3 | 4;
  dash: "solid" | "dashed" | "dotted" | "dashdot";
}

export type TruthSeries =
  | ({
      kind: "instant";
      id: string;
      label: string;
      points: InstantPoint[];
    } & SeriesStyle)
  | ({
      kind: "interval" | "governing";
      id: string;
      label: string;
      values: IntervalValue[];
    } & SeriesStyle);

/** One device signal's due attempts, in source-time order. */
export interface ReportedTrack {
  address: string;
  device_id: string;
  signal_id: string;
  reading_class: string;
  unit: string;
  cadence_minutes: number | null;
  attempts: RunHistoryAttempt[];
}

export interface ChartPanel {
  id: string;
  title: string;
  unit: string;
  statement: string;
  series: TruthSeries[];
  reported: ReportedTrack[];
  /** Draw a zero line: the series is signed. */
  signed: boolean;
  /**
   * T025e: a value range the frozen inputs declare (state of charge 0-100 %,
   * a held rating), or absent when none is declared and the axis ratchets.
   */
  bound?: { min: number; max: number };
}

export interface StateRun {
  from: number;
  to: number;
  value: string;
}

export interface StateLane {
  id: string;
  label: string;
  /** POST_EVENT: state at T. FOR_STEP: state over `[T, T + dt)`. */
  phase: "POST_EVENT" | "FOR_STEP";
  runs: StateRun[];
}

export interface StatePanel {
  id: string;
  title: string;
  address: string;
  lanes: StateLane[];
  reported: ReportedTrack[];
}

export interface ChartModel {
  /** The window drawn: the whole run, so an unrecorded remainder is visible. */
  domain: [number, number];
  timestep: number;
  panels: ChartPanel[];
  states: StatePanel[];
  /** Reported signals no panel pairs with a recorded quantity. */
  unpaired: ReportedTrack[];
}

function component(address: string): string {
  const at = address.lastIndexOf("@");
  return at < 0 ? address : address.slice(at + 1);
}

function stateKey(address: string): string {
  const at = address.lastIndexOf("@");
  return at < 0 ? address : address.slice(0, at);
}

function tracks(history: RunHistory): ReportedTrack[] {
  const bySignal = new Map<string, ReportedTrack>();
  const cadence = new Map<string, RunHistorySignal>();
  for (const signal of history.signals) {
    cadence.set(`${signal.device_id}|${signal.signal_id}|${signal.address}`, signal);
  }
  for (const attempt of history.attempts) {
    const key = `${attempt.device_id}|${attempt.signal_id}|${attempt.address}`;
    let track = bySignal.get(key);
    if (track === undefined) {
      track = {
        address: attempt.address,
        device_id: attempt.device_id,
        signal_id: attempt.signal_id,
        reading_class: attempt.reading_class,
        unit: attempt.canonical_unit,
        cadence_minutes: cadence.get(key)?.cadence_minutes ?? null,
        attempts: [],
      };
      bySignal.set(key, track);
    }
    track.attempts.push(attempt);
  }
  for (const track of bySignal.values()) {
    track.attempts.sort((a, b) => a.at_offset_minutes - b.at_offset_minutes);
  }
  return [...bySignal.values()];
}

/**
 * One recorded flow's mean power over each step, read as the host recorded
 * it: never summed with another flow here, so the curve is the record's own.
 */
function fromFlow(history: RunHistory, flowId: string): IntervalValue[] {
  return history.intervals.flatMap((interval) =>
    interval.flows
      .filter((flow) => flow.flow_id === flowId)
      .map((flow) => ({
        from: interval.from_offset,
        to: interval.to_offset,
        exact: flow.mean_power,
        value: plotted(flow.mean_power),
      })),
  );
}

/** The largest value a frozen input holds under `name`, or null. */
function heldRating(history: RunHistory, name: string): number | null {
  const values = history.intervals
    .flatMap((interval) =>
      interval.view
        .filter((entry) => entry.name === name && entry.value !== null)
        .map((entry) => plotted(entry.value ?? "")),
    )
    .filter((v) => Number.isFinite(v) && v > 0);
  return values.length === 0 ? null : Math.max(...values);
}

/**
 * Build the chart model from what was recorded - the history alone.
 *
 * T025e (closes carry C3): no per-step execution data reaches a chart, so no
 * curve can run ahead of the history the others are drawn from. PV and the
 * battery are drawn as the host's own recorded flows, one curve per flow;
 * nothing is summed or recomputed here.
 */
export function chartModel(
  history: RunHistory,
  timestepMinutes: number | null,
): ChartModel {
  const offsets = history.boundaries.map((b) => b.offset_minutes);
  const timestep =
    timestepMinutes ??
    (offsets.length > 1 ? offsets[1] - offsets[0] : 1);
  const end = Math.max(
    (history.boundaries_total - 1) * timestep,
    offsets[offsets.length - 1] ?? 0,
    timestep,
  );
  const all = tracks(history);
  const used = new Set<ReportedTrack>();
  const claim = (match: (track: ReportedTrack) => boolean) => {
    const found = all.filter((track) => !used.has(track) && match(track));
    found.forEach((track) => used.add(track));
    return found;
  };

  const panels: ChartPanel[] = [];

  const pvPotential = fromFlow(history, "pv_potential");
  if (pvPotential.length > 0) {
    panels.push({
      id: "pv",
      title: "PV power",
      unit: "kW",
      statement:
        "Mean power over each step, one curve per recorded flow. Potential is what the array offered; the inverter delivered the rest to loads and to the battery; curtailed was refused by the controller and clipped exceeded the inverter's rating - two different losses.",
      signed: false,
      series: [
        { kind: "interval", id: "pv-potential", label: "Potential", slot: 1, dash: "dashed", values: pvPotential },
        { kind: "interval", id: "pv-to-load", label: "To loads", slot: 2, dash: "solid", values: fromFlow(history, "pv_to_load") },
        { kind: "interval", id: "pv-to-battery", label: "To the battery", slot: 2, dash: "dashdot", values: fromFlow(history, "pv_to_battery") },
        { kind: "interval", id: "pv-curtailed", label: "Curtailed", slot: 3, dash: "dotted", values: fromFlow(history, "curtailed_pv") },
        { kind: "interval", id: "pv-clipped", label: "Clipped", slot: 4, dash: "dashdot", values: fromFlow(history, "inverter_clipping") },
      ],
      reported: claim((t) => stateKey(t.address) === "pv-ac-power"),
    });
  }

  // Each load is its own panel: three loads on one axis would be nine lines,
  // and two loads with the same state key must never become one series.
  const loadAddresses: string[] = [];
  for (const interval of history.intervals) {
    for (const load of interval.loads) {
      if (!loadAddresses.includes(load.address)) {
        loadAddresses.push(load.address);
      }
    }
  }
  for (const address of loadAddresses) {
    const pick = (
      field: "demand_power" | "served_power" | "unserved_power",
    ): IntervalValue[] =>
      history.intervals.flatMap((interval) =>
        interval.loads
          .filter((load) => load.address === address)
          .map((load) => ({
            from: interval.from_offset,
            to: interval.to_offset,
            exact: load[field],
            value: plotted(load[field]),
          })),
      );
    panels.push({
      id: `load-${component(address)}`,
      title: `Load ${component(address)}`,
      unit: "kW",
      statement: `Mean power over each step at ${address}.`,
      signed: false,
      series: [
        { kind: "interval", id: "demand", label: "Demand", slot: 1, dash: "dashed", values: pick("demand_power") },
        { kind: "interval", id: "served", label: "Served", slot: 2, dash: "solid", values: pick("served_power") },
        { kind: "interval", id: "unserved", label: "Unserved", slot: 3, dash: "dotted", values: pick("unserved_power") },
      ],
      reported: claim(
        (t) =>
          stateKey(t.address) === "load-served-power" &&
          component(t.address) === component(address),
      ),
    });
  }

  const socAddresses = [
    ...new Set(
      history.samples
        .filter((s) => s.phase === "POST_EVENT" && s.unit === "%")
        .map((s) => s.address),
    ),
  ];
  const governing = (prefix: string): IntervalValue[] =>
    history.intervals.flatMap((interval) =>
      interval.effective_controls
        .filter((control) => stateKey(control.address) === prefix)
        .map((control) => ({
          from: control.from_offset,
          to: control.to_offset,
          exact: control.value,
          value: plotted(control.value),
        })),
    );
  for (const address of socAddresses) {
    const reserve = governing("battery-reserve-state-of-charge");
    const stop = governing("generator-stop-soc-threshold");
    const series: TruthSeries[] = [
      {
        kind: "instant",
        id: "soc",
        label: "State of charge at T",
        slot: 1,
        dash: "solid",
        points: history.samples
          .filter((s) => s.address === address && s.phase === "POST_EVENT")
          .map((s) => ({ offset: s.offset_minutes, exact: s.value, value: plotted(s.value) })),
      },
    ];
    if (reserve.length > 0) {
      series.push({ kind: "governing", id: "reserve", label: "Reserve in effect", slot: 2, dash: "dashed", values: reserve });
    }
    if (stop.length > 0) {
      series.push({ kind: "governing", id: "stop-threshold", label: "Generator stop threshold", slot: 3, dash: "dotted", values: stop });
    }
    panels.push({
      id: `soc-${component(address)}`,
      title: `Battery state of charge (${component(address)})`,
      unit: "%",
      statement:
        "State of charge sampled at each boundary after its events; lines join samples. The reserve and the stop threshold are the controls in effect over each step.",
      signed: false,
      // A state of charge is a percentage of capacity: 0-100 % is declared.
      bound: { min: 0, max: 100 },
      series,
      reported: claim((t) => t.address === address),
    });
  }

  const batteryToLoad = fromFlow(history, "battery_to_load");
  if (batteryToLoad.length > 0) {
    const series: TruthSeries[] = [
      { kind: "interval", id: "battery-to-load", label: "Discharged to loads", slot: 1, dash: "solid", values: batteryToLoad },
      { kind: "interval", id: "pv-to-battery", label: "Charged from PV", slot: 2, dash: "dashed", values: fromFlow(history, "pv_to_battery") },
    ];
    const fromGenerator = fromFlow(history, "generator_to_battery");
    if (fromGenerator.length > 0) {
      series.push({ kind: "interval", id: "generator-to-battery", label: "Charged from the generator", slot: 3, dash: "dotted", values: fromGenerator });
    }
    panels.push({
      id: "battery-power",
      title: "Battery power",
      unit: "kW",
      statement:
        "Mean AC power over each step at the battery's converter, one curve per recorded flow: what it discharged to loads and what it took in to charge.",
      signed: false,
      series,
      reported: claim((t) => stateKey(t.address) === "battery-ac-power"),
    });
  }

  const generatorOutput: IntervalValue[] = history.intervals.flatMap(
    (interval) =>
      interval.flows
        .filter((flow) => flow.flow_id === "generator_output")
        .map((flow) => ({
          from: interval.from_offset,
          to: interval.to_offset,
          exact: flow.mean_power,
          value: plotted(flow.mean_power),
        })),
  );
  const generatorRating = heldRating(history, "generator-rated-power");
  if (generatorOutput.length > 0) {
    panels.push({
      id: "generator-output",
      title: "Generator output",
      unit: "kW",
      statement: "Accepted generator output, mean power over each step.",
      signed: false,
      ...(generatorRating === null ? {} : { bound: { min: 0, max: generatorRating } }),
      series: [
        { kind: "interval", id: "generator-output", label: "Output", slot: 1, dash: "solid", values: generatorOutput },
      ],
      reported: claim((t) => stateKey(t.address) === "generator-output-power"),
    });
  }

  const fuelAddresses = [
    ...new Set(
      history.samples
        .filter((s) => s.phase === "POST_EVENT" && s.unit === "L")
        .map((s) => s.address),
    ),
  ];
  for (const address of fuelAddresses) {
    panels.push({
      id: `fuel-${component(address)}`,
      title: `Fuel (${component(address)})`,
      unit: "L",
      statement:
        "Volume in the tank at each boundary after its events; lines join samples.",
      signed: false,
      series: [
        {
          kind: "instant",
          id: "fuel",
          label: "Volume at T",
          slot: 1,
          dash: "solid",
          points: history.samples
            .filter((s) => s.address === address && s.phase === "POST_EVENT")
            .map((s) => ({ offset: s.offset_minutes, exact: s.value, value: plotted(s.value) })),
        },
      ],
      reported: claim((t) => t.address === address),
    });
  }

  const stateAddresses = [
    ...new Set(
      history.samples.filter((s) => s.unit === "state").map((s) => s.address),
    ),
  ];
  const states: StatePanel[] = stateAddresses.map((address) => {
    const lane = (phase: "POST_EVENT" | "FOR_STEP"): StateLane => {
      const samples = history.samples.filter(
        (s) => s.address === address && s.phase === phase,
      );
      const runs: StateRun[] = [];
      for (const sample of samples) {
        const to =
          phase === "FOR_STEP"
            ? sample.offset_minutes + timestep
            : sample.offset_minutes;
        const last = runs[runs.length - 1];
        if (
          last !== undefined &&
          last.value === sample.value &&
          sample.offset_minutes - (phase === "FOR_STEP" ? last.to : last.to + timestep) === 0
        ) {
          last.to = to;
        } else {
          runs.push({ from: sample.offset_minutes, to, value: sample.value });
        }
      }
      return {
        id: phase === "POST_EVENT" ? "at" : "for-step",
        label: phase === "POST_EVENT" ? "Physical state at T" : "State over the step from T",
        phase,
        runs,
      };
    };
    return {
      id: `state-${component(address)}`,
      title: `Generator state (${component(address)})`,
      address,
      lanes: [lane("POST_EVENT"), lane("FOR_STEP")],
      reported: claim((t) => t.address === address),
    };
  });

  return {
    domain: [0, end],
    timestep,
    panels,
    states,
    unpaired: all.filter((track) => !used.has(track)),
  };
}

/**
 * The reported trace as unbroken runs of REPORTED attempts.
 *
 * A due attempt that produced no reading ends a run; the next reading starts a
 * new one. Instants where the signal was not due have no attempt and so never
 * split a run: sparse is not missing.
 */
export function reportedRuns(track: ReportedTrack): RunHistoryAttempt[][] {
  const runs: RunHistoryAttempt[][] = [];
  let current: RunHistoryAttempt[] = [];
  for (const attempt of track.attempts) {
    if (attempt.outcome === "REPORTED" && attempt.reported_value !== null) {
      current.push(attempt);
    } else if (current.length > 0) {
      runs.push(current);
      current = [];
    }
  }
  if (current.length > 0) {
    runs.push(current);
  }
  return runs;
}

export type ReadingAt =
  | { kind: "reported"; attempt: RunHistoryAttempt }
  | { kind: "missing"; attempt: RunHistoryAttempt; last: RunHistoryAttempt | null }
  | { kind: "not_due"; last: RunHistoryAttempt | null };

/**
 * What a consumer of one signal held at T, by the transform's own rule.
 *
 * `a-retained-reading-carries-its-own-time`: the newest reading at or before T
 * is the one held, GOOD when it is from T and STALE when it is older, and it
 * keeps its own source time. This reads the recorded attempts; it does not
 * decide anything the transform did not.
 */
export function readingAt(track: ReportedTrack, offset: number): ReadingAt {
  const upTo = track.attempts.filter((a) => a.at_offset_minutes <= offset);
  const here = upTo.find((a) => a.at_offset_minutes === offset);
  const published = upTo.filter(
    (a) => a.outcome === "REPORTED" && a.reported_value !== null,
  );
  const last = published.length === 0 ? null : published[published.length - 1];
  if (here === undefined) {
    return { kind: "not_due", last };
  }
  if (here.outcome === "REPORTED" && here.reported_value !== null) {
    return { kind: "reported", attempt: here };
  }
  return { kind: "missing", attempt: here, last };
}
