# W4-02 unit 3 handoff (complete) -> unit 4

Branch `task/W4-02-mini-grid-depth`. Unit 1 `00a5703a` (+ q1-ruling-2 repairs `1c1655ed`..`57aaf24e`); unit 2
`0f70936f` (unit-2 readings 1-15 are in this file's git history at `aca68ab4`; q2 is being ruled on them, reading 8
`HEADROOM_NON_POSITIVE` included; unit 3 did not touch unit-2 code). Unit 3: `97401ff0`, `e8142298`, `596d8368`,
`535658be`. `git merge main` at start: already up to date.

## Unit 3 anchors
- `mini_depth/rules.py` (still pure): fuel `SfcValue`, `FuelInputs(sfc, upper_multiplier)`, `FuelRow`, `FuelHour`,
  `FUEL_TERMS`, `assess_fuel_hour`; backup `Observation` (STATE/EVENT rows), `Step`, `Recovery`, `BackupChain`,
  `BackupHour`, `BACKUP_STEPS`, `assess_backup_hour(w, observations, readings, recovery_target_min)`.
  Unit 4 `inputs.py` supplies SFC revisions (selected as `financials/fuel_cost.py` does), `fuel_cost.MULTIPLIER`,
  the `backup-recovery-target` value in minutes, and `Observation`s (may include the last supply state before the hour).
- `contracts/.../source_envelope_v4.py`: `V4_MINI_MAPPING_PROFILE_ID/VERSION` (`authored-mini-depth-cases`/1),
  `V4_MINI_CHANNEL_MAPPINGS` (exact three B2 rows), added to `V4_CHANNEL_MAPPINGS` and `..._BY_PROFILE`.
- `sites/binding_service.py`: `_V4_TABLE_BY_ROLE_SET[minigrid-roles-4]` = that table; `_MIXED_V4_ROLES_BY_ROLE_SET`
  implements q1 ruling 1 (v4 roles need their exact tuple, publish or not; v3 roles may not take a tuple; metadata
  pinned only on the three). `_decide_v4` unchanged.
- `evidence/adapters/postgres_evidence_ledger.py`: `_site_type_on` + cold append requires `site_type == "COLDCHAIN"`.
- MG-W402-001: `backend/tests/fixtures/w4/mg-w402-001.yaml`, `backend/conversions/mg-w402-001-minigrid-roles-4.json`
  (20 rows), `sites/w402_demo.py:install_mg_w402_site` (+ `python -m assetops_backend.sites.w402_demo --tenant demo`).
- Authored cases: `backend/conversions/w4-mini-depth-cases-v1.json` (registered in `authored_fixture_specs.py`),
  `tools/w402_mini_depth_cases.py` (`load_spec`, `plan_variant`, `build_batches`, `seal_for`, `accepted_ids`,
  `message_ids`, `replay_record`; CLI `run --api --credential-file --out` posts over HTTP).
- Tests: `test_w402_rules.py::{test_fuel_interval_and_completeness,test_backup_chain_order_and_no_event}`;
  `test_w402_site_registration_postgres.py::test_mg_w402_import_binding_and_kobo_rerun_isolation`;
  `test_w402_authored_v4_postgres.py::{test_w402_v4_mapping_exact_rows_and_metadata,
  test_w402_mixed_v3_v4_binding_publish_refusals,test_w402_authored_backup_batch_accepted}`;
  `test_w402_cold_enqueue_gate_postgres.py::test_site_type_gates_cold_jobs_even_for_shared_role`.
  Updated: `gateway/tests/test_source_envelope_v4.py` (global count 32), `test_w205a_ev_foundation_postgres.py`
  (legacy filter excludes mini tuples), `test_s3_role_vocabulary.py` (stale unit-1 `not serves(roles-4)` literal).
- Non-vacuity: removing the `COLDCHAIN` condition fails the gate test; disabling the mixed v3 skip refuses every
  MG-W402-001 v3 channel (`BINDING_CHANNEL_V4_UNKNOWN`). Both reverted by `git checkout`.

## Readings applied in unit 3 (for review; none changes a spec rule)
1. Fuel: one SFC must be in force over each whole interval (none, several or non-positive -> expected use null).
   `nominal_l` = sum(kW x h x SFC); `expected_use_l = {0, multiplier x nominal}` only for a COMPLETE generator series.
2. Fuel opening/closing = the GOOD `fuel_level` reading(s) at the earliest/latest in-hour instant: basis
   ACCEPTED_READING, treatment MISSING (no uncertainty property), value null; differing values at that instant ->
   CONFLICT. No reading -> basis/treatment MISSING. DELIVERIES = AUTHORED_EVIDENCE_UNAVAILABLE/COMPLETENESS_UNCONFIRMED;
   RESIDUAL = MISSING/MISSING. USE treatment CONFLICT on a generator conflict, else MISSING when not computed.
3. Fuel limitations always include `DELIVERY_COMPLETENESS_MISSING` and `CLOSING_READING_MISSING` (no bounded closing
   in W4-02); `COVERAGE_GAP`/`CONFLICT` as for other domains. **Fuel status is never SUPPORTED** (residual is never
   established): LIMITED on conflict/gap, else UNKNOWN, even with a modelled expected use. Flag for review.
