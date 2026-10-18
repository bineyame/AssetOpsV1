# W2-04 phase handoff - run 2 (spec commit 1 COMPLETE)

Branch `task/W2-04-cold-site-evidence-money`. Spec commit 1 is three commits:

- `11abf439`: the 0023 schema (run 1).
- `07e51a0d`: 1a, aligning 0023 with the Architect's Q1-Q10 rulings (`.agent/W2-04-build-spec.md`, section "Final
  Architect rulings").
- `527d5342`: 1b, the rule-8 policy and probes.

Nothing is merged. The private DB is `assetops_w204_test`. The environment lives in the scratchpad file
`w204env.sh`. It sets PYTHONPATH, `ASSETOPS_TEST_DATABASE_URL`, `ASSETOPS_GUARD_PYTHON` and `PY`, then changes into
`backend`.

## Landed in this run

### 0023 changes (`backend/migrations/versions/0023_w2_cold_consequence.py`)

- **Q1, room:** `cold_consequence_room(tenant, site, assessment_revision_id)` takes the one `COLD_ROOM` component of
  the Foundation listed in `analytic_run.foundation_revision_ids` for the assessment's run. It maps that component
  to a scoped `asset` by `asset_code`.
  - This is the same lookup as `postgres_assessment_store.py:cold_inputs` `asset_of(room)`, which W2-03 uses for
    `ColdPolicy.room_asset_id`.
  - All three triggers and both backfills use it.
  - The episode asset and the Finding subject are no longer used, so the generator is never stored.
- **Q8:** zero rooms, or more than one, raises and rolls back the W2-03 append. An empty window fails the work CHECK.
- **Q3:** `cold_consequence_instant(timestamptz)` writes whole seconds, or `.ffffff` when the microseconds are
  nonzero. `cold_consequence_dirty_key` uses it.
- **Q2:** every head subquery (max-revision, link and evidence) is scoped by tenant and Site.
- **Q7:** a CHECK limits `source_classification` to `AUTHORED_DEMONSTRATION`, `REGISTERED_SIMULATION`, `MIXED` and
  `UNKNOWN`.
- **Q4, Q5, Q6:** accepted as built; no change.

### Tests

- `test_w203_cold_migration_postgres.py:Ctx` now builds `cold_room_assessment()`: a superseded Foundation valid
  only in 2000 that names `assets[0]` as `COLD_ROOM`, plus copies of the run and the assessment.
  - `ctx.assessment` and `ctx.run` are now the copies.
  - `ctx.mini_assessment` is the original, which resolves no room.
  - `ctx.room` is `assets[0]`.
  - `insert_revision(..., assessment=)` takes an override.
- `test_w204_cold_migration.py` adds:
  - Q3 golden vectors, SQL against Python, for whole-second and fractional windows.
  - Q1: EXCURSION and START_RESPONSE episodes and Findings all store the chamber room, never the generator.
  - Q8: an unresolvable room raises and rolls back.
  - Q7: two refused classes.
- Results:
  - The w204 and w203 migration tests: 16 passed.
  - `test_w203_cold_replay_postgres.py`: 14 passed. That replay fires the triggers against the real COLD-LAB-001
    Foundation, so a room-resolution failure would have raised.

### Rule 8 (`tools/checks/configuration-persistence.ps1`)

- The three tables in `$coldConsequenceTables` are appended to `$consequenceTables`. Their only owner is
  `postgres_consequence_store.py`.
- Each of them also gets its own insert-only check (failure text: "Cold consequence table '...' is insert-only").
- They are on the DO UPDATE refusal list.
- `cold_consequence_work` is trigger-only: any runtime verb against it fails.
- Owner and migration existence, and probe-name registration, fail closed.
- The Q9 migration-text check runs after stripping comments and the docstring:
  - at least one `INSERT INTO cold_consequence_work` must exist;
  - each must carry exactly one `ON CONFLICT (tenant_id, site_id, dirty_key_sha256) DO NOTHING`;
  - the file has no `DO UPDATE`.
- `$coldConsequenceInsertsSeen` counts the owner's INSERTs per table. It is not asserted yet (Q10 stages that to
  commit 2).

### Probes (`tools/writer_guard_probes.py`)

