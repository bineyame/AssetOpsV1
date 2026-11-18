# CH-1a pre-flight (P1-P7) and Architect questions

Branch `task/CH-1a-snapshots` (worktree `AssetOpsV1-ch1a`) from main `7fffc8358`. Groundwork commit `25b8fa5ab`:
the 0043 migration, config files, `chain/policy.py`, `chain/grading.py`, the store and reader, the guard registration.
L0 passes: `test_ch1a_grading.py` 25 passed. Everything else (adapters, input reader, builder, CLI, L2) is waiting on
the answers below. `B/` is `backend/assetops_backend/`.

## Answers

- **P1 Prices.**
  - **Productive.** 0040 adds no table. It widens `financial_assumption_revision` to cover `productive_use_price_per_kwh`.
    - The read is `AssumptionReadService.series(t, s, key, valid_at=, recorded_at=)` (`B/financials/assumption_read.py:63`), composed by `financials.composition.build_assumption_read_service`.
    - The rule is `covers` (`:55`): `valid_from <= at < valid_to`.
    - `selection` = {state PRICED|NO_PRICE|CONFLICT, revision_id, price.value, price.currency}.
    - The board samples it once, at window start (`B/site_outcomes/mini.py:749`).
    - Money is `(kwh*value).quantize(0.01, HALF_UP)` (`mini.py:779`). For 168.33 kWh × 0.25 that gives 42.08.
  - **EV.** Key `ev_gross_tariff_per_kwh`. The money is already stored in `ev_consequence_revision` (M/0026:48: quantity_kwh, tariff_revision_id, amount, currency). It is read through `EvSiteReads.overview(...)`, `consequence_summary` (`B/ev_site_reads.py:611`).
- **P2 Productive assets.** These are LOAD components in `foundation_revision.content` that have `supply-use=PRODUCTIVE`.
  - `MiniDepthRead.productive_users` (`B/mini_depth/read.py:358`) finds them.
  - `productive_readings` (`:382`) returns the accepted GOOD/other `feeder_demand` rows, with interval_start and interval_end, under the `_ACCEPTED` received_at/decided_at cutoff.
  - `productive_energy` (`B/site_outcomes/productive_use.py:37`) is pure and is called unchanged.
- **P3 Dispatch.**
  - `DispatchReadService.window(t, s, day)` (`B/analytics/dispatch_read.py:123`) works on a **UTC day** [00:00Z, 24:00Z).
    - Its intervals carry `result.portions_minutes{candidate, necessary, indeterminate}`, `interval{first_on, last_on, lower_minutes, upper_minutes}` and `generator_asset_id`.
    - Its status is one of UNASSESSED|PENDING|CURRENT|STALE_PROJECTION|FAILED.
  - The board's sum is the private `_dispatch_minutes` in QW-touched `B/site_outcomes/mini.py:615`, which returns (Σcandidate, Σindeterminate).
  - PENDING comes from `recompute_job` (M/0005:289) with status PENDING or LEASED. The domains are `dispatch`, `mini_renewable` (enqueued for local hour 12 only), `cold_chain` and `ev_charging`.
- **P4 Cold.**
  - The chamber role is `chamber_temperature` (`B/sites/binding_roles.py:152`), bound to `probe-1`.
  - The backup chain is `backup_start_event` (START_REQUEST and START_RESULT; failure is `outcome='FAILED'`), along with the grid, generator, transfer, bus and compressor roles (`B/analytics/cold.py:39-55`).
  - The reads are `ColdReadService.temperature(...)` (`B/analytics/adapters/postgres_assessment_store.py:2191`), which gives excursions with `peak_observed` plus `coverage` and `gaps`, and `backup_chain(...)` (`:2240`), which gives chains with result OBSERVED_SUCCESS|OBSERVED_FAILURE|UNKNOWN|CONTRADICTORY and steps marked OBSERVED|MISSING.
  - The chamber and the generator are identified through the Foundation components COLD_ROOM, TEMPERATURE_PROBE and GENERATOR.
- **P5 EV.**
  - `ev_measurement` is only a partial index (M/0024:23).
  - Sessions are in `ev_session_revision` (M/0025:108): `state` is COMPLETED|OBSERVED_ABORT|INCOMPLETE|CONTRADICTORY, and the rows carry `start_at`, `end_at`, `supported_kwh` and `unknown_meter_seconds`.
  - The board takes `EvSiteReads.overview` → `denominator.{started, completed, ...}` and `energy.complete_kwh`.
- **P6 QW-touched calls.**
  - `productive_energy` is pure, so it is called as is.
  - `_dispatch_minutes` is **private** in `site_outcomes/mini.py`. See Q3.
  - Nothing needs an edit to a QW module.
