# W2-06 phase handoff — after spec commit 1 and q1 fixes (2026-10-19)

Branch `task/W2-06-ev-assessment` (worktree `AssetOpsV1-review5`), from main `3c4a2ebc`. Not merged.

## Landed (spec commit 1)

- `cb470909` migration `backend/migrations/versions/0025_w2_ev_session.py` (`down_revision=0024_w2_ev_config`):
  `ev_session`, `ev_session_revision`, `ev_session_evidence`, `ev_meter_interval` exactly per the Pre-build closure
  DDL (scoped FKs, scope uniques, value CHECKs, GiST SUPPORT-overlap exclusion, four indexes, `ledger_append_only`
  triggers); `finding_domain_subject` / `finding_revision_domain_minutes` recreated with an `ev_charging` arm;
  guarded downgrade (EV rows, `ev_charging` Finding/revision/job) restoring the 0022 text. Head pins moved
  0024→0025 in 10 existing test files. Rule 8 (`tools/checks/configuration-persistence.ps1`): four tables in
  `$assessTables`, `$evSessionTables` in the insert-only DO UPDATE list and a fail-closed EV probe enumeration.
  `tools/writer_guard_probes.py`: per table foreign insert / update / delete / upsert + owner-insert control.
- `3af70964` migration test fixes; `fc231615` four cross-writer `ev <table> reverse update` probes.

## Focused checks (private DB `w206_test`, dropped afterwards)

- `test_w206_ev_migration_postgres.py` 7 passed; with `test_w203_cold_migration_postgres.py`,
  `test_w204_cold_migration.py`, `test_w205a_ev_migration.py`: 26 passed. Head-pinned migration tests in
  s1_bindings, s2_evidence_ledger, s405_publication, s4_consequence_store, s4_evidence_consequence_work,
  w200_source_events, w201_cold_foundation (`-k` selection): 21 passed.
- Writer probes (`--seam`): 20 EV CAUGHT/ALLOWED + 4 reverse CAUGHT. Non-vacuity: with the EV tables removed from
  `$assessTables`, all 4 reverse probes MISSED; renaming one EV probe makes rule 8 fail with "Rule 8 EV writer probe
  ... is missing". Tree restored.
- `tools/check-all.ps1`: all 10 guards passed.
- No full backend/host suite run (brief: memory is low).

## Run 2 (after q1 merge, 2026-10-19)

- `13c6ef33` q1 R1: 0025 edited in place — `unknown_meter_seconds integer NULL`, exact
  `ev_session_revision_unknown_seconds` and new `ev_session_revision_quantity_state` CHECK; migration test adds the
  contradictory null pair, NULL energy with integer seconds, five refusals. R10 ratified as built (no change).
- Focused + adjacent (`test_w206*`, `test_w203*`, `test_w205*`, `test_s2*`) on private `w206q1_test` (dropped);
  `tools/check-all.ps1` 10/10 passed. 486 passed, 0 skipped (JUnit), 927 s.

## Run 3 (after q2 merge, 2026-10-19)

- `27ceef76` commit 2b: pure `backend/assetops_backend/analytics/ev.py` (`EvInputs`, `EvRecord.from_row`,
  `EvConnector`, `EvWindow`, `assess(inputs)->EvAssessment` with `.sessions/.denominator/.claim_level/.status_state/
  .orphan_terminal_ids`; `EvSession` carries links, intervals, `basis_sha256`, `finding_key_sha256`,
  `finding_support_sha256`; helpers `assessment_key`, `run_input_sha256`, `configuration_sha256`, `cohort_sha256`,
  `EMPTY_SUPPORT_SHA256`, `plain`); `SESSION_ANALYTIC` declared in `analytics/declaration.py`.
  `test_w206_ev_session_rules.py` 42 passed.
- `0eeb57ef` commit 3a: 0025 `ENQUEUE`/`DROP_ENQUEUE` (`ev_enqueue_floor/ceil/window/configuration`,
  `enqueue_ev_assessment` deferred constraint trigger on `accepted_evidence`); `PostgresAssessmentStore.
  ev_enqueue_configuration` (above `transaction`); rule 8 `$evEnqueueSql` (non-vacuity proven);
  `test_w206_ev_enqueue_postgres.py` 16 tests; `test_w200_source_events_postgres.py` adjusted for EV jobs.
  Publish-path wiring NOT done (P7).
