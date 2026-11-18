# MD-0 phase 1 handoff (PARTIAL: resume at phase 2)

- Branch `task/MD-0-mechanism`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-md0`. Commits: `de327ebbb` (pre-flight), `7016c0a17` (phase 1).
- Authority: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-MD-0.md` §0-§13, as amended by **§14 MD0-PF**. Pre-flight facts with anchors: `.agent/MD-0-preflight.md`. Read both; do not re-survey what they already anchor.
- The first agent stopped at about 110k context, by the budget rule.

## Landed (phase 1)

- **`backend/conversions/mechanism-v1.json`.** Inputs only, every value with a `source`.
  - `schema` is the object `{"id","version"}`, because the registry reads `schema.id`/`schema.version` (`B/evidence/adapters/authored_fixture_specs.py:28-35`). This is a deviation from the string form in §2.1.
  - `day_sets.full` and `day_sets.states` (MD0-PF Q2 parameter). `delivery.max_envelopes_per_batch` = 256.
  - The generator reading key is named `generator`, not `state`, because L0 bans output keys.
  - `variants.close` is deferred to MD-0b (Q3).
- **`B/evidence/adapters/authored_fixture_specs.py`:** the one registry line `assetops.mechanism-dataset` (Q1). This is the only B/ change.
- **`backend/tests/mechanism_dataset.py`:** `load`/`validate` (the §2.1 rules), `day`, `local_instant`, `mechanism_db_allowed`/`require_mechanism_db` (R2), `fill_target` (§4 refusals), and `MechanismRefused`.
  - Code choice to record: an undeclared day → `DUPLICATE_DAY`, a non-fillable gap → `DAY_HAS_EVIDENCE`, a wrong kind → `PREPARE_ONLY_KIND`.
- **`backend/tests/test_md0_fixture.py`:** L0, 20 passed.
- **Checks:** `test_s405_publication_postgres.py` 21 passed. Guards A and W passed.

## Build facts the next phase needs

- **Batch limit.** At most 256 envelopes per batch (`contracts/assetops_contracts/ingestion_batch_v2.py:203`). Group by device, chunk at 256, and give each chunk a decision instant ≥ its last source time + 5 min. Run workers with a clock ≥ the **latest** decision instant, or their jobs stay PENDING (seen in the spike).
- **Authored publish before submit.** Write each sealed batch body to a temp file, then call `publish_source.main(["--site", code, "--fixture-id", "assetops.mechanism-dataset", "--fixture-version", "1", "--batch-file", path], ledger=PostgresEvidenceLedger(URL), specs=build_authored_fixture_specs())`, then submit (`T/test_w402_reads_postgres.py:122-146`). `evidence_publication.recorded_at` = build time (no clock seam): an R4 entry → DD-1, listed in the packet.
- **Kobo.** Start from `CaseRunner` (`T/test_s4_finding_store_postgres.py:79-180`: `seal`, `submit`, `match`). The Kobo configuration is not `DEMO`: use `tools/demo_combined_kobo.py:76 configure_at(store, result, install_at)` (roles-2 → roles-3 → uses → roles-4). Build a CaseRunner-like class in `mechanism_dataset.py` that owns its resources (R5), not a subclass with the s4 setup.
  - Spike numbers: 2,016 readings per day, 13 batches, 40 s ingest, 11 s `chain_snapshots`.
- **Noon (P4).** The w4 spec has only the `positive` and `missing-conflicting` variants, for MG-W402-001 (hours 09:00-10:00Z). Build D12/D13's noon hour from `positive` via `cases.build_batches` (`T/test_w402_reads_postgres.py:136`), remapped to KOBO-001's roles-4 bindings; if remapping is not possible, report it. Other days keep the normal hour; report the product's eligibility.
- **Cold.** `install_cold_lab` (`B/sites/cold_lab.py:53`). The time zone is Africa/Addis_Ababa. 11 channels; the failure shape is `T/fixtures/w2/cold-w203-vectors.json` `backup-failed`.
  - `ColdAssessmentWorker(store, findings, clock=)` writes COLD_START_FAILURE inside the worker (`B/analytics/adapters/postgres_finding_store.py:595`).
  - backup_start_chain needs start-response windows that cover 100% of the day (`B/chain/measure_impls.py:294-309`). Report the grade the product gives.
