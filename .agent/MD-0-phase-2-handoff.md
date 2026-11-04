# MD-0 phase 2 handoff (PARTIAL: resume inside phase 2)

- Branch `task/MD-0-mechanism`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-md0`. Read `.agent/MD-0-phase-1-handoff.md` first; this file only adds to it.
- The second agent stopped at about 95k context, by the budget rule. It ran no DB build and took no measurements.

## Landed (this commit, drafted and not yet run against a DB)

- `backend/tests/mechanism_dataset.py`, after `fill_target`:
  - `Deliverer.deliver(rows, real_clock=False)`. Groups rows by device and chunks them at 256. Each chunk is written to `work/batch-N.json`, published through `publish_source.main` (`assetops.mechanism-dataset` v1), then submitted with the decision clock at last source time + 5 min. `real_clock=True` is the late_fill path. It tracks `latest`, `batches` and `readings`.
  - `kobo_rows(spec, n, kind)`. Smoke-checked: 2,016 rows per day; the D4 overrun has 13 RUNNING steps (08:00-09:00 local, both ends included); D4 runs 21:00Z D3 to 20:55Z.
  - `KoboSite(spec, store, engine, work)`. It runs `converted_enabled`, `demo_combined_kobo.configure_at` (install_at from the fixture), the reserve/runtime controls, then `Kit` on the latest (roles-4) binding set. It also exposes the S6 runner surface (`tick`, `step`, `reload`, `tenant`, `site`, `engine`, `findings`).
  - Methods: `deliver_day`, `settle_day(n)` (dispatch assess at day end + 10 min, at or after `latest`; mini-depth noon reconcile; match), `studies()` (`mini_decisions.worker.build_worker` reconcile + run_pending, lease clock at window end + 30 min), `close`.

## Not done (resume here, in order)

1. **`seed_database(store, engine, variant="main", day_set="full") -> dict`.**
   - Call `require_mechanism_db(engine)` first. Make a tempdir work folder.
   - Steps:
     - `KoboSite`;
     - `publish_price(url, recorded_at)` (`tools/demo_combined_kobo.py:137`) at D0 12:00 local;
     - `B/declare_objective.py:68 main` at build time (R4 → DD-1);
     - for each `day_sets[day_set]["kobo"]` day: `deliver_day` + `settle_day`;
     - `studies()`;
     - ACT-K1, then step 10;
     - dispose everything.
   - Return the manifest by anchor (Finding id by `anchor_start`).
2. **ACT-K1.** `test_s6_action_apply_postgres.applying(runner)` / `test_s6_verification_plan_postgres.verifying(runner)`: pass the `KoboSite` as `runner`.
   - Set `h.clock.at` to D11 13:00 local, then `h.recommendation(fid)` and `h.accept(...)`.
   - At D11 14:00, POST `/apply` with `effective_from` D12 00:00 local, following `tools/demo_combined_kobo.py:420-428`. Then `assess` + `match`.
   - Stop at CHANGE_APPLIED (Q3).
   - Caveat: the `Harness` uses its module-global `URL` (env `ASSETOPS_TEST_DATABASE_URL`), so the L3m tool must set that env var to the mechanism URL before it imports.
3. **Step 10.**
   - `B/chain/backfill.py:108 _step_a(reader, t, s, url, False)`;
   - `run_threads(build_thread_sources(url), build_thread_store(url), t, s, ("b","c","d"))`;
   - `stages.chain_snapshots(url, {tenant_id, site_id, consume_limit:500, items:500})` repeated until 0, then `stages.chain_threads(url, {..., limit:500})`;
   - `run_lifecycle(reader, writer, t, s)` returns `skipped_causes` (the D-AW-3 record).
4. **Cold (not started).**
   - Cold readings need **V4 EVENT envelopes**: grid-meter `event` POWER_LOSS/POWER_RESTORED, generator-controller `start-event` START_REQUEST/START_RESULT FAILED, with `record_kind`, `event_id`, `correlation_id`, `actor` and `outcome`.
   - `Kit.envelope` is V3 MEASUREMENT only. Build `SourceEnvelopeV4` + `canonical_envelope_v4_text` (`contracts/assetops_contracts/source_envelope_v4.py:126,303-351,378`).
   - Row shapes come from `T/fixtures/w2/cold-w203-vectors.json` (`normal`, `backup-failed`; 7 measurement channels every 5 min ≈ 2,016 per quiet day).
   - Install with `tools/demo_combined_cold.py:93 install`. `ColdAssessmentWorker` writes the Findings itself.
5. **EV (not started).**
   - The W2-06 path also needs a SYSTEM simulated clock attestation for every EV-LAB-001 source (`T/test_w205b_ev_replay_postgres.py:108-115`) and V4 session/connector envelopes. Check whether EV assess refuses without an attestation before you write rows.
   - If authoring V4 EV envelopes is not feasible from the vectors (`T/fixtures/w2/ev-w206-vectors.json`), report it (R7/§11 P3) rather than inventing a path.
6. **The rest of phase 2.** `setup_cache.FUNCTION_OPS` entry, `fresh()`, L2m tests 1-4 and 7, D-AW-3 record, and timings for `states`, `full` and the cache hit.
   - Fingerprint gap: `tools/demo_combined_kobo.py` is imported but is not in the setup_cache fingerprint. Note it in the packet.
7. **Phase 3** as listed in the phase-1 handoff.

## Open risks

- `KoboSite.__init__` uses `converted_enabled` (its own fixed import/convert times) and then `configure_at` at 2026-10-12. Confirm the binding valid_from order is accepted, against the demo's `pgb.imported` + `pgb.convert` at story time (`tools/demo_combined_kobo.py:340-345`).
- The noon `positive` remap is not done. The noon hour is the normal-day hour on every day, so W2 is likely to show 0 eligible days; report it (R7).
