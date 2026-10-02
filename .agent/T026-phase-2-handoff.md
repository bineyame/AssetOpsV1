# T026 phase 2 handoff (History, AC13 host side)

Branch `task/T026-dispatch-capable-evidence`. Phase 2 commits: `8508a7c` (build
and tests) and the handoff commit that adds this file and
`.agent/T026-phase-2-probes.sh`. No named stop was hit: contract still 9,
`git diff main -- host/tests/contract9_gate contracts/assetops_contracts/execution_contract.py`
is empty, and the gate passes in the host suite. Nothing touches the projection
document, `FrozenWorldInputs` or any existing reporting-path cause.

## What landed

- **History schema 3** (`contracts/assetops_contracts/lab_history.py:60`).
  `READABLE_LAB_HISTORY_SCHEMA_VERSIONS = (2, 3)`, `SCHEMA_3_FAMILIES`,
  `SCHEMA_2_UNRECORDED_STATEMENT`. `HISTORY_FAMILIES` gains `records` and
  `publications` (7 coverage rows, in order); `LabHistory.records` /
  `.publications` fields.
- **`HeldPublication`** (`contracts/assetops_contracts/observation.py`, after
  `publication_delay_minutes`): kind `READING`/`RECORD`, path, source offset
  and time, `released_offset_minutes`, `published_at` (latency included, as the
  envelope), `held_minutes` (host-derived total), `delay_event_id` (Lab-only).
- **Gateway rule, once** `held_publications(...)` at the end of
  `simulator/assetops_simulator/gateway/publish.py`: the same publish/skip rules
  as `publish`, and only publications released by `reached_offset_minutes` (a
  publication still held is not yet a fact). Ordered by release.
- **Capture** `host/lab_history.py` `capture(..., records=None, publications=())`:
  records coverage `RECORDED` when the frozen mapping has a non-MEASUREMENT
  entry, else `NOT_APPLICABLE`; publications always `RECORDED` (empty with no
  delay). Wired in `HostLabExecution._captured` (`host/lab_execution.py`, ~:2180)
  from `generate_records` + `held_publications`, delays = reporting + records.
- **Persist/read**: `render_history` writes `records` (18-wide rows) and
  `publications` (9-wide); `_parse_record_rows` / `_parse_publications` read
  strictly (in-window offsets, ordering, contract validation). A schema-2
  artifact reads (digest verified as written), returns
  `history_schema_version=2` and appends both families as `UNAVAILABLE` with
  the schema-2 statement; a schema-2 document carrying either key, or schema 4,
  is `HISTORY_UNREADABLE` and untouched.
- **Wire** `backend/assetops_backend/simulator_lab_api.py`:
  `HISTORY_APPEND_FAMILY_KEYS` gains `records: at_offset_minutes` (occurrence;
  a future effective time is only a field) and `publications:
  released_offset_minutes`; `history_payload` serializes both (dict rows, field
  names as the dataclasses). No new static or step-owned family.

## Family classification (AC13)

| Family | Class | Key | Why prefix-stable |
| --- | --- | --- | --- |
| attempts (incl. capability, status) | append (existing) | `at_offset_minutes` | unchanged; new signals are just more rows |
| `records` | append | `at_offset_minutes` | `generate_records` emits only `at <= reached`; policies at 0 |
| `publications` | append | `released_offset_minutes` | emitted only once released; a delay is a new row, never an edit |

## AC13 host-side evidence

- `host/tests/test_lab_history_prefix.py`: new fixture `degraded-evidence`
  (profile 5, mini-grid v3); every append family grows only at its end and
  folds to the full read, for both new families; non-vacuity requires rows of
  both; new `test_every_listed_wire_family_is_classified` (only `coverage`
  and `notes` may be whole-sent lists).
- `host/tests/test_t026_history.py` (11 tests): held row at release not source
  (SOC 240 -> 250, 07:10:03Z, 10 min, attempt row unchanged); still-held not
  recorded at 245, recorded at 250; history held set == stage's delayed
  envelopes; records at occurrence with outcome (missing override =
  `SUPPRESSED_BY_GAP`, nothing staged); delayed override record = RECORD held
  row 120 -> 125; reload (PERSISTED, schema 3) equals live for records,
  publications and attempts incl. both capability signals, status members and
  the suppressed capability gap; wire carries both and a delta sends the
  release once; schema-2 artifact discloses both UNAVAILABLE; schema-2-with-
  records and schema 4 unreadable and unchanged; profile 4 records
  NOT_APPLICABLE and still reloads.
- Guard probes `.agent/T026-phase-2-probes.sh` (bash, from repo root): 5 of 5
  CAUGHT (publication keyed at source, unclassified family, early release,
  schema 2 unreadable, held record not recorded); tree clean after.
- Checks: host 588 passed; backend 1375 passed; simulator 244 passed;
  `check-architecture` and `check-agent-workflow` passed. Frontend not run
  (phase 3).

## What phase 3 needs (must)

- **Frontend mirror**: `frontend/src/shell/liveHistory.ts:35` `APPEND_FAMILY_KEYS`
  must add `records: "at_offset_minutes"` and `publications:
  "released_offset_minutes"`. Until then a live-follow delta's partial lists
  would be treated as whole fields (`WHOLE_FIELDS`, ~:75) - a screen bug.
  `runHistory.ts:309` guard tolerates the extra keys today; add types/guards.
- Coverage now has 7 families; any frontend fixture/test that counts 5 must
  move. Schema-2 artifacts show `history_schema_version` 2 and two UNAVAILABLE
  rows (the HistoryInspector prints the version, `HistoryInspector.tsx:317`).
- Screen side of AC13: markers for records (effective start/end are fields)
  on the Applied timeline, publication delay in the inspector (source vs
  `published_at`, `held_minutes`), and the T025d C2 carry (declared
  `reporting_gaps` are static whole-window declarations; clip to
  `recorded_through_offset_minutes` or use suppressed attempts).
- AC15: re-measure delta bytes and both 50 ms p95 budgets; this phase added
  `generate_records` + `held_publications` to every live capture (not measured).

## Decisions for the reviewer

1. Two families, not one: records are occurrences (append at occurrence), held
   publications are gateway facts (append at release). Undelayed publications
   are not rows: their time is source + the mapping's declared latency.
2. Records coverage keys on the frozen mapping having a record channel, not on
   rows existing (a profile-5 run with no override still records policies).
3. `held_publications` re-derives publish's skip rules rather than reading
   envelopes; the stage-agreement test binds the two.
4. Record `members` are component ids (lower case), so the reader checks a
   non-empty list, not the enum-member pattern.

## Open risks

- The stage (phase 1) stages a held envelope as soon as its source boundary is
  published, carrying a `published_at` the run has not reached yet; history now
  says "not yet a fact" until release. A stage read mid-hold shows a future
  publication time. Reviewer/phase 3 to decide whether the stage should also
  withhold it until release (stage content, AC7/AC10 territory).
- A run stopped inside a hold window never records its publication row.