- Parked, uncommitted, in `.agent/W2-06-2a-wip/`: `W2-06-2a-wip.patch` (vector producer inside
  `test_w205b_ev_replay_postgres.py::test_six_registered_replays`, `git apply --check` clean), generated
  `ev-w206-vectors.json` (destination `backend/tests/fixtures/w2/`, all `clock_attested=false`),
  `test_w206_ev_vectors.py` (destination `host/tests/`), `W2-06-ev-vector-tests.py.txt` (destination
  `backend/tests/test_w206_ev_vectors.py`; 9 of 10 fail against the parked file on P1/P2).
- Checks at `0eeb57ef`: `test_w206*`, `test_w203*`, `test_w205*`, `test_s2*` on private `w206r3_test` (dropped): 544 passed, 0 failed, 0 skipped (JUnit), 963 s; `tools/check-all.ps1` 10/10 passed.

## Stopped: pending rulings q3 (P1-P8)

`.agent/W2-06-pending-rulings.md` "run 3 (q3)". P1 (EV clock attestation source) blocks the vector fixture and
3b's inputs; P2-P4 block 3b hashing/inputs; P7 blocks publish wiring. Resume: apply rulings to the parked 2a work
and `ev.py`, commit 2a, then 3b (store `ev_*` methods, `PostgresFindingStore.ev_apply`, `EvAssessmentWorker`,
`build_ev_assessment_worker`, `test_w206_ev_store_postgres.py`), then P7 wiring.

## Anchors for commit 4 (selected reads)

- Router pattern: `backend/assetops_backend/cold_assessment_api.py` (`_Refused` :45, `_refusal` :51,
  `build_cold_assessment_router` :69, `opened` :74, `served` :105); mount beside `main.py:403-406`
  (`build_cold_read_service` → `build_cold_assessment_router(registry, cold_reads)`).
- Read helpers: `analytics/cold_reads.py` (`ColdReadUnavailable` :37, `ColdCursorRefused` :41,
  `currentness_state` :53, `encode_cursor` :66, `decode_cursor` :72); service factory
  `analytics/composition.py:118 build_cold_read_service`; cold read SQL in `postgres_assessment_store.py` ~:1390-1410.
- Watermark: `postgres_assessment_store.py:769 cold_watermark`.

## Anchors for commits 2–3

- Pure analogue: `backend/assetops_backend/analytics/cold.py` (constants :31-34, input dataclass with `quality`
  :80 and `clock_attested` :87, `basis_sha256` :238, gap/use classification :271-281). Canonical JSON:
  `financials/fuel_cost.py:84 canonical_json`, `:100 iso` (as imported by cold).
- Worker: `analytics/assessment_worker.py:207 ColdProjection`, `:216 ColdAssessmentWorker` (`run_once` :254).
- Assessment store cold path: `analytics/adapters/postgres_assessment_store.py:769-1026` (`cold_watermark`,
  `cold_still_mine`, `cold_complete`, `cold_windows`, `cold_inputs` :800, `cold_persist` :911, `cold_episodes` :984).
- Finding store cold path: `analytics/adapters/postgres_finding_store.py:519 cold_apply`, `:560
  _insert_cold_finding`, `:576 _insert_cold_revision`.
- Source gate: `evidence/source_provenance.py:244 SourceProvenanceResolver`.
- EV inputs: `accepted_evidence_ev_measurement` index (0024); fixtures `contract-fixtures/w2/ev/*.json`
  (`assertions` keys), Foundation fixture `backend/tests/fixtures/w2/ev-lab-001.yaml`.
- Test-row helpers for EV schema: `backend/tests/test_w206_ev_migration_postgres.py` (`Ctx`, `insert_session`,
  `insert_revision`, `insert_link`, `insert_interval`, `insert_ev_finding`, `remove_ev`).

## Open risks

- 0023's cold triggers fire only for `domain='cold_chain'`; the 0012 fuel trigger only for `mini_grid`, so an EV
  FindingRevision enqueues no fuel/cold work (checked by trigger WHEN clauses, not yet by an EV Finding test).
