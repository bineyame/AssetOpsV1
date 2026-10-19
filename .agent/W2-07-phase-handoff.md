# W2-07 phase handoff (run 1, 2026-10-20)

Branch `task/W2-07-ev-site-evidence-money`, worktree `AssetOpsV1-review5`. Private DB `w207a_test` (dropped at end of
run). Stopped after spec commit 1: commit 2 is blocked on pending ruling R2 (`.agent/W2-07-pending-rulings.md`).

## Landed (commit 1)

- `backend/migrations/versions/0026_w2_ev_money.py`: the spec's literal 0026 body (key/unit CHECK widening, EV-only
  positive CHECK, five scoped append-only tables, tariff key trigger, trigger-only work via `ev_consequence_enqueue`
  with `ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING`, backfill, guarded
  downgrade) plus a leading catalog assertion that the two 0010 CHECK names exist.
- `financials/assumptions.py`: `ASSUMPTION_KEYS` gains `ev_gross_tariff_per_kwh`; `EV_TARIFF_KEY`, `UNITS`,
  `unit_for`, EV-only `VALUE_NOT_POSITIVE` and active-ISO-4217 `CURRENCY_NOT_ISO` (R4). Diesel digest/unit unchanged.
  `postgres_assumption_store.py` and `assumption_read.py` use `UNITS[key]`.
- Rule 8 (`tools/checks/configuration-persistence.ps1`): `$evConsequenceTables` (revision, session, evidence,
  work_attempt) in `$consequenceTables`, insert-only per table, `ev_consequence_work` runtime-forbidden, 0026
  migration-text arbiter check, required EV probe names. Probes in `tools/writer_guard_probes.py`
  (literal `ev ...` negatives and `controls ev ...`; rule 8 matches names textually).
- Tests: `backend/tests/test_w207_ev_money_postgres.py` (named proofs `test_0026_follows_installed_0025_and_
  preserves_diesel`, `test_0026_trigger_only_work_and_exact_conflict_constraint`, plus
  `test_0026_scoped_constraints_state_arithmetic_and_append_only`). Head literals moved to `0026_w2_ev_money` in 11
  existing test files (head assertions only).

## Evidence (commit 1, `601456bc` + `a471f3f4`)

- `test_w207_ev_money_postgres.py` 3 passed. Adjacent: 14 head/assumption/migration files 214 passed + 1 fixed
  (`test_w204_cold_migration.py` snapshot now expects the 0010 diesel-only checks below 0026: `below_0026`), then
  `test_w204_cold_migration.py` + `test_w206_ev_store_postgres.py` + `test_w206_ev_reads_postgres.py` 44 passed.
- Rule-8 EV probes (`tools/writer_guard_probes.py --seam`, 33 EV names): 28 CAUGHT, 5 ALLOWED, tree restored.
- `tools/check-all.ps1`: all 10 guards passed. Full backend/host suites not run (by brief).

## Commit 2 anchors (after R2/R5/R6 rulings)

- Pure module (new) `financials/ev_money.py`: price state table from "Commits 2-3" + reconciliation table; SHA row
  forms from "Use exact SHA row forms" (canonicalization = W2-06 rule, `analytics/ev.py` helpers such as `ev.plain`).
- Store: add `ev_unit`/`ev_record_failure`/`ev_pending_work`/`ev_claim_site` to
  `financials/adapters/postgres_consequence_store.py`, mirroring the cold pattern at `:513-659` and `ColdUnit`
  `:666-823` (advisory work lock, REPEATABLE READ, check basis before `revision_no`, attempt insert like
  `_cold_attempt`; no `consequence_revision_ids` column on the EV attempt table). Runner mirrors
  `financials/cold_recompute.py` (`retry_due_at` from `financials/recompute.py`).
- Enable the "inserts seen" vacuity check for `$evConsequenceTables` in rule 8 (cold precedent
  `configuration-persistence.ps1` `coldConsequenceInsertsSeen`) and add `ev ... owner insert unseen` probes.
