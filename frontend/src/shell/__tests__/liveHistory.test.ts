import { describe, expect, it } from "vitest";

import {
  APPEND_FAMILY_KEYS,
  appendFrame,
  appendHistory,
  extendSliceIndex,
  historyFrame,
  sliceIndex,
  STATIC_FAMILIES,
  type AppendResult,
  type HistoryFrame,
} from "../liveHistory";
import type { RunHistory, RunHistoryDeltaEnvelope } from "../runHistory";
import wire from "./kobo-mini-grid-history-deltas.json";

/**
 * The live-follow merge (T025e AC3), against the backend's own answers.
 *
 * `kobo-mini-grid-history-deltas.json` is written by
 * `host/tests/make_history_fixtures.py` (`live_deltas`): the prolonged
 * mini-grid recipe's full read after start, the `?since_boundary=` answer
 * after each of 7 single steps, one answer covering all 7, and the full read
 * at the end. Nothing is edited after serialization.
 */

interface DeltaRead {
  history: RunHistory;
  delta: RunHistoryDeltaEnvelope;
}

const fixture = wire as unknown as {
  base: RunHistory;
  deltas: DeltaRead[];
  jump: DeltaRead;
  full: RunHistory;
};

/** A fresh deep copy, so no test can leak into another through the import. */
function copy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value as Record<string, unknown>)) {
      deepFreeze(child);
    }
  }
  return value;
}

function accepted(result: AppendResult): RunHistory {
  if ("refused" in result) {
    throw new Error(`refused: ${result.refused.reason} ${result.refused.statement}`);
  }
  return result.ok;
}

function refusal(result: AppendResult): string {
  if ("ok" in result) {
    throw new Error("accepted a delta that should have been refused");
  }
  return result.refused.reason;
}

/** The base folded with the first `count` single-step deltas. */
function folded(count: number): RunHistory {
  let held = copy(fixture.base);
  for (const read of copy(fixture.deltas).slice(0, count)) {
    held = accepted(appendHistory(held, read.history, read.delta));
  }
  return held;
}

describe("the fixture is what the test needs", () => {
  it("starts from an empty record and grows one boundary per delta", () => {
    expect(fixture.base.boundaries_recorded).toBe(0);
    expect(fixture.deltas.map((d) => d.delta)).toEqual(
      [0, 1, 2, 3, 4, 5, 6].map((n) => ({
        since_boundary: n,
        through_boundary: n + 1,
      })),
    );
    expect(fixture.full.boundaries_recorded).toBe(7);
    // Non-vacuity: the deltas carry rows of the families the merge checks,
    // and the static families are non-empty in the full reads only.
    const rows = (family: keyof RunHistory) =>
      fixture.deltas.reduce(
        (n, d) => n + (d.history[family] as unknown[]).length,
        0,
      );
    expect(rows("samples")).toBeGreaterThan(0);
    expect(rows("intervals")).toBeGreaterThan(0);
    expect(rows("attempts")).toBeGreaterThan(0);
    expect(rows("applied_events")).toBeGreaterThan(0);
    expect(fixture.base.signals.length).toBeGreaterThan(0);
    expect(fixture.base.drawing_context).not.toBeNull();
  });
});

describe("appendHistory accepts what the backend sends, in order", () => {
  it("folding every delta from 0 to N equals the full read at N", () => {
    expect(folded(7)).toEqual(fixture.full);
  });

  it("each prefix of the fold is a full read's shape: counts and edge agree", () => {
    for (let n = 1; n <= 7; n += 1) {
      const held = folded(n);
      expect(held.boundaries_recorded).toBe(n);
      expect(held.boundaries).toHaveLength(n);
      expect(held.recorded_through_offset_minutes).toBe(
        held.boundaries[n - 1].offset_minutes,
      );
    }
  });

  it("one delta covering several boundaries is the same as them one by one", () => {
    const read = copy(fixture.jump);
    expect(read.delta).toEqual({ since_boundary: 0, through_boundary: 7 });
    expect(accepted(appendHistory(copy(fixture.base), read.history, read.delta))).toEqual(
      fixture.full,
    );
  });

  it("an empty delta at the edge is accepted and changes no family", () => {
    const held = folded(7);
    const empty = copy(fixture.deltas[6].history);
    for (const family of Object.keys(APPEND_FAMILY_KEYS) as (keyof typeof APPEND_FAMILY_KEYS)[]) {
      (empty[family] as unknown[]) = [];
    }
    const next = accepted(
      appendHistory(held, empty, { since_boundary: 7, through_boundary: 7 }),
    );
    expect(next).toEqual(held);
    expect(next.samples).toBe(held.samples);
    expect(next.boundaries).toBe(held.boundaries);
  });
});

