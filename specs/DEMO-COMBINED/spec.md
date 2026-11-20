# Build sheet: combined three-Site demo dataset (DEMO-COMBINED), rev 1, 2026-10-31

Architect: Claude (`.ai/ROLE_CONFIG.md` row 9, owner 2026-10-27). Checked against code on main `e19bb687`.
Owner trigger, word for word: "start the combined three-site dataset" (`.agent/owner-client-demo-sequence-2026-10-30.md`).
This sheet wins over earlier carry-over notes wherever they disagree. Builders read this sheet, the files it cites by
line, and nothing older.

## 0. Acceptance spine (carry-over list → IDs used below)

| ID | Carry-over (owner file + addendum 6, `build-spec-outcome-sprint-2026-10-29.md:1037-1043`) | Register |
|---|---|---|
| CO-1 | One Kobo board day shows F-104 under Cost, Protect lists it as checked, and Cost has the Must-not-harm line with ACT-048's verification link | R552 |
| CO-2 | Mini rows are current: Overview `freshness.state == CURRENT` (S2 comparison passed), Finding index not UNASSESSED, no measured row UNKNOWN for "producer read unsettled" | OUT-B4 add. 6 |
| CO-3 | MG-2 Cost-row Earlier ACT entry carries the modelled cost line on real data | R595 |
| CO-4 | Captures of the cost check (OUT-E L1) | — |
| CO-5 | At least one "On track", reached honestly (never forced) | R585 |
| CO-6 | Portfolio counts all 3 Sites; `objective_site_count == 3` | R535 |
| CO-7 | GreenHarvest Earlier shows the completed inspection | B.7 #4 |
| CO-8 | Estate Finding-row keys (`finding_id\|finding_revision_id`) match the B2 fake's key shape | add. 6 |
| CO-9 | Depot readiness settled (Assure not UNKNOWN from a refusal) | add. 6, R577 |
| CO-10 | Kobo and Depot plan warnings and the charger-fault warning on real data | R569 |
| CO-11 | Repeat visits, plans and objectives present on all three Sites | OUT-C/D |
| CO-12 | Slice outputs render on this one dataset: category labels (A), outcome boards (B), early warnings (C), declared objectives (D), estate event window (W, `LATEST_EVENT`), MG-2 cost check (E) | — |

## 1. Code-reality check (the seven questions)

**Q1. One DB for three producers.** Feasible. No real conflict. There are five frictions, each handled in §3:
- **Tenant.** All three use tenant `demo`: Kobo through `pgb.converted` in the S6 replay, cold through
  `install_cold_lab(tenant_slug=...)` (`sites/cold_lab.py:52`), EV through `install_ev_lab(tenant_slug="demo")`
  (`test_w205b_ev_replay_postgres.py:254`). `DEVELOPMENT_TENANT_SLUG = "demo"` (`config.py:105`).
- **IDs.** Every row ID is a random `uuid4`, and the Site codes differ (KOBO-001, COLD-LAB-001, EV-LAB-001). Nothing is
  pinned by ID. The v2 manifest says so (`d-verification-window-v2.json` `expected.identifiers`). s602b's "holds are
  battery-scoped, so cases cannot share one" (`s602b_verification_walkthrough.py:18`) applies only to its *several*
  test-scoped Kobo cases. We build one Kobo chain.
- **Migrations.** Each producer runs `command.upgrade(..., "head")`. That is idempotent, so we migrate once at
  `prepare`, and the later calls are no-ops.
- **DB-name guards.** These clash. `s602b_test_scoped_cases.py:362` refuses any `*_test` name. The w504 child
  requires `*_test` (`w504_ev_work_walkthrough.py:114`). w502 also uses `*_test`. The combined tool therefore calls
  the producers' in-process functions, never their `main()`, and uses one `*_test` name of its own (§5).
- **Clocks.** There are three unrelated families:
  - Kobo: the fixed manifest instants of `d-verification-window-v2.json`.
  - Cold: shifted from DB now (`w502_cold_work_cases.py:69-74`, `D = floor(now) − 1 d`).
  - EV: fixed module constants (`test_w205b_ev_replay_postgres.py:102-120`, E = 2026-10-06 08:00-09:00).
  - **Ruling:** one story day `S` drives all three (§2).
- **Legacy Site documents.** The serving tree's `var/sites/` must hold only `kobo-001.yaml` (the s602b pattern,
  `s602b_verification_walkthrough.py:228-231`). Cold and EV are imported with `legacy_documents=()`
  (`cold_lab.py:61`).
- **Install clocks.** These follow DD-13's rule (strategy doc DD-13 card): Kobo → cold → EV → objectives, strictly
  increasing, else stop with `INSTALL_CLOCK_CONFLICT`.

**Q2. S2 Evidence comparison.**
- **`NO_LEGACY_EVIDENCE` is not honest for Kobo.** The basis is meant only for a Site that no legacy document declares
  (`sites/w402_demo.py:63-66`). KOBO-001 *is* declared: it is a shipped YAML Site, and the tree copies
  `kobo-001.yaml` into `var/sites`.
