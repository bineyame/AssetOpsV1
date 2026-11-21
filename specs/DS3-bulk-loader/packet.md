# DS3 review packet: the bulk loader

Builder (Claude), 2026-11-21. Branch `task/DS3-bulk-loader` off `main` `8eff70625`; commits `6267f6b18` (guard gate),
`efb706103` (unit 1), `3dc53aef8` (unit 2), `149c77f7b` (test 3 binding check), `2ff3ab41a` (xdist clone
names), `68d022b3c` (unit 3), `64a2868e1` (docs), `a7f7e7547` (guard placement fix; head). Spec rev 2, rulings
D-DS3.1-19, reviewer guide rev 2. Evidence: `/opt/assetecon/evidence/DS3-bulk-loader/2026-11-21-build/`.
`USER_REVIEW_REQUIRED: false` (non-screen, no served text; D-DS3.7). **Mid-build questions: 0 open** (Q1 to Q3 answered, D-DS3.20 to D-DS3.22; no xfail): `mid-build-questions.md`.

## Outcome

A trusted build tool can load SIMULATED Batch V2 telemetry into a permitted test or audit database through the
evidence ledger's one writer, one transaction and one set-based statement per table per batch, after the real path's
own admission and `decide`; a world command loads a tenant's commercial files through 3A2's intake and its telemetry
in bulk. Parity with central ingestion holds on two Kobo days (equal rows, recompute-job rules, census).

## Files

New: `evidence/bulk_load.py`, `load_world_inputs.py`, tests `test_ds3_bulk_load.py`, `test_ds3_bulk_load_postgres.py`,
`test_ds3_parity_postgres.py`, `test_ds3_bench_postgres.py`. Edited: `evidence/adapters/postgres_evidence_ledger.py`
(3 `_BULK_*` constants, `BulkAdmitted`/`BulkAdmissionRefused`/`BULK_REFUSALS`, `_bulk_evidence_params`,
`gateway_principal`, `bulk_admit`, `_enqueue_admitted` extracted), `evidence/ledger_service.py` (`admit` extracted,
`Admission`, `Refuse`), `tests/pg_harness.py`, `tests/test_pg_harness.py`. No migration, nothing under `tools/checks/`.

## Done questions (spec §7)

1. Parity: yes for two Kobo days (10 batches, 960 envelopes): `accepted_evidence`, `ingestion_batch`,
   `ingestion_disposition` equal; dispatch coverage and mini-domain jobs equal. Census deltas real/bulk:
   accepted_evidence 960/960, ingestion_batch 10/10, ingestion_disposition 960/960, recompute_job 102/100,
   chain_input_change 4408/1526 (scopes equal), **event_outbox 1062/110** (Q2, D-DS3.21: event_outbox per statement, equal subject cover). The v4 slice of three shapes runs and passes (Q1, D-DS3.20).
2. Refusals before writes, one code each, nothing recorded: yes, test 6 (12 cases, counts and batch rows unchanged,
   `batch_refusal` 0).
3. Re-run loads nothing: yes, tests 5 and 7.
4. Targets and guard: yes; test 3 (targets, no COPY/MERGE/DO UPDATE, 42 columns in `_persist`'s order, binding
   value by value); guard gate below; triggers fire as on the real path (census).
5. Unreachable from HTTP; commercial only through 3A2: yes, test 3 and `test_3a3_single_writer.py`.
6. S2, S3, W2-03 unchanged after the extractions: yes (regression below); the 11 failures there fail identically
   on `main` `8eff70625` (`base-main.log`), so they are not DS3's.
7. Non-MINIGRID refused, unlisted integrity errors propagate: yes, test 6 `coldchain_site`, `foreign_key`.
8. Plants: all 24 fail a test (P1, P9, P15 after strengthening, below); P15 also needs the v4 slice to show in
   test 8. Plants were run before `a7f7e7547`'s placement fix (it moves types, not the planted lines).

## Checks (real output)

- Guard gate (D-DS3.18) at `6267f6b18` (the `_BULK_*` constants), `ASSETOPS_GUARD_PYTHON` set:
  `pwsh -NoProfile -File tools/check-architecture.ps1` exit 0, "Architecture check passed." (the script prints no
  per-check line on success). Plant P12 (a COPY literal in the adapter): exit 1, "No product writer runs MERGE or
  COPY; ... postgres_evidence_ledger.py:1264: COPY accepted_evidence (id) FROM STDIN." (`arch_p12.log`).
- Focused and regression at `a7f7e7547` (`regress.sh`, `-n 4`, slot `ds3-final`, 189 s): ds3 x4, pg_harness, s2_*, s3
  dispatch, w203_*, w200, s405, s4 decided_at, 3a2_*, 3a3_*: **11 failed, 568 passed, 1 skipped, 2 xfailed**. The 11
  (`test_s4_evidence_decided_at_postgres` 10 race/restart cases, `test_s2_rejection_placement` 1) also fail on
  `main` at `8eff70625` in a detached worktree (11 failed, 1 passed; `base-main.log`): pre-existing. The 2 xfails of that run were removed by D-DS3.20/21.