4. Backup outage = an observed `site_supply_state` ENERGIZED->LOST transition with LOST inside the hour; a LOST with
   no earlier ENERGIZED observation witnesses no loss. The outage ends at the next ENERGIZED or the hour end.
5. REQUEST = first START_REQUEST/REQUESTED in the outage; START = START_RESULT(s) with the same correlation after
   it (differing outcomes -> CONFLICT); `chain_id` = that correlation ID, else the LOSS evidence ID.
6. POWER = first `mini_backup_bus_state` ENERGIZED after START plus a usable `generator_power` interval > 0 ending
   after it; LOAD = first critical delivered interval > 0 starting at/after POWER (at = interval start); SERVICE =
   end of the first aligned critical interval from LOAD with delivered >= requested. Steps after a failed or
   conflicting start stay MISSING.
7. PASS/FAIL need a declared target: PASS = all six OBSERVED, strictly increasing, recovery seconds (SERVICE - LOSS)
   <= target; FAIL = recovery > target, or no SERVICE while complete aligned critical requested/delivered cover
   [LOSS, LOSS+target) inside the outage with delivered < requested throughout. Otherwise INCOMPLETE.
   `critical_recovery` only with a complete chain and target. `service_outcome` RECOVERED also for a complete chain
   without a target (result INCOMPLETE). Card `critical_recovery` = the latest chain's.
8. Backup status: conflict -> LIMITED; >=1 chain and all PASS/FAIL -> SUPPORTED; else UNKNOWN with
   `BACKUP_CHAIN_INCOMPLETE` (no chain included); `RECOVERY_TARGET_MISSING` when no target. Hour coverage = critical
   requested/delivered interval coverage (supply state is instant and covers 0 s, so Q22's "No outage in the selected
   hour" is never reachable from instant reports; UI shows `No complete outage chain can be assessed`). Flag.
9. MG-W402-001 Foundation: KOBO-shaped components with `SITE` property sources, `pv-available-uncertainty` 1 kW,
   `renewable-retained-margin` 3 kW, `backup-recovery-target` 5 min on the one `ac-bus`; both mini bus meters on
   `ac-bus`; no legacy `signal_mappings` (all bindings `legacy_mapping_id: null`). The clinic has no
   `feeder_requested_power` binding (its one `requested-power` channel is the critical request; unit-2 reading 12).
10. Event `component_id` is the literal `generator`. Import path is the absolute fixture path per closure 5 (a moved
   checkout re-importing into the same DB would be `ImportConflict`).
11. Authored cases: positive = five noon hours 2026-10-06..10 (one-minute means; feeders 8/4/8 kW, PV 20, capability
   42, charge 0, critical 4/4) with the backup chain on 2026-10-06 (critical deficit 12:10-12:12 makes that day
   EXCLUDED for renewable); missing-conflicting = 2026-10-12 noon without requests/charge/backup bus, an overlapping
   PV minute and contradictory start results. In-process proof: every authored row ACCEPTED, mini jobs, zero cold.
12. Unit-3 replay ran in process (`BatchIngestionService.submit` with the registered principal), not over HTTP:
   the CLI `run` path (server + issued credential) was not executed this run. Unit 4 reruns it for selection seqs.
13. Closure 5's "rejects an unregistered fixture ID" = `AuthoredFixtureSpecs.declared(...)` returns None (unknown).

## Checks (private DB `w402d_test`, dropped afterwards; no full suite)
- Focused + adjacent, `-n 3 --dist loadfile`: unit-3 files, `test_w402_migration_postgres`, `test_w402_rules`,
  `test_w402_roles_properties`, `test_s2_evidence_ledger_postgres`, `test_w200_source_events_postgres`,
  `test_w200_binding_metadata`, `test_w201_cold_vocabulary`, `test_w202_cold_lab_bindings_postgres`,
  `test_w205a_ev_*`: 230 passed (3m53s); the 7 failures + 2 errors in that run were gateway files collected from
  `backend/` (rootdir import) plus the stale `test_s3_role_vocabulary` literal, since fixed. Gateway files from
  `gateway/`: 93 passed. Cold/provenance adjacent (`test_w203_cold_reads/replay`, `test_w204_cold_worker`,
  `test_w301_provenance_dto`, `test_w202_cold_replay`, `test_s3_role_vocabulary`, `test_w205a_ev_foundation`):
  74 passed (8m43s).
- `tools/check-all.ps1`: all 10 guards passed.

## Next: unit 4
Enqueue/worker (`mini_depth/worker.py`, domain-filtered lease/settle on `postgres_assessment_store.py`, S7 tick
stage), `inputs.py` (closure 1 Q13 cutoff query; `AcceptedReading` -> `Reading`/`Observation`; SFC, multiplier,
Foundation properties, pinned `site.timezone`), `projection.py`, selection proof; rerun the authored cases (N4) to
record five local-day selection seqs and revision IDs. Apply the q2 ruling to unit-2 code when it lands.