- **The honest route is the real comparison**, the s501 route (`s5_overview_walkthrough.py:175-179`):
  `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001`.
  - On a fresh tree its legacy file store holds no evidence for KOBO-001. It then writes a PASSED report with
    `empty_set: true` and the statement "Empty-set comparison: the legacy file store holds no evidence for KOBO-001…"
    (`evidence/legacy_comparison.py:196`).
  - `permits_cutover` accepts exactly that report (`:258-273`), and only while the store stays empty, in the same
    environment and store root. So prepare and serve must use the same tree.
- **Never** call `record_no_legacy_evidence_basis` for Kobo. Cold and EV do not use the S2 Overview gate.

**Q3. Making the mini Overview and the Finding index CURRENT.**
- **Why they are stale today.** The s602b builders never run the schedule. The Overview is STALE_PROJECTION and the
  Finding index has no S3 selections (`build-spec-outcome-sprint:985-987`).
- **The route** is the one s501 proves to CURRENT (`s5_overview_walkthrough.py:190-193`, `:248-256`):
  1. Run the S2 comparison.
  2. Run `python -m assetops_backend.scheduling.run tick --environment default --max-sites 5 --s3-jobs 10
     --consequence-items 100` twice (S3 selections plus the S5 projection).
  3. Run `python -m assetops_backend.performance_migration run --tenant demo --site KOBO-001` (the Performance gate).
- **Heartbeat.** The heartbeat thresholds are 300 s per environment and 900 s per Site (`scheduling/health.py`). The
  served Overview turns SCHEDULE_STOPPED five minutes after the last tick, so **serve runs a tick loop** (§3 U6).
- **Unproven point, so U1 probes it first.** The tick runs at real DB time, after the Kobo chain's pinned instants.
  The probe checks whether that creates a new F-104 revision or withdraws the resolution (the `withdrawn` mechanism).

**Q4. One Kobo board day.** Yes, but the cause is not the board's rules.
- **How the board selects.** The mini board takes Findings for the UTC day (by episode) and Actions created in
  `[end − 31 d, end)` (`site_outcomes/mini.py:34`, `:270`; Action membership is `created_at`,
  `actions/site_index.py:3-4`).
- **Why the days split.** ACT-048 lands on another day because its Finding is recorded the next day: v2 sets
  `received_at` 10-14 00:00 for the 10-13 run, and the accept follows at 10-14 01:00. An Action cannot precede the
  Finding revision it accepts.
- **The fix.** Re-time the replay so the baseline is received, assessed, accepted, applied and frozen on day S itself,
  with the later run on S+1 (§2). Board day S then holds F-104, ACT-048 (created S 13:00) and its verification. This
  also gives CO-3: the Action is VERIFIED, so the OUT-E hook has appended the cost check.
- **Use the registered replay, not the s602b `verified` case.** v2 is "two separate fixed-policy registered Lab runs…
  nothing in either window is authored or test-scoped" (`d-verification-window-v2.json` `status`). Its screen label is
  "Generated test data" / "Registered Lab trial data". The authored case is the fallback in owner decision 1.

**Q5. "On track".** It can only appear where a measure meets its declared objective on a complete window
(`outcomes/status.py:85-86`, R585). We do not tune any target.
- **First candidate: GreenHarvest on a normal night.** A second cold registered replay of `config/scenarios/cold-normal.yaml`
  at S−7 16:00. CC-1 (chamber range) and CC-6 (0 backup start failures) can both be MET there, and no Finding, visit or
  plan falls in that window. The CC-1 path is unit-proven (`test_out_d4_board.py:209-220`).
- **Second candidate: Kobo on board day S+1, after the trial.** MG-5 `unserved_critical_kwh` target 0; v2 baseline
  records 0.
- **Acceptance.** At least one candidate reads ON_TRACK, or the sheet's stop rule applies (§7): R585 stays standing,
  with the measured values recorded.

**Q6. The 30-day back-dating limit.**
- **What it checks.** It is a write-time check against DB now (`work/model.py:37`, `:236-240`, `tx.db_now()` in
  `work/service.py:383`, `:502`). Reads never apply it.
- **What follows.** Any fixed calendar date expires 30 days after itself. That is why R569 was carried.
- **Ruling.** Every date is relative: `S = floor_utc_day(DB now at prepare) − 2 d`, and every work `occurred_at` lies in
  `[S − 24 d, S + 1 d)`, which is inside the limit by construction.
- **Consequences.** A built DB stays readable for ever. A rebuild moves every date, and `links` prints the current ones.
  The Postgres build test stays green on any day.

