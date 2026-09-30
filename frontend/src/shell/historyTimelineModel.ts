import type {
  RunHistory,
  RunHistoryAppliedEvent,
  RunHistorySample,
} from "./runHistory";

/**
 * The applied timeline of a recorded run (T025d, Lab cockpit C3). Pure.
 *
 * Three lanes that are never merged: what the run's ledger APPLIED (scenario
 * events, model-law contributions and the forcing levels in effect), the
 * PHYSICAL transitions that followed (bounded and discrete), and REPORTING
 * conditions and attempts. A reporting gap sits in its own lane because it is
 * not a physical outage: the state it hides went on regardless.
 *
 * Everything here is read from the ledger. There is no planned lane: a frozen
 * event the run never reached is not in `applied_events`, so nothing here can
 * label a plan as applied.
 *
 * Phases are the execution contract's boundary-cycle phases. What each one
 * governs is stated per entry, and a discrete transition is checked against
 * the recorded state sample it should show up in, so the reader sees the
 * agreement rather than being told it.
 */

export type TimelineLane = "APPLIED" | "PHYSICAL" | "REPORTING";

export const LANE_HEADINGS: Record<TimelineLane, string> = {
  APPLIED: "Applied scenario and model events",
  PHYSICAL: "Physical transitions: bounded and discrete",
  REPORTING: "Reporting conditions and attempts",
};

export interface TimelineEntry {
  key: string;
  lane: TimelineLane;
  kind: string;
  /** The cause's identity: an event id, a bound case, a device and signal. */
  source: string;
  address: string;
  phase: string | null;
  origin: string | null;
  share: string | null;
  /** `[from, to)` in minutes; `from === to` is an instant. */
  span: [number, number];
  /** Which state or step the entry governs, in words. */
  applies: string;
  detail: string;
  /** For a discrete transition: whether the recorded sample shows it. */
  agrees: boolean | null;
  /** How many recorded rows this entry stands for (whole-run grouping). */
  count: number;
}

function stepEnd(history: RunHistory, at: number): number | null {
  return history.intervals.find((i) => i.from_offset === at)?.to_offset ?? null;
}

/** What a boundary-cycle phase governs, in words. */
export function phaseApplies(
  history: RunHistory,
  phase: string,
  at: number,
): string {
  if (phase === "apply-events") {
    return `state at ${at} min, after that instant's events`;
  }
  if (phase === "physical-acceptance") {
    return `the step beginning at ${at} min (state for the step)`;
  }
  if (phase === "evolve") {
    const end = stepEnd(history, at);
    return end === null
      ? `accumulated over the step beginning at ${at} min`
      : `accumulated over [${at}, ${end}) min, reached in the state at ${end} min`;
  }
  return `phase ${phase} at ${at} min`;
}

function appliedSpan(history: RunHistory, event: RunHistoryAppliedEvent): [number, number] {
  if (event.phase_id === "evolve") {
    return [event.at_offset_minutes, stepEnd(history, event.at_offset_minutes) ?? event.at_offset_minutes];
  }
  return [event.at_offset_minutes, event.at_offset_minutes];
}

/** The sample a discrete transition of this phase must show up in. */
function witness(
  history: RunHistory,
  address: string,
  phase: string,
  at: number,
): RunHistorySample | null {
  const samplePhase =
    phase === "apply-events"
      ? "POST_EVENT"
      : phase === "physical-acceptance"
        ? "FOR_STEP"
        : null;
  if (samplePhase === null) return null;
  return (
    history.samples.find(
      (s) =>
        s.offset_minutes === at &&
        s.address === address &&
        s.phase === samplePhase,
    ) ?? null
  );
}