describe("appendHistory never mutates and shares what did not change", () => {
  it("leaves a frozen base and a frozen delta exactly as they were", () => {
    const base = deepFreeze(folded(3));
    const read = deepFreeze(copy(fixture.deltas[3]));
    const before = JSON.stringify(base);
    const deltaBefore = JSON.stringify(read);

    const next = accepted(appendHistory(base, read.history, read.delta));

    expect(JSON.stringify(base)).toBe(before);
    expect(JSON.stringify(read)).toBe(deltaBefore);
    expect(next).not.toBe(base);
    expect(next.boundaries_recorded).toBe(4);
  });

  it("keeps static families, old rows and unchanged whole fields by reference", () => {
    const base = folded(3);
    const read = copy(fixture.deltas[3]);

    const next = accepted(appendHistory(base, read.history, read.delta));

    for (const family of STATIC_FAMILIES) {
      expect(next[family]).toBe(base[family]);
    }
    expect(next.samples).not.toBe(base.samples);
    base.samples.forEach((row, i) => expect(next.samples[i]).toBe(row));
    base.intervals.forEach((row, i) => expect(next.intervals[i]).toBe(row));
    // The delta's own rows are placed, not copied.
    expect(next.samples[base.samples.length]).toBe(read.history.samples[0]);
    // A whole-sent field that did not change keeps the base's identity.
    expect(next.coverage).toEqual(base.coverage);
    expect(next.coverage).toBe(base.coverage);
    // Exposures are append-class (owner approved 2026-09-30): the delta
    // carries only the new ones, and the ones already held keep identity.
    expect(read.history.exposures.length).toBeGreaterThan(0);
    expect(read.history.exposures.length).toBeLessThan(base.exposures.length);
    base.exposures.forEach((row, i) => expect(next.exposures[i]).toBe(row));
    expect(next.exposures).toEqual(base.exposures.concat(read.history.exposures));
    // A family the delta adds nothing to keeps its array.
    for (const family of ["bounded_transitions", "discrete_transitions"] as const) {
      if (read.history[family].length === 0) {
        expect(next[family]).toBe(base[family]);
      }
    }
    expect(next.history_digest).toBeNull();
  });
});