**Q7. Build time and the long-run design.**
- **Expected inside one tree:**
  - Kobo replay: about 4 min (`s602b_verification_walkthrough.py:248`), two 8-hour mini-grid v5 runs at 5-min steps.
  - Cold: two 65-min replays, about 2-4 min.
  - EV: one 1-hour replay, about 1-2 min.
  - Comparisons and two ticks: about 2 min.
  - Work, objectives and checks: under 1 min.
  - **Total about 10-15 min.** This is inside the accepted long-run budget: one producer ≤ 30 min, peak ≤ 0.25 GB target
    (1.5 GB hard stop), one heavy job at a time, never beside a full suite, keep-awake on, a 2× wall cap enforced by
    the producer.
- **What it does not use.** None of the 91-day machinery (DD-05a..DD-07b, DD-13), which is not built on main (no DD
  merge in `git log`). The windows are the existing hours-long registered windows. DD-13 replaces this dataset later
  (owner decision 2).

## 2. Data timeline (S = floor_utc_day(DB now at `prepare`) − 2 d; all UTC)

| When | Kobo (KOBO-001, minigrid-roles-3) | GreenHarvest (COLD-LAB-001) | Depot (EV-LAB-001) |
|---|---|---|---|
| install, I0<I1<I2 | `pgb.converted` import (Foundation valid_from 2026-09-29 unchanged) | `install_cold_lab` | `install_ev_lab` |
| S−24 d | — | Earlier visit 1 "Starter battery replaced" (wr_at−24 d, OUT-C §C.3) | — |
| S−20 d | Generator visit 1 "Generator inspection" completed | — | — |
| S−15 d | — | — | Connector visit 1 "Connector inspection" completed |
| S−11 d | — | Earlier visit 2 "Control relay reset" | — |
| S−9 d | Generator visit 2 completed | — | — |
| S−8 d | Plans recorded (`occurred_at`): "Generator 500-hour service" RUN_HOURS 500; "Battery capacity test" CALENDAR due S+4 d | — | Plan "Connector inspection" CALENDAR due S−6 d (overdue) |
| S−7 16:00 | — | **normal night**: cold-normal replay `[16:00, 17:05)` (On track candidate) | — |
| S−5 d | — | — | Connector visit 2 completed |
| S−4 d | — | plan "Witnessed backup start test" due (overdue) | — |
| S 03:00-11:00 | baseline registered run; window 06:00-07:00 | — | — |
| S 08:00-09:00 | — | — | E: registered `fault` replay (the case w504 `positive` uses), decision 09:00, late 09:05 |
| S 12:00 / 12:05 | received; S3 assess + S4 match → **F-104** | — | — |
| S 13:00 / 14:00 / 15:00 | **ACT-048** accept / apply reserve 30→25 % (effective S+1 00:00) / freeze plan (baseline S 06:00, later S+1 06:00) | — | — |
| S 16:00-17:05 | — | **failure night**: cold-backup-failed replay; incident 16:11, WR 16:20 linked to the start-failure Finding, record 16:40, assign 16:41, complete 16:42 | — |
| S+1 03:00-11:00 | later registered run (new reserve), window 06:00-07:00 | — | — |
| S+1 12:00 / 13:00 | received, assess, match / bind later selection, evaluate → VERIFIED, cost-check hook appends | — | — |
| S+9 d | — | plan "Compressor coil cleaning" due (due soon) | — |
| build day T ≥ S+2 | S2 comparison, 2 ticks, Performance comparison; objectives declared (`demo-objectives.json`); price v1 published before evaluation (valid_from 2026-10-01 ≤ S) | — | — |

Notes:
- Work rows are written at T through `WorkService` in process, by actor `service:w401-fixture`, with `occurred_at` as
  listed. That is the w403 pattern (`w403_mini_decisions_walkthrough.py:198`).
- The cold rows keep w502's offsets from `d16` (`w502_cold_work_walkthrough.py:148`, `:213`, `:460-476`), with
  `D = S`.
- The EV fault row and the plan sit on the same connector asset. Pre-flight P-C3 of OUT-C applies.

## 3. Slice DEMO-A · `task/DEMO-A-combined-dataset` · 6 units · 5.0 builder-days

New files:
- `tools/demo_combined.py`: the CLI `prepare|serve|tick|links|drop`.
- `tools/demo_combined_kobo.py`, `tools/demo_combined_cold.py`, `tools/demo_combined_ev.py`: the child-side builders.
- `backend/conversions/demo-combined-story-v1.json`: the S-relative offset manifest and labels.
- `backend/tests/test_demo_combined_postgres.py`.

Edits, all keyword-only with byte-identical defaults so the existing walkthroughs are unchanged:
- `tools/w502_cold_work_cases.py:69` `target_delta(db_now, *, story_day=None)`, plus a `scenario_path` keyword on the
  case builder that produces `ShiftedCase` (`:143`).
- `tools/w504_ev_work_walkthrough.py:105` `native_replay(..., window=None)`.

