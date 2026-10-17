# W2-00 review - source-event format extension

Reviewer: fresh independent Claude reviewer (did not author the slice). Revision `482d0c5d` (detached worktree `AssetOpsV1-review5`). Diff `git diff 8f54508d..482d0c5d -- ':!.agent'` (27 files). `8f54508d` is an ancestor of the packet base `dc643215`; the only extra files in that range are `.ai/DECISIONS.md` and the task file. The review packet is on `task/W2-00-source-events` (worktree `review2`), not in the reviewed tree.

## Verdict: ACCEPT

There are no High or Medium findings. The three Lows below can go to the backlog or a small follow-up. None of them blocks the merge.

## Focus checks (against design section 1, its rulings 1-6, section 2 / migration 0020, and the rule-8 contract)

1. **Envelope.**
   - The v4 parser requires every key to be present. MEASUREMENT has 8 payload keys and EVENT has 12, with explicit nulls (`source_envelope_v4.py:397-426`).
   - A missing ID key is `CORRELATION_INVALID`, as ruling 2 says. V4 has its own `V4_MEASUREMENTS` and kind-to-outcome lists (`:61-89`).
   - The v3 module is untouched. The dispatcher sends a v4-only kind declared under schema 3 to `SCHEMA_UNSUPPORTED` at `payload.family` or `payload.measurement` (`:521-530`).
   - `event_identity_text` (`:380-389`) is canonical JSON over exactly `source` (complete), `timing{source_time,interval_start,interval_end}` and `payload` (complete). It is recomputed from the stored text, with no new column. This matches ruling 1.
2. **Batch and S2.**
   - `seal_batch_v2` reads only the header of a schema-4 text, or of a schema-3 text that carries a v4-only kind. A bad header still fails the whole batch with `INVALID_ENVELOPE`.
   - `decide` turns parser refusals into per-ordinal refusals and keeps the header's message ID (`ledger.py` `decide`). This matches ruling 3.
   - The `MESSAGE_CONFLICT` receipt bytes match the fixture frozen at `dc643215`. I re-ran that test and it passed.
3. **Collisions.**
   - The single INSERT keeps the `ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING` target.
   - Each insert runs inside its own savepoint (`postgres_evidence_ledger.py:503`). Only the two listed partial indexes become a reread. Any other integrity error is raised again.
   - `_collision` rereads in the fixed `_REREAD_ORDER`: message, then event, then session. A message row wins with DUPLICATE or MESSAGE_CONFLICT. Next comes the event row, compared by event identity. A session row is used only when neither of those exists.
   - Message+event and event+session double collisions resolve as section 2 says, and each conflict references the winning key's first row. This is tested in `test_duplicates_conflicts_and_precedence_with_receipts_after_reload`, the race test (the loser is shown blocked in `pg_stat_activity`) and the propagation test for an unlisted primary-key violation.
4. **Receipt counts.**
   - Receipt counts come from the batch tally, where all three conflict kinds land as `CONFLICT`. The Site-window conflict count keys on `conflicts_with_evidence_id`, so it covers all three.
   - `CONFLICT_KINDS` drives both list splits (`ledger_reads.py:239-240,385`). The test asserts replay counts `(5,0,2,0,3)`, with `rejected` at 0.
5. **Migration 0020.**
   - The CHECK texts match ruling 2 exactly: `accepted_evidence_ev_delta_shape` and `accepted_evidence_measurement_ids`.
   - The rest matches section 2: the event shape, kind/outcome, actor, family and ID-length 1..128 checks; both partial unique indexes on the specified columns; the correlation and session indexes; and the conflict-kind CHECK rebuilt over three kinds.
   - Existing MEASUREMENT rows satisfy every new CHECK: the new columns are null and the old columns are still non-null.
   - The downgrade refuses while an accepted event or delta, an `EVENT_ID_CONFLICT`/`SESSION_ID_CONFLICT`, or a `cold_chain` job exists. It deletes nothing, then restores the one-kind CHECK and the NOT NULLs. `TestMigration0020` proves the round trip and all four refusals.
6. **Rule 8.**
   - The guard adds a single-writer list for the ledger tables, a per-INSERT check for the message arbiter, a vacuity check and a pin on the exact `_REREAD_ORDER` line.
   - **I broke it myself:** I swapped `_REREAD_ORDER` to message, session, event in `postgres_evidence_ledger.py` and ran `tools/check-architecture.ps1`. It failed with "The evidence ledger rereads collisions in the fixed order message, event, session ... found 1: _REREAD_ORDER = (_REREAD_MESSAGE_SQL, _REREAD_SESSION_SQL, _REREAD_EVENT_SQL)". I then reverted the change and the tree was clean.
   - `writer_guard_probes.py --seam` with the 11 `w200` probes plus controls: 11/11 CAUGHT, 6/6 controls ALLOWED, tree restored.
   - The order is enforced by a fixed line rather than by behaviour, but `_collision` iterates exactly that tuple, so the pinned line is the real control flow. The behaviour is proven separately by the Postgres tests.