- **P7 Lab windows.**
  - **Cold: none outside the story-day file.**
    - 16:00–17:05 UTC (19:00–20:05 Addis) appears only in `backend/conversions/demo-story-days-v1.json:17-20`.
    - The registered scenarios run 19:00–20:00 **UTC** (`config/scenarios/cold-*.yaml:10-11`), which is 22:00–23:00 Addis.
    - So the cold calendar hours are inferred from the data, and SWEEP-DS should re-examine them.
  - **EV: a real declaration exists, and it is not 08:00–09:00.**
    - `backend/tests/fixtures/w2/ev-lab-001.yaml:154-168` declares `connector_enable_schedules` as TUESDAY 08:00–16:00, UTC offset 0. `host/ev_publication.py:331-336` enforces it.
    - 08:00–09:00 is only the run window (`config/scenarios/ev-*.yaml:7-8`, story-day file :24-26).

## Questions for the Architect (one batch)

1. **EV calendar (DS-R1 item 5).** The declared schedule is Tuesday 08:00–16:00, and the sheet's 08:00–09:00 is the run window, which is fitted to the data. Under 08:00–16:00, a one-hour session graded on session or meter seconds is 12.5%, so LOW.
   - Proposal: declare 08:00–16:00 with `source` = `ev-lab-001.yaml:154-168`.
   - Define `charging_kwh` coverage as the metered seconds of the period, meaning the support meter intervals plus the idle time the charger reports as available. If that is not wanted, rule the coverage basis instead.
   - Or keep 08:00–09:00 labelled as inferred.
2. **Cold calendar `source`.** No scenario declares 19:00–20:05 Addis. Proposal: keep the hours, set `source` = `demo-story-days-v1.json:17-20 (inferred from story runs; no scenario declaration; SWEEP-DS)`. Confirm.
3. **`avoidable_gen_min`.**
   - (a) **Coverage basis.** The dispatch window is the whole UTC day, so window coverage would make Kobo 21 of 24 h, which grades COMPLETE, not the PARTIAL the sheet expects. Proposal: covered = the union of accepted-reading intervals the selected dispatch run used (the interval rows' `evidence_ids`), clipped to the local period. That gives 8 h, PARTIAL.
   - (b) **Value.** Should the value be Σcandidate only, or candidate + indeterminate? Proposal: `{"minutes": Σcandidate, "indeterminate_minutes": Σindeterminate}`.
   - (c) **The private helper.** May the adapter import the private `site_outcomes.mini._dispatch_minutes` read-only? The alternative is to re-sum, which would be a second copy of the rule.
   - (d) **Which UTC days to read.** Read both UTC days that overlap the local day. Confirm.
4. **`noon_headroom_kw`.** Proposal: read the stored, selected `mini_depth_revision.result`, latest by known_at, rather than recompute. Recomputing would need `load_hour_inputs`, which needs a DB connection inside mini_depth.
   - value = `hour.headroom_kw.low/high`.
   - decision: ELIGIBLE and EXCLUDED are kept as is; LIMITED and CONFLICT map to null.
   - covered = the noon hour minus `result.coverage.gaps`.
   - PENDING = a live `mini_renewable` job for the window.
   - `summarize_renewable` is not called.
   - Confirm.
5. **`backup_start_chain` coverage.** Events are instants, so they have no seconds. Proposal:
   - covered = the full period when a chain is observed with no MISSING steps;
   - otherwise period × observed/total steps;
   - NO_DATA when no chain exists.
   - value = `{"starts": chains, "failed": OBSERVED_FAILURE count}`.
   - Confirm, or rule.
6. **`chamber_temp_c` coverage and peak.**
   - Proposal: covered = the period minus `temperature().gaps`.
   - For the peak: there is no excursion on a normal day, so propose the max observed probe value in the period. That needs the raw `chamber_temperature` readings through `ChainInputReader`. Is that acceptable, or is the peak meant to come only from excursions?
7. **Zero-kWh productive money.** `productive_kwh` money on a 0-kWh priced day: 0.00 USD (sheet: kWh × price), or null (the board shows no money on a zero day)? Proposal: 0.00.
8. **L2 seeding.**
   - The MG-W402-001 fixture (`_ingest`/`_reconcile`) gives real stored renewable selections, but it has no productive user.
   - Proposal: prove `noon_headroom_kw` through the real adapter on MG-W402. Prove `productive_kwh`, idempotency and revision 2 through a stub `ChainInputReader` against the real store. The real productive adapter is then proven on the L3 clone.
   - Alternatively: add a WALK1 `configure_at`/`publish_price` set-up plus seeded feeder_demand readings.

## Notes, not questions (recorded deviations)

- **Rule 2 placement.** Rule 2 (`tools/checks/configuration-persistence.ps1:263`) bans `pathlib` and `open(` in a domain package outside `adapters/`. So the JSON read lives in `chain/adapters/file_chain_config.py`, re-exported by `chain/composition.py`, and `chain/policy.py` keeps the records and the validation.
  - The v1 calendar loader requires one contiguous window per day, because `period_bounds` returns one span.
- **Branch name.** The dispatch's `task/CH-1a-snapshots` is used, not the sheet's `task/CH-1a-day-snapshots`.
- **Execution policy (coordinator).** From Bash, `powershell -File tools/run-host-tests.ps1` is refused because the policy is Restricted. The PowerShell tool's process already reports `Bypass`; I set no override. I ran the L0 step through the PowerShell tool. Please confirm this is acceptable for the guards and the L2 step.