### U1 · Probe (no product code) · 0.5 d · go/no-go gate for U3-U5
Build v2 unmodified, plus a re-timed copy (§2 Kobo rows), into `assetops_demo3_probe_test`. Then run the S2 comparison,
the two ticks and the Performance comparison, and record in `.agent/DEMO-A-probe.md`:
- (a) `freshness.state` of `GET /api/sites/KOBO-001/overview?date=S`;
- (b) the Finding index state and rows for day S;
- (c) the F-104 revision count and the ACT-048 events, before and after the ticks;
- (d) the cost-check state (`verification` summary `cost_check`);
- (e) the board rows for S and S+1;
- (f) whether `rp._draft` accepts the shifted run interval (Kobo forcing, `packs/minigrid.py:517`);
- (g) the w502 `positive` work window, and why B4 found 0 completed requests (`OUT-B-phase-handoff.md:370`);
- (h) where the EV Chain asserts its committed manifest (`contract-fixtures/w2/ev`), so the shift in U5 can be checked.

**Stop rules.** Each stops and goes to the Architect:
- The tick makes a new F-104 revision, or `RESOLUTION_WITHDRAWN`.
- Freshness is not CURRENT after two ticks.
- The cost check reads "Not calculated yet" (then owner decision 1 applies).

### U2 · Orchestrator, tree, DB, story clock · 0.75 d
- `tools/demo_combined.py`, modelled on `s602b_verification_walkthrough.py:203-259`:
  - `git archive HEAD` into `<work>/tree`, with `var/sites/kobo-001.yaml` only.
  - A marker file.
  - The DB guard regex `^assetops_demo3_[a-z0-9]{1,20}_test$`.
  - `DROP`/`CREATE`, then upgrade to head once.
  - The child env: PYTHONPATH (§5), `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` both set to the DB; clear
    `ASSETOPS_TEST_RUN_ID` and `ASSETOPS_TEST_DATABASE_BASE_URL` (`w403_mini_decisions_walkthrough.py:323-324`).
- Story clock:
  - Read `clock_timestamp()` once and set `S`.
  - Write `<work>/story.json` (S, every resolved instant, and the install clocks I0..I3).
  - Assert the order I0 < I1 < I2 < I3 and every `occurred_at ≥ T − 30 d + 1 h`; otherwise `INSTALL_CLOCK_CONFLICT` /
    `STORY_CLOCK_OUT_OF_RANGE`.
- Keys:
  - Generate the random 32-byte hex keys `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` (`estate/scope.py:313`) and
    `ASSETOPS_WORK_CURSOR_KEY_HEX` (`work/global_index.py:57`) into `<work>/keys.json` (in the gitignored work folder;
    never committed, never printed).
  - Without them the Portfolio and global Work return 503 (`fix-slices.md` B18-18).
- Wall cap: twice the U1-measured wall time, enforced by the tool. It stops only the PIDs it started. On Windows use
  `taskkill /PID <pid> /T /F` (`w504_ev_work_walkthrough.py:732`).
- Commands:
  `.venv\Scripts\python.exe tools\demo_combined.py --db assetops_demo3_main_test --work var\demo3_main prepare`, and
  likewise `links`, `serve`, `tick` and `drop`.

### U3 · Kobo chain · 1.0 d
- `demo_combined_kobo.build(url, work, story)`.
  - It reuses the s602b REPLAY body (`s602b_verification_walkthrough.py:60-145`).
  - The resolved manifest is a deep copy of `rp.MANIFESTS["v2"]` (`host/tests/test_s6_verification_replay.py:49`),
    with every instant replaced from `demo-combined-story-v1.json`: run start/end, `received_at`,
    `foundation_known_at`, accept/apply/freeze/evaluate, `effective_from`, window starts.
  - The baseline and later runs are drafted through `rp._draft` (`:149`) and published and accepted through
    `rp._publish_and_accept` (`:192`), with a real gateway process.
  - `rp.LabRunner` (`:88`) runs assess and match.
  - The Action calls go through the real HTTP routes of `verifying(runner)`, with `h.clock.at` set to the story
    instants.
- Then:
  - Publish price v1 (`publish_price_v1`, `s602b_test_scoped_cases.py:185`) before the evaluation.
  - Write the Kobo work rows from §2 through `build_work_service(url).create_case/post_record/post_event/post_plan`
    (`work/service.py:424`).
- After every Site is installed, and therefore in U6's orchestration:
  - the S2 comparison;
  - `scheduling.run enrol` for KOBO-001, only if the probe shows it is not already enrolled;
  - two ticks;
  - `performance_migration run`.
- Output: `<work>/kobo.json` with the Finding, revision, Action and code, plan, outcome, cost-check row and run IDs.
- Unit test: an extension of the Postgres test, run in U6.

### U4 · GreenHarvest · 0.75 d
- `demo_combined_cold.build`. Two `ShiftedCase`s through the w502 BUILD body (`w502_cold_work_walkthrough.py:82-505`,
  mode `positive`):
  - `cold-backup-failed.yaml` with `story_day=S` (start S 16:00);
  - `cold-normal.yaml` with `story_day=S−7`, a distinct `scenario_id` and no work rows.