- 12 per-table probes: a foreign insert from the Finding store, plus update, delete and upsert.
- 6 `cold cold_consequence_work runtime <verb>` probes: insert, update, delete, truncate, merge and copy.
- 5 `cold work migration ...` probes, each a temporary replace or append on the 0023 file, restored afterwards.
- 4 controls that must pass.

## Probe evidence

On `527d5342`, run with `--seam` on a clean tree:

- 23 of 23 fail probes were CAUGHT.
- 4 of 4 controls were ALLOWED.
- "tree restored", exit 0.
- The seam guard passes on the clean tree.

## Next run: spec commit 2 (pure derivation, store, worker)

Read these spec sections first: "Money schema `0023` and rules" (its last three paragraphs), "Implementer dry-read:
exact backend behavior", and Q4, Q5, Q6 and Q10.

1. **Pure module.** Create `financials/cold_consequence.py` with `derive` and `basis_sha256`. No SQL and no driver.
   - Put a Python `selected_instant` here using the Q3 spelling. Have `test_w204_cold_migration._z` reuse it.
   - Put the overlap-group helper here as well: `'cold:' + sha256(canonical [t,s,ws,we,room])`.
   - Use `canonical_json` from `contracts/assetops_contracts/source_envelope.py`.
2. **Store.** Add cold methods to `financials/adapters/postgres_consequence_store.py`, the only allowed INSERT
   owner.
   - Leave out the server-time columns (Q6).
   - Check that the predecessor is the same Finding and kind (Q5).
   - Leave the mini-grid methods unchanged.
3. **Worker.** Create `financials/cold_recompute.py` with `ColdConsequenceWorker.run` and `process_one`, written
   against store protocols.
   - The store holds the lock `pg_advisory_xact_lock(hashtextextended('cold_consequence:' || work_id, 0))`.
   - Use `retry_due_at` from `recompute.py`.
   - Write a FAILED attempt in a fresh transaction.
   - When an episode trigger yields no consequence, write a success attempt with `[]` IDs.
   - A basis mismatch fails with `COLD_BASIS_MISMATCH`.
4. **Q10 assertion.** In rule 8, require each `$coldConsequenceInsertsSeen[...]` to be at least 1, beside the
   provenance loop near line 1062.
   - Write it so it fails with a "vacuous" message.
   - Prove it is not vacuous by removing one store INSERT on a committed tree.
5. **Tests.** Write `test_w204_cold_consequence.py` and `test_w204_cold_worker.py`.
   - Run the six W2-02 replays through S2 and then W2-03, reusing the `chain` fixture from
     `test_w203_cold_replay_postgres.py` and W2-02.
   - Assert Q6: server times lie inside the transaction interval.
   - Cover race, retry, idempotence and the failed attempt.
6. **Finish.** Rerun the cold probe set and the inserts-seen mutation. Commit, then write the handoff.

After commit 2, continue in spec order:

- **Commit 3:** the reads and API.
- **Commit 4:** the frontend.
- **Commit 5:** final guards, suites and the review packet.

The retro-ruling corrections below go in their own commit alongside commit 4.

## Retro-ruling corrections (carried forward, unchanged)

The exact text is in `.agent/W2-retro-rulings.md`, rows "Deviation 14" and "Deviation 17". List both in the review
packet.

- **Dev 14.** A cold Analysis link may render only after an integration test proves that the exact
  `record`/`assessment` target shows the selected cold ID in the existing Evidence Analysis route. The proof must
  show that Site, window and cutoff are preserved.
  - Until that proof exists, show the reference as labelled text with "Analysis view not available for this cold
    record".
  - Never render a dead link.
- **Dev 17.** Restore the mock's exact "Loading / batch" row label, and keep "Not established" when there is no
  loading record.
  - Make the capture/settling detector match the real loading-state element, or the exact loading sentences, rather
    than any text containing "Loading".
  - Recapture the affected cold screens.

## Open risks

- `cold_consequence_room` relies on W2-03 `record_cold_assessment` writing the Foundation ID into
  `analytic_run.foundation_revision_ids`. If W2-03 stops doing that, every cold append is refused (fail closed).
- W2-05a is building in parallel, and this run edited the shared files `configuration-persistence.ps1` and
  `writer_guard_probes.py`. Merge carefully. Before any full backend suite, confirm no other pytest is running.