- Measurement (§5, `bench.log`, slot `ds3-bench`; the other heavy slot was busy, so not an idle machine): 14 Kobo
  days, 70 batches, 6,720 envelopes. Real: 48.3 s; statements accepted_evidence 6720, ingestion_disposition 6720,
  ingestion_batch 210, recompute_job 140; rows event_outbox 6748, chain_input_change 20538. Bulk: 20.5 s (wall
  includes Python parse and `decide`); statements 70 per table; rows event_outbox 84, chain_input_change 364.
  accepted_evidence 13.7 MB after on both; ingestion_batch 2.7 MB real, 1.1 MB bulk. Full JSON line in `bench.log`.
- At `a7f7e7547`: check-architecture exit 0; check-agent-workflow exit 0; fast check-all exit 0, "All 40 guards
  passed" (79 s). The first check-all (at `64a2868e1`) failed two guards: adapter imports outside
  `evidence/composition.py` (bulk_load, load_world_inputs), a driver import (`sqlalchemy.exc`) in the command, and
  `specs/INDEX.md` 9 bytes over its cap; fixed by placement in `a7f7e7547` (bulk types on the `ledger.py` port, the
  command composes through `build_evidence_ledger`), **no guard change**.
- Clones (all `pg_harness.clone_database`, `*_test`, dropped in `finally`): `ds3s`, `ds3c1`..`ds3c15`, `ds3pseed`,
  `ds3preal`, `ds3pbulk`, `ds3bseed`, `ds3breal`, `ds3bbulk`, harness `ds3hone`, `ds3hsrc`, `ds3hleft`; after the
  runs no `*ds3*` database is left (`pg_database` read on `assetops_test`: `[]`). Under xdist the worker tag is
  appended (`ds3sgw0`).

## Plants (`plants-result.txt`; each applied to the committed tree, its test run, reverted)

P2, P7, P19 tests 4/5/7; P3, P4, P5, P5b, P6, P8, P13, P16, P17, P18 test 6 (named case fails); P20 test 8
("mini-depth accepted evidence requires same-transaction ACCEPTED disposition"); P10 `test_w203_cold_replay_postgres`
(14 failed); P11, P12, P21, P23 tests 2/3/1; P14 `test_3a3_single_writer`; P22 `TestCloneDatabase`; P1, P9, P15 after
the strengthening below.

## Known deviations

- P1 did not fail test 8: every Kobo binding is an IDENTITY conversion, so `normalized_value_text` equals the value.
  Test 3 gained `test_the_bulk_statement_binds_what_persist_binds_column_by_column` (`_persist` run on a fake
  connection beside `_bulk_evidence_params`, every field distinct): P1 and P15 fail it.
- P9 ("any name containing test") did not fail the spec's test-1 list; one case added: `assetops_testbed` false.
- `clone_database` waits up to 5 s for a disposed engine's backend to exit before asserting zero sessions (seen once:
  a seed's session still listed right after dispose), as CREATE DATABASE does; the count is still named.
- The persistence guard passed at the first commit (constants only) but rejected the later imports; fixed without
  a guard change (above). D-DS3.14's harness names gain the xdist worker tag (two workers shared `ds3s` otherwise).
- Test 7's bad third batch is a LIVE batch; test 6's malformed case asserts `BatchRejected.kind` from the parser.

## Residual risk

`R-TRUST`: the command admits batches with no gateway credential, behind `permitted_database` (name, host, port)
and the SIMULATED refusal. The walkthrough database no longer passes (D-DS3.22: audit names and harness clones only).

Cover limit (D-DS3.21): an event_outbox cover is a least start and a greatest end, so a batch spanning gap days would resolve days the real path did not; checking that is DS4's. The cover test fails on a subject key it does not read (F5).

## Review focus

`bulk_admit`'s order and transaction; `_bulk_evidence_params` against `_persist`; the census and the cover test.

## Mid-build answers applied (D-DS3.20 to D-DS3.23)

- Merged `task/DS3-midbuild-answers` and main (`caaaa1174`); `check-decision-index.py` passes.
- D-DS3.22: `permitted_database` allows only `_audit*` names and harness clones (`..._pt<hex>_<tag>_test`) with a
  `walk|serve` deny. Test 1 refuses `assetops_test`, `assetops_polish_walk1113_test`, `assetops_walk_audit1121`,
  `assetops_other_test`. No other test relied on a bare `_test` name. P24 (allow widened to `_test`): test 1 fails (2
  cases). P25 (deny removed): test 1 fails on `assetops_walk_audit1121`.
- D-DS3.20: the v4 slice is event, start, point (963 envelopes in all, 3 in the v4 batch); xfail removed. `v4.delta` is
  test-6 case `v4_delta`: `BULK_REJECTED_ORDINAL`, `MAPPING_INCOMPATIBLE` in the detail, counts and batches unchanged.
  P15 (event_id/correlation_id swapped in the bulk statement) fails the v4 parity test.
- D-DS3.21: `event_outbox` parity is the event cover per (tenant, site, source, type): equal groups, bulk count at
  most real, equal subject cover; named in the census as a second per-statement table; xfail removed.
- Run (host tests inside `heavy-slot.sh --db`, harness clones only, all dropped): DS3 tests, test_s2_evidence_ledger_postgres,
  test_pg_harness, 3A2 and 3A3 files: 309 passed, 0 xfail, 99.7 s.