- Keep OUT-C's authored visits and plans unchanged (`build-spec-outcome-sprint:1716-1731`). Add nothing else.
- CO-7: if probe (g) shows the WR is outside the board's work window, the builder records the cause. The fix, chosen by
  the Architect from that cause, is either the WR's `occurred_at` (it stays inside `[16:00, 17:05)`) or the window
  passed. The board rule is never changed.
- Output: `<work>/cold.json`.

### U5 · Depot · 1.0 d
- `demo_combined_ev.build`.
  - Swap the EV module constants (`test_w205b_ev_replay_postgres.py:103-120`: `INSTALL_AT`, `SETUP_AT`, `WINDOW`,
    `RELEASE`, `ATTEST_FROM/TO`, `FIRST/LATE_DECISION`, `ATTESTED_AT`, `_t`) by the whole-day delta `S − 2026-10-06`.
    This is the w601 module-swap pattern (`w601_seed.py:529-545`).
  - Call `native_replay(..., window=(S 08:00, S 09:00))`.
  - Then w504's `_declare` (`:214`) and the work steps, with every `occurred_at` taken from §2 instead of `now`
    (`:316`).
  - Add the plan "Connector inspection" (due S−6 d) on the `CONNECTOR_FAULT` row's asset, and the two completed
    connector visits.
- If probe (h) shows the Chain asserts the committed manifest digests:
  - the shifted build asserts the same *counts and assertion keys* (`ASSERTION_KEYS`, `:117`) instead;
  - and records its own digests in `<work>/ev.json`.
  - It never edits `contract-fixtures/`.
- Stop rule: if the shift needs a change to a test module, stop and go to the Architect.

### U6 · Acceptance, serve loop, register · 1.0 d
- `prepare`. The order is:
  1. U2;
  2. U3 Kobo build;
  3. U4;
  4. U5;
  5. `python -m assetops_backend.declare_objective` over `backend/conversions/demo-objectives.json` (six objectives,
     all three Sites);
  6. the S2 comparison;
  7. two ticks;
  8. the Performance comparison;
  9. the self-check: the same assertions as the test, read through the served app in process;
  10. `<work>/manifest.json`.
- `serve`:
  - Runs `host/lab_app.py` on 127.0.0.1:8990 with the keys from `<work>/keys.json`. The Action clock is **not**
    pinned: every story instant is in the past.
  - Starts a labelled walkthrough-only schedule loop: one `tick` every 120 s, then the Performance comparison. It is
    never an OS timer and stops with serve.
  - Prints `cd frontend; npm run dev -- --port 5490` with the API base env the s602b `links` uses (`:267-295`).
- `links` prints the demo URLs for S (§4).
- The test (§4) passes.
- Register rows: R535, R552, R569 and R595 → `resolved by DEMO-A (<sha>)`. R585: add the note "On track shown on
  <surface>", or keep it standing under the stop rule. New departures, if any, take R600-R609.

## 4. Tests and captures

**`backend/tests/test_demo_combined_postgres.py`** (marked slow tier; its own DB `assetops_demo3_t<run>_test`).
- It runs `prepare` once in a module fixture through the tool's in-process entry, then asserts the following with
  `TestClient(lab_app.app)`. Each line maps one-to-one:

| Assertion | CO / R |
|---|---|
| `GET /api/sites/KOBO-001/outcome-board?from=S&to=S+1`: Cost lists F-104 (state ∈ {NEEDS_ATTENTION, WATCH}, reason recorded, R542); Protect lists F-104 as "checked here as a safeguard"; Cost `must_not_harm` names "Reliable service and battery and generator life" with the ACT-048 verification href; ACT-048 on the Cost row; no item says "linked finding outside this view" | CO-1, R552 |
| Same day: `GET /api/sites/KOBO-001/overview?date=S` `freshness.state == "CURRENT"`; it equals the board's mini overview port; the Finding index for S has ≥1 row, not UNASSESSED; no measured mini outcome UNKNOWN with "producer read unsettled" | CO-2 |
| ACT-048 verification summary `cost_check.state` set (MODELLED_IMPROVEMENT or MODELLED_NO_IMPROVEMENT); the Cost-row Earlier ACT-048 entry carries the modelled line with "not realised savings" | CO-3, R595 |
| ≥1 row or line ON_TRACK, on the cold S−7 window or the Kobo S+1 board; the source window is complete | CO-5, R585 |
| `GET /api/estate/portfolio?from=S&to=S+1`: `status == CURRENT`; three Sites; Assure says "targets declared at 3 sites" (`objective_site_count == 3`); cold and EV `window_basis == "LATEST_EVENT"`; `double_count_violations == []` | CO-6, R535, CO-12 |
| Cold board on the failure event window: Earlier holds ≥1 completed inspection with its result text; repeat-visit warning present | CO-7, CO-11 |
| Estate Finding rows for S: every key is `"{finding_id}\|{finding_revision_id}"`, the B2 fake's shape; F-104 present | CO-8 |
| EV board (covering day S): `evidence_readiness` port equals the Portfolio EVIDENCE cell; Assure ≠ UNKNOWN from a refusal | CO-9 |
| Kobo board S: PLAN_DUE_SOON "Battery capacity test"; EV board: PLAN_OVERDUE "Connector inspection" and CHARGER_FAULT_OVERDUE_INSPECTION | CO-10, R569 |
| On each Site: ≥2 completed visits, ≥1 plan, ≥1 declared objective line; category pills on Finding reads; warnings never carry money (`test_out_c1_never_money` rule) | CO-11, CO-12 |
| Rebuild determinism: dates are relative; a second `story.json` S equals `floor(now) − 2 d` | Q6 |

