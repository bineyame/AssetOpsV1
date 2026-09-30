/**
 * Live follow (T025e): appending the history a run records while it plays.
 *
 * The Lab reads a run's whole history once, on load, and then only what each
 * tick recorded - the gated history read's `?since_boundary=n` answer, a
 * delta. This module is the one place a delta meets the history it extends.
 * It is pure: it computes no quantity, parses no value, never mutates what it
 * is given, and never repairs a delta it cannot place. A delta it refuses is
 * the caller's cue to make one full read, not to patch.
 *
 * The family classes are the backend's own (`simulator_lab_api.py`,
 * `HISTORY_APPEND_FAMILY_KEYS`): append families grow only at their end
 * (proven per boundary by `host/tests/test_lab_history_prefix.py`), static
 * families come with the full read alone, and everything else - the manifest,
 * `coverage`, `notes`, `failure` - arrives whole in each delta.
 */

import type {
  RunHistory,
  RunHistoryAppliedEvent,
  RunHistoryAttempt,
  RunHistoryBoundary,
  RunHistoryBoundedTransition,
  RunHistoryDeltaEnvelope,
  RunHistoryDiscreteTransition,
  RunHistoryInterval,
  RunHistorySample,
} from "./runHistory";

/**
 * Each append family and the time key its rows are recorded at: the offset
 * of the boundary that records the row. An interval is recorded by the
 * boundary that decided it, so it is keyed on `from_offset`.
 */
export const APPEND_FAMILY_KEYS = {
  boundaries: "offset_minutes",
  samples: "offset_minutes",
  intervals: "from_offset",
  attempts: "at_offset_minutes",
  applied_events: "at_offset_minutes",
  bounded_transitions: "at_offset_minutes",
  discrete_transitions: "at_offset_minutes",
  // Append-class by owner approval (2026-09-30) after phase 1 measured a
  // 71,935 B one-boundary delta with `exposures` sent whole.
  exposures: "from_offset",
} as const;

export type AppendFamily = keyof typeof APPEND_FAMILY_KEYS;

const APPEND_FAMILIES = Object.keys(APPEND_FAMILY_KEYS) as AppendFamily[];

/** Frozen with the run: the full read's alone, kept from the base. */
export const STATIC_FAMILIES = [
  "signals",
  "bus_attachments",
  "reporting_gaps",
  "sample_phases",
  "drawing_context",
] as const;

/** Sent whole in every delta, replacing the base's. */
const WHOLE_FIELDS = [
  "status",
  "source",
  "statement",
  "history_schema_version",
  "boundaries_total",
  "boundaries_recorded",
  "recorded_through_offset_minutes",
  "content_digest",
  "observation_series_digest",
  "notes",
  "failure",
  "coverage",
] as const;

export type AppendRefusalReason =
  | "IDENTITY_MISMATCH"
  | "SINCE_MISMATCH"
  | "NOT_A_DELTA"
  | "BOUNDARY_GAP"
  | "ROW_NOT_AFTER_RECORDED"
  | "ROW_AHEAD_OF_RECORDED"
  | "ROW_OUT_OF_ORDER";

export interface AppendRefusal {
  reason: AppendRefusalReason;
  statement: string;
}

export type AppendResult = { ok: RunHistory } | { refused: AppendRefusal };

function refuse(reason: AppendRefusalReason, statement: string): AppendResult {
  return { refused: { reason, statement } };
}

type Row = object;

function keyOf(family: AppendFamily, row: Row): number {
  return (row as Record<string, number>)[APPEND_FAMILY_KEYS[family]];
}

/** Structural equality over wire values: text, numbers, null, arrays, objects. */
function same(a: unknown, b: unknown): boolean {
  if (a === b) {
    return true;
  }
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") {
    return false;
  }
  if (Array.isArray(a) !== Array.isArray(b)) {
    return false;
  }
  if (Array.isArray(a)) {
    const other = b as unknown[];
    return a.length === other.length && a.every((item, i) => same(item, other[i]));
  }
  const left = a as Record<string, unknown>;
  const right = b as Record<string, unknown>;
  const keys = Object.keys(left);
  return (
    keys.length === Object.keys(right).length &&
    keys.every((key) => Object.prototype.hasOwnProperty.call(right, key) && same(left[key], right[key]))
  );
}

/**
 * A whole-sent value, sharing what did not change with the base: the base's
 * own value when equal, else (for a list) the base's rows where they are equal
 * at the same place. The result always equals `next`; only identities differ.
 */
