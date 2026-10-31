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