**Captures** are slice DEMO-B, below.

## 5. Validation tier and pre-flight gotchas

- **Tier.**
  - Per unit: the scoped files only, `tools\run-host-tests.ps1 -- backend/tests/test_demo_combined_postgres.py
    backend/tests/test_out_b4_board_postgres.py backend/tests/test_out_e4_readback_postgres.py
    backend/tests/test_out_d5_objectives_postgres.py backend/tests/test_out_c4_ev_warnings_postgres.py`.
  - The w502/w504 edits also need `backend/tests/test_out_c3_repeat_visits_postgres.py` and both producers' existing
    `prepare` once, to show they are byte-unchanged (the manifests compared against a run on main).
  - At slice merge: **one `tools\run-backend-suite-in-container.ps1 -Tier all`** on an idle machine. Any `tools/*.py`
    change selects the whole suite (`tools/select-tests.py:45-47`, `:168`).
  - `tools\check-all.ps1` at every commit.
- **PYTHONPATH** (Windows, `;`): `<tree>\backend;<tree>\backend\tests;<tree>\contracts;<tree>\gateway;<tree>\simulator;
  <tree>\host;<tree>\host\tests;<tree>\gateway\tests`. Without `contracts` the venv resolves another tree's copy
  (`OUT-B-phase-handoff.md:342`). Python is `AssetOpsV1-plan2\.venv\Scripts\python.exe`.
- **DB names.** Only `assetops_demo3_*_test` (owner-authorized `*_test`) in `assetopsv1-postgres-1`. Drop only through
  `demo_combined.py drop`, which acts only on the names its marker records. Never touch another DB. `<prefix>_audit*`
  is not used, because the EV helpers need `*_test`.
- **No `-ExecutionPolicy`** anywhere (ROLE_CONFIG §check-all). Run the guards directly.
- **No BOM writes.** Python `write_text(..., encoding="utf-8")`; PowerShell `Out-File -Encoding utf8` is forbidden for
  repo files. Run `git ls-files --eol` on the new files.
- **Cursor keys.** Both, at random, per `prepare`, from the work folder. They are never committed, never logged and
  never placed in a URL.
- **Machine.** Keep-awake script on (`tools\keep-awake-during-tests.ps1`). One heavy job at a time. Never `prepare`
  beside a suite. The builder batches all questions into `.agent/DEMO-A-preflight.md` before any code.
- **Clock traps.**
  - Never call `datetime.now()` for a story instant. Every instant comes from `story.json`.
  - Work `occurred_at` must be ≥ T − 30 d and ≤ T + 5 min (`FUTURE_SLACK`).
  - The tick loop must be running while anyone views the mini Overview.

## 6. Slice DEMO-B · `task/DEMO-B-captures` · 3 units · 1.25 builder-days (after DEMO-A merges)

- **B1 (0.5 d): the capture tool.** `tools/demo-combined-evidence.mjs`, a `.mjs` tool, so it selects no backend tests.
  It reads `<work>/story.json` for the URLs and captures at 1440 and 390 px:
  - Portfolio S;
  - Kobo Overview board S, default and all-open;
  - Kobo S+1;
  - ACT-048 verification page, with its cost check (CO-4, OUT-E L1);
  - GreenHarvest board on the failure event and on the normal event;
  - Depot board E;
  - estate Findings with lenses;
  - Maintenance preventive;
  - Work request overview.
- **B2 (0.5 d): capture and compare.** Capture, then compare against `frontend/mockups/v70` with
  `tools/measure-mock-panels.mjs --mock frontend/mockups/v70`. Every mismatch is a register row (R600+), or a defect
  for the polish round. No visible MOCK DEVIATION label.
- **B3 (0.25 d): runbook and packet.** `.agent/DEMO-B-packet.md` holds the runbook (prepare → serve → frontend →
  links, plus timings). `serve` is restarted the same way for the owner walkthrough (sequence step 2).

## 7. What cannot be met, and why