7. **Deviations.**
   - Producer and profile are deferred to W2-02 and W2-05b, as the task and ruling 4 explicitly allow.
   - No delta can be accepted yet, because the closed table has no `INTERVAL_DELTA` tuple. This follows from section 4 and is fine; the delta CHECK is proven by direct insert.
   - The connector public identifier is taken to be `asset.asset_code`. That is reasonable, fails closed when there is no asset, and is flagged to the Architect.
   - The open sub-codes are chosen fail-closed and recorded.
   - Snapshot keys are all-or-none. That is the stricter reading and is consistent with ruling 4's "requires all five".
   - Savepoint cost: the design text (section 2, "For each ordinal ... opens a savepoint around that INSERT") supports the implementation as written. The 144 s vs 114 s comparison is one run each, so it is not a reliable measurement. Narrowing the savepoint to EVENT rows would behave the same, because the partial indexes cannot fire for MEASUREMENT rows. That is an Architect performance choice, not a correctness defect, and it does not block the merge.

## Findings

1. **Low (test gap) - `backend/tests/test_w200_source_events_postgres.py:334`.** `test_site_evidence_and_rejection_reads_count_every_conflict_kind_as_a_conflict` stores the new conflict kinds, but it only asserts membership of the `CONFLICT_KINDS` constant. It never calls the Postgres Site-evidence read or the rejection-list read (`ledger_reads.py:239-240,385`) to show that `EVENT_ID_CONFLICT`/`SESSION_ID_CONFLICT` appear under `conflicts` and not under `rejected`. The code is correct by inspection and the receipt-count half of the plan fix is tested, but the test name claims more than it checks. **Fix:** call `site_evidence`/`rejections` through `ImportedEvidenceReads` and assert the split.
2. **Low (acceptance nuance) - `backend/assetops_backend/evidence/ledger.py:401-430`.** Ruling 4 says S2 checks "tuple, family, kind, outcome, role, unit". `_decide_v4` does not compare the binding's `role` against anything, because the closed table carries no role (deviation 4). This is harmless until W2-01 defines the cold roles. **Fix:** W2-01/W2-02 should add the role column to `V4_CHANNEL_MAPPINGS`, or the Architect should confirm that role is out of scope for W2-00.
3. **Low (residual) - `backend/migrations/versions/0020_w2_source_event.py:102`.** The downgrade allows v4 point and mean MEASUREMENT rows, whose stored `envelope_text` declares schema 4. This matches the design, which refuses only events and deltas. But after a downgrade to 0019, any 0019-era code that re-parses stored text with the v3 parser would refuse those rows. No such reader on the current path was found. **Fix:** none needed for this slice. The Architect may later decide whether the downgrade should also refuse rows with `envelope_text` at schema 4.

## Checks run (by me, at 482d0c5d)

- I used a private DB `w200rv5_test` on 127.0.0.1:55432, created it at the start and dropped it at the end.
- `pytest test_w200_source_events_postgres.py test_w200_binding_metadata.py test_w200_receipt_bytes_postgres.py gateway/tests/test_source_envelope_v4.py`: **81 passed**, 140 s.
- `pytest test_s2_evidence_ledger_postgres.py test_s2_receipt_v2.py test_s2_site_evidence_postgres.py test_s2_registered_basis_postgres.py gateway/tests/test_wire_contracts.py`: **80 passed**, 269 s. I ran it serially.
- `tools/check-architecture.ps1`: passed. With my deliberate `_REREAD_ORDER` break it failed with the rule-8 order message; I reverted the break.
- `tools/check-agent-workflow.ps1`: passed.
- `tools/writer_guard_probes.py --seam` (the w200 set plus controls): 11 CAUGHT, 6 ALLOWED, tree restored.

## Not verified by me

- I did not run the full backend suite, as instructed. I am citing the implementer's run: 2607 tests, 0 failures, 0 errors, 0 skipped, 2205 s. That run was at code revision `d9b3bd01`. Commit `482d0c5d` changes only `.ai/CODE_STATE.md` on top of it (a probe count), so the evidence applies to the reviewed code. The coordinator is running the host suite separately.
- I did not rerun the drain-test timing or the simulator suite. Layout evidence does not apply because the slice is backend only.
