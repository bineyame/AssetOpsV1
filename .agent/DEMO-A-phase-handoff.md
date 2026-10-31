# DEMO-A phase handoff

Sources: `AssetOpsV1-plan2\.agent\build-sheet-DEMO-SPARSE.md` (wins where it differs) over
`build-sheet-DEMO-COMBINED.md` (rev 1 + Addendum 1). Branch `task/DEMO-A-combined-dataset`.

## State (2026-10-31, DEMO-SPARSE)

- Pre-flight + Q1 ruling (demo configurations re-timed to Kobo commissioning): `.agent/DEMO-SPARSE-preflight.md`.
- **U1 probe: done**, `.agent/DEMO-SPARSE-trial-probe.md`. normal = necessary-run; overcast = necessary-run
  (daytime-overcast refused the 8 h interval); overuse = reserve-trial; Kobo degraded = first-half delivery
  (degraded-evidence refused under v4). Trial hour (a) 06:00, cost check `MODELLED_NO_IMPROVEMENT` 0 USD. Reported.
- **U2: built** `tools/demo_story_days.py` (`load`, `resolve`, `DayRun` + `known_at`, `plan_add_day`),
  `backend/conversions/demo-story-days-v1.json`, `prepare --days`, `<work>/days.json` (`days` + `doc`), story v2
  (install S-29d 11:00, import -1 h, price +1 h), Kobo cap 80 s/run + 60. Tests `backend/tests/test_demo_story_days.py`.