- **No story without fixture-pinned clocks.** Writing a past history at all needs the fixture-pinned ingestion and
  decision clocks (`test_decision_clock_override`, used by all three producers). No product path writes the past.
  The data is therefore registered simulation placed on a story calendar. It is never presented as live operation.
- **"On track" is not guaranteed.** If neither candidate meets its objective on a complete window, R585 stays standing
  with the measured values. We never lower a target to force it (status rule `outcomes/status.py:85`).
- **Kobo repeat-visit warning.** It cannot fire: F-104 is RESOLVED after VERIFIED, and the rule needs an open linked
  Finding (OUT-C §C.1). The Kobo visits show under Earlier only. The cold and EV repeat warnings do fire.
- **Open register rows that need reads that do not exist.** These stay open: R561 (running hours), R562 (reserve dwell),
  R565 (connector rating), R566 (fault date), R551 (restart reading) and R546 (warranty).
- **Rows that stay as the data says.** R563 (EV peak at 60 of 80 kW; tuning a scenario to trip the warning would be a
  forced state), R547 (mock numbers), R582 (MG-1 sales "Not checked yet") and R583 (EV cost per km not measured).
- **The mock's IDs.** "F-104" and "ACT-048" are the mock's illustrative codes. Screens show the codes the product
  allocates (R550 standing).
- **Not part of this dataset.** The 91-day histories and the four reference Sites (DD-05a..DD-13) are unbuilt. This
  dataset uses hours-long windows.
- **Dates move.** Fixed calendar dates are impossible: the 30-day rule would expire them. Every rebuild moves the demo
  dates, and the demo script must quote dates from `links`.

## 8. Prepared example data and on-screen labels

| Data | Kind | On screen |
|---|---|---|
| Kobo, GreenHarvest and Depot readings, Findings, verification windows | Registered Lab runs (`REGISTERED_SIMULATION`) on the story calendar | Source chip "Generated test data" (`frontend/src/sites/sourceProvenance.tsx:95-98`); verification "Registered Lab trial data" (`verificationWords.ts:212`) |
| MG-2 cost check | Modelled from the trial hours and diesel price v1 | "not realised savings" (R591); the intervention cost is "no direct cost declared" |
| Objectives | Declared fixture | Their `source_note` "Declared for the demonstration; not a customer target" |
| Visits, incidents, plans | Prepared example data by `service:w401-fixture` | The actor on the record; no per-record marker today (owner decision 3) |
| Fallback (decision 1 only): s602b `verified` authored windows | `AUTHORED_DEMONSTRATION` | "Prepared example data" / "Authored test data (test-scoped example)" |

## 9. Decisions for the owner

1. **The cost check on the registered trial.**
   - *Situation.* If the probe (U1) shows the registered reserve trial gives "no modelled improvement" or "not
     calculated", there are two choices.
   - *(a), the Architect's recommendation.* Show that honest result.
   - *(b)* Switch Kobo's trial to the authored s602b `verified` windows (generator 40 → 28 kWh). Those are labelled
     "Prepared example data" on screen.
2. **Short windows now, long histories later.** The dataset uses the existing hours-long windows now. The 91-day
   reference histories (DD-13) replace it later. Confirm, or wait for DD-13 (about 18 builder-days of DD work first).
3. **A "demonstration data" banner?** Work records (visits, plans, incidents) carry no example marker on screen. Is a
   one-line app-wide "Demonstration data" banner wanted for the client demo? It is not in the mock: a new register row,
   about 0.25 d, in the polish round.

## Addendum 1 (2026-10-31): U1 probe rulings (probe: `AssetOpsV1-demo3/.agent/DEMO-A-probe.md`)

Supersedes §2's "price v1 published before evaluation" row, §1 Q1's install-order bullet and §3 U3/U5 where they
conflict. Probe results that stand: freshness CURRENT, Finding index CURRENT, no revision or withdrawal from the ticks,
shifted `_draft` accepted, total wall 246 s (so the U2 cap is 500 s), and the (g) cold cause fixed on main by OUT-C U2.

**R1. Cost check: option 2, a test-seam recorded clock on the assumption store. Options 1 and 3 are refused.**
- *Why not 1.* Evaluating at build time T would record RESOLVED days after the trial with no cause. It would also
  price the trial with a price learned after it. A real customer's history never reads like that.
- *Why not 3.* "Not calculated" is honest but it is not the true history. The price really is known before the trial:
  a customer declares the diesel price at onboarding.
- *Why 2 is the established pattern, not a new kind of thing.* `PostgresEvidenceLedger(url,
  test_decision_clock_override=...)` (`evidence/adapters/postgres_evidence_ledger.py:141-146`, `:526-527`) is already
  how every producer places a past history.
- **Seam.**
  - `PostgresAssumptionStore(url, *, test_recorded_clock_override: Callable[[], datetime] | None = None)`.
  - When set, the one publication instant `at` (`financials/adapters/postgres_assumption_store.py:131`) comes from
    the override instead of `clock_timestamp()`.
  - `RECORDED_TIME_NOT_LATER` (`:132-137`) and every other check is unchanged. No money rule changes.
