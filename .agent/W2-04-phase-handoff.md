# W2-04 phase handoff - run 3 (spec commits 1 and 2 COMPLETE)

Branch `task/W2-04-cold-site-evidence-money`. Nothing is merged. Private DB `assetops_w204_test`; environment in
the scratchpad file `w204env.sh` (PYTHONPATH, `ASSETOPS_TEST_DATABASE_URL`, `ASSETOPS_GUARD_PYTHON`, `PY`, cd
`backend`).

- Spec commit 1: `11abf439` (0023 schema), `07e51a0d` (Q1-Q10 alignment), `527d5342` (rule-8 policy and probes).
- Spec commit 2: `bf3dd9aa` (derivation, store, worker, Q10 guard, tests), `cc6f83bf` (Q10 inserts-unseen probes).

## Landed in spec commit 2

- `backend/assetops_backend/financials/cold_consequence.py` (pure; no SQL): `derive`, `basis_sha256`,
  `basis_document`, `check_basis` (raises `ColdBasisMismatch`, code `COLD_BASIS_MISMATCH`), `warranted`,
  `merged_evidence`, `source_gate` (S4-05 `classify`/`link_of` over the cited IDs; gate digest is SHA-256 of the
  canonical classify result), `overlap_group`, `selected_instant` (Q3; `test_w204_cold_migration._z` now reuses it),
  `decimal_text`.
- `financials/adapters/postgres_consequence_store.py`: `__init__(..., link_rows=)`; `cold_unit` (REPEATABLE READ,
  first statement `pg_advisory_xact_lock(hashtextextended('cold_consequence:' || work_id, 0))`) yielding `ColdUnit`
  with `work`, `targets`, `basis`, `append`, `succeed`; `cold_record_failure` (fresh transaction; records nothing if
  the work already succeeded); `cold_pending_work`; `cold_claim_site`; `cold_rows`. Server times are column
  defaults (Q6). `append` takes an extra Finding/kind advisory lock and checks the predecessor's Finding and kind (Q5).
  Mini-grid methods unchanged.
- `financials/cold_recompute.py`: `ColdConsequenceWorker.process_one/run/run_pending` on store protocols;
  `retry_due_at` schedule; empty-ID success when no Finding warrants an exposure.
- `financials/composition.py`: `build_cold_consequence_store`, `build_cold_consequence_worker`.
- Rule 8: `$coldConsequenceInsertsSeen[...] -lt 1` fails with "...insert-only check is vacuous" (after the provenance
  loop). Probes `cold <table> owner insert unseen` (x3) prove it.

## Evidence (final revision `cc6f83bf`)

- Cold probe set with `--seam` on a clean tree: 29/29 CAUGHT (incl. the 3 new unseen probes), 4/4 controls ALLOWED,
  "tree restored", exit 0. `tools/check-architecture.ps1`: passed.
- `test_w204_cold_consequence.py`: 29 passed (6 replays + late-reading history + 22 pure). `test_w204_cold_worker.py`:
  4 passed (trigger work/drain/idempotence, race, failed attempt/rollback/retry/no starvation, unpaired basis and
  foreign scope). Adjacent run on `cc6f83bf` (w204 migration/consequence/worker, s4 consequence store/recompute/dispatch/history postgres, w203 cold migration): 84 passed, 0 failed, 0 skipped, 6m38s.
- Replay results: normal and missing-probe have no exposure row. Excursion, backup-failed, late-reading (20:05) and
  contradictory each have one `UNPRICED` `PRODUCT_EXPOSURE`, REGISTERED_SIMULATION, chamber room, amounts null.
  Bounds copied from the episode: excursion 19/23, backup-failed 19.5/24, late-reading 18.5/23 degC_min. Late reading
  at 20:10 appends revision 2 with `prior_revision_id` = revision 1 and a new basis; revision 1 is unchanged.

## Implementer readings to confirm (spec does not name these values; no design was intended)

1. **Q4 vs. data.** W2-03 stores both `degree_minutes_low` and `degree_minutes_high` for the open excursion
   (`claim.open = true`; duration upper is null). As the dry-read says to copy the bounds, the row has both, and
   `OPEN_EPISODE_UPPER_UNKNOWN` is set only when the upper bound is null. So none of the six replays carries that
   limit; it is covered by a pure test. Architect question: should an open episode carry
   `OPEN_EPISODE_UPPER_UNKNOWN` (or a null upper bound) even when W2-03 gives a degree-minute upper bound?
2. **Stored codes.** Reasons are `COLD_VALUATION_NOT_APPROVED` (UNPRICED), `SOURCE_GATE_WITHHELD` and
   `TECHNICAL_CLAIM_LIMITED`. Limitation codes are `OPEN_EPISODE_UPPER_UNKNOWN`, `CONTRADICTORY_EVIDENCE`,
   `CLAIM_LEVEL_<level>`, `COVERAGE_INCOMPLETE` (below 0.8, the floor in the spec's EXCURSION_BOUNDS rule),
   `EXPOSURE_LOWER_BOUND_UNKNOWN` and `SOURCE_CLASS_<class>`; several are joined with "; ".
3. **Withholding.**
   - A technical limit nulls the quantity.
   - Withholding for the source alone keeps the proved bounds.
   - Currentness (pending or historical) is applied at read time in commit 3, not stored.
4. **Worker error codes.** `COLD_BASIS_MISMATCH` (from the spec). The others are this run's choice:
   - `COLD_RECOMPUTE_FAILED` for any other fault;
   - `STORE_UNAVAILABLE`;
   - `WORK_SCOPE_MISMATCH` for foreign work, which records no attempt.
5. **Race.** The RR snapshot starts at the lock statement, so a racing loser hits a unique constraint. It then
   records nothing, because `cold_record_failure` sees the success, and reports `already_succeeded`. The test proves
   one attempt and one revision.

## Residual

- The `SOURCE_GATE_CHANGED` worker path (`ColdUnit.targets` SOURCE_GATE SQL) has no positive test. In the chain,
  every batch is linked before acceptance, so no source-gate work arises. The 0023 trigger itself is tested in
  commit 1.

## Next run: spec commit 3 (five selected API reads)

Read the spec sections "Five API reads", "Selection, projection and capability", the dry-read rows "How does the API
keep one snapshot?", "What is a valid explicit selection/cursor?" and "What do `as_of` and contact mean?", and the
W2-03 `cold_reads.py`/`cold_assessment_api.py` anchors.

- Add `analytics/cold_site_reads.py:ColdSiteReadService` (pure; no SQLAlchemy) and `cold_site_api.py:build_cold_site_router`.
- Add read-only caller-connection methods on `PostgresAssessmentStore` and `PostgresConsequenceStore`.
- Mount the router in `main.py:create_app` beside the W2-03 and cold-foundation routers.
- Write `test_w204_cold_reads.py`.
- Consequence reads take the head per Finding/kind (highest `revision_no`), grouped by `overlap_group`. A relevant
  cold work item with no SUCCEEDED attempt means `PENDING_RECOMPUTE`.

Then commit 4 (frontend plus the retro corrections below), then commit 5 (final guards, one full backend suite and
the review packet).

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