- **EV.** `install_ev_lab` (`B/sites/ev_lab.py:52`). Vectors from `T/test_w205b_ev_replay_postgres.py:100-134`. `EvAssessmentWorker` (`B/analytics/assessment_worker.py:309`). Jobs are enqueued by trigger (migration 0025) at DB time.
  - GAP-E2: leave D2's job unrun. Check how to skip one job (for example, run with `assess_explicit` for D9 only); never delete a job row.
- **Actions.**
  - ACT-K1: the s6 harness (`T/test_s6_action_store_postgres.py:61-131`), `store_accept(..., at)` (`T/test_s6_verification_evaluator_postgres.py:189`), then `ActionService.apply` with `effective_from` and the clock at story time. **It stops at CHANGE_APPLIED (Q3).**
  - ACT-C1/E1: `PostgresDomainIntentStore(test_db_clock_override=)` and `PostgresWorkStore(test_db_clock_override=)`.
  - ACT-C1 adds a maintenance record at D7 09:55 before COMPLETE (Q6; find its writer in `B/work/service.py`).
- **Prices.** `tools/demo_combined_kobo.py:137 publish_price` and `tools/demo_combined_ev.py:240 publish_tariff`. MG-1 is declared at build time through `B/declare_objective.py:68 main` (Q5).
- **Derived chain.** `B/chain/backfill.py:108 _step_a`, then `run_threads(..., ("b","c","d"))` (:33), then `B/scheduling/stages.py:273 chain_snapshots` and `:203 chain_threads` per Site.

## Remaining (phases 2-3)

1. **Phase 2.**
   - `seed_database(store, engine, variant="main", day_set="full")`: call `require_mechanism_db` first. Seed order per §3, steps 1-10, with no step 9 (Q3).
   - Return a plain manifest keyed by anchor. Register `("mechanism_dataset", "seed_database")` in `T/setup_cache.py:77-81`.
   - Add `fresh(variant, day_set)`. Write `backend/tests/test_md0_mechanism_postgres.py` tests 1-4 and 7:
     - kobo-generator is ACTION_IN_HAND then CHANGE_APPLIED; RESOLVED is not reached (Q3);
     - cold-start-failure: record D-AW-3 (the D13 occurrence while CHANGE_APPLIED) verbatim from `run_lifecycle(...)["skipped_causes"]`;
     - for disagreements, use `pytest.xfail("MD-0-Fn ...")` (R7).
   - Measure the first build for **both** day sets (Q2) and the cache hit with VERIFY (test 9).
2. **Phase 3.**
   - `late_fill` (tests 5-6) and `build_work`.
   - `tools/mechanism_dataset.py build|drop` (main only; close → MD-0b).
   - R8/R9 in `tools/checks/chain_coherence.py:1012-1031,698-719`, with tests in `tools/checks/test_chain_coherence.py`.
   - `expected-mechanism.json` as `[]`, the P7 `chain_clone` name, L3m, the packet `.agent/review-packet-MD-0.md`, and the ACTIVE_CONTEXT/CODE_STATE updates.
   - Cold `days.json` entries are `[d-1 21:00Z, d 21:00Z)` (Q4).

## Open risks

- The full-day build is about 25-30 min (P0). Run one DB build at a time, foreground, in chunks of ≤ 600 s; use a per-Site seed entry if one call would exceed the cap.
- The noon `positive` remap onto KOBO-001 roles-4 has not been checked.
- backup_start_chain on quiet days and Cold PARTIAL on D3 have not been measured.