- Inputs: exact selected `ev-session/1` assessment with both bounds equal (reconciliation "Commits 2-3"); reuse
  `EvReadService` caller-connection reads (`analytics/ev_reads.py`), S4-05 link rows as `ColdUnit.basis` does.
- Replay fixtures: `test_w205b_ev_replay_postgres.py:chain`, `test_w206_ev_store_postgres.py:run_worker`; the
  chain test recreates the module DB, so keep chain tests after `site` tests in a module.

## Open risks

- R2 decides whether any replay case can be ESTIMATED. R1: source-gate trigger is inert for ordinary batches.
- Rule-8 probes run against a committed tree only (`tools/writer_guard_probes.py` refuses a dirty `backend/`).

## Run 2 (2026-10-20): stopped on pending ruling R7

- Landed `7cbe440c`: q1 R3 (`TestMigration0026::test_r3_store_publishes_ev_tariff_and_public_post_stays_401`:
  store publish under SYSTEM_PUBLISHER/SYSTEM_FIXTURE returns ID/`recorded_at`; unauthenticated POST 401, no new
  revision) and q1 R4 (`test_r4_ev_currency_and_value_validation_is_ev_only`: KES ok, ABC/0/-1 EV refused, diesel
  ABC/0 still valid). No product code changed (R4 validation was already in commit 1). Both tests pass.
- R1 not applied: its premise fails (`.agent/W2-07-pending-rulings.md` R7, with empirical failing trial). Commits
  2-3 not started. Resume: apply the R7 ruling to 0026 + the trigger test, then build commit 2 from the anchors above.
- Private DB `w207b_test` dropped at end of run.

## Run 3 (2026-10-20): q2 R7 landed; stopped at context budget before commit 2

- Landed `69ea6aee` (q2 R7): `0026_w2_ev_money.py` `ev_consequence_on_accepted()` replaced by the literal R7 body
  (immediate link trigger and its body unchanged). `test_0026_trigger_only_work_and_exact_conflict_constraint`
  splits the late delivery by wrapping `PostgresEvidenceLedger.decide_chunk` (monkeypatch; first call per batch
  snapshots work + link count), then asserts the R7 literal set: pre-decide work == after_run, link==1, gate
  disjoint; post == after_run | late ACCEPTED_EV | gate; one row per gate hash; double re-enqueue unchanged.
- Linked non-EV batch: the registered late phase delivers exactly one (EV) batch, so the test uses the first
  upload's committed linked batches with zero qualifying EV rows (work stayed empty across that upload); asserts
  link==1 and their SOURCE_GATE hashes disjoint from final work. No later linked non-EV batch is reachable through
  the registered fixture without a new publication path (noted, not decided).
- Unlinked EV acceptance: helper `unpublished_ev_upload` re-seals one late EV envelope (new sequence/message_id and
  event_id or value) as an unpublished upload via `BatchIngestionService` + the same ledger; runs last (after
  backfill) because it makes the Site source MIXED; asserts ACCEPTED_EV only, no SOURCE_GATE, no link.
- Non-vacuity: removing the R7 `IF EXISTS ... SOURCE_GATE` block fails the test (missing gate rows); reverted.
- Resume: spec commit 2 from the "Commit 2 anchors" above plus q1 R2/R5/R6 and the reconciliation's
  "Commits 2-3" (exact-bounds selection). Commit 3 after. Private DB `w207c_test` dropped at end of run.
- Evidence (`69ea6aee`): `test_w207_ev_money_postgres.py` 5 passed; adjacent `test_w206_ev_store_postgres.py` +
  `test_w205b_ev_replay_postgres.py` + `test_w204_cold_migration.py` 37 passed (12m13s); `tools/check-all.ps1`
  all 10 guards passed. Full backend/host suites not run (by brief).