/** Every recorded entry, ungrouped, in ledger order within each family. */
function allEntries(history: RunHistory): TimelineEntry[] {
  const entries: TimelineEntry[] = [];

  history.applied_events.forEach((e, index) => {
    entries.push({
      key: `applied-${index}`,
      lane: "APPLIED",
      kind: e.origin === "ACCEPTED_FLOW" ? "Model-law contribution" : "Applied event",
      source: e.event_id,
      address: e.address,
      phase: e.phase_id,
      origin: e.origin,
      share: e.share,
      span: appliedSpan(history, e),
      applies: phaseApplies(history, e.phase_id, e.at_offset_minutes),
      detail: `${e.direction}, share ${e.share} of declared ${e.declared}`,
      agrees: null,
      count: 1,
    });
  });

  history.exposures.forEach((x, index) => {
    entries.push({
      key: `exposure-${index}`,
      lane: "APPLIED",
      kind: "Forcing level in effect",
      source: `${x.event_id} (${x.parameter_id})`,
      address: x.address,
      phase: null,
      origin: "SCENARIO",
      share: null,
      span: [x.from_offset, x.to_offset],
      applies: `the level over [${x.from_offset}, ${x.to_offset}) min`,
      detail: `value ${x.value}`,
      agrees: null,
      count: 1,
    });
  });

  history.bounded_transitions.forEach((t, index) => {
    const contribution = history.applied_events.find(
      (e) =>
        e.at_offset_minutes === t.at_offset_minutes &&
        e.address === t.address &&
        t.event_ids.includes(e.event_id),
    );
    const phase = contribution?.phase_id ?? null;
    entries.push({
      key: `bounded-${index}`,
      lane: "PHYSICAL",
      kind: "Bounded transition",
      source: t.bound_case_id,
      address: t.address,
      phase,
      origin: null,
      share: null,
      span:
        contribution === undefined
          ? [t.at_offset_minutes, t.at_offset_minutes]
          : appliedSpan(history, contribution),
      applies:
        phase === null
          ? `at ${t.at_offset_minutes} min`
          : phaseApplies(history, phase, t.at_offset_minutes),
      detail: `${t.bound_kind} ${t.bound_value}: requested ${t.requested}, accepted ${t.accepted}, refused ${t.refused} (events ${t.event_ids.join(", ")})`,
      agrees: null,
      count: 1,
    });
  });

  history.discrete_transitions.forEach((t, index) => {
    const sample = witness(history, t.address, t.phase, t.at_offset_minutes);
    entries.push({
      key: `discrete-${index}`,
      lane: "PHYSICAL",
      kind: "Discrete transition",
      source: t.state_key,
      address: t.address,
      phase: t.phase,
      origin: null,
      share: null,
      span: [t.at_offset_minutes, t.at_offset_minutes],
      applies: phaseApplies(history, t.phase, t.at_offset_minutes),
      detail:
        `${t.previous} to ${t.next}: ${t.cause}` +
        (sample === null
          ? ""
          : `. Recorded ${sample.phase} sample at ${t.at_offset_minutes} min: ${String(sample.value)}`),
      agrees: sample === null ? null : sample.value === t.next,
      count: 1,
    });
  });

  history.reporting_gaps.forEach((g, index) => {
    entries.push({
      key: `gap-${index}`,
      lane: "REPORTING",
      kind: "Reporting condition",
      source: `${g.event_id}: ${g.device_id} ${g.signal_id}`,
      address: g.address,
      phase: null,
      origin: g.timing_shape,
      share: null,
      span: [g.start_offset_minutes, g.end_offset_minutes],
      applies: `readings of ${g.address} over [${g.start_offset_minutes}, ${g.end_offset_minutes}) min`,
      detail:
        "The reporting path carries no reading; the physical state it would have described is unaffected.",
      agrees: null,
      count: 1,
    });
  });

  history.attempts.forEach((a, index) => {
    entries.push({
      key: `attempt-${index}`,
      lane: "REPORTING",
      kind: "Observation attempt",
      source: `${a.device_id} ${a.signal_id}`,
      address: a.address,
      phase: null,
      origin: a.outcome,
      share: null,
      span: [a.at_offset_minutes, a.at_offset_minutes],
      applies:
        a.reading_class === "INTERVAL_SIGNAL"
          ? `source time ${a.source_sample_time}; an interval reading of the step that ended there`
          : `source time ${a.source_sample_time}; state at that instant`,
      detail:
        a.reported_value === null
          ? `no reading: ${a.suppression_reason ?? a.outcome}`
          : `reported ${a.reported_value} ${a.canonical_unit}`,
      agrees: null,
      count: 1,
    });
  });

  return entries;
}

/**
 * The entries that bear on one selected boundary T and the interval
 * `[T - dt, T)` that ended there: everything at the instant T, the
 * interval-wide causes of that interval (its evolution contributions and the
 * forcing levels over it), the step decision that governed it, and the
 * reporting conditions and attempts touching it.
 */
export function intervalTimeline(
  history: RunHistory,
  offset: number,
): TimelineEntry[] {
  const interval = history.intervals.find((i) => i.to_offset === offset) ?? null;
  const start = interval?.from_offset ?? null;
  return allEntries(history).filter((entry) => {
    const [from, to] = entry.span;
    if (entry.lane === "REPORTING" && entry.kind === "Reporting condition") {
      return from <= offset && to > (start ?? offset - 1);
    }
    if (entry.kind === "Observation attempt") return from === offset;
    if (from === to) {
      // An instant: at T, or the step decision at the interval's start.
      return (
        from === offset ||
        (start !== null && from === start && entry.phase === "physical-acceptance")
      );
    }
    // A span: it overlaps the interval that ended at T.
    return start !== null && from < offset && to > start;
  });
}

function signature(entry: TimelineEntry): string {
  return [
    entry.lane,
    entry.kind,
    entry.source,
    entry.address,
    entry.phase ?? "",
    entry.origin ?? "",
    entry.detail,
  ].join("|");
}

/**
 * The whole run, with contiguous repeats of one cause grouped into one span.
 *
 * Grouping is visual only: a group keeps its full span, its row count and
 * every distinct share it stood for, so an interval-wide cause stays
 * inspectable. Successful observation attempts are left out of this view -
 * they are in the charts and at each boundary - and every other attempt stays.
 */
export function runTimeline(history: RunHistory): TimelineEntry[] {
  const groups: TimelineEntry[] = [];
  const open = new Map<string, { entry: TimelineEntry; shares: Set<string> }>();
  const entries = allEntries(history)
    .filter((e) => !(e.kind === "Observation attempt" && e.origin === "REPORTED"))
    .sort((a, b) => a.span[0] - b.span[0]);

  for (const entry of entries) {
    const key = signature(entry);
    const current = open.get(key);
    const spans = entry.span[1] > entry.span[0];
    if (current !== undefined && spans && current.entry.span[1] === entry.span[0]) {
      current.entry.span = [current.entry.span[0], entry.span[1]];
      current.entry.count += 1;
      if (entry.share !== null) current.shares.add(entry.share);
      current.entry.share = [...current.shares].join(", ");
      continue;
    }
    const copy = { ...entry, span: [...entry.span] as [number, number] };
    groups.push(copy);
    open.set(key, {
      entry: copy,
      shares: new Set(entry.share === null ? [] : [entry.share]),
    });
  }
  for (const group of groups) {
    if (group.count > 1) {
      group.applies = `each step over [${group.span[0]}, ${group.span[1]}) min (${group.count} recorded rows)`;
    }
  }
  return groups;
}
