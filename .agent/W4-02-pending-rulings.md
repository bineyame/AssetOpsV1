# W4-02 pending rulings (builder questions; Architect decides)

Raised by the unit-1 builder run on `task/W4-02-mini-grid-depth`. Unit 1 did not need either ruling, so this run
did not stop for them. Unit 3 cannot build B2 or the closure-5 `MG-W402-001` install path without the first.

## R1 (blocks unit 3): mixed v3/v4 channel validation for `minigrid-roles-4`

Closure 4 B2 says `sites/binding_service.py` "must point `minigrid-roles-4` to this exact table" (the three-row
authored profile `authored-mini-depth-cases/1`). Closure 5 installs `MG-W402-001` with
`BindingService.publish(..., role_set="minigrid-roles-4")`, which is a non-conversion publish, so
`validate_bindings(..., v4_metadata=True)` runs (`binding_service.py:684`).

In the shipped validator (`binding_service.py:391-417`), when a role set is in `_V4_TABLE_BY_ROLE_SET`, every
channel binding of that set must appear in the role set's v4 table. If it does not, the binding is refused as
`BINDING_CHANNEL_V4_UNKNOWN`. Cold and EV bind only v4 channels, so this has not mattered for them. Roles-4 is
different: it keeps the 14 roles-3 channels on v3 sources, such as `generator_power` and `feeder_demand`, and adds
only three v4 tuples. Mapping roles-4 to the three-row table therefore refuses every v3 channel binding.

Options the spec does not choose between:
- (a) For `minigrid-roles-4` only, apply the v4 checks and pin v4 metadata only for the roles that a row of the
  authored table names (`site_supply_state`, `mini_backup_start_event`, `mini_backup_bus_state`). The other
  channels stay v3 bindings with no v4 metadata.
- (b) Decide v4 versus v3 per bound source (its envelope schema), not per role set.
- (c) Another rule.

The answer also decides whether `_decide_v4`'s pinned-metadata check stays exactly as it is for a mixed binding set.

## q6 (unit 4 step 3, `e0f7c9de` `mini_depth/projection.py`): projection readings to confirm or replace

Step 3 is built with these readings; none blocks step 4's worker, but each fixes a persisted `result` shape, so a
change after revisions exist needs a new model version. Please rule before step 5's selection proof.

1. **Renewable per-hour result has no `status` or `cards`.** Each revision is one noon hour (closure 1 Q4); the
   result holds `hour:{capability_kw,used_kw(number),headroom_kw,decision}`, the one day `rows[]` entry, empty
   `limitations`, `coverage` and `basis`. The read composes cards (`summarize_renewable`, `used_kw` as a bound) and
   the envelope status over the selected days. Is that right, and what is the renewable envelope status rule
   (e.g. any LIMITED/CONFLICT day -> LIMITED; all days ELIGIBLE/EXCLUDED -> SUPPORTED; else UNKNOWN)?
2. **Fuel and backup rows carry no `coverage`.** Q8 says every row has `coverage`; `FuelRow` and `BackupChain` have
   none. Should fuel term rows / backup chain rows get one (which seconds?), or does Q8's sentence apply to
   renewable and service rows only?
3. **Backup `role_coverage` for instant roles.** `site_supply_state`, `mini_backup_start_event`,
   `mini_backup_bus_state` are listed with `observed_seconds:0`, a whole-hour gap and `source_count:0`
   (`Observation` carries no source ID). Accept, or should `Observation` carry `source_id` for a real count?
4. **`specific_fuel_consumption_property_revision_id`** is the one SFC revision used, or null when the hour used
   none or several (rules allow different in-force SFCs on different intervals). Accept null for several?
5. **`source_freshness` at assessment** = CURRENT iff every `role_coverage` entry is complete with no gap, every
   required series is COMPLETE with no unusable row, and no CONFLICT/REQUIRED_INPUT_UNUSABLE/COVERAGE_GAP
   limitation; else UNKNOWN. "Cited source gate resolves" is taken as satisfied by the Q13 gated selection. Thus
   fuel (tank instants) and backup (instant roles) are always UNKNOWN in W4-02. Accept?
6. **`cards.start_success_count`** stays the rule's count (only `outage_count` is nulled per q3 8). Accept?

## q7 (unit 4 step 4, `1e4baa8c`/`a2953175`): the S7 tick stage needs DDL outside 0029's catalog (BLOCKS the stage)

`mini_depth/worker.py` is built (lease -> inputs -> projection -> `append_selection(job_id)` -> `settle_mini_job`
in one REPEATABLE READ transaction; CLI `run-pending`, `reconcile`). The S7 `mini` stage is **not** built:

1. **Persisted stage shape.** Closure 4 S7 says to add the stage result "to the tick's persisted/report shape".
   `schedule_site_head.stage` is `CHECK (stage IN ('IDLE','S3','S4','CONSEQUENCE'))` (`0013_schedule_state.py:65`),
   so `ScheduleStore.set_stage(..., "MINI")` (the per-stage claim check every stage uses, `tick.py:_site`) fails,
   and there are no `mini_processed/mini_deferred/mini_failed` columns (S3 has `s3_processed/s3_deferred`;
   `last_failure_stage` is unconstrained text). Closure 2's 0029 catalog delta is closed ("three SQL functions and one
   constraint trigger ... no `recompute_job` DDL") and names no `schedule_site_head` change. Options: (a) extend
   0029 with the CHECK widening and three counter columns (and `record_mini` on the schedule store, the schedule
   writer); (b) a new migration 0030; (c) report-only: the stage result goes into `TickReport`/`as_json` only and
   the Site claim is checked with the existing `S3` stage value. Which?
2. **Discovery.** `discover` selects Sites from `live_jobs(dispatch_v3.ANALYTIC_ID, 'dispatch')`. "Discovery includes
   Sites with pending mini work" needs a four-domain live-job read; the assessment store owns `recompute_job` reads.
   Confirm a new `PostgresAssessmentStore.live_mini_jobs(tenant?, site?)` (PENDING/LEASED, and FAILED until a later
   selection, per closure 1 Q3 currentness) feeding `select_sites` as `live_jobs` do.
3. **Budgets.** Proposed `TickLimits.mini_jobs_per_site=10`, `mini_seconds=120` (< the worker's 5-minute lease, like
   S3), the existing `statement_timeout_ms` (must stay below `mini_seconds`), and `site_lease_seconds` += `mini_seconds`.
   Confirm or give values.

Readings applied in step 4 (for review; none changes a spec rule):
- R1 `inputs.input_sha256` now returns `sha256:<hex>`: 0029's column CHECK (spec line 88) requires it; step 3 returned
  bare hex, which the writer would refuse.
- R2 A refused input set (`MiniInputsRefused`, e.g. `CONFIGURATION_MISSING`) fails the job through `fail_mini_job`
  (RETRY with back-off, FAILED on the last attempt; `last_error` starts with the code), as the Dispatch worker does
  for every error. No UNKNOWN revision is persisted for a refusal.
- R3 `reconcile` assesses each first-occurrence Site-local hour wholly inside `[from,to)`, all four domains
  (renewable at local noon only, as 0029's enqueue functions), one transaction per hour at its DB `clock_timestamp()`
  cutoff, appending `backfill=True` selections with `job_id=null`; it reads/writes no job.
- R4 The CLI subcommand is `run-pending` as specified, but its name is derived from `MiniDepthWorker.run_pending`:
  `tools/checks/run-setup.ps1` bans a quoted `run-` literal outside `runs/identity.py`. Accept, or should the guard
  allow this one CLI spelling?
