# DS3 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a second write path into the evidence ledger. Read
`spec.md`, `rulings.md`, then the diff. Done means every question of spec §7 answers yes with evidence and every plant
below fails its named test. Run nothing heavy yourself unless a finding needs it; cite the builder's gate run at the
same commit (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **Two extractions, no behaviour change.** `admit` (ledger service) and `_enqueue_admitted` (ledger adapter) move
   lines without editing them; diff them side by side; the S2, S3 and W2-03 regression runs are in the packet.
2. **The bulk statement binds what `_persist` binds.** Compare `_BULK_EVIDENCE_SQL`'s columns and the Python building
   its arrays with `_persist`'s INSERT and parameter dict, column by column (test 3 checks the column list; you check
   the values).
3. **One transaction per batch.** `bulk_admit` does every write inside one `self._run(work, write=True)`; test 6's
   collision case shows no `ingestion_batch` row is left behind.
4. **Refusals before writes, and none recorded.** Tests 2 and 6 assert unchanged row counts; `refuse` in `bulk_load.py`
   records no `batch_refusal`.
5. **Parity is independent (W2).** Test 8's expected counts are hand literals; its comparisons read both databases
   with their own `SELECT`s, never through `bulk_load` or the ledger adapter.
6. **Guard and seams.** `git diff main...HEAD --stat` lists only spec §0's files; no change under `tools/checks/`;
   check-all passes; no HTTP module imports the bulk path (test 3).
7. **Databases.** The packet lists every clone created and dropped; all are `pg_harness`-owned `*_test` names.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | `normalized_value_text` bound from `e.value` in the bulk statement | test 8 (`accepted_evidence` rows differ) |
| P2 | `ordinal` numbered from 1 | tests 4 and 8 |
| P3 | a LIVE batch admitted | test 6 (`BULK_NOT_SIMULATED`) |
| P4 | a `Rejected` ordinal skipped instead of refusing | test 6 (`BULK_REJECTED_ORDINAL`) |
| P5 | the collision check removed (fewer ids returned ignored) | test 6 (`BULK_MESSAGE_COLLISION`) |
| P6 | the evidence INSERT in its own transaction | test 6 (collision leaves an `ingestion_batch` row) |
| P7 | a re-run raises instead of `already_loaded` | tests 5 and 7 |
| P8 | `refuse` records a `batch_refusal` row | test 6 (row counts) |
| P9 | `permitted_database` accepts any name containing `test` | test 1 (`assetops_polish_walk1113`, `assetops_op_kobo_test`) |
| P10 | the cold enqueue left out of `_enqueue_admitted` | `test_w203_*` regression |
| P11 | `main.py` imports `bulk_load` | test 3 |
| P12 | a `COPY` statement added to the adapter | persistence guard (exit and message in the packet); test 3 |
| P13 | `BULK_PUBLISHED_BATCH` check removed | test 6 |
| P14 | the commercial step writes `commercial_record` directly | `test_3a3_single_writer.py` (S1) |

## Not findings

No `COPY` (D-DS3.1). No commercial parity half (D-DS3.2). Different recompute-job row counts within D-DS3.3's rule.
No estimates for lines not received (D-DS3.8). No template ladder or world build (DS4).