function share<T>(previous: T, next: T): T {
  if (same(previous, next)) {
    return previous;
  }
  if (Array.isArray(previous) && Array.isArray(next)) {
    return next.map((row, i) =>
      i < previous.length && same(previous[i], row) ? previous[i] : row,
    ) as T;
  }
  return next;
}

/**
 * Append one delta to the history it was read against.
 *
 * Accepted only when the delta names the same run and inputs, was read from
 * exactly the base's recorded count, carries its boundaries contiguously from
 * there to `through_boundary`, and every appended row is recorded after the
 * base's last boundary, no later than the delta's, and in order. Otherwise it
 * is refused with the reason, and nothing is merged.
 *
 * The result is a new object. Append families are the base's rows followed
 * by the delta's (row objects shared, never copied; an unchanged family keeps
 * the base's array); static families are the base's own; whole-sent fields
 * are the delta's values, keeping the base's identity wherever equal. A
 * delta is not a verifiable document, so the result's `history_digest` is
 * null. Nothing given is mutated.
 */
export function appendHistory(
  base: RunHistory,
  delta: RunHistory,
  envelope: RunHistoryDeltaEnvelope,
): AppendResult {
  if (base.run_id !== delta.run_id || base.inputs_identity !== delta.inputs_identity) {
    return refuse(
      "IDENTITY_MISMATCH",
      `The delta is for ${delta.run_id} with inputs ${delta.inputs_identity}; ` +
        `the history held is ${base.run_id} with inputs ${base.inputs_identity}.`,
    );
  }
  if (envelope.since_boundary !== base.boundaries_recorded) {
    return refuse(
      "SINCE_MISMATCH",
      `The delta was read after boundary ${envelope.since_boundary}; the ` +
        `history held records ${base.boundaries_recorded}.`,
    );
  }
  if (
    delta.history_digest !== null ||
    delta.drawing_context !== null ||
    STATIC_FAMILIES.some(
      (family) => family !== "drawing_context" && delta[family].length > 0,
    ) ||
    delta.boundaries_recorded !== envelope.through_boundary
  ) {
    return refuse(
      "NOT_A_DELTA",
      "The answer carries a digest, a static family or a recorded count " +
        "that disagrees with its envelope, so it is not a delta to append.",
    );
  }
  const added = delta.boundaries;
  if (added.length !== envelope.through_boundary - envelope.since_boundary) {
    return refuse(
      "BOUNDARY_GAP",
      `The delta says it covers boundaries ${envelope.since_boundary + 1} to ` +
        `${envelope.through_boundary} and carries ${added.length}.`,
    );
  }
  for (let i = 0; i < added.length; i += 1) {
    if (added[i].step_index !== envelope.since_boundary + i) {
      return refuse(
        "BOUNDARY_GAP",
        `The delta's boundaries are not contiguous from ` +
          `${envelope.since_boundary + 1}: position ${i + 1} is step ` +
          `${added[i].step_index}.`,
      );
    }
  }
  const after = base.recorded_through_offset_minutes;
  const through =
    added.length > 0 ? added[added.length - 1].offset_minutes : after;
  if (delta.recorded_through_offset_minutes !== through) {
    return refuse(
      "NOT_A_DELTA",
      `The delta says it is recorded through ${delta.recorded_through_offset_minutes} ` +
        `and its last boundary is at ${through}.`,
    );
  }
  for (const family of APPEND_FAMILIES) {
    let previous = after;
    for (const row of delta[family] as Row[]) {
      const key = keyOf(family, row);
      if (after !== null && key <= after) {
        return refuse(
          "ROW_NOT_AFTER_RECORDED",
          `A ${family} row at ${key} is not after the ${after} already held.`,
        );
      }
      if (through === null || key > through) {
        return refuse(
          "ROW_AHEAD_OF_RECORDED",
          `A ${family} row at ${key} is after the delta's last boundary ${through}.`,
        );
      }
      if (previous !== null && key < previous) {
        return refuse(
          "ROW_OUT_OF_ORDER",
          `A ${family} row at ${key} follows one at ${previous}.`,
        );
      }
      if (family === "boundaries" && previous !== null && key === previous) {
        return refuse(
          "ROW_OUT_OF_ORDER",
          `Two boundaries are recorded at ${key}.`,
        );
      }
      previous = key;
    }
  }

  const merged: RunHistory = { ...base, history_digest: null };
  for (const field of WHOLE_FIELDS) {
    (merged as unknown as Record<string, unknown>)[field] = share(
      base[field],
      delta[field],
    );
  }
  for (const family of APPEND_FAMILIES) {
    const rows = delta[family] as Row[];
    if (rows.length > 0) {
      (merged as unknown as Record<string, Row[]>)[family] = (
        base[family] as Row[]
      ).concat(rows);
    }
  }
  return { ok: merged };
}

