# T025e phase 1 handoff: data path (AC1-AC3)

Branch `task/T025e-cockpit-organisation-and-live-playback`. Commits:
`77bc846` (backend route and host guard), `945a07c` (client merge and fetch).
Nothing on screen changed. `RunFrame` does not call the delta read yet.

## What landed

- **AC1 backend** (`backend/assetops_backend/simulator_lab_api.py`).
  - `HISTORY_APPEND_FAMILY_KEYS` and `HISTORY_STATIC_FAMILIES` sit next to
    `RUN_EXECUTION_HISTORY_ROUTE`. They are the one table of family classes.
  - `history_delta_payload(history, since, run)` is a `dataclasses.replace`
    selection followed by `history_payload`. The manifest fields
    `boundaries_recorded` and `recorded_through_offset_minutes` are overridden
    with the whole-history values. `sample_phases=[]`, `drawing_context=None`
    and `history_digest=None`.
  - `_parse_since_boundary` refuses a malformed value with 422
    `EXECUTION_REQUEST_INVALID` (it accepts `[0-9]+` only) and a value ahead of
    the record with 409 `HISTORY_SINCE_AHEAD`.
  - The route `read_run_execution_history` gains the optional `since_boundary`
    query. Without it the response is byte-identical and has no `delta` key.
- **AC1 tests**: `backend/tests/test_run_history_delta_api.py` (19 tests).
  - Unchanged without the parameter.
  - For every k, the delta equals the full read filtered by key.
  - Whole fields equal; `history_digest` null; static families empty or null.
  - The interval is keyed by the boundary that decided it.
  - Edge delta; 9 malformed values; ahead; 404; gate closed.
- **AC2 guard**: `host/tests/test_lab_history_prefix.py` (18 tests).
  - Prefix stability per append family between every pair of consecutive
    boundaries (transitive to every k < m) of two live sessions: the mini-grid
    `PROLONGED` session (97 boundaries) and the fuel run with a gap (493
    boundaries).
  - A non-vacuity test shows the two sessions between them record a row of
    every append family.
  - Folding `history_delta_payload` at every boundary reproduces
    `history_payload` at the end.
  - A delta read of a persisted run changes no artifact byte.
  - The keys come from the backend table, so the guard binds the real
    selection.
- **AC3 client**.
  - `frontend/src/shell/liveHistory.ts` provides `appendHistory`,
    `sliceIndex`, `extendSliceIndex`, `historyFrame`, `appendFrame` and the
    `BoundarySlice` / `SliceIndex` / `HistoryFrame` types.
  - `runHistory.ts` adds `fetchRunHistorySince` and `RunHistoryDeltaResult`
    (`loaded | refused{code} | not_found | unavailable`).
  - `runSetupClient.ts` adds `getExecutionHistorySince(runId, since)`.
  - `__tests__/executionFixtures.ts` `executionMethods` answers
    `unavailable` by default.
- **AC3 tests**.
  - `__tests__/liveHistory.test.ts` (17 tests) runs against backend-generated
    deltas in `__tests__/kobo-mini-grid-history-deltas.json`, which
    `make_history_fixtures.py live_deltas()` writes. It holds the base after
    start (0 boundaries), 7 single deltas, one 0 to 7 jump, and the full read
    at 7.
  - `__tests__/runHistorySince.test.ts` has 5 tests.

## Checks (this phase)

- Host: prefix, lab_history, cockpit_window and contract9_gate: **85 passed**.
- Backend: the delta, history, gate and execution API tests: **85 passed**.
  The 2 warnings are pre-existing starlette/httpx deprecations.
- Frontend: 9 affected files, **129 passed**. `tsc --noEmit` is clean.
- `tools/check-architecture.ps1` passed.
- Non-vacuity proofs, each committed first and then reverted with
  `git checkout`:
  - Backend key `intervals: to_offset`: host 2 failed, backend 1 failed.
  - Attempts not filtered: host 2 failed, backend 4 failed.
  - `capture` sorting attempts by address: 5 host failures.
  - Four merge mutations (since check off, base mutated by `push`, whole-field
    sharing off, order check off): each failed 1-2 merge tests.
- Full suites have not been run; they belong to phase 3.

## Deviations from the guidance

1. **The interval key is `from_offset`, not `to_offset`** (A1 said
   `to_offset`). The first run of the prefix guard failed under `to_offset`.
   `capture` records the interval `[0,5)` at boundary 0, so under `to_offset`
   it sits outside the prefix it belongs to. The interval belongs to the
   boundary that decided it, which is also AC7's "interval decided at T". This
   is the same selection mechanism with the correct key, and every family
   stays in the append class.
2. `appendHistory` also refuses `NOT_A_DELTA` (a digest, a non-empty static
   family, or a recorded count or edge that disagrees with the envelope) and
   `ROW_AHEAD_OF_RECORDED`. This is stricter than A2, not looser.
3. The slice index keys on `step_index`. A row belongs to the boundary whose
   offset is the first one at or after the row's key.

## Measurements (in-process, `history()` capture plus `history_delta_payload` plus `json.dumps`, no HTTP)

| session | boundaries | full read | 1-boundary delta max / median | server ms, last 20 ticks p95 / max |
|---|---|---|---|---|
| mini-grid PROLONGED | 97 | 1,122,198 B | **71,935 B / 42,972 B** | 21.1 / 32.6 |
| fuel with gap | 493 | 230,398 B | 11,654 B / 7,999 B | 36.9 / 38.1 |

The worst mini-grid delta (at boundary 94) is **57,443 B of `exposures`**,
which is 376 rows sent whole as AC1 requires. The interval is 8,393 B, attempts
1,956 B, samples 1,475 B and coverage 1,536 B. Without exposures the delta is
about 14.5 KB.

## Open risks for phase 2 and 3

- **The AC12 payload budget (32 KB) fails on the mini-grid because exposures
  are sent whole.** A probe found exposures append-only and exactly selectable
  by `from_offset` on both fixtures, so moving them to the append class would
  bring the delta under budget. AC1 and A1 name exposures "whole", so I did
  not change the class. This needs an Architect or owner call before phase 3
  measures.
  - If they agree: add `"exposures": "from_offset"` to both tables
    (`HISTORY_APPEND_FAMILY_KEYS` and `APPEND_FAMILY_KEYS`), move it out of
    `WHOLE_FIELDS`, and let the prefix guard cover it.
  - The client merge already keeps held exposure rows by reference, so render
    identity is not the issue. Wire bytes are.
- The server time is within the 50 ms budget in process. HTTP and the
  demo-window measurement on the running app are still to be taken (phase 3).
- For phase 2:
  - Call `getExecutionHistorySince(runId, history.boundaries_recorded)` inside
    the awaited `show`, then `appendFrame`.
  - On `refused` or `unavailable`, or when the append is refused, do one full
    `getExecutionHistory` read at the next tick.
  - A `loaded` delta whose `since_boundary` does not equal the held count is
    refused by the merge (`SINCE_MISMATCH`). Never retry the same delta.
- Terminal reconcile: the full read of a terminal run is the persisted
  document, and it has a non-null `history_digest`. Accumulated history always
  has `history_digest: null`. The AC6 deep-equal check must therefore compare
  append families only (as the AC says), not the whole object.
- `executionMethods` answers `unavailable` for the delta read, so phase-2
  screen tests need to feed deltas explicitly. The deltas fixture is available
  for that.
