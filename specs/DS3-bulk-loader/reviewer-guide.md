# DS3 reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake answers D-DS3.9 to D-DS3.19 folded in). Discovery review (W5): a second write path into the evidence ledger. Read
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
4. **Refusals before writes, in order, and none recorded.** Tests 2 and 6 assert unchanged row counts; `refuse` in
   `bulk_load.py` records no `batch_refusal`. `load` follows spec §2.4's table order; "same batch ID, other bytes" is
   `BATCH_ID_CONFLICT` from both `admit` and `bulk_admit` (no second code); `_check_claims`'s `BatchRefused` is
   caught around `admit` only and re-raised with its `kind`; `gateway_principal` has no disabled filter (D-DS3.9).
   Only `_COLLISION_INDEXES` map to `BULK_MESSAGE_COLLISION`; other integrity errors propagate (D-DS3.15).
5. **Parity is independent (W2) and covers what triggers write.** Test 8's expected counts are hand literals; its
   comparisons read both databases with their own `SELECT`s, never through `bulk_load` or the ledger adapter. The
   census enumerates tables from `information_schema` at run time (not a hand list of today's triggers); only
   `recompute_job` and `chain_input_change` have their own rules; a mini-domain job exists (the relabel took
   effect); the v4 batch is in the equal-rows lists (D-DS3.10, D-DS3.11).
6. **Guard and seams.** `git diff main...HEAD --stat` lists only spec §0's files; no change under `tools/checks/`;
   the packet shows the first-commit `check-architecture.ps1` run (exit 0, at the commit holding the `_BULK_*`
   constants; D-DS3.18) and check-all at the end; no HTTP module imports the bulk path (test 3).
7. **Databases.** The packet lists every clone created and dropped; all come from `pg_harness.clone_database`, are
   `*_test` names, and no test reads the module `URL` for a connection (D-DS3.14). `permitted_database` checks host
   and port as well as name (D-DS3.12).
8. **Site types.** `bulk_admit` refuses a non-MINIGRID Site before any write (D-DS3.11); the check is not weakened to
   pass test 8.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | `normalized_value_text` bound from `e.value` in the bulk statement | test 8 (`accepted_evidence` rows differ) |
| P2 | `ordinal` numbered from 1 | tests 4 and 8 |
| P3 | a LIVE batch admitted | test 6 (`BULK_NOT_SIMULATED`) |
| P4 | a `Rejected` ordinal skipped instead of refusing | test 6 (`BULK_REJECTED_ORDINAL`) |
| P5 | the collision check removed (fewer ids returned ignored) | test 6 (`BULK_MESSAGE_COLLISION`) |
| P5b | every `IntegrityError` mapped to `BULK_MESSAGE_COLLISION` | test 6 (the foreign-key case expects `IntegrityError`) |
| P6 | the evidence INSERT in its own transaction | test 6 (collision leaves an `ingestion_batch` row) |
| P7 | a re-run raises instead of `already_loaded` | tests 5 and 7 |
| P8 | `refuse` records a `batch_refusal` row | test 6 (row counts) |
| P9 | `permitted_database` accepts any name containing `test` | test 1 (`assetops_polish_walk1113`, `assetops_op_kobo_test`) |
| P10 | the cold enqueue left out of `_enqueue_admitted` | `test_w203_*` regression |
| P11 | `main.py` imports `bulk_load` | test 3 |
| P12 | a `COPY` statement added to the adapter | persistence guard (exit and message in the packet); test 3 |
| P13 | `BULK_PUBLISHED_BATCH` check removed | test 6 |
| P14 | the commercial step writes `commercial_record` directly | `test_3a3_single_writer.py` (S1) |
| P15 | `event_id` and `correlation_id` swapped in the bulk statement's arrays | test 8 (v4 batch's `accepted_evidence` row differs) |
| P16 | `gateway_principal` keeps `disabled_at IS NULL` | test 6 (disabled gateway gives `BULK_UNKNOWN_GATEWAY`, not `GATEWAY_DISABLED`) |
| P17 | `load` lets `_check_claims`'s `BatchRefused` escape | test 6 (disabled source: `BulkLoadRefused` expected) |
| P18 | the non-MINIGRID refusal removed from `bulk_admit` | test 6 (`BULK_SITE_TYPE_UNPROVEN`) |
| P19 | `bulk_admit` calls `_enqueue_admitted` with an empty list | tests 4 and 8 (dispatch coverage) |
| P20 | the bulk evidence and disposition inserts in two transactions | test 8 (`enqueue_mini_depth` raises 23514 at the first commit) and test 6 (P6) |
| P21 | `permitted_database` ignores host and port | test 1 (`10.0.0.5`, port 5432) |
| P22 | `clone_database` does not register its name | `test_pg_harness.py` (cleanup leaves the clone) |
| P23 | the world command passes the tenant directory, not `commercial/`, as `--dir` | test 2 (stub's `--dir`) |
| P24 | `permitted_database`'s allow widened back to any name ending `_test` | test 1 (`assetops_polish_walk1113_test`, `assetops_test`) |
| P25 | the `walk\|serve` deny removed | test 1 (`assetops_walk_audit1121`) |

## Not findings

The 11 failures identical on `main` at `8eff70625` (`test_s4_evidence_decided_at_postgres` x10, `test_s2_rejection_placement` x1; D-DS3.23). `event_outbox` rows fewer in bulk with the same subject cover (D-DS3.21). `v4.delta` refused in bulk (D-DS3.20). No `xfail` may remain in `test_ds3_parity_postgres.py`: one is a finding. A bare `*_test` database no longer passes `permitted_database` (D-DS3.22). 
No `COPY` (D-DS3.1). No commercial parity half (D-DS3.2). Different dispatch or cold recompute-job row counts within
D-DS3.3's rule; fewer `chain_input_change` rows in bulk with the same scopes (D-DS3.10). Zero
`financial_consequence_work` and EV consequence work on both paths (D-DS3.10's stated limit). No bulk loading at
cold-chain or EV Sites (D-DS3.11). No estimates for lines not received (D-DS3.8). No template ladder or world build
(DS4).
