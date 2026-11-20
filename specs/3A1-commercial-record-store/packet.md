# 3A1 packet: the commercial record store

Implementer (Claude, fresh `assetops-implementer`), 2026-11-20. Branch `task/3A1-commercial-record-store`, base main
`8c9af447b`, worktree `/opt/assetecon/AssetOpsV1-3a1`. Not merged. `USER_REVIEW_REQUIRED`: not set by the spec; non-screen
slice, so no owner walkthrough item. Discovery review (W5).

## Commits

- `f7b8b5bb3` migration `0063_commercial_records`, `backend/assetops_backend/commercial/**`, the two test files.
- `f1acaf201` guard registration in `tools/checks/configuration-persistence.ps1`.
- third commit: this packet, spec `Status: in_review`, `specs/INDEX.md` row, `.ai/state/data.md` entry + `index-2.md` line 147.

## Module paths (P1)

`PYTHONPATH=<tree>/backend:<tree>/backend/tests:<tree>/contracts:<tree>/simulator:<tree>/gateway:<tree>/field:<tree>/host:<tree>/tools`:
`assetops_backend` -> `/opt/assetecon/AssetOpsV1-3a1/backend/assetops_backend/__init__.py`; `assetops_contracts` ->
`/opt/assetecon/AssetOpsV1-3a1/contracts/assetops_contracts/__init__.py`; `fixtures.__file__` is `None` (namespace
package), `fixtures.__path__` = `[<tree>/backend/tests/fixtures, <tree>/host/fixtures, /opt/assetecon/AssetOpsV1/host/fixtures, editable finder]`, worktree first.

## Done (spec §7)

| # | Question | Evidence |
|---|---|---|
| 1 | One call, every outcome, a refused record never stops others | `test_a_refused_record_never_stops_the_others`, `test_a_service_ticket_is_not_commercial`, envelope x4 + tenant tests |
| 2 | Same file twice adds nothing; correction supersedes; conflict refused | `test_the_same_file_twice_...` (R8), `test_new_then_revised_then_unchanged`, `..._conflict`, `..._provenance_...` (R12), in-batch R9 test |
| 3 | Other tenant refused; append-only in DB | `test_another_tenants_batch_is_refused`, Site of another tenant -> `INTAKE_SITE_UNKNOWN`; PG `test_the_four_tables_are_append_only` (UPDATE/DELETE -> 23001 on all four) |
| 4 | 2a's 17 batches and DS1b's | 22 NEW + 1 `INTAKE_NOT_COMMERCIAL`; DS1b CLI subprocess: 142 NEW then 142 UNCHANGED, 0 rejections; all `source-emulated`; exactness over every amount/quantity in both stores |
| 5 | Lock proven; guard catches a second writer | lock proof below; three guard plants below |
| 6 | Nothing outside the list | `git diff --stat main`: migration, `commercial/**`, 2 tests, guard, packet + finish bookkeeping |

## Tests (revision `f1acaf201`)

- No DB: `test_3a1_commercial_service.py` 24 passed, 0.61 s.
- Pooled `tools/heavy-slot.sh --db`: `test_3a1_commercial_postgres.py test_pg_harness.py test_up1_reading_upload_postgres.py test_3c0a_accounts_postgres.py`: **52 passed, 0 skipped**, wall 194 s (`/opt/assetecon/evidence/3A1/build-1/pooled.log`). 3C0a's downgrade crosses 0063 green (P6).
- `tools/checks/test_estate_guard.py`: 17 passed, 532 s (`estate-guard.log`); again inside check-all (-n 4): 17 passed.
- `select-tests --base main`: `mode: full (519 of 519)`, because of the migration; not run (spec §6); the focused and regression set above stands in.
- `check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON` = main's venv; without it the chain guard cannot find Python). Fast check-all: "All 41 guards passed", 616.5 s wall (348.4 s waiting for a slot) (`check-all.log`). `check-agent-workflow.ps1` passed; `check-decision-index.py` OK.

## Lock proof (R4)

`test_lock_two_intakes_of_one_new_record`: the test holds `commercial:<tenant>`, starts two `ingest` of the same new
record, waits until `pg_locks` advisory waiters reach 2, sleeps 0.5 s, asserts both threads alive and waiters `== 2`,
releases: one NEW + one UNCHANGED, rows `[2 intakes, 1 record, 1 revision, 0 rejections]`. Writer runs
`isolation_level="READ COMMITTED"` (DB default also checked).
**Plant** (re-read moved before the lock, `existing()` outside the transaction): FAILED with
`StoreRefused('commercial_record_tenant_id_source_system_source_record_id_key')` in one thread
(`lock-plant.log`). Reverted with `git checkout`.

## Double-count proof (R7, D-3A1.8)

Month move Oct -> Nov: `latest_revisions(recognition_period="2026-10") == ()`, Nov returns revision 2, in the memory
store and Postgres; `test_the_two_stores_agree_and_sort_alike` compares both stores' rows and order under 4 filter
sets on the same IDs. **Plant** (period filter inside the DISTINCT ON): both Postgres tests FAILED, October returned
revision 1 of `MOVE` (`r7-plant.log`). Reverted.

## Guard (spec §5)

Baseline `-Only configuration-persistence.ps1` passed. Plants, each failing (logs `guard-plant-*.log`):
`UPDATE commercial_record_revision` in the writer -> "The commercial record store runs only one plain INSERT ...";
`INSERT INTO commercial_record` in `commercial/service.py` -> "A second product database writer ..."; the same INSERT
in the reading-upload writer -> "Only .../postgres_commercial_store.py writes commercial table 'commercial_record'".

## Known deviations and choices

- `ExistingRecord` carries `provenances: Mapping[str, str]` beside `versions`: R12 needs each stored version's
  provenance, and the spec's field list has no place for it.
- `StoreRefused(constraint)` in `model.py`: an integrity error leaves with the constraint name only, raised outside
  the handler (no cause, no context); `hide_parameters` alone does not hide DETAIL (P6 test).
- An UNCHANGED outcome has `revision_no = None` (nothing written).
- No mid-build question. **Mid-build count: 0.**

## Not verified

- Full suite (by design). Real concurrency beyond two writers. The in-memory lock proves nothing (R15).
- Renumbering against 3C1a: tests read head/down_revision from modules, not exercised against a second migration.

## Follow-up after review r1 (ACCEPT with Lows)

- Mid-build count 3: the three unstated choices; the Architect will ratify them in 3A2's spec.
- L1: `test_downgrade_refused_with_only_a_refused_intake` added; with `commercial_intake` removed from the 0063 refusal check it fails, restored it passes.
- L4: `service.py` imports 2a's `PROVENANCES`. Migration stays 0063; 3A1 merges first and 3C1a renumbers.