describe("appendHistory refuses what it cannot place, and merges nothing", () => {
  it("refuses a delta read from a different boundary count", () => {
    const read = copy(fixture.deltas[4]);
    expect(refusal(appendHistory(folded(3), read.history, read.delta))).toBe(
      "SINCE_MISMATCH",
    );
    // The same delta twice is the same refusal: the base has moved on.
    const once = folded(4);
    const again = copy(fixture.deltas[3]);
    expect(refusal(appendHistory(once, again.history, again.delta))).toBe(
      "SINCE_MISMATCH",
    );
  });

  it("refuses a gap in the boundaries it carries", () => {
    const read = copy(fixture.jump);
    read.history.boundaries.splice(3, 1);
    expect(refusal(appendHistory(copy(fixture.base), read.history, read.delta))).toBe(
      "BOUNDARY_GAP",
    );
    // The delta after boundary 5 offered as if read after 4: boundary 5 is
    // missing from what it carries.
    const skipped = copy(fixture.deltas[5]);
    expect(
      refusal(
        appendHistory(folded(4), skipped.history, {
          since_boundary: 4,
          through_boundary: 6,
        }),
      ),
    ).toBe("BOUNDARY_GAP");
  });

  it("refuses a duplicate boundary", () => {
    const held = folded(4);
    const read = copy(fixture.deltas[4]);
    read.history.boundaries.unshift(copy(held.boundaries[3]));
    read.history.boundaries_recorded = 6;
    expect(
      refusal(
        appendHistory(held, read.history, { since_boundary: 4, through_boundary: 6 }),
      ),
    ).toBe("BOUNDARY_GAP");
  });

  it("refuses a row at or before what is already recorded", () => {
    const held = folded(4);
    const read = copy(fixture.deltas[4]);
    read.history.samples.unshift(copy(held.samples[held.samples.length - 1]));
    expect(refusal(appendHistory(held, read.history, read.delta))).toBe(
      "ROW_NOT_AFTER_RECORDED",
    );
    const interval = copy(fixture.deltas[4]);
    interval.history.intervals.unshift(copy(held.intervals[held.intervals.length - 1]));
    expect(refusal(appendHistory(held, interval.history, interval.delta))).toBe(
      "ROW_NOT_AFTER_RECORDED",
    );
  });

  it("refuses rows out of order and rows after its own last boundary", () => {
    const read = copy(fixture.jump);
    read.history.samples.reverse();
    expect(refusal(appendHistory(copy(fixture.base), read.history, read.delta))).toBe(
      "ROW_OUT_OF_ORDER",
    );
    const ahead = copy(fixture.deltas[4]);
    ahead.history.attempts.push({
      ...copy(ahead.history.attempts[0] ?? fixture.full.attempts[0]),
      at_offset_minutes: 10_000,
    });
    expect(refusal(appendHistory(folded(4), ahead.history, ahead.delta))).toBe(
      "ROW_AHEAD_OF_RECORDED",
    );
  });

  it("refuses another run or other inputs", () => {
    const held = folded(4);
    const run = copy(fixture.deltas[4]);
    run.history.run_id = "run-00000000000000000000000000000009";
    expect(refusal(appendHistory(held, run.history, run.delta))).toBe(
      "IDENTITY_MISMATCH",
    );
    const inputs = copy(fixture.deltas[4]);
    inputs.history.inputs_identity = "other-inputs";
    expect(refusal(appendHistory(held, inputs.history, inputs.delta))).toBe(
      "IDENTITY_MISMATCH",
    );
  });

  it("refuses a full read or a digest offered as a delta", () => {
    expect(
      refusal(
        appendHistory(copy(fixture.base), copy(fixture.full), {
          since_boundary: 0,
          through_boundary: 7,
        }),
      ),
    ).toBe("NOT_A_DELTA");
    const digest = copy(fixture.deltas[0]);
    digest.history.history_digest = "sha256:x";
    expect(refusal(appendHistory(copy(fixture.base), digest.history, digest.delta))).toBe(
      "NOT_A_DELTA",
    );
  });
});

describe("the slice index", () => {
  it("folds to the index of the full read, keeping every earlier slice", () => {
    let frame: HistoryFrame = historyFrame(copy(fixture.base));
    const kept: HistoryFrame["slices"][] = [];
    for (const read of copy(fixture.deltas)) {
      const result = appendFrame(frame, read.history, read.delta);
      if ("refused" in result) {
        throw new Error(result.refused.statement);
      }
      for (const [step, slice] of frame.slices) {
        expect(result.ok.slices.get(step)).toBe(slice);
      }
      kept.push(frame.slices);
      frame = result.ok;
    }
    expect(frame.history).toEqual(fixture.full);
    expect(frame.slices).toEqual(sliceIndex(fixture.full));
    expect(frame.slices.size).toBe(7);
  });

  it("gives each boundary its own rows and the interval it decided", () => {
    const index = sliceIndex(fixture.full);
    let owned = 0;
    for (const slice of index.values()) {
      const at = slice.boundary.offset_minutes;
      for (const sample of slice.samples) {
        expect(sample.offset_minutes).toBe(at);
      }
      if (slice.interval !== null) {
        expect(slice.interval.from_offset).toBe(at);
      }
      owned += slice.samples.length;
    }
    expect(owned).toBe(fixture.full.samples.length);
    expect([...index.values()].filter((s) => s.interval !== null).length).toBe(
      fixture.full.intervals.length,
    );
  });

  it("an empty delta returns the same index", () => {
    const index = sliceIndex(fixture.full);
    const empty = copy(fixture.deltas[6].history);
    empty.boundaries = [];
    expect(extendSliceIndex(index, empty, 35)).toBe(index);
  });
});