- **Never wired.** `financials/composition.py:39,43,58,72,148` and `main.py` construct the store without it.
- **Tests.**
  - A new test asserts (by AST) that no module under `assetops_backend/` passes the keyword.
  - A Postgres test: with the override at instant X, the publication's `recorded_from == X`; `snapshot(known_at=X−1s)`
    is empty and `snapshot(known_at=X)` selects it.
  - Without the override, behaviour is byte-identical.
- **Story instant.** The demo publishes price v1 through `publish_assumption.main([... "--step","v1"],
  store=PostgresAssumptionStore(url, test_recorded_clock_override=...))` at **Kobo install + 1 h**: onboarding, always
  before S. The valid time stays 2026-10-01 from the fixture.
- **Placement.** It is product adapter code, so it goes in its own slice: **DEMO-A0 · `task/DEMO-A0-assumption-clock-seam`
  · 1 unit · 0.5 d**. It gets its own review, scoped tests (`test_s402*`, `test_s408*`, `test_out_e3*`, `test_out_e4*`
  and the new tests) and `check-all`. Its full suite is folded into DEMO-A's `-Tier all`, which must run on a tree
  containing both. DEMO-A U3 resumes after A0 merges.
- **Owner.** This needs no decision. The owner has already accepted pinned fixture clocks for evidence; this applies
  the same rule to one money record. *Their veto:* the price's recorded time will read as onboarding, not build day,
  wherever recorded times show (the assumption history page).
- **Decision 1 is narrowed.** The fix gives a calculated check. Decision 1 now asks only what to show if that check is
  MODELLED_NO_IMPROVEMENT. Recommendation unchanged: show it. Option (b), the authored windows, needs this same seam
  and is no longer a fix for the price.

**R2. (e) CO-1 is a gap in the re-time. It does not wait on objectives.**
- *Why objectives cannot explain it.* Objectives change a row's state only (`outcomes/status.py:73-90`). They never
  add items, `must_not_harm`, or link resolution. The suffix means that ACT-048's linked Finding ID is not in
  `facts.findings` (`site_outcomes/board.py:265-275`). Yet the probe's index read for S returned F-104.
- **U3 diagnoses before U6.** 0.25 d, results recorded in the probe file:
  1. Call the board's own `finding_index` port (`site_outcomes/read.py:229-234`) over `[work_lo, end)`; does it hold
     F-104's `finding_id`?
  2. Does ACT-048's link (`origin` / selected revision) name that same `finding_id`, or the recommendation's or
     another revision's ID?
  3. Does `_findings` (`site_outcomes/mini.py:~430-447`) drop the row, for example on a missing estate row or on
     lifecycle?
  4. Why does the Action land on Protect and not Cost? Is it the reserve Action's map entry (`outcomes/outcome_map.py`)?
- **Stop rule.** If the cause is a board rule acting as designed (for example a RESOLVED Finding is not an item, or a
  reserve change maps to Protect), stop and report. The owner's ruling "do not change the board rules" (2026-10-30)
  then makes the remedy a choice of story stage, which is an owner decision. The alternative would be a second,
  unverified Kobo trial on S that shows the issue and Must-not-harm, beside the verified one on S−3.
- **If it is a data or ID mismatch,** fix it in the producer.

**R3. Install clocks: install each Site before its earliest dated row. Work rows never predate their Site's import.**
- A real Site exists in the system before any record about it.
- **Install instants.**
  - Kobo stays at its fixed 2026-10-07 11:00. Its earliest row is S−20 d ≥ 2026-10-09 whenever S ≥ 10-29, so the rule
    holds.
  - GreenHarvest: `S − 26 d 06:00`.
  - Depot: `S − 26 d 06:30`. Set the EV module's `INSTALL_AT`/`SETUP_AT` to that instant and +1 h; the E-window
    constants keep the whole-day shift. `ATTEST_FROM/TO` must still cover E.
- **Order.** §1's "Kobo → cold → EV strictly increasing" becomes: the orchestrator installs **in increasing install
  instant**, whichever Site that is. The instants must be distinct, and each must be ≥ 1 h before that Site's earliest
  row; otherwise `INSTALL_CLOCK_CONFLICT`. Objectives are declared after the last install.
- **U5 pre-flight.** The probe's three EV checks (h1-h3) stand:
  - the `window=` keyword;
  - the scenario document shifted in memory (`runs/service.py:562-571`);
  - `Chain.open`'s hard-coded `now` (~`test_w205b_ev_replay_postgres.py:261`). If that one can only be changed by
    editing the test module, U5's stop rule applies; it goes to the Architect, not the owner.

**Effect.** DEMO-A0 is new (0.5 d). U3 grows by 0.25 d (R2). Total 7.0 builder-days. The sheet now runs past its
400-line budget by this addendum only.