- **U3: built and run** `tools/demo_combined_kobo.py`: `configure_at` (Q1), `run_day`, `publish_first_half`,
  `_trial_chain` (opens the S6 harness after the trial-day Finding exists: its demo grant snapshots Finding ids at
  open, `backend/tests/test_s6_action_store_postgres.py:46-55`), `kobo.json` `days[]` + `configuration`.
  Dev prepare `--sites kobo` at `57397cea1` on `assetops_demo3_dev_test` / `var/demo3_dev` (KEPT for U4 add-day
  checks; drop with the tool's `drop`): 7 runs + 1 missing day, Findings on S-14, S-7, S; VERIFIED ACT-000001,
  `MODELLED_NO_IMPROVEMENT` 0 USD; Kobo child 746 s (about 105 s/run, not 80: raise `kobo_expected_seconds` to
  110 s/run + 60 before U6), total 813 s, cap 1480 s. **Still to do in U3:** the child's unit check
  (`GET /api/sites/KOBO-001/finding-index?domain=mini-grid-dispatch&from=S&to=S+1` holds the accepted Finding).
- **U3 done** (`11da30c75`): `trial_day_index` unit check (one-day index [S, S+1) CURRENT, holds the accepted
  Finding; proved on the dev DB: CURRENT 1 [fbedca42...]); `kobo_expected_seconds` 110 s/run + 60.
- **U4 done, exercised on the dev DB** (2026-10-31 ~07:20 UTC): `--day S-14d` refuses `DAY_HAS_EVIDENCE` (evidence
  check now precedes the calendar duplicate check); live `normal` S-13d and `late` S-20d / `late --as overuse`
  S-18d (91 s each) read PENDING on their one-day index until a tick, then CURRENT (S-18d: 1 Finding after one
  `tick`); `--assess-now` normal S-19d CURRENT at once; `missing` default (S+2) appends days.json only.
  Observed: assessment is Site-wide, so an `--assess-now` (or any assess) also assesses earlier pending live days,
  and a pending live day turns other one-day windows `STALE_PROJECTION` until assessed. Dev days.json now holds
  these extra days; a fresh dev prepare is needed for U5.
- **U5: both children written, NOT run** (Postgres held for IDX-GAPS `-Tier all` when written).
  - `tools/demo_combined_cold.py`: per day one `ShiftedChain` replay; swaps (process-local) `pg_harness.fresh_database`
    -> no-op (else it WIPES Kobo), `producer.target_delta` -> D 16:00, `producer.BASE_SCENARIO` -> kind yaml,
    `producer.shifted_case` -> mode `ordinary`, `P.ShiftedChain` factory -> case `ordinary-day-<n>` (unique gateway
    epoch / attestation keys), w202 `PostgresEvidenceLedger`/`BatchIngestionService` clock -> `received_at`
    (D 17:05). Install once at `cold.install_at`. `failure` day execs `w502_cold_work_walkthrough.BUILD` (positive)
    with `sys.argv` swapped; others replay only. Writes `cold.json` `days[]`. Untested risks: received 17:05 equals
    window end (if late-released readings refuse, use received + 5 min); `install_cold_lab` re-calls inside
    `open()` with start-4 h clock assumed idempotent; BUILD's reads at db_now +-1 d see 0 rows (`blocked`, not fatal).
  - `tools/demo_combined_ev.py`: per day `registered.Chain` subclass (attest assertion re-checked per epoch),
    w205b constants shifted by whole days, INSTALL/SETUP at `ev.install_at`/+1 h, `RunSetupService` now ->
    SETUP_AT, `ev_parsing.EV_WINDOW` + in-memory shifted scenario (`FakeScenarios`, id `<scenario>-day-<n>`),
    `open(fresh=False, scenarios=, scenario_id=)`, then `run_worker` + `select_exact`. Pure check passed: shifted
    ev-complete / ev-fault parse. **Missing:** fault-day work rows: w504 `_declare` (`w504_ev_work_walkthrough.py:214`;
    Action `raised_at` = DB now, must be within 30 d), connector visits conn-v1/conn-v2 and plan-connector from
    `story.json` `ev` via `build_work_service` + `test_w401_work_service_postgres` helpers (w502 BUILD :456-502
    pattern); CO-10 needs PLAN_OVERDUE "Connector inspection" and CHARGER_FAULT_OVERDUE_INSPECTION on the EV board.
  - Next: when `docker ps` shows no `assetops-ops03-*`: `drop` the dev DB, then `prepare --sites kobo,cold,ev
    --no-finish` (estimate 2x(30+940+300+200) s, about 49 min cap; ask the coordinator first: over 20 min), or
    first a cold-only/EV-only dev prepare (Kobo is needed by neither child).
- U6 (self-check child `tools/demo_combined_finish.py`, slow build test, R535/R552/R569/R595 resolutions, packet,
  task status, CODE_STATE/ACTIVE_CONTEXT): not started. Register R615/R616/R618 added (`4992b6677`). R595 still
  open on main at `ca6d7d61b` (IDX-GAPS not merged).

## Resume notes for U5 (from DEMO-A Explore)

- Cold: `test_w502_cold_scenario_producer.ShiftedChain.open` (:73-108) reads DB now (:79), calls
  `producer.shifted_case` (:80); install = start - 4 h, setup = start - 1 h (:82). Thread `story_day`/`install_at`/
  `scenario_path` through `target_delta` (`tools/w502_cold_work_cases.py:69`), `shifted_case` and `ShiftedChain.open`.
- EV: `Chain.open`'s `now=lambda: "2026-10-06T07:00:00Z"` (test_w205b :258-263) -> swap `registered.RunSetupService`
  (w601 swap pattern `tools/w601_seed.py:529-545`); shifted scenario via `open(scenarios=..., scenario_id=...)`;
  `native_replay` guard `tools/w504_ev_work_walkthrough.py:122-124` needs `window=`.

## State 2026-10-31 (second implementer; returned early near its context limit)

Postgres stayed held: `assetops-ops03-20261031-102659-a376df` (IDX-GAPS `-Tier all`) was still running after ~40 min
of polling, so **nothing below has run on a DB**. Dev DB `assetops_demo3_dev_test` / `var/demo3_dev` NOT dropped yet.

- `4baa8fda1` **Depot fault-day work rows** in `tools/demo_combined_ev.py`: `declare_and_work` (called inside
  `run_day` while the w205b/w504 swaps are active, only when `day.kind == "fault"` and `story` is passed by `build`;
  live `add-day` passes no story, so no work rows) runs `W._declare(url, "positive", f"demo3-{epoch}", ...)` then
  `write_work` (Kobo child pattern): `story.json` `ev.visits` (conn-v1/conn-v2, completed) and `ev.plans`
  (plan-connector, due S-6d) on `selection.connector_asset_id`. `ev.json` `days[fault].fault_day` = {action, intent_id,
  finding ids, work {asset_id, visits, plans}}. Untested risk: the CHARGER_FAULT rule matches the plan's asset to the
  health CONNECTOR fault row's `asset_id` (`outcomes/warnings.py:236-248`, `site_outcomes/ev.py:157`); if CO-10's
  charger-fault half fails, use the fault row's asset (EV health read) instead of the session's connector.
- `8d613a968` **U6 code**: `tools/demo_combined_finish.py` (`CHECKS` rows CO-1,2,3,5/SP-1,SP-2..SP-6,CO-6..CO-12;
  `idx=True` rows skip until `analytics.finding_index.POLICY_VERSION == "finding-index/2"`; `check` writes
  `<work>/check.json`, exit 1 on any fail; reads via `lab_app.app` with keys.json env). `prepare`'s `finish()` already
  calls it when all three Sites are built. `backend/tests/test_demo_combined_postgres.py` (slow; 18 tests collected:
  one per non-mutating row + `test_self_check_ran_in_prepare` + SP-7 last; DB from the test URL's host/port by
  patching `tool.PG_ADMIN` and `Demo.url`). `prepare` now copies the tree when `git` is absent (test container).
  `backend/TESTING.md` slow-tier list names the test. Guards: `check-all.ps1` 11/11 at `8d613a968`.
  Check assumptions to verify on the first full DB (shapes from an Explore survey, not yet read on real data):
  SP-3 looks for `finding_gaps` anywhere in the board body; SP-4 reads `index["gaps"]` {day, state|status} (both
  IDX-GAPS shapes, unknown until it merges); SP-5 looks for any `first_on` in the dispatch window body; CO-9 checks
  EV Assure != UNKNOWN and the Portfolio EVIDENCE cell != UNKNOWN (not the port-equality spy of test_out_b4).
- **Resume, in order:** (1) when `docker ps` shows no `assetops-ops03-*`: `python tools/demo_combined.py --db
  assetops_demo3_dev_test --work var/demo3_dev drop`; (2) `prepare --sites cold --no-finish`, then `--sites ev
  --no-finish` (each < 20 min; watch cold `received_at` == window end, `install_cold_lab` re-open idempotency, 0-row
  reads at DB now +-1 d); (3) ask the coordinator before the full three-site prepare (cap ~49 min); the self-check
  runs in it; (4) register R535/R552/R569 -> resolved by DEMO-A (<sha>) once their rows pass (R595 left to
  IDX-GAPS); packet `.agent/DEMO-A-packet.md` (force-add) with the runbook caution below; task status in_review,
  CODE_STATE, ACTIVE_CONTEXT.
- **Runbook caution for the packet:** `add-day --assess-now` assesses the whole Site, and while a live late day is
  pending (before a tick), other one-day windows read `STALE_PROJECTION`; during a live demo add a late day only after
  the boards you will show have been opened, or tick before showing other days.

## State 2026-10-31 (third implementer: single-site dev prepares run)

Old dev DB `assetops_demo3_dev_test` / `var/demo3_dev` dropped. Kept for inspection: `assetops_demo3_cold_test` /
`var/demo3_cold` and `assetops_demo3_ev_test` / `var/demo3_ev` (both `--no-finish`, built at `f320ac636`; drop with
the tool's `drop`). Probe DB `assetops_demo3_probe5_test` dropped.

- `c81b062d8` **Cold attestation instant**: first run wrote no Finding on the failure day; every reading was
  `CLOCK_UNATTESTED` because `ShiftedChain.attest` records at `datetime.now` (wall), after the `received_at`
  knowledge cutoff. The cold child's `DayChain.attest` swaps the producer module's `datetime.now` to the day's setup
  instant (start - 1 h) for that call only. `received_at` == window end (17:05) is fine (all accepted).
  `install_cold_lab` re-open at start-4 h is idempotent (3 days ran).
- `c81b062d8` **EV days on Tuesday**: ev-charger/1 refuses any window not on a TUESDAY
  (`host/ev_publication.py` `ev_parameters`). `demo_story_days.SITE_WEEKDAY = {"ev": 1}` + `weekday_offset`: each EV
  day falls back to the Tuesday on or before its listed day (S = 10-29 Thu -> fault 10-27, normal 10-20); `add-day`
  for EV defaults to last + 7. The EV work rows (S-relative visits/plan in `story.json` `ev`) move by the same shift
  (`write_work(shift=)`), so they keep their places before the fault. Test `test_ev_days_fall_back_to_the_ruled_tuesday`.
  SHEET DEVIATION (record in the packet): sheet §2 puts EV on S-7 / S; they are on the Tuesday on or before.
- `f320ac636` **EV fault scenario**: `ev-fault.yaml` faults before any session starts and gives no EV Finding, so
  w504 `_declare` refused ("expected one SUPPORTED EV Finding on a fault-ended selected session, found 0"). The
  `fault` kind now uses `ev-interrupted` v1 (w504's own `POSITIVE_SCENARIO`, unchanged). SHEET DEVIATION: sheet §2
  table names `ev-fault.yaml`; reported to the coordinator.
- `f320ac636` cold `findings_on` now counts open episodes (`episode_end IS NULL`); cold.json `findings` was [] before.
- Overcast (SCN sheet): 720-min `kobo-daytime-overcast` v2 re-run is **BLOCKED** `INITIAL_VALUE_NOT_RESOLVED`
  (fuel-tank-volume@fuel-tank, generator-state@generator not stated by the scenario; mini-grid v5 needs them).
  Overcast keeps `kobo-s3-dispatch-necessary-run`; day list unchanged; row in `DEMO-SPARSE-trial-probe.md`.

Real-data results (single-site, no objectives declared since `finish` needs all three Sites):
- Cold: normal 10-22 (no Finding), degraded 10-26 (`cold-missing-probe`: a COLD_START_FAILURE Finding, Protect
  NEEDS_ATTENTION; real data, not a beat the sheet promised either way), failure 10-29 (COLD_EXCURSION +
  COLD_START_FAILURE, w502 positive work: 2 cases, 2 records, 2 plans). BUILD's own index reads at DB now +-1 d
  record `blocked` (expected, not fatal). 126.6 s for 3 runs.
- Self-check rows on the single-site builds (scratch driver calling the unmodified row functions):
  SP-2 pass (Protect NO_OBJECTIVE here; CC-1 ON_TRACK; **re-check on the full build**, where objectives exist);
  CO-7 pass; CO-9 pass (Assure WATCH, Portfolio EVIDENCE LIMITED); CO-10 EV half pass with the plan on the
  session's connector (PLAN_OVERDUE "Connector inspection overdue" + CHARGER_FAULT_OVERDUE_INSPECTION; no asset
  change needed). EV: 143.2 s for 2 runs; Action raised, visits 10-12/10-22, plan due 10-21.
- Not run (need all three Sites / Kobo / IDX): CO-1..3, SP-1, SP-3..7, CO-6, CO-8, CO-11, CO-12, Kobo half of CO-10.

Guards: `check-all.ps1` 11/11 at `f320ac636`; `test_demo_story_days.py` 18 passed.

Resume: wait for the coordinator (new Kobo trial scenario from the SCN lane, IDX-GAPS merge); then the full
three-site prepare (cap ~49 min) runs `finish` + the self-check; then U6 closeout as listed above.

## State 2026-10-31 (third implementer, after Addendum 1 of the DEMO-SPARSE sheet)

- `2d836485e` merged main `89280952d` (IDX-GAPS): `finding_index.POLICY_VERSION == "finding-index/2"`, so the [IDX]
  rows of `demo_combined_finish.py` and `test_demo_combined_postgres.py` now run (no skip). One conflict, in
  `.agent/mock-departure-register.md`: took main's R595 (resolved by IDX-GAPS) + R610-R613, kept R615/R616/R618, and
  added **R619** (Depot's story hour on the Tuesday on or before S; Portfolio/links on the week period).
- `be0d21b88` Addendum 1 (a): CO-6 reads `/api/estate/portfolio` and `/outcome-summary` over `from=S-6d&to=S+1d`;
  `links` prints the Portfolio on that week and, per Site, every story day from `days.json` with its kind and board
  URL (EV shows its Tuesdays). `mini_summary_day(to)` (`site_outcomes/read.py:138`) returns the previous day for a
  midnight `to`, so `to = S+1d 00:00` resolves Kobo to S: confirmed by reading the code. On the EV build the week
  outcome-summary gives EV `LATEST_EVENT` (read, 200).
- **Predicted CO-6 risk, not forced:** `estate/coverage.py:98-100` marks the Site `UNKNOWN` when any day in the
  period has no available selection (R613's all-days rule). Kobo has runs only on S-3 and S inside S-6d..S+1d, so
  CO-6's `body["status"] == "CURRENT"` may fail on the full build. If it does, record it with this cause and take it
  to the Architect; do not loosen the row.
- (b) `ev-interrupted`: CO-9 and the EV half of CO-10 held on the single-site build (above). Cold degraded Finding
  kept; SP-2 stays on S-7. Overcast day list unchanged (720-min change withdrawn).
- Guards: `check-all.ps1` 11/11 at `be0d21b88`; `test_demo_story_days.py` 18 passed.
- Next: wait for the coordinator (the SCN trial result decides the trial kinds); then the full three-site prepare.
