# W4-02 handoff (unit 5 reads/API BUILT incl. q9) -> unit 6 renewable/service pages + Overview cards

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

## Run 4 (this run): q2 applied; unit 4 NOT started (context budget)
- Merges: main at start (handoff conflict: main carried the older unit-2 copy; this file restored from `e35d9239`
  in `4bb6f8fa`), then main again for q3 (`Run 3 rulings (q3)` now in the spec).
- Commit A `96945c4f`: q2 rulings 1-15 in `mini_depth/rules.py` + `test_w402_rules.py` (6 pass, pure).
  `REQUIRED_INPUT_UNUSABLE` ("Required reading could not be used") after `COVERAGE_GAP`, limiting;
  `Series.unusable` (in-window rows failing `_usable`, instant reports included); upper-bound
  `HEADROOM_NON_POSITIVE`; negative uncertainty = CAPABILITY_MISSING; `LoadAsset.feeder_request_bound` (new
  required 5th field; critical request used only for a critical load with no feeder-request binding);
  `_service_row` returns `_Built` (partial vs absent request); hour LIMITED on any LIMITED row; service
  `REQUIRED_INPUT_UNUSABLE` limitation cites only the unusable IDs; `critical_delivered_kw` from the one pinned
  critical asset (None when zero or several critical loads). Renewable critical series still `any_asset=True`
  (q2 14 names only the service card; unit-4 inputs should pass only the bound critical asset's rows).
  Fuel/backup do not yet raise `REQUIRED_INPUT_UNUSABLE` (q2 says units 3-5 consume the same predicates; q3 did
  not say so for fuel): open question for the next run, or apply if the Architect confirms.
- `tools/check-all.ps1`: all 10 guards passed (after commit A). No DB tests this run (`w402e_test` never created).

## Run 5 (this run): step 0 done, q4 merged, steps 1-5 NOT started (context budget)
- `git merge main` at start: up to date. Commit `46682cfc`: q3 step-0 assertions in `test_w402_rules.py`
  (fuel: same-instant tank CONFLICT, no-SFC USE MISSING/MISSING, the q3-3 status/nullable table over six cases;
  backup: bus without positive output, unaligned critical, aligned witnessed-miss FAIL + one-minute-hole
  countercase, instant supply covers 0 s). No rule change needed; 6 pure tests pass.
- Then merged main for **q4** (`Run 4 rulings (q4)` in the spec; merge commit after `46682cfc`; only `.agent/`
  files changed). `tools/check-all.ps1`: all 10 guards passed. No DB tests this run (`w402e_test` never created).
- Step-1 survey (not yet written): Dispatch `lease_job`/`_still_mine`/`complete_job`/`fail_job` at
  `analytics/adapters/postgres_assessment_store.py:313-380`; `JobLease` at `analytics/assessment_ports.py:29`.
  Guard regexes for recompute_job writes: `tools/checks/configuration-persistence.ps1:667-670` (assessment store
  may `UPDATE recompute_job SET status =`), probes `tools/writer_guard_probes.py:138`. Plan: add
  `lease_mini_job(lease, *, max_attempts, tenant_id=None, site_id=None, now=None)` (expire+lease, both with literal
  `domain IN ('mini_renewable','mini_service','mini_fuel','mini_backup')`, DB `clock_timestamp()` unless a test
  `now`), `settle_mini_job(connection, lease)` (still-mine check + `SET status = 'DONE'` with id/tenant/site/domain
  predicates, on the worker's connection so revision+selection+DONE commit together) and `fail_mini_job(...)`.

## Run 6 (this run): q4 rule repairs + step 1 done
- `git merge main` at start: up to date. Private DB `w402f_test` (dropped afterwards).
- Commit `aa5c724e` (q4 1-3, `mini_depth/rules.py` + `test_w402_rules.py`, 6 pure pass):
  - q4-1: `_unusable(r, unit=KW)` split from `_usable`: non-GOOD, nonnumeric, wrong unit or `_malformed_bounds`
    (one bound, or start>=end). GOOD numeric instants are cited, 0 s, not unusable. `_in_window` judges a
    malformed interval by `source_time`. `Series.source_ids` added; `_sources(parts)` now unions them.
  - q4-2: `RenewableInputs.critical_asset_id: UUID | None` (new required 4th field); `_pinned()` builds both
    critical series from that asset only, MISSING when `None` -> `CRITICAL_SERVICE_MISSING`.
  - q4-3 fuel: unusable bound `generator_power` row -> `REQUIRED_INPUT_UNUSABLE`, null nominal/expected, LIMITED.
    Tank candidates use `_unusable(r, "L")`. **Reading (flag for review):** a bad tank candidate makes OPENING
    unavailable when at/before the earliest valid instant, CLOSING when at/after the latest, both when no valid
    one (row basis/treatment MISSING/MISSING, citing the valid edge rows plus the bad ones); a bad candidate strictly
    between them adds only the limitation.
  - q4-3 backup: `_bad_observation` (non-GOOD; supply state not in `MINI_SUPPLY_STATES`; bus not in
    `MINI_BUS_STATES`; start kind/outcome not in `START_REQUEST/REQUESTED|START_RESULT/SUCCEEDED|FAILED` or no
    correlation). Per chain `_chain_unusable`: in-outage bus rows, start rows of the chain's correlation (all
    in-outage start rows while no request is selected), and in-outage `_unusable` generator/critical interval
    rows. **Readings (flag):** any bad supply row passed in (hour + prior witness) blocks every chain of the hour;
    an unusable chain has `result=INCOMPLETE` and `critical_recovery=None`; `BackupChain.unusable` added; hour
    limitation lists all IDs; status LIMITED. Backup critical series still match any asset (`_witnessed_miss`,
    `_interval_rows`, hour coverage): **unit 4 must pass only the pinned critical asset's rows** to
    `assess_backup_hour` (and only the pinned generator/tank rows to fuel).
  - Non-vacuity: blanking the chain `unusable` fails `test_backup_chain_order_and_no_event`; reverted.
- Commit `120ee51e` (step 1) on `analytics/adapters/postgres_assessment_store.py`: `MINI_JOB_DOMAINS`,
  `_MINI_DOMAIN_SQL` literal; `lease_mini_job(lease, *, max_attempts=3, tenant_id=None, site_id=None, now=None)`
  (expire+lease, DB `clock_timestamp()` unless `now`; returned `JobLease.knowledge_cutoff` = lease instant);
  `settle_mini_job(connection, lease)` (caller connection; still-mine `FOR UPDATE` + DONE with id/tenant/Site/
  domain/LEASED/attempts; raises `LeaseLost`); `fail_mini_job(lease, error, *, max_attempts, backoff, now=None)`
  (own txn; RETRY/FAILED/LEASE_LOST). `lease_job` now raises `ValueError` for a mini domain. Guard regex
  (`UPDATE recompute_job SET status =`) already admits these; no guard change.
  Test `backend/tests/test_w402_mini_lease_postgres.py` (2 tests). Non-vacuity: replacing the domain literal with
  `domain IS NOT NULL` fails it (the older Dispatch job is leased); reverted.
- Checks: `test_w402_rules`, `test_w402_mini_lease_postgres`, `test_w402_migration_postgres`,
  `test_s3_dispatch_assessment_postgres`, `test_w402_roles_properties` (`-n 3 --dist loadfile`): 49 passed (78 s).
  `tools/check-all.ps1`: all 10 guards passed.
- Open for step 4: the worker's cutoff. `lease_mini_job` returns the lease instant as `knowledge_cutoff`; whether
  the Q13 read uses it or a `clock_timestamp()` taken in the read transaction is not settled here (spec Q3/Q13).

## Run 7 (this run): q5 merged; q5 rulings 2 and 4 + step 2 done
- `git merge main` brought q5 (`Run 5 rulings (q5)` in the spec). Private DB `w402g_test` (dropped afterwards).
- Commit `9a64931e` (`rules.py` + `test_w402_rules.py`): **q5-4** `assess_backup_hour(..., *, critical_asset_id)`
  (required keyword); critical rows of other assets are dropped before `_witnessed_miss`/`_load_and_service`/
  `_chain_unusable`; hour coverage via `_pinned`; no pin -> chains INCOMPLETE, `CRITICAL_SERVICE_MISSING`, LIMITED.
  All selected rows (incl. unrelated assets) stay cited. **q5-2** causal supply veto: a bad supply row joins a chain
  only when at/after its usable ENERGIZED witness and at/before the restoration instant (or before hour end when
  unrestored); any bad in-hour supply row still limits the hour; every passed supply row (prior included) is
  cited. RECOVERED outcome now also requires a usable, pinned chain (q5-3). Tests: `backup()` wrapper passes
  `pin=CRIT`; two-chain/inside/edge/outside/early-prior, wrong-asset, mixed-asset, no-pin, unrelated-bad-row cases.
  Non-vacuity: making the pin filter pass every asset fails the test; reverted.
- **Not done (q5 1 and 3 test extensions):** q5-1 asks for explicit tank-edge cases (bad before/at/between/after
  two valid instants, single-valid tie, no valid) in `test_fuel_interval_and_completeness`; q5-3 a SUSPECT duplicate
  critical row with retained step timestamps. Rule behaviour already matches both rulings (readings unchanged);
  only the assertions are missing. Add them in step 3's run.
- Commits `0ed36f9c` + `9adfa90d` (step 2): `mini_depth/inputs.py` (driver-free; guard allows SQL only in the
  listed adapters + `mini_depth/store.py`) and `store.py:read_hour_rows(c, tenant, site, lo, hi, k, *, role_set,
  roles, supply_role) -> HourRows` (SELECT only, caller connection). Q13 `_ACCEPTED` (`e.received_at <= :k AND
  d.decided_at <= :k`, gate roles of 0029, overlap as `_EVIDENCE`) and `_PRIOR_SUPPLY` (all rows at the latest
  cutoff-visible supply instant before the hour). `inputs.py`: `local_hour/local_noon` (fold 0; nonexistent or
  missing/unknown zone -> `MiniInputsRefused(INVALID_WINDOW)`), `load_hour_inputs(c, tenant, site, window, k) ->
  HourInputs` (exactly one Foundation and one roles-4 set covering the hour else `CONFIGURATION_MISSING`; rows kept
  only when bound in force under that set; properties pinned to the Foundation revision; critical pin = first
  `critical-load-priority` member that is a LOAD and equals every bound critical-role asset; `LoadAsset`s from
  `feeder_demand` bindings; SFC per as-accepted Foundation revision of the pinned generator's rows plus the pinned
  one; `MULTIPLIER`). `HourInputs.fuel_readings()/backup_readings()` (pinned rows only), `committed_watermark`,
  `evidence_ids`, `digest_basis()` (includes `site_timezone`, cutoff, property/SFC revision IDs, pin) and
  `input_sha256`. Step 4 must pass the lease `knowledge_cutoff` unchanged (q5-5) inside its REPEATABLE READ txn.
- Tests: `test_w402_inputs.py` (pure windows/refusals), `test_w402_inputs_postgres.py` (MG-W402-001 + positive
  authored batches: pins, SFC, loads, one outage with witness; cutoff equality included, +1 us received or decided
  excluded, digest changes, later cutoff readmits). Non-vacuity: dropping `e.received_at <= :k` fails it; reverted.
- Checks: `test_w402_inputs`, `_inputs_postgres`, `_rules`, `_mini_lease_postgres`, `_authored_v4_postgres`,
  `_site_registration_postgres`, `_migration_postgres`, `_roles_properties`, `_cold_enqueue_gate_postgres`
  (`-n 3 --dist loadfile`): 40 passed (105 s); after the store move, the first six: 22 passed (95 s).
  `tools/check-all.ps1`: all 10 guards passed (first run failed on the driver import in `inputs.py`; fixed by the move).
- Readings for review: rows whose binding is not in force under the pinned set are dropped (not cited); the
  `local_hour` end is start + 1 h UTC; the q5-5 worker-level cutoff test belongs to step 4.

## Run 8 (this run): q5-1/q5-3 assertions + step 3 done; q6 asked
- `git merge main` at start (clean; brought W3-01 estate files). Private DB `w402h_test` (dropped afterwards).
- Commit `69adb9d9` (`test_w402_rules.py` only): q5-1 tank edges (bad before/at/between/after valid 10/50-min
  instants, single-valid tie, no valid; basis/treatment/value/citations/limitation/status/residual) and q5-3
  (SUSPECT duplicate critical row in the second of two chains: identical OBSERVED step times/IDs, INCOMPLETE/
  UNKNOWN/null, in `unusable`; first chain and hour card keep their recovery). No rule change needed.
- Commit `e0f7c9de`: `mini_depth/projection.py` (pure; imports `store.MODEL_VERSIONS/DOMAINS/MiniRevision`, no SQL):
  `assess(domain, inputs)` (fuel/backup get `fuel_readings()`/`backup_readings()`, backup the pin and target),
  `result(domain, inputs, hour)` -> `{schema_version, domain, status?, cards?, rows, limitations, coverage, basis}`
  (Q8 keys, sort orders, numbers via `_num`, times via `fuel_cost.iso`), `project(domain, inputs) -> MiniRevision`
  (evidence = `inputs.evidence_ids`, digest = `inputs.input_sha256`, cutoff unchanged). Basis = Q15 keys +
  `site_timezone`; fuel adds `generator_power_evidence_ids`, `specific_fuel_consumption_property_revision_id`.
  `cards.outage_count` is always null (q3 8). Test `backend/tests/test_w402_projection.py` (2 pure tests).
  Non-vacuity: projecting `h.outage_count` fails both tests; reverted by `git checkout`.
- Readings for review: `.agent/W4-02-pending-rulings.md` **q6 1-6** (renewable per-hour result has no status/cards;
  fuel/backup rows have no `coverage`; instant backup roles in `role_coverage` with source_count 0; SFC ID null
  when several; `source_freshness` predicate; `start_success_count` kept). Step 4 can proceed; q6 must be ruled
  before step 5's selection proof (it fixes the persisted `result` shape).
- Checks: `test_w402_projection`, `_rules`, `_inputs`, `_inputs_postgres`, `_mini_lease_postgres`,
  `_authored_v4_postgres`, `_site_registration_postgres`, `_migration_postgres`, `_roles_properties`
  (`-n 3 --dist loadfile`): 41 passed (122 s). `tools/check-all.ps1`: all 11 guards passed.

## Run 9 (this run): step 4 worker done; S7 tick stage blocked (q7)
- `git merge main` at start (clean; W3-02 `.agent` files only). Private DB `w402i_test` (dropped afterwards).
- `1e4baa8c`/`a2953175`: `mini_depth/worker.py` `MiniDepthWorker(jobs, store, lease=5 min, max_attempts=3,
  backoff=30 s, test_lease_clock=)`: `run_once/run_pending(limit, tenant_id, site_id)` lease via `lease_mini_job`
  (cutoff = lease instant, unchanged), `store.snapshot()` (REPEATABLE READ write txn) -> `load_hour_inputs` ->
  `projection.project` -> `append_selection(job_id, connection=c)` -> `settle_mini_job(c, lease)`; any error ->
  `fail_mini_job`. `reconcile(site_code, from, to)` = backfill selections (q7 R3). `hours_within()`; `MiniOutcome`.
  CLI `python -m assetops_backend.mini_depth.worker run-pending [--limit] | reconcile --site --from --to`
  (`build_worker` uses `analytics.composition.build_postgres_assessment_store`). `store.py` gained `from_url`,
  `dispose`, `snapshot`, `clock`, `site_scope` (code -> tenant/Site/timezone). `inputs.input_sha256` is now
  `sha256:<hex>` (0029 CHECK; q7 R1).
- Test `test_w402_mini_lease_postgres.py::test_mini_worker_lease_instant_is_the_one_cutoff` (q5-5: lease at T, row
  received T+1 us absent, rows at T present, re-lease at T+1 us includes it; revision+selection+DONE; Dispatch jobs
  unchanged; refusal -> RETRY with `CONFIGURATION_MISSING`; reconcile -> 4 backfill selections, no job written).
  Non-vacuity: passing `store.clock(c)` instead of the lease cutoff fails it; reverted by `git checkout`.
- Checks: `_projection`, `_rules`, `_inputs_postgres`, `_mini_lease_postgres`, `_authored_v4_postgres`,
  `_migration_postgres`, `_site_registration_postgres`, `_roles_properties` (`-n 3 --dist loadfile`): 41 passed
  (122 s). `tools/check-all.ps1`: all 11 guards passed.
- NOT built: S7 `mini` stage in `scheduling/stages.py`/`tick.py` (persisted shape needs `schedule_site_head` DDL
  outside 0029's closed catalog; see `.agent/W4-02-pending-rulings.md` q7 1-3). No CLI subprocess test yet.

## Run 10 (this run): q6 applied + step 5 done
- `git merge main` (`0b97e51d`): q6 in the spec (`Run 6 rulings (q6)`); `.agent/W4-02-pending-rulings.md` took main's
  copy as instructed, which drops this branch's q7 text (q7 is with the Architect). Private DBs `w402j_test` and
  `w402j_live_test` (both dropped afterwards).
- `a41c47ec` (q6): `rules.FuelRow.coverage` (USE = generator `gen.coverage`; OPENING/CLOSING `_instant_coverage`: 0 s,
  whole-hour gap, distinct sources of the term's usable cited tank rows; DELIVERIES/RESIDUAL 0 s, 0 sources);
  `BackupChain.coverage` (`_combined` of pinned critical requested+delivered over `[LOSS, end)`) and `start_pair`;
  `BackupHour.start_success_count: int | None` (null until one chain has an OBSERVED START with a single
  SUCCEEDED/FAILED outcome; counts SUCCEEDED pairs). `Observation.source_id` (2nd field; `inputs.py` from `r[12]`).
  `projection.py`: row `coverage` on fuel/backup rows; instant-role `role_coverage` counts usable in-hour sources;
  `specific_fuel_consumption_property_revision_ids` array; required roles with no series get a zero-coverage entry
  (service always keeps `feeder_demand`). Tests: 5 new `test_q6_*` in `test_w402_projection.py`. Non-vacuity:
  reverting the null start count and the `_bad_observation` source filter fails two of them; reverted.
- `20e8a4e7` (step 5): `store.PostgresMiniDepthStore.site_selections(tenant, site) -> SelectionRecord` (seq order,
  joined revision + exact evidence set + stored freshness); `tools/w402_mini_depth_cases.py` `selection_record()` and
  `record --replay <file>` (needs `DATABASE_URL`). Test `test_w402_replay_selection_postgres.py`: credential issued by
  the provisioning CLI, both variants POSTed to `/api/ingestion/batches` (TestClient, HTTPS boundary), worker drains
  all jobs DONE, every recorded seq joined to its Site/domain/hour revision and full accepted-ID set, exactly one noon
  selection per authored day per domain, 6 Oct backup chain observed + renewable EXCLUDED, 12 Oct backup LIMITED /
  fuel not SUPPORTED / all UNKNOWN freshness, no token in the record. Non-vacuity: dropping one ID from the recorded
  set fails it; reverted.
- Live operator run (real `serve_tls` on 127.0.0.1:18443, self-signed cert, `run --insecure`, then `worker
  run-pending`, then `record`): accepted positive 3321 / missing-conflicting 326; 394 selections, all jobs DONE (the
  install's publication enqueues every hour since its effective time). Noon seqs (local day: fuel/backup/renewable/
  service): 10-06 369/375/376/377; 10-07 370/378/379/380; 10-08 371/381/382/383; 10-09 372/384/385/386; 10-10
  373/387/388/389; 10-12 390/392/393/394. Renewable+service freshness CURRENT on positive days, fuel/backup UNKNOWN;
  12 Oct all UNKNOWN. The artifact was `var/w402/replay.json` (ignored; the DB is dropped, so seqs/UUIDs are this
  run's only; a rerun records new ones).
- Readings for review: `Observation.source_id` is required positionally after `evidence_id`; a chain's start pair
  counts only when START is OBSERVED with exactly one SUCCEEDED|FAILED outcome; tank-term source count uses the
  term's cited usable rows (in the rival case, the valid edge rows). q6 1/5 read-time parts (envelope composition,
  `STALE_SOURCE`, `test_w402_reads_postgres.py`) belong to unit 5 and are not built.
- Checks: `_projection`, `_rules`, `_inputs`, `_inputs_postgres`, `_mini_lease_postgres`, `_authored_v4_postgres`,
  `_site_registration_postgres`, `_migration_postgres`, `_roles_properties`, `_replay_selection_postgres`
  (`-n 3 --dist loadfile`): 48 passed (255 s). `tools/check-all.ps1`: all 11 guards passed.

## Run 11 (this run): q7 built (S7 tick `mini` stage); q8 asked
- `git merge main` (`5bad7625`, q7 in the spec; `.agent` conflicts none). Private DB `w402k_test` (dropped afterwards).
- `07af0afb` (+ `52e60066` probe literal fix, `8c394e93` F3 health-test expectation + q8):
  - `0029`: SCHEMA replaces `schedule_site_head_stage_check` (adds `MINI`) and adds `mini_processed/deferred/failed`
    (integer NOT NULL DEFAULT 0); `SITE_STAGE_DOWN` (after `REFUSE_IF_USED`, before `DROP`): `LOCK TABLE
    schedule_site_head IN EXCLUSIVE MODE`, ruled MINI-active refusal, four-stage CHECK restored, counters dropped.
    Docstring carries the q7 catalog. The spec's own Q25/closure-2 text was not edited (Architect document).
  - `PostgresScheduleStore.record_mini(t, s, token, processed, deferred, failed)` (nonnegative, token-scoped, one
    line), `_SITE_HEAD` + port; guard rule 8 admits the three columns; probes `q7 unlisted mini Site-head column`,
    `q7 mini counter outside the schedule store` CAUGHT, control `_OPS02_M` ALLOWED.
  - `PostgresAssessmentStore.live_mini_jobs(tenant_id=None, site_id=None)` (`_LIVE_MINI_JOBS`: FAILED live until a
    later same-Site/domain/overlapping selection); `stages.discover` adds `live_mini_jobs`; `tick.select_sites`
    unions it (excluded diagnostics carry `live_mini_jobs`).
  - `stages.mini` (child: `build_worker(lease=300 s).run_pending(limit, tenant, site)`; returns processed/failed/
    deferred/outcomes/live_jobs), `stages.MINI_JOB_LEASE_SECONDS=300`; `TickLimits.mini_jobs_per_site=10`,
    `mini_seconds=120` (0 < x < 300, in the statement-timeout min), `site_lease_seconds` 480; `_site` runs
    S3 -> MINI -> S4 -> CONSEQUENCE, records counts on OK, keeps first failure, stops on a lost claim.
  - Tests: `test_w402_mini_stage.py` (11 pure: limits, order/budget, failure retention x3, lost claim x2, selection
    with mini work, DST/partial reconcile hours, R4 CLI token, no second install path);
    `test_w402_mini_stage_postgres.py` (3: live-mini supersession matrix; real tick on MG-W402-001 incl. head counters,
    report JSON, R1 digest, decommissioned EXCLUDED_WITH_WORK; R1 reuse, R2 RETRY/RETRY/FAILED with no revision, R3
    reconcile 11:00+12:00 domains/cutoffs/jobs unchanged); `test_w402_migration_postgres.py` Site-head shape before/
    after/downgrade + `test_downgrade_refuses_active_mini_stage`. Not covered: "another Site" selection case of q7-2.
  - Non-vacuity: dropping the domain predicate in `_LIVE_MINI_JOBS` and dropping the `record_mini` call each fail a
    test; reverted by `git checkout`.
- Checks: W4-02 focused (`_mini_stage`, `_mini_stage_postgres`, `_migration_postgres`, `_mini_lease_postgres`,
  `-n 3 --dist loadfile`): 27 passed (137 s). Adjacent tick/health/deferred/decided-at/install-gate/upstream/
  replay-selection/S3 dispatch: 57 passed, 2 failed; F3 lost-claim expectation updated to `MINI` (now passes);
  **`test_s4_schedule_health_postgres.py::TestHealthAndSeam::test_fence_moved_streak_terminal_s3_failure_requeue_and_recovery`
  still FAILS** (q8: legacy MINIGRID Site keeps live FAILED mini jobs, so a decommissioned Site is still visited and
  its S4 backlog is matched). `tools/check-all.ps1`: all 11 guards passed. Writer probes (targeted): all CAUGHT/ALLOWED.

## Run 12 (this run): q8 applied
- `git merge main` (q8 in the spec; no `.agent` conflicts). Private DB `w402l_test` (dropped afterwards).
- `605ac2d7`:
  - Ruling 1: `0029` `mini_enqueue_hour` rechecks, under its advisory lock and before insert or PENDING lift, that
    exactly one current (`superseded_at IS NULL`) `minigrid-roles-4` set overlaps `[p_lo,p_hi)` and covers it whole
    (`valid_from <= p_lo`, `valid_to IS NULL OR >= p_hi`); else RETURN (no-op). Refusals unchanged. `ROLE_SET_4` literal.
  - Ruling 2: `tick.RUNNABLE_MINI_STATUSES = {PENDING, LEASED}`; `select_sites` skips FAILED mini rows (diagnostics
    list only runnable ones). `live_mini_jobs`, worker and `fail_mini_job` unchanged.
  - Ruling 3: health test unchanged in expectation; adds a zero-mini-jobs assertion for KOBO-001 before the
    decommissioned tick. It now passes.
  - Ruling 4 + tests: `test_w402_mini_stage.py` select matrix (decommissioned PENDING/LEASED selected, FAILED-only and
    orphan FAILED unselected); `_mini_stage_postgres.py` another-Site case (`_other_site` test-only Site) and tick
    tail (decommissioned PENDING visit runs S4; FAILED-only tick: unselected, no stage calls, rows+error queryable);
    `_migration_postgres.py` `mg4` fixture (relabels current sets roles-4, restored), five enqueue tests moved to it,
    `TestRoles4Gate` (legacy evidence+publication+direct call: zero jobs; straddled hour: no job, no PENDING lift).
  - Non-vacuity (reverted by `git checkout`): gate disabled -> both `TestRoles4Gate` fail; FAILED filter removed ->
    pure select test fails; `_LIVE_MINI_JOBS` site predicate removed -> another-Site assertion fails.
- Checks: `test_w402_*.py` + `test_s4_schedule_{health_postgres,install_gate,tick_postgres,upstream_unit}.py`
  (`-n 4 --dist loadfile`): 95 passed (406 s). No `test_s3*schedul*` file exists. `tools/check-all.ps1`: 11/11 passed.

## Run 13 (this run): unit 5a (reads, provenance, API) built; q9 asked
- `git merge main` (only `.agent/W3-02-0c-rereview.md` came in). Private DB `w402m_test` (dropped afterwards).
- `476773e9`:
  - `mini_depth/read.py:MiniDepthRead(engine, link_rows, *, test_read_clock_override)`, `.read(tenant_id=, site_id=,
    site_code=, domain=, lo=, hi=, known_at=)` -> envelope; `hour_windows`, `compose_renewable` (q6-1 via
    `rules.summarize_renewable` over stored hours), `MiniReadRefused(code)` 422, `MiniReadUnavailable` 503.
    Per hour `_hour`: Q14 head SQL `_HEAD`, live-job SQL `_JOBS`, STALE by `_cutoff_sha` (q6-5), lineage 503.
  - `mini_depth/provenance.py:mini_blocks(c, link_rows, t, s, ...)` -> W3-01 `dual_blocks` (detail omitted).
    `link_rows` is injected (`evidence/composition.py:build_link_rows_reader`); no adapter import (guard rule 1).
  - `mini_depth_api.py:build_mini_depth_router(reader, registry, access)`: `GET .../performance/mini/capabilities`
    and `.../performance/mini/{domain}`; mounted in `main.py` after `build_performance_router` (no Dispatch gate).
  - `tools/checks/configuration-persistence.ps1` `$pgReaders` += `mini_depth/read.py` (Q25 allowlist).
  - Tests: `backend/tests/test_w402_reads.py` (14: windows, composition, 5 parametrized refusals, N7, non-MINIGRID,
    capabilities) and `test_w402_reads_postgres.py` (3: five-day compose SUPPORTED/LIMITED/UNKNOWN, stale/pending/
    historical/equality/future cutoff, router over a real reader incl. fuel bridge order and window refusals).
  - Non-vacuity: STALE check disabled -> `test_stale_pending_and_historical_currentness` fails (reverted).
- Checks: `test_w402_reads.py` 14 passed; `test_w402_reads_postgres.py` 3 passed (192 s); `tools/check-all.ps1`
  11/11 passed. No frontend change yet.
- q9 in `.agent/W4-02-pending-rulings.md`: ten read/API readings (wire additions `basis`, no API default window,
  job visibility at a cutoff, claim downgrade, renewable aggregation, links, retained-margin source). 5b consumes
  this wire, so q9 should be ruled before or alongside 5b.

## Run 14 (this run): q9 applied to unit-5 reads/API; unit 6 NOT started (context budget)
- `git merge main` (q9 rulings, W3-02 `.agent` files). Private DB `w402n_test` (dropped afterwards).
- `190735fb` + `39a22be1` (line wrap):
  - `mini_depth/read.py`: pure helpers `site_path` (URL-encoded code), `links` (Dispatch `?day=YYYY-MM-DD` only
    for one UTC day, else null; encoded Evidence; `financials:null`; `actions:"/actions"`), `aggregate_state`,
    `aggregate_job`, `limit_claim` (q9-4; merges/sorts limitations), `renewable_envelope` (q9-6, `basis:null`),
    `check_lineage` (q9-10, 503 without IDs). `_read`/`_hour` call them; behaviour otherwise as unit 5a.
  - `mini_depth_api.py`: non-MINIGRID echoes each parseable `from/to/known_at` as UTC independently, bad -> null
    (`_lenient`); encoded Evidence link.
  - Retained margin (q9-7): no wire field added; the UI gap copy is unit 6 work.
  - Tests: `test_w402_reads.py` 21 passed (q9-1 window/known_at refusals, q9-4 downgrade, q9-5 aggregates, q9-6
    missing middle day, q9-8 links/encoding/cross-UTC-day, q9-9 exact non-MINIGRID shape + auth-before-domain,
    q9-10 lineage). `test_w402_reads_postgres.py` 5 passed (293 s): + `test_q9_2_cutoff_visible_jobs` (equality,
    lifted `available_at` invisible at k, other-hour selection does not clear, matching later selection clears),
    + `test_q9_3_read_only_stale_source` (ambiguous Foundation, changed Foundation, missing binding set via
    replica-role SQL; HISTORICAL at the old cutoff; row counts unchanged), renewable `basis:null`/no `retained`
    in wire, router `?day=` link. `tools/check-all.ps1` 11/11 passed. No frontend change; frontend suite not run.

## Run 15 (this run): unit 6 renewable page built; q10 readings logged (non-blocking)
- No main merge. `ee461681` + `512a5429` + the closeout commit:
  - `frontend/src/sites/miniDepthClient.ts`: mini client (`getCapabilities`, `getRenewable`; refusals from
    `{detail:{code,message}}`), envelope types, Site-local time helpers (`localMidnightUtc`, `localDaysWindow`,
    `renewableWindowFromParams`: URL `from/to/known_at`, else the local date of `?date=`/today's UTC day start, Q5).
  - `frontend/src/sites/MiniPerformance.tsx`: `MiniPerformanceSubtabs` (Dispatch + `/capabilities` through
    `performanceSubtabs`; `BUILT_MINI_PAGES={renewable}`; unbuilt mini tabs are left out of the row, q10-3), `MiniRenewable`
    (period bar `.site-date-bar`, 1-5 local days; loading; 401/403/404/422 API message/503 retry), `MiniRenewablePage`
    (strip, 4 cards, headroom + productive-use pair, windows table with `Not assessed` rows, blue notice, opportunity
    drawer). CSS `w4-mini-performance.css`. Shared `performanceSubtabsLabel.ts`.
  - `SiteAnalyticsFrames.tsx` `SitePerformanceFrame`: MINIGRID branch for built mini pages before the generic return;
    `miniDepth` prop (App wires `createMiniDepthClient`). `SitePerformance.tsx` imported-Site branch now renders
    `MiniPerformanceSubtabs` (MINIGRID only). `SITE_SCREEN_DESCRIPTIONS.renewable` (Q20). `settled.ts` knows
    `Loading the site's mini-grid assessment.`
  - Profile: MINIGRID capabilities `service1,dispatch2,fuel3,renewable4,backup5`; `EXPECTED_ORPHANS` lists the four.
    T028 tests now use `battery-stress` as the unknown-id example.
  - Registry/ledger: renewable pilot panels 1-3 (`gap`, awaits review), nodes `I-mini-depth-read`/`I-mini-depth-ui`
    (open, W4-02), ledger `renewable` bounded/W4-02. Service row still deferred (do it with the service page).
- **Dispatch label left as is**: the profile says `Dispatch assessment`; the imported-Site subtab row keeps
  rendering `Dispatch` (hard-coded in `MiniPerformanceSubtabs`, as before). S6 says `Dispatch`; not changed here.
- Checks: `miniRenewableRoutes.test.tsx` 7 passed (expectV69Panels + planted-panel rejection, cards, margin gap,
  missing-middle-day rows, empty, historical, drawer, 503 retry, 422 message, local-day bounds); focused
  Performance/profile set 11 files 367 passed; `tsc` 0; backend `test_t028_presentation_profile.py` 7 passed (no DB);
  `tools/check-all.ps1` 11/11 passed; full frontend suite: see the commit message of the closeout commit.
- Not done: imported-Site Dispatch route test showing the mini tabs; layout capture (unit 7 per spec).

## Run 16: unit 6 service page built
- No main merge. `8925399a`:
  - `miniDepthClient.ts`: `ServiceCards`/`ServiceRow`/`ServiceRead`, `getService`, `localWallUtc`, `localHourWindow`,
    `serviceWindowFromParams` (URL `from/to/known_at`, else local 12:00-13:00 of the local date of `?date=`/today).
  - `MiniPerformance.tsx`: `BUILT_MINI_PAGES={service,renewable}`; `MiniHourBar` (day + hour), `MiniServicePage`
    (strip, 4 cards with `Measured n of N minutes`, `Where the power went` ValueBars + hatched `What was needed`,
    addressed-load table in `.mini-service-table` (min-width 511), supported/unlock pair, verification
    `UnavailableLinkEntry`), `MiniService`. `REQUEST_BASELINE_MISSING` limitation copy.
  - `SiteAnalyticsFrames.tsx`: MINIGRID branch picks `MiniService`/`MiniRenewable` and the matching description;
    `SITE_SCREEN_DESCRIPTIONS.service` (Q20). Profile unchanged (already had `service`).
  - Registry: service panels 1-4 `gap`; ledger `service` bounded/W4-02 with `P-mini-area`.
- q10 item 5 logged (verification CTA copy, critical card label, What was needed, default hour); non-blocking.
- Checks: `miniServiceRoutes.test.tsx` 5 + `miniRenewableRoutes.test.tsx` 7 passed (renewable tab order now
  `Service, Dispatch, Renewable`); `tsc` 0; full frontend 96 files / 2385 tests passed; `check-all.ps1` 11/11.

## Run 17 (this run): main merged (q10 rulings), q10 applied, unit 6 fuel page built
- Merged main (`784b7228`, kept ours for pending-rulings). q10 applied `a82c7a6a`: renewable `statusWord` now
  LIMITED->`Evidence limited`, SUPPORTED low<=0 ->`No usable headroom`, positive but downgraded (PENDING/STALE/UNKNOWN
  currentness or UNKNOWN/MIXED/absent provenance) ->`Evidence limited`, else `Watch`; two new renewable tests.
  Registry `I-mini-depth-read` requires `A-mini-breadth-projections`, `I-mini-depth-ui` requires
  `D-mini-breadth-windows`. Ledger node_ids must equal the panel `requires` union (checker), so the A node is not
  listed on ledger rows. q10-1 (tabs) and q10-4 (Opportunity CTA) already matched.
- Fuel `f1ba0962` (+ ledger fix): `miniDepthClient.ts` `FuelCards`/`FuelRow`/`FuelRead`/`FUEL_TERMS`/`getFuel`;
  `MiniPerformance.tsx` `MiniFuelPage`/`MiniFuel` (status `Fuel balance: evidence limited|Unknown`, 4 cards incl.
  `Modelled expected use`, 5 ValueBars, 3-col bridge, notice, interpretation with inert `No linked dispatch
  consequence` + `Inspect fuel basis` drawer citing SFC revision IDs/generator power IDs); window reuses
  `serviceWindowFromParams`/`MiniHourBar`; `BUILT_MINI_PAGES` has fuel; frame branch + `SITE_SCREEN_DESCRIPTIONS.fuel`;
  registry fuel panels 1-3 `gap`; ledger fuel `bounded`/W4-02. Readings logged as pending q11 (non-blocking).
- Checks: `miniFuelRoutes` 5, `miniRenewableRoutes` 9, `miniServiceRoutes` 5 passed (tab order now
  `Service, Dispatch, Fuel, Renewable`); `tsc` 0; full frontend 97 files / 2392 tests passed; `check-all.ps1` 11/11.

## Run 19 (this run): unit 6 Overview cards built
- `88294183`: `SiteWindowOverview.tsx` `useOverviewMini`/`MiniObjectiveCard`/`serviceWords`/`fuelWords`/`renewableWords`;
  five cards kept (Service, Dispatch, Battery, Fuel, Renewable), no Backup card or Overview backup read; one shared
  `known_at`; service/fuel read local 12:00 hour, renewable the local day; `View detail →` to the Performance tab
  with exact `from`/`to`/`known_at`; failed read `Unavailable` + closure-2 note, no link. Plumbing: `SiteDetails`
  `overview(siteId, site)`, `SiteDetailFrame` `miniDepth` prop (MINIGRID + timezone only), `SiteOverview.mini`,
  `App` passes `miniDepth`. Tests: 3 cases in `s5SiteWindowOverview.test.tsx` (NO_MINI stub for the S5-01 cases).
  Provisional readings logged as q11-5 (incl. no capability-table Backup row in this tree).
- Checks: overview files 4 / 101 passed; `tsc` 0; full frontend 98 files / 2399 passed; `check-all.ps1` 11/11.

## Run 20 (this run): main merged (q11), q11 applied, unit 7 captures, review packet
- `c632077b` merge (pending-rulings kept ours); `607f73f5` q11 on pages + Overview; `33780a7a` q12 readings;
  `3ec1fb25` captures (`.agent/W4-02-evidence/`, private `w402p_test` dropped); packet `.agent/W4-02-review-packet.md`.
- Open: q11-5, q12-1..8 (q12-7: 39 region heights over budget; q12-6: Overview unreachable live).
- Checks: tsc 0; build ok; frontend 2401/2402 (intermittent `siteFindingEvidence`); check-all 11/11. No full backend suite.

## Run 21 (this run): main merged (q12 rulings), q12 applied, unit 7 recaptured (424/424)
- `067113ec` merge; q12-7 `46226fe3`/`0ef42ba5`/`9e8d9e5d`/`b065ee8d`: `MiniPerformance.tsx` `MoreList`, `StripLimitations`,
  `BoundedPanel` (CSS `.mini-bound`, `.mini-max--*` budgets 1440/<=760 in `w4-mini-performance.css`); `MetricCards`
  `boundClass` (V69Layout). q12-6 `34ab5d22`: `site_cutover_basis` in 0029, Foundation store
  `record_/no_legacy_evidence_basis`, installer records it, `SiteOverviewRoute.no_legacy_basis` (main wires it);
  test `test_w402_overview_basis_postgres.py`. q12-8 `ef979314`: `seed.py` publishes via `publish_source`.
  q12-5/q11-5 `99ce8f19`. Capture `capture.mjs` (+ `ONLY=` filter, opened-disclosure checks); private DBs dropped.
- Checks: tsc 0; build ok; frontend 98 files / 2404 passed; check-all 11/11; focused backend 3 + adjacent 110 passed.

## Run 20: final fix round
- Branch `task/W4-02-mini-grid-depth-clean`. Fixes `a9fdc260`..`9efa6715` (H2, H3, H4, M1, M2, M4, L1, L2, L4, L5,
  B-M1, B-L1..L4, L3); this round adds the recapture commit and records (see `git log 9efa6715..HEAD`).
- q14 readings 1-5 (`.agent/W4-02-pending-rulings.md` "## q14 (final fix round)") are applied and pending confirmation.
- Captures at `9efa6715` (private `w402r_test`, dropped; uvicorn 9748 + vite 6146, stopped): `capture.mjs` 556/556,
  new assertions H2/H3/H4/M1/M2/M3/M4/L1; M3 closed (08 Oct Overview `Headroom 18–20 kW`); M3 regex break proved
  non-vacuous and reverted.
- Checks: focused backend 149 passed (`test_w402_*` + `test_s5_overview_read` + `test_w401_migration_postgres`);
  frontend 98 files / 2412 passed; tsc 0; build ok; check-all 11/11.
- Migration note: a non-test DB already at 0029 must be downgraded and upgraded again to pick up the changed 0029
  (B-M1/B-L1 `site_cutover_basis` locks and rule).
- Next: independent re-review, plus the full backend suite at the same revision.

## Next (superseded by Run 20: final fix round): final review (full backend suite runs beside it); q13 readings

## Run 18: unit 6 backup page built
- Backup `2c0085c2`: `miniDepthClient.ts` `BackupCards`/`BackupRow`/`BackupStep`/`BackupRecovery`/`BACKUP_STEPS`/`getBackup`;
  `MiniPerformance.tsx` `MiniBackupPage`/`MiniBackup` (heading always `Backup readiness: Unknown`, LIMITED adds
  `Outage-chain assessment: evidence limited`; 4 cards, null outage count `Unknown`; 8-col chain table, empty = one
  `No event` row with `No complete outage chain can be assessed`; 4 fixed readiness rows; pair Operating/Next with
  `Open Dispatch`/`Browse Actions`); css `.mini-backup-chains` 719 / `.mini-backup-readiness` 326; `BUILT_MINI_PAGES`
  has backup; frame branch + `SITE_SCREEN_DESCRIPTIONS.backup` (mock subtitle); registry backup panels 1-4 `gap`;
  ledger backup `bounded`/W4-02 (node_ids = panel requires). New provisional choices logged as q11-3/q11-4.
- Checks: `miniBackupRoutes` 4 (incl. `expectV69Panels("backup")`), fuel 5, renewable 9, service 5 passed; tab order now
  `Service, Dispatch, Fuel, Renewable, Backup`; `tsc` 0; full frontend 98 files / 2396 passed; `check-all.ps1` 11/11.

## Next (superseded by Run 19): Overview cards (unit 6), then unit 7 captures

## Next (superseded by Run 18): backup page
Same pattern as fuel: `BackupCards`/`BackupRow`/`getBackup` (row shape `mini_depth/projection.py:_backup`), one local
hour via `serviceWindowFromParams`/`MiniHourBar`, add `backup` to `BUILT_MINI_PAGES`, the backup view (q9 dry-read
backup row; chains table min-width 719, readiness 326 at 390), `SITE_SCREEN_DESCRIPTIONS.backup`, frame branch,
route test with `expectV69Panels("backup")`, ledger/registry backup rows (ledger node_ids = panel requires union),
add `getBackup` to the three other route-test mocks and the final tab order. Then Overview cards (B3), then unit 7.

## Next (superseded by Run 17): fuel page
Same pattern: `getFuel` + `FuelRead` (fixed `OPENING,DELIVERIES,USE,CLOSING,RESIDUAL` term rows; check
`mini_depth/projection.py:_fuel` for the row shape), one local hour via `serviceWindowFromParams`/`MiniHourBar`
(rename to a shared hour helper if useful), add `fuel` to `BUILT_MINI_PAGES`, the fuel view (spec q9 fuel row, copy
ledger fuel rows, Q20 fuel copy), `SITE_SCREEN_DESCRIPTIONS.fuel`, the frame branch, a route test with
`expectV69Panels("fuel")`, ledger/registry fuel rows; update both route tests' tab-order expectations. Then backup,
then Overview cards (B3), then unit 7.

## Next (superseded by Run 16): service page
Read this section, q10 in `.agent/W4-02-pending-rulings.md`, the service row of the q9 page table (spec l.517+), the
service rows of `.agent/W4-02-mock-measurements.md`, Q20 service copy. Add a `getService` read + `ServiceRead` types
in `miniDepthClient.ts` (hour window: local 12:00-13:00 of the selected local day, Q5), add `service` to
`BUILT_MINI_PAGES`, a service view in `MiniPerformance.tsx`, `SITE_SCREEN_DESCRIPTIONS.service`, a route test with
`expectV69Panels("service")`, ledger/registry service rows. Then Overview cards (B3), then unit 7.

## Next (superseded by Run 15): unit 6 - renewable page, then service page, then Overview cards (B3); commit per page
Read: this section, spec "Run 9 rulings (q9) and pages dry-read" (awk from its heading), spec base "Mock content and
copy ledger" (l.45-76), Q5/Q10/Q19/Q20/Q21/Q24/Q29/Q30/Q33 (l.148-208), closure 4 B3, S1, S6, S9, N1, N3, N8
(l.307-345), `.agent/W4-02-mock-measurements.md`. Survey anchors found this run (no code read beyond these):
- Mount point: `frontend/src/shell/SiteAnalyticsFrames.tsx:149 SitePerformanceFrame` dispatches by `site.site_type`
  (EV l.178, COLDCHAIN l.197 via `COLD_PERFORMANCE_VIEWS`), else renders `SitePerformance` (l.242). Add a MINIGRID
  branch for `service|fuel|renewable|backup` before the generic return; Dispatch stays on `SitePerformance`.
- `frontend/src/sites/SitePerformance.tsx:56 RENDERABLE = new Set(["dispatch"])`; imported Sites take the
  `awaitingMigration` branch (l.120-150) with a hard-coded single Dispatch subtab: the mini capabilities merge
  (S6 order `service,dispatch,fuel,renewable,backup`) must land in that branch too (MG-W402-001 is imported).
- Profile: `frontend/src/sites/presentationProfiles.json` MINIGRID `capabilities` has only `dispatch`; add
  Service/Fuel/Renewable/Backup (keys `id,label,order,group,emphasis`; S6 labels; Dispatch label is
  "Dispatch assessment" today - S6 says `Dispatch`, check before changing). `performanceSubtabs`
  (`presentationProfile.ts:143`) sorts by profile `order`. Backend pin `backend/tests/test_t028_presentation_profile.py`
  `EXPECTED_ORPHANS` (l.22) must list the four mini ids for MINIGRID (they are not AnalyticDeclarations, S6).
- Site detail carries `timezone` (`siteReadModel.ts:49`); `site.site_id` is the public code (S9) -> mini client
  `/api/sites/{code}/performance/mini/{domain}` and `/capabilities`.
- Descriptions: `SITE_SCREEN_DESCRIPTIONS` (exported from `frontend/src/ui`, `V69Layout.tsx`); Q20 copy.
- Tests helpers: `frontend/src/test/panelStructure.ts` (`expectV69Panels`), `v69PanelTitles.ts`, `settled.ts`.
  Overview tests: `frontend/src/shell/__tests__/s5SiteWindowOverview.test.tsx`, `siteOverviewScreen.test.tsx`,
  `overviewDispatchAssessment.test.tsx` (N1); Overview component `SiteWindowOverview.tsx`.
- Registry/ledger (N8): `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `v69-screen-ledger.json`
  rows renewable/service (fuel/backup in unit 7); guards via `tools/check-all.ps1`.
- Wire facts for the UI: `links.dispatch` is `/sites/{code}/performance/dispatch?day=` (PerformanceDispatch must
  read `?day=`, verify in its router test); `actions` is `/actions` (label `Browse Actions`, not a verification
  link); renewable `basis:null` -> render `Retained margin: Unknown` + q9-7 sentence; 422 shows API message,
  503 `Mini-grid evidence is unavailable right now. Try again.` with retry.
- Then unit 7: fuel/backup pages, navigation/descriptions, guard fixtures, captures (`node tools/measure-mock-panels.mjs`).

## Earlier unit 5b list (superseded by unit 6/7 above; kept for its item detail)
- (b) Frontend: mini client (`/api/sites/{code}/performance/mini/{domain}` + `/capabilities`), routes
  `/sites/:siteId/performance/{service,fuel,renewable,backup}?from&to&known_at` (Q5 local-day/noon default, Q33),
  merge capabilities into `performanceSubtabs` + MINIGRID profile + `SitePerformance.RENDERABLE` (S6 order
  `service,dispatch,fuel,renewable,backup`; cold `backup` by Site type), four pages with v69 panel set/order/titles/
  copy (base "Mock content and copy ledger", Q19-Q22, closure 2 copy, q6 mock-panel source check), drawers (Q21),
  `V69Layout.tsx:SITE_SCREEN_DESCRIPTIONS` (Q20), `expectV69Panels` in `miniDepth.test.tsx` (Q29), registry/ledger
  rows (N8), navigation guard fixtures. Overview cards (B3) are Q28 unit 6 scope.
- (c) Captures at 1440/390 vs mock + `node tools/measure-mock-panels.mjs`, per `.agent/W4-02-mock-measurements.md`.

### Unit 4 step history
0. DONE in `46682cfc` except the projection part (`cards.outage_count=null`, step 3). Original text:
   q3 1-3 (`test_fuel_interval_and_completeness`: status table, same-instant tank conflict, no-SFC row),
   q3 6-8 (`test_backup_chain_order_and_no_event`: bus without positive output, unaligned critical, aligned
   witnessed miss and missing-span countercase, zero supply seconds). q3 8: projection must emit
   `cards.outage_count=null` unless complete supply coverage (unreachable in W4-02, so always null).
1. DONE in `120ee51e` (see Run 6). Original text: Store lease/settle: domain-filtered methods on `analytics/adapters/postgres_assessment_store.py` (closure 4 S2:
   `domain IN (mini_*)` + tenant/Site predicate; the worker issues no recompute_job SQL). Selection writer is
   `mini_depth/store.py:PostgresMiniDepthStore.append_selection(revision, job_id=, connection=)` (caller-owned
   connection supported; job row lock + window match already there).
2. DONE in `0ed36f9c`/`9adfa90d` (Run 7). Original text: `mini_depth/inputs.py`: closure 1 Q13 query (`e.received_at <= :k AND d.decided_at <= :k`, own SQL, not
   `_EVIDENCE`); pin `site.timezone` (S8, into `result.basis.site_timezone` and the digest); local noon (first
   occurrence; nonexistent -> refuse) and local hour; Foundation properties (pv uncertainty, margin, recovery
   target) with revision IDs; SFC via `financials/fuel_cost.py` + `MULTIPLIER`; `LoadAsset` from bindings with
   `feeder_request_bound`; last supply state before the hour (q3 4); `AcceptedReading` -> `Reading`/`Observation`.
3. DONE in `69adb9d9`/`e0f7c9de` (Run 8). Original text: `mini_depth/projection.py`: wire rows/cards (closure 1 Q8, closure 2 renewable `used_kw` bound), `result.basis`
   (Q15 keys + `site_timezone`), sorted arrays.
4. WORKER DONE in `1e4baa8c`/`a2953175` (Run 9); (resume here) the S7 tick stage once q7 is ruled. Original text: `mini_depth/worker.py`: lease -> inputs -> rules -> projection -> `append_selection` in one transaction ->
   settle DONE (use `projection.project(domain, inputs)`; the lease `knowledge_cutoff` goes to `load_hour_inputs` unchanged, plus the q5-5 worker cutoff test in `test_w402_mini_lease_postgres.py`); CLI `run-pending`, `reconcile --site --from --to`. S7: `mini` stage in `scheduling/stages.py`
   (`STAGES` dict, pattern of `s3`) and `scheduling/tick.py` after S3/before S4, with limits/budgets.
5. DONE in `a41c47ec`/`20e8a4e7` (Run 10). NEXT: step 4's S7 tick `mini` stage once q7 is ruled, then unit 5
   (reads: renewable envelope composition per q6 1, `STALE_SOURCE` per q6 5, `test_w402_reads_postgres.py`).
   Original text: (needs q6; uses `MiniDepthWorker.run_pending` / CLI `run-pending`, not the tick, so q7 does not block it) Selection proof + replay: rerun both authored variants over HTTP (`tools/w402_mini_depth_cases.py run --api
   --credential-file --out`, q3 12), run the worker, record per-day seq/revision/accepted IDs; integration test
   joining each seq to its revision and full accepted-ID set (q3 11-12).
