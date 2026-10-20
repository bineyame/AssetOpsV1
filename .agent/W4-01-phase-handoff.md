# W4-01 phase handoff - run 3: commit 2 landed (2026-10-20)

Branch `task/W4-01-work-case-core` (worktree `AssetOpsV1-review5`). Commit 1 `4cb89c68`; merge of main `10d0dcc1`
(`.agent/W3-01-*` conflicts took main's version); **commit 2 `9533d97d`**. The saved patch was applied and removed.

## What landed in commit 2

- `backend/assetops_backend/work/{model,service,composition}.py`, `work/adapters/postgres_work_store.py`: the q2
  ruling 4 clock. `PostgresWorkStore(..., test_db_clock_override=None)` (constructor-only); `transaction()` takes ONE
  `command_now` per command (`SELECT clock_timestamp()` or the injected clock), kept across a 40001 retry, asserted
  UTC; `_Tx.db_now()` returns it; every W4 INSERT binds `created_at`/`recorded_at` = `:command_now`; the evidence gate
  is `accepted_evidence_by_command_now` (`received_at <= :command_now` in SQL). Composition never passes the override.
- `backend/tests/test_w401_work_service_postgres.py` (7 nodes): `VirtualDbClock` + `clocked` fixture (start
  `2026-11-01T01:00Z`, actor `occurred_at` `2026-11-01T00:59:00Z`); the positive test asserts cited `received_at <=
  command_now`, case/revision/event stamps `== command_now`, and an early-clock in-scope refusal (422, no rows).
  Foreign test: F01 public accept, then `run_case(F02)` + `accepted_before_battery_hold(h, f02, "w401-wrong-action-f02")`,
  DB-read ACCEPTED `action_event` of the second Action (same tenant/Site), wrong pair `(a1, e2)` refuses 422, no rows.
- `tools/checks/configuration-persistence.ps1`: `work` domain (adapter isolation), `$workWriter` + 11 `$workTables`
  in `$pgWriters`/`$pgWritesSeen`/`$pgDriverSeen`, sole-owner + insert-only + upsert rules, per-table
  `$workInsertsSeen` anti-vacuity, fail-closed probe-name presence. `tools/writer_guard_probes.py`: 58 `work ...`
  negatives + 11 `controls work <table> insert`.

## Checks (this run)

- Focused: `tests/test_w401_work_service_postgres.py` on private `w401c_test` (created, then dropped): 7 passed, 35 s.
- Rule-8 seam guard on the commit: 0 failures.
- Work probes (`writer_guard_probes.py --seam`, 69 names): 58 CAUGHT, 11 ALLOWED, tree restored, exit 0.
- `tools/check-all.ps1`: all 10 guards passed on `9533d97d`.

## Readings made in this run (none chosen as product semantics; confirm at review)

1. The DB `clock_timestamp()` value is normalised with `.astimezone(timezone.utc)` before the ruling's UTC assert (a
   non-UTC session TimeZone would otherwise fail it); the injected clock is asserted as given.
2. `command_now` is selected inside the first attempt's SERIALIZABLE transaction and reused on retry attempts.
3. The virtual clock returns its value then advances 1 s per call; the positive test resets it to `01:00Z` right
   before the successful create so that command's `command_now` is exactly the ruled instant.
4. All later commands in the positive test (request, record, plan, OperationalRecord) run on the clocked store with
   `occurred_at` `00:59:00Z`, not machine-time-relative values.
5. The `received_at > command_now` refusal uses clock `2026-10-29T00:00Z`, `occurred_at` `2026-10-28T23:59Z` and
   only the cited F01 evidence (no links), and asserts at least one cited row has `received_at` after that instant.
6. The foreign test's final positive create now pins F01's own pair `(a1, e1)`; no W4 case links the historical
   second Action.
7. `evidence_received` was replaced by `accepted_evidence_by_command_now` (predicate in SQL, set comparison in the
   service), matching the ruling's shape.
8. Rule 8: a `work` configuration domain was added (rule 1 adapter isolation required it; not named in the spec).
   The work store reuses `$actionForbidden` (any ON CONFLICT is refused). Probes are per table for foreign INSERT,
   UPDATE, DELETE, DO UPDATE and owner-insert-unseen; TRUNCATE, MERGE and COPY are one store-level probe each.
9. Q2 reading 1: no "active state" note existed in code; a clarifying comment was added at the REOPEN cells
   (`model.py`).

Q2 readings 2-8 are implemented as ruled (unchanged from the patch). No open questions.

## Next

Commit 3 (`work_api.py`, routes, `test_w401_work_api.py` per S25/S27), then UI per the spec. Lane A's W3-01
prerequisite branch also edits `configuration-persistence.ps1`; merge-resolve both registrations later.