/**
 * What one boundary recorded: the boundary itself and every append row whose
 * time key it owns - keys after the previous boundary's offset and at or
 * before its own. The interval is the one decided at this boundary.
 */
export interface BoundarySlice {
  boundary: RunHistoryBoundary;
  interval: RunHistoryInterval | null;
  samples: RunHistorySample[];
  attempts: RunHistoryAttempt[];
  applied_events: RunHistoryAppliedEvent[];
  bounded_transitions: RunHistoryBoundedTransition[];
  discrete_transitions: RunHistoryDiscreteTransition[];
}

/** Boundary slices by `step_index`, in boundary order. */
export type SliceIndex = ReadonlyMap<number, BoundarySlice>;

const SLICED = [
  "samples",
  "attempts",
  "applied_events",
  "bounded_transitions",
  "discrete_transitions",
] as const;

/**
 * Slices for `boundaries`, which follow a boundary recorded at `after` (null:
 * none), taking their rows from `history`'s families. Rows are walked once.
 */
function slicesFor(
  boundaries: RunHistoryBoundary[],
  after: number | null,
  history: RunHistory,
): BoundarySlice[] {
  const slices: BoundarySlice[] = boundaries.map((boundary) => ({
    boundary,
    interval: null,
    samples: [],
    attempts: [],
    applied_events: [],
    bounded_transitions: [],
    discrete_transitions: [],
  }));
  if (slices.length === 0) {
    return slices;
  }
  const owner = (key: number): BoundarySlice | null => {
    if (after !== null && key <= after) {
      return null;
    }
    // Rows are in order, so a binary search is not needed for correctness;
    // a linear find keeps this obviously right at a tick's few boundaries.
    return slices.find((slice) => key <= slice.boundary.offset_minutes) ?? null;
  };
  for (const family of SLICED) {
    for (const row of history[family] as Row[]) {
      const slice = owner(keyOf(family, row));
      if (slice !== null) {
        (slice[family] as Row[]).push(row);
      }
    }
  }
  for (const interval of history.intervals) {
    const slice = owner(interval.from_offset);
    if (slice !== null && slice.boundary.offset_minutes === interval.from_offset) {
      slice.interval = interval;
    }
  }
  return slices;
}

/** Every boundary's slice of a whole history (a full read). */
export function sliceIndex(history: RunHistory): SliceIndex {
  const index = new Map<number, BoundarySlice>();
  for (const slice of slicesFor(history.boundaries, null, history)) {
    index.set(slice.boundary.step_index, slice);
  }
  return index;
}

/**
 * `index` extended by the boundaries an accepted `delta` added. The existing
 * slice objects keep their identity; only the new boundaries get entries.
 * `after` is the recorded-through offset of the history the delta extended.
 */
export function extendSliceIndex(
  index: SliceIndex,
  delta: RunHistory,
  after: number | null,
): SliceIndex {
  if (delta.boundaries.length === 0) {
    return index;
  }
  const extended = new Map(index);
  for (const slice of slicesFor(delta.boundaries, after, delta)) {
    extended.set(slice.boundary.step_index, slice);
  }
  return extended;
}

/** A history and its slices, as the live-follow owner holds them. */
export interface HistoryFrame {
  history: RunHistory;
  slices: SliceIndex;
}

export function historyFrame(history: RunHistory): HistoryFrame {
  return { history, slices: sliceIndex(history) };
}

/** `appendHistory` over a frame, extending its slices on acceptance. */
export function appendFrame(
  frame: HistoryFrame,
  delta: RunHistory,
  envelope: RunHistoryDeltaEnvelope,
): { ok: HistoryFrame } | { refused: AppendRefusal } {
  const result = appendHistory(frame.history, delta, envelope);
  if ("refused" in result) {
    return result;
  }
  return {
    ok: {
      history: result.ok,
      slices: extendSliceIndex(
        frame.slices,
        delta,
        frame.history.recorded_through_offset_minutes,
      ),
    },
  };
}
