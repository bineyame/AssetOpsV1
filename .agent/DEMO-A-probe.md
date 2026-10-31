# DEMO-A U1 probe (build sheet `AssetOpsV1-plan2/.agent/build-sheet-DEMO-COMBINED.md` §3 U1)

Base: main `e19bb687`, branch `task/DEMO-A-combined-dataset`. No product code. Probe scripts were scratch only
(not committed): a driver that makes a `git archive HEAD` tree with `var/sites/kobo-001.yaml` only, a child that
runs the s602b REPLAY body (`tools/s602b_verification_walkthrough.py:60-143`) over a manifest file and publishes
diesel price v1 (`publish_assumption fixture --step v1`) before the evaluation, and an in-process
`TestClient(lab_app.app)` reader. Then `evidence_migration run`, two `scheduling.run tick --environment default
--max-sites 5 --s3-jobs 10 --consequence-items 100`, `performance_migration run`, then the reads again.

Runs (DB now 2026-10-31 04:0x UTC):
- **shift**: v2 re-timed per §2 with S = 2026-10-29 into `assetops_demo3_probe_test`. Baseline run S 03:00-11:00,
  foundation_known_at S-6d 12:00, received S 12:00; accept S 13:00, apply S 14:00 (reserve 25, effective S+1 00:00),
  freeze S 15:00; later run S+1 03:00-11:00, foundation_known_at S 16:00, received S+1 12:00; evaluate S+1 13:00;
  windows S 06:00 / S+1 06:00. Wall: replay 187 s, S2 1.5 s, ticks 11.9 s + 10.2 s, Performance 1.5 s,
  **total 246 s** (U2 wall cap basis).
- **v2**: unmodified manifest into `assetops_demo3_probev2_test` (see §v2 below).

## STOP RULE FIRED: the cost check is not calculated

ACT verification `cost_check` (on `GET /api/sites/KOBO-001/actions/{id}`, `.verification.cost_check`):
`{"state": "UNAVAILABLE", "reason": "PRICE_MISSING", "recorded_at": "2026-10-30T13:00:00+00:00"}`.
On the board this reads "Modelled change not calculated: no diesel price covers both hours"
(`site_outcomes/board.py:71`, `:384`).

Cause (structural, not the trial data):
- The hook selects the price **as known at the evaluation clock**: `price_selection(..., now)`
  (`actions/verification.py` `_cost_check`, ~`:908`) -> `prices.snapshot(..., known_at)`
  (`financials/composition.py:150-152`).
- The evaluation clock is the story instant S+1 13:00 (in the past), but a price revision is always stamped
  `clock_timestamp()` at real build time T (`financials/adapters/postgres_assumption_store.py:131`); the store has no
  decision-clock override. So no price revision is ever known at a story evaluation instant before T.
- The sheet's §2 last row ("price v1 published before evaluation") cannot hold while evaluation is story-timed and
  the publication is real-timed. The s602b `verified` case avoided this only because its evaluation clock
  (2026-11-02) was later than its real publication time.
- Consequence for owner decision 1: option (b) (s602b authored windows) does **not** fix this by itself; the
  price-knowledge cause is the same for any story-timed evaluation.

Options for the Architect (not taken):
1. Publish price v1 first, then evaluate at a clock after that publication (for example T + 1 min). Every story
   instant is before T, so RESOLVED and the cost check then land on day T, not on S+1; whether the board/verification
   reads stay as the sheet expects on S is unproven.
2. A decision-clock override on the assumption store (product/adapter change; outside the sheet).
3. Accept the honest "not calculated" result (decision 1(a)) - but then CO-3/R595 stay open.

## Findings (a)-(h)

**(a) Overview freshness, day S.** Before S2: 409 `AWAITING_EVIDENCE_MIGRATION`. After S2 + 2 ticks + Performance:
S and S+1 `freshness.state == "CURRENT"`, `source_reason` "Empty-set comparison: the file-backed baseline holds no
dispatch claim for KOBO-001…", schedule IDLE, heartbeat fresh. S-1 and S+2: UNASSESSED (no evidence). S2 printed
"Evidence cutover: permitted"; Performance "Performance cutover: permitted". No `enrol` needed: the tick selects
KOBO-001 with reason `EVIDENCE` (`scheduling/tick.py:208-209`).

**(b) Finding index, day S** (`GET /finding-index?domain=mini-grid-dispatch&from=S&to=S+1`; `domain` is required,
422 `UNSUPPORTED_DOMAIN` without it): status CURRENT, 1 row (the F-104 Finding). S+1: CURRENT, 0 rows.

**(c) F-104 revisions and ACT events, before -> after the ticks.** `finding_revision` rows for the Finding: 2 -> 2
(same IDs). Tick 1 S4 `MATCHED` with `revision_ids: []`; tick 2 `SKIPPED_UNCHANGED_FENCE`; S3 processed 0 both
times. ACT events ACCEPTED S 13:00, APPLIED S 14:00, RESOLVED S+1 13:00 -> unchanged; no RESOLUTION_WITHDRAWN.
Outcome VERIFIED `TARGET_AND_GUARDRAILS_PASS`, still latest. **Stop rule 1 does not fire.**

