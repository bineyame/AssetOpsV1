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

## q8 (unit 4 S7 tick `mini` stage, `07af0afb`): live mini work on a legacy MINIGRID Site without `minigrid-roles-4`

Raised by run 11 after building q7 rulings 1-5. One adjacent test fails; the builder did not change its intent.

The 0029 trigger enqueues `mini_*` jobs on every MINIGRID Site for mapped roles (closure 4 B1), including legacy
Sites bound under roles 1-3 (KOBO-001 in `test_s4_schedule_health_postgres.py`). On such a Site the worker always
refuses `CONFIGURATION_MISSING` ("exactly one minigrid-roles-4 set must cover the hour"), so after three attempts
each job is FAILED, and q7 ruling 2 keeps a FAILED job live until a later matching selection, which can never
come. The Site therefore stays scheduled for good, even when DECOMMISSIONED (`EXCLUDED_WITH_WORK`, MINI stage
running every tick), and the tick's S4 stage then also runs for it.

Failing test: `test_s4_schedule_health_postgres.py::TestHealthAndSeam::test_fence_moved_streak_terminal_s3_failure_requeue_and_recovery`
(lines ~237-246). It decommissions KOBO-001 and asserts that (a) no work keeps it selected and (b) its unmatched S4
selection stays as `s4.backlog` in health. With mini work live, the Site is visited, S4 matches, and (b) fails
(`s["s4"]["backlog"]` is False). Updating (a) alone to expect `EXCLUDED_WITH_WORK` does not save (b).

Options:
- (a) Enqueue mini jobs only for Sites with a `minigrid-roles-4` binding set in force (0029 trigger/configuration
  enqueue change), so legacy Sites get no mini work.
- (b) Keep enqueue; treat a FAILED `CONFIGURATION_MISSING` mini job as not live (discovery predicate change).
- (c) Keep both; rewrite the health test to clear the Site's mini jobs before decommissioning (test-only), and
  accept that legacy MINIGRID Sites stay scheduled with permanently FAILED mini jobs.
- (d) Another rule.

Also confirm two readings in the q7 build: `mini_failed` counts jobs this stage left FAILED (RETRY outcomes are
not counted; they are in `mini_deferred` as PENDING), and `live_mini_jobs` returns the `live_jobs` fields plus the
job `domain`. The Site health report exposes no Site-head counts today, so the three counters are only in
`site_head(s)` reads and the tick report; no health field was added. Downgrade takes `LOCK TABLE
schedule_site_head IN EXCLUSIVE MODE` before the ruled MINI-stage check.

## q9 (unit 5a, `476773e9` `mini_depth/read.py`, `mini_depth_api.py`): read/API readings to confirm or replace

Built and tested (`test_w402_reads.py` 14, `test_w402_reads_postgres.py` 3). None changes a spec rule; each fills a
gap the spec leaves open. Confirm or replace each; the UI piece (5b) consumes this wire.

1. **No default window at the API.** `from` and `to` are required (missing/repeated/naive/malformed -> 422
   `INVALID_WINDOW`); the shell default (Q5 local day / local noon) is computed by the frontend. Offset input is
   normalized to UTC (Q33).
2. **Historical job visibility.** A job counts as live at cutoff `k` iff `status IN (PENDING,LEASED,FAILED)`,
   `available_at <= k`, and no selection of its exact hour has `available_at < selected_at <= k`. (`created_at <= k`
   was wrong: `mini_enqueue_hour` lifts `available_at` on an old PENDING row, so a lifted job would read as pending
   before its new cause existed.) Job status itself is current, not reconstructed.
3. **STALE_SOURCE (q6-5) test.** At the read cutoff `load_hour_inputs` is rerun on the snapshot and its digest is
   recomputed with the selected revision's own `knowledge_cutoff`; inequality with the stored `input_sha256` (a
   newer eligible accepted row, Foundation, binding set or property revision) is STALE_SOURCE. If the configuration
   no longer yields one covering basis (`CONFIGURATION_MISSING`), it is also STALE_SOURCE. Nothing is persisted.
