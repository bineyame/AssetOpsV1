# W2-06 phase handoff — after spec commit 1 (2026-10-19)

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

## Stopped: commit 2 not started

`.agent/W2-06-pending-rulings.md` R1–R10. R1 is a conflict (contradictory manifest asserts NULL
`unknown_meter_seconds`/`supported_kwh`; 0025/spec say integer `>=0` and SUPPORT sum). R2–R9 are unruled computations
of the pure correlation (bounds, INCOMPLETE active span, exclusion-reason mapping, overlap, error bound, linked record
set, basis literals, reason-code content/order). R10 asks to ratify commit-1 readings.

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

- If R1 rules NULL unknown seconds, 0025 needs `unknown_meter_seconds` nullable (one-line change + test update).
- 0023's cold triggers fire only for `domain='cold_chain'`; the 0012 fuel trigger only for `mini_grid`, so an EV
  FindingRevision enqueues no fuel/cold work (checked by trigger WHEN clauses, not yet by an EV Finding test).
