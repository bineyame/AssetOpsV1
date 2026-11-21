# DS3 review packet: the bulk loader

Builder (Claude), 2026-11-21. Branch `task/DS3-bulk-loader` off `main` `8eff70625`; commits `6267f6b18` (guard gate),
`efb706103` (unit 1), `3dc53aef8` (unit 2), `@@T3@@` (test 3 binding check), `@@U3@@` (unit 3). Spec rev 2, rulings
D-DS3.1-19, reviewer guide rev 2. Evidence: `/opt/assetecon/evidence/DS3-bulk-loader/2026-11-21-build/`.
`USER_REVIEW_REQUIRED: false` (non-screen, no served text; D-DS3.7). **Mid-build questions: 3 open** (Q1, Q2 each
hold one xfail(strict) test; Q3 stops nothing): `mid-build-questions.md`.

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
   chain_input_change 4408/1526 (scopes equal), **event_outbox 1062/110** (Q2: per statement, no rule named; that
   assertion is held). **The v4 slice is held** (Q1: the real path refuses `v4.delta`).
2. Refusals before writes, one code each, nothing recorded: yes, test 6 (12 cases, counts and batch rows unchanged,
   `batch_refusal` 0).
3. Re-run loads nothing: yes, tests 5 and 7.
4. Targets and guard: yes; test 3 (targets, no COPY/MERGE/DO UPDATE, 42 columns in `_persist`'s order, binding
   value by value); guard gate below; triggers fire as on the real path (census).
5. Unreachable from HTTP; commercial only through 3A2: yes, test 3 and `test_3a3_single_writer.py`.
6. S2, S3, W2-03 unchanged after the extractions: @@REG@@.
7. Non-MINIGRID refused, unlisted integrity errors propagate: yes, test 6 `coldchain_site`, `foreign_key`.
8. Plants: 23 of 24 fail their test; P15 and P1 fail test 3's binding check (not test 8, see deviations).

## Checks (real output)

- Guard gate (D-DS3.18) at `6267f6b18` (the `_BULK_*` constants), `ASSETOPS_GUARD_PYTHON` set:
  `pwsh -NoProfile -File tools/check-architecture.ps1` exit 0, "Architecture check passed." (the script prints no
  per-check line on success). Plant P12 (a COPY literal in the adapter): exit 1, "No product writer runs MERGE or
  COPY; ... postgres_evidence_ledger.py:1264: COPY accepted_evidence (id) FROM STDIN." (`arch_p12.log`).
- Focused and regression: @@REGLINE@@
- Measurement (§5): @@BENCH@@
- check-architecture at the end: @@ARCH@@; check-agent-workflow: @@WF@@; fast check-all: @@CHECKALL@@.
- Clones (all `pg_harness.clone_database`, `*_test`, dropped in `finally`): `ds3s`, `ds3c1`..`ds3c15`, `ds3pseed`,
  `ds3preal`, `ds3pbulk`, `ds3bseed`, `ds3breal`, `ds3bbulk`, harness `ds3hone`, `ds3hsrc`, `ds3hleft`; after the
  runs no `*_ds3*_test` database is left: @@LEFT@@.

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
- Test 7's bad third batch is a LIVE batch; test 6's malformed case asserts `BatchRejected.kind` from the parser.

## Residual risk

`R-TRUST`: the command admits batches with no gateway credential, behind `permitted_database` (name, host, port)
and the SIMULATED refusal. Q3: the walkthrough database `assetops_polish_walk1113_test` passes the name rule.

## Review focus

`bulk_admit`'s order and transaction; `_bulk_evidence_params` against `_persist`; the census and the two held tests;
Q1-Q3.