4. **Claim downgrade.** A SUPPORTED status becomes LIMITED when the selected provenance class is UNKNOWN/MIXED
   (adds `SOURCE_CLASS_*`) or currentness is PENDING_RECOMPUTE (`RECOMPUTE_PENDING`) or STALE_SOURCE
   (`SOURCE_STALE`). HISTORICAL never downgrades. Limitations are merged per code and sorted by `LIMITATION_ORDER`.
5. **Aggregate `job_state`** precedence FAILED > LEASED > PENDING > NONE > SETTLED (a requested hour with no
   selection and no job is NONE).
6. **Renewable envelope.** `rows` = the selected hours' stored rows sorted `(day, from)`; a requested day without a
   selection has no row (its `windows[]` entry has null IDs and `state=UNKNOWN`). `limitations` = each row's
   constraint codes with that row's evidence IDs. `coverage` = required `3600 x requested days`, observed = sum,
   `source_count` = max per hour (distinct sources across days are not stored), gaps = stored gaps plus each
   unselected hour whole.
7. **Wire additions.** Top-level `basis` = the selected revision's stored `result.basis` for service/fuel/backup
   (the fuel drawer needs SFC and generator-power IDs), `null` for renewable and for no selection. `site` =
   `{id, code, timezone}` as in the base example. The renewable retained-margin value (mock-panel source check:
   "pinned `renewable-retained-margin` property revision") is **not** in the stored hour; should the read add it
   from the pinned Foundation revision (e.g. `retained_margin_kw: number|null` per `windows[]` entry), or the UI
   show the margin as unknown?