**(d) Cost check.** UNAVAILABLE / PRICE_MISSING - see the stop rule above. **Stop rule 3 fires.**

**(e) Board rows S and S+1** (`/outcome-board?from=S&to=S+1`; no objectives declared yet, so every row
NO_OBJECTIVE):
- S: Cost headline "exposure in this hour" (0.00-0.00 USD), "200 min avoidable, 30 min unclear", fuel price
  "Declared at 1.25 USD per litre"; Cost `must_not_harm` null; **no F-104 item listed on Cost or Protect**;
  ACT-000001 sits under **Protect** `earlier` with result "Verified on test data · linked finding outside this view";
  Assure "1 verified result", readings "Generated test data source · readiness Full".
- S+1: Cost "No priced exposure in this hour", "0 min avoidable"; Protect "condition not assessed", same ACT earlier
  entry; Assure UNKNOWN with MG-7 `PRODUCER_NOT_SETTLED` ("Source not resolved · readiness Unknown").
- So F-104 and ACT-048 are now on one board day (the re-time works), but CO-1's "Cost lists F-104 / no item says
  linked finding outside this view" does not hold yet without objectives; U3 must re-check after objectives are
  declared (open risk, not a stop rule).

**(f) `rp._draft` with the shifted interval.** Accepted: both drafts returned READY with no blocking reasons
(`host/tests/test_s6_verification_replay.py:174`), both publications COMPLETED (582 batches / 1036 envelopes each,
no duplicates/rejections). Forcings are run-offset based (`simulator/assetops_simulator/packs/minigrid.py:505-545`),
so a whole-day shift keeping 03:00 UTC starts is safe. Outcome VERIFIED as in v2.

**(g) w502 `positive` work window and B4's 0 completed requests.** Scenario `cold-backup-failed` shifted to
[D 16:00, D 17:00), board window [D 16:00, D 17:05) (`tools/w502_cold_work_cases.py:56, 69-73, 118-144`). Incident
D 16:11, WR D 16:20, record 16:40, assign 16:41, complete 16:42 (`tools/w502_cold_work_walkthrough.py:146-222`);
earlier visits `wr_at - [24, 11] d` (`:459-480`). Cause of B4's 0: the work index selects maintenance requests by
`created_at` (`work/adapters/postgres_work_read.py:70-73`), the rows are written at real time R > `to`, and at B4
(`c3613c2db`) `site_outcomes/cold.py` made a single `[to-31d, to)` read. OUT-C U2 already fixed it: the forward
read `[to, to+31d)` plus an `occurred_at` filter (`site_outcomes/visits.py:3-5, 23-25, 42`). The WR's `occurred_at`
is inside the window; no fix to the WR or window is needed on current main (U3/U4 to confirm on the build).

**(h) EV Chain and committed manifests.** `native_replay` (`tools/w504_ev_work_walkthrough.py:105-146`) never
compares against `contract-fixtures/w2/ev`; the digest/byte assertions are only in the w205b tests
(`backend/tests/test_w205b_ev_replay_postgres.py` `manifest()` :545-570, `pinned()` :573-582,
`test_six_registered_replays` :892-950, vector tests :714-991). But a whole-day shift hits three other checks on
the path, each a U5 stop-rule candidate:
1. `w504_ev_work_walkthrough.py:122-124` refuses unless `registered.WINDOW == P.E_START/P.E_END`
   (`tools/w504_ev_work_cases.py:39-40`, literal 2026-10-06) - the planned `window=` keyword covers this.
2. The Draft run refuses INTERVAL_INVALID unless the interval start equals the scenario start
   (`runs/service.py:562-571`); `config/scenarios/ev-interrupted.yaml:7-8` is fixed at 2026-10-06 08:00. The
   scenario document (or the `open(scenarios=...)` repository) must be shifted in memory too.
3. `Chain.open` hardcodes `now=lambda: "2026-10-06T07:00:00Z"` (w205b test module ~:261) instead of `SETUP_AT`, so
   the module-constant swap does not reach it. Needs checking in U5 against the "change to a test module" stop rule.
Also: `EXPECTED` is built at import from `_t`, so swapping `_t` later has no effect (harmless: `native_replay`
never reads it). w601's swap pattern: `tools/w601_seed.py:529-545` (save, assign module globals, restore in
`finally`).

## v2 unmodified

Wall: replay 200 s, total 271 s. Same results as the shifted run, confirming the causes are not the re-time:
- VERIFIED `TARGET_AND_GUARDRAILS_PASS`; F-104 revisions 2 -> 2 across the ticks (S4 `MATCHED`, `revision_ids: []`);
  events ACCEPTED 10-14 01:00, APPLIED 10-14 02:00, RESOLVED 10-16 01:00, unchanged; no withdrawal.
- Freshness CURRENT on 10-13 and 10-15 (assessed days), UNASSESSED on 10-12 and 10-14; Finding index 10-13 CURRENT,
  1 row.
- The day split the sheet describes is real: the Finding is on 10-13; ACT-000001 first appears on the 10-14 board.
- Cost check `UNAVAILABLE / PRICE_MISSING` (recorded 10-16 01:00): the same price-knowledge cause.