8. **Links.** `dispatch` = `/sites/{code}/performance/dispatch?date=YYYY-MM-DD` only when one UTC day encompasses
   every requested hour (Q5), else null; `evidence` = `/sites/{code}/evidence`; `financials` null; `actions` =
   `/actions` (W3-01's estate root is merged; it has no Site filter). The `?date=` parameter is assumed to be the
   Dispatch day selector; unit 5b verifies it.
9. **Non-MINIGRID direct read** (S1 order: type before parameters): 200 UNKNOWN, `SITE_ROLE_UNSUPPORTED`, the empty
   provenance alias, null cards, `windows: []`, `coverage: null`, `site` without `id`; parseable `from/to/known_at`
   are echoed, malformed ones become null. Unknown `{domain}` is 404 `MINI_DOMAIN_NOT_FOUND / This page was not
   found.`
10. **Lineage 503.** A selected revision whose domain/window differs from its selection, or whose
    `basis.accepted_evidence_ids` differs from its `mini_depth_revision_evidence` set, is 503 (Q15 "broken stored
    basis").

## q10 (unit 6, `ee461681`/`512a5429` renewable page): readings applied provisionally, to confirm or replace
None blocks the service page; each is a one-line change.
1. **Status word for SUPPORTED without positive headroom.** q9's table lists `Watch` (supported positive headroom),
   `Evidence limited` or `Not assessed`. Built: LIMITED -> `Evidence limited`; SUPPORTED with `headroom_kw.low > 0`
   -> `Watch`; everything else, including SUPPORTED with non-positive headroom, -> `Not assessed`. Confirm or name
   the word for an assessed hour with no usable headroom.
2. **Productive-use CTA copy.** q9's table says the CTA is disabled with `Opportunity decisions are planned for
   W4-03`; Q21/N3 say no internal task IDs and pass the bare label. Built: N3's `UnavailableLinkEntry` ->
   `Opportunity decision · Not available yet`.
3. **Unbuilt mini tabs.** Until their pages land, Service/Fuel/Backup are left out of the subtab row (S6 order kept
   over the built tabs: `Dispatch, Renewable`). An inert `UnavailableTab` entry was tried and the
   navigation-truthfulness guard rejects it ("a new unbuilt entry is a ruling"); untagged placeholder copy fails the
   missing-claim scan. A direct `/performance/service` URL falls through to the existing imported-Site route.
   `SitePerformance.RENDERABLE` is unchanged: the mini pages render from the frame's MINIGRID branch, and adding
   their ids there would render the Dispatch body for them.
4. **Registry nodes.** N8 needs a `ui` and a `projection` gate per pilot panel; added `I-mini-depth-read`
   (projection) and `I-mini-depth-ui` (ui), both `open`, `task:W4-02`, and set `I-mini-breadth-store.task` to
   `W4-02`. Renewable ledger row is `bounded`/`W4-02` with product node `P-mini-area`.
5. **Service page (`8925399a`), same pattern, provisional.** (a) The `See effect on verification` CTA uses N3's
   `UnavailableLinkEntry` (`See effect on verification · Not available yet`), not the copy-ledger text
   `No linked verification for this window`, matching item 2; confirm or name the copy. (b) The mock's
   `Clinic (critical)` card label is not kept as a literal: it reads `{critical row load_label} (critical)`, else
   `Critical load`. (c) `What was needed` is always the hatched `Unknown` bar: the public service row carries a request
   state but no requested-kW value. (d) Default hour with no `from/to` is local 12:00-13:00 (handoff Run 15).

## q11 (unit 6, q10 applied and fuel page): readings applied provisionally, to confirm or replace
None blocks the backup page; each is a one-line change.
1. **Downgraded positive renewable label.** q10-3 says the currentness/provenance downgrade runs before the label
   mapping so pending/stale/unknown never gets `Watch`, but names no replacement word. Built: SUPPORTED with
   `headroom_kw.low > 0` and currentness `PENDING_RECOMPUTE`/`STALE_SOURCE`/`UNKNOWN`, or provenance (pending alias,
   else selected) `UNKNOWN`/`MIXED`/absent -> `Evidence limited`. `No usable headroom` (low <= 0) is not downgraded.
   Registry/ledger q10-2 applied: `I-mini-depth-read` requires `A-mini-breadth-projections`, `I-mini-depth-ui`
   requires `D-mini-breadth-windows`. Ledger rows keep `I-mini-depth-read`, `I-mini-depth-ui`, `D-mini-breadth-windows`:
   the ledger checker requires them to equal the panel `requires` union; `A-mini-breadth-projections` is reached
   through `I-mini-depth-read`.
2. **Fuel page (`f1ba0962`), provisional.** (a) The third card is labelled `Modelled expected use` (q3-3), not the
   mock's `Expected use`. (b) Q20's note `Modelled: {mean kW} for {minutes} min × {L/kWh}` has no kW or L/kWh in the
   public read, so it reads `Modelled: generator output for {USE minutes} min × selected fuel coefficient with selected
   bound` (numbers omitted per Q20). (c) Bridge treatment copy: MODELLED `Modelled range, not a fuel-meter reading`,
   COMPLETENESS_UNCONFIRMED `Delivery completeness unconfirmed`, CONFLICT `Conflicting records`, ACCEPTED_READING
   without bound `No bounded tank uncertainty is registered`, RESIDUAL `Needs every term with a supported range; never
   infers theft`, else `Missing`; the term's value sits beside its name. (d) `No linked dispatch consequence` is an
   inert tagged span (not N3's `· Not available yet` form), per the q9 dry-read wording. (e) Any non-LIMITED status,
   including an unreachable SUPPORTED, reads `Fuel balance: Unknown`.
3. **Backup page, provisional.** (a) `Start success` shows `{n} witnessed success(es)` with note `Of {N} witnessed
   starts`; the read has no denominator, so N is the number of chains whose START step is not MISSING. (b) A chain
   cell reads `Observed HH:MM`, `Conflicting records HH:MM` or `No accepted record`; `When` is the local outage start;
   `Outcome for service` appends `Recovered`/`Missed recovery target`/`Unknown`. (c) A LIMITED chain assessment adds
   the strip chip `Outage-chain assessment: evidence limited`; the heading stays `Backup readiness: Unknown`. (d) The
   empty-table copy shows `No outage in the selected hour` only when `cards.outage_count === 0` (never in W4-02,
   q3-8), else `No complete outage chain can be assessed`. (e) Card notes: `Supply reports do not cover the whole
   hour`, `No witnessed start request`, `No accepted witnessed test record`, `Needs requested and delivered
   critical-service power`; recovery `{min} min` with `Target {min} min · latest valid chain`. (f) Limitation words:
   RECOVERY_TARGET_MISSING `No pinned critical-service recovery target`, BACKUP_CHAIN_INCOMPLETE `No complete outage
   chain`. (g) Header description is the mock subtitle `Performance · backup start and service recovery` (Q20 gave
   no backup line). (h) `Open Dispatch`/`Browse Actions` null links use `UnavailableInline` (`· Not available yet`).
4. **Backup readiness rows.** Available evidence is the union of cited IDs of non-MISSING mapped steps across all
   chains (Q22 mapping); current claim is the latest chain's mapped-step word (`Observed`, `Partly observed`,
   `Conflicting records`, `No accepted record`) plus `· chain result {Pass|Fail|Incomplete}`. With no chain: `No
   accepted record` / `No outage-chain assessment`; `Witnessed outcome` is always `No accepted record` / `Readiness
   remains unverified`.
5. **Overview cards (B3/Q24), provisional.** (a) A value shows only when the read's `currentness.state` is not
   `PENDING_RECOMPUTE`/`STALE_SOURCE`/`UNKNOWN` (q11-1's downgrade applied to all three cards). (b) Service's
   "complete aligned feeders" is read as `status === SUPPORTED` with non-null `cards.delivered_load_kw`; its coverage
   note is `{observed/required}% of the hour covered` (else `coverage unknown`). (c) Renewable's "supported selected
   noon hour" is read as day-read `status === SUPPORTED` with both `cards.headroom_kw` bounds (no per-hour row check).
   (d) Fuel shows `Expected use {low}–{high} L` from both `cards.expected_use_l` bounds at any status. (e) Any
   non-loaded read (503, other refusal, transport, malformed) is `Unavailable` + the closure-2 note, no link; a
   loading card shows `Loading the site's mini-grid assessment.`. (f) `View detail →` opens the Performance tab with
   the card's exact `from`/`to`/`known_at`. (g) Dispatch is not refreshed (B3). (h) The Site capability table has no
   `Backup readiness` row in this tree, so B3's capability-row destination test is not built here.

## q12 (unit 7 run, q11 applied): readings applied provisionally, to confirm or replace
None blocks unit 7; each is a one-line change.
1. **q11-1 "selected/pending provenance".** Read as: selected provenance absent/UNKNOWN/MIXED, or a present pending
   provenance UNKNOWN/MIXED, downgrades a positive read (`renewableDowngraded` in `miniDepthClient.ts`). A null pending
   block alone does not downgrade.
2. **q11-1 on the Overview renewable card.** The same downgrade withholds the card's `Headroom {low}–{high} kW` value
   (shows `Unknown`). q11-5 (Overview readings) remains otherwise open.
3. **q11-3(a) plural.** `Of 1 witnessed request/result pair in shown chains` (singular at N = 1).
4. **q11-4 scope label.** The column header reads `Current claim (latest observed outage chain)`.
5. **q11-2 USE minutes.** "Observed USE minutes exist" is read as a non-null USE-row coverage
   (`floor(observed_seconds/60)`, which may be 0).
6. **Overview cards not reachable live (unit 7).** On the seeded `w402p_test` (test-harness install of MG-W402-001),
   `/sites/MG-W402-001?date=2026-10-06|12` renders the S5 `Awaiting evidence migration` Overview, so the five mini
   cards never mount through the real backend; the Overview capture shows that state and the card evidence stays
   jsdom-only (`s5SiteWindowOverview.test.tsx`). Needs a ruling: accept, or name the Overview window source for this Site.
7. **Height budgets exceeded (unit 7 captures, `.agent/W4-02-evidence/evidence.json`).** 39 of 296 capture checks are region-height failures
   against the Run 9 budgets on all four pages, both widths (no page overflow on the four pages). Largest: backup
   `Backup readiness evidence` 598 px at 1440 (budget 316) and 2441 px at 390 (budget 471): the q11-4 row lists every
   distinct cited UUID across the shown chains. Others are 5-45% over (status strips at 390, card rows, renewable
   windows table at 390 693-722 vs 482, fuel bridge 601-678 vs 579). Not fixed in this run: the remedy for the readiness
   ID list (bounded cell scroll, count + drawer, or budget change) and whether to bound the rest by panel scrolling
   are choices; the spec allows "wrapping or bounded panel scrolling" but names no per-region treatment.
8. **Selected provenance is UNKNOWN on every seeded read.** The harness install reports `Selected sources: unknown`
   and `Limited by: Source class unknown`, so renewable and service read LIMITED on positive days. The positive
   `Watch`/`Supported` states are therefore jsdom-only.

## q13 (q12 run): builder readings applied provisionally, to confirm or replace (none blocks review)
1. **q12-6 storage.** The basis is table `site_cutover_basis` (tenant, site, `site_import_id`, `source_sha256`,
   `basis = 'NO_LEGACY_EVIDENCE'`), added to this branch's unmerged 0029 (not a new 0030); it matches only while it
   names the Site's current import row and digest. Written by the Foundation store, called only by `install_mg_w402_site`.
2. **q12-7 strip copy.** The closed strip disclosure reads `Limited by {N} condition(s)`, counting the page's claim-limit
   sentence (service `requested-service baseline is incomplete`, fuel and backup secondary sentences) with the codes;
   on backup a LIMITED chain makes the chip `Outage-chain assessment: evidence limited` the summary. Source chips now
   precede currentness (renewable, fuel, backup) so the 390 strips fit.
3. **q12-7 card values.** Gap words in the fuel and backup cards (`Unknown`, `No record`, `Delivery completeness
   unconfirmed`, `Cannot compute`, `{n} witnessed success`) use the existing word value size; numbers are unchanged.
4. **q12-5 minutes.** Observed USE time of 60 s or more is shown as `{seconds/60} min` (up to 2 decimals); under 60 s
   as `{seconds} s`.
5. **q11-5 (b) note.** Service coverage note is `{observed/60} of {required/60} min covered` (else `coverage unknown`).


## q14 (final fix round)

Readings taken by the Group 1 presentation fixer; each is applied and needs only confirmation.

1. **H3 Dispatch readability.** Dispatch is the loaded Overview summary itself, so it is counted readable whenever
   the S5 Overview renders (CLOSED and UNKNOWN assessment states included, as well-formed authorized answers). The
   empty-set sentence is therefore unreachable on the rendered route and is tested through the exported
   `overviewReadsStrip` helper. Confirm, or rule that a CLOSED Dispatch assessment is not readable.
2. **H3 objective scope.** The MINIGRID objective sentence replaces the objective line for every assessment state
   on a MINIGRID Overview (not only the CLOSED branch that carried `nothing here is a current answer`), since the
   not-stated sentence would contradict it equally. Non-MINIGRID keeps both existing branches.
3. **M2 row label.** The critical row's bar label and its table `Load` cell both read exactly
   `Clinic feeder delivered power` (the ruled text), whatever the critical load's own label; the card keeps
   `{load_label} (critical)`.
4. **M4 reach.** The empty-legacy reason is applied through one basis-aware wrapper of the Performance gate on the
   Overview route and on the Site Finding index route (the Overview's Needs-attention list reads the index refusal
   message); other Performance routes keep the plain gate reason.
