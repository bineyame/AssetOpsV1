# Review packet: MD-0 Kobo-only mechanism dataset (phases 1-4)

- Branch `task/MD-0-mechanism`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-md0`. Authority: build sheet
  `AssetOpsV1-plan2\.agent\build-sheet-MD-0.md` §0-§16 (MD0-PF §14, MD0-S2 §15 Kobo only, MD0-S3 §16).
- Phase-4 commits: `22306be29` template, clone/derive, refusal, L2m on clones, studies seam; `90a075835` tool loads
  the harness by path; `d8814817f` tag without bind parsing; `24be47728` late overrun shape, ASSET grades, R7; `a35bfbad7` late overrun R7;
  `a4f6b2e38` collect R8 domain sites. Not merged.
- USER_REVIEW_REQUIRED: the MD0-S2 Kobo-first scope and the per-gate (not per-merge) full build are flagged for
  owner confirmation (§15, §16). Material findings F2/F5 below go to the Architect.

## Outcome delivered

- `backend/conversions/mechanism-v1.json`: KOBO-001 inputs only, `full` (13 delivered days) and `states` (10) day
  sets, GAP-K7, overruns D4/D11/D14, ACT-K1, studies W1/W2, the noon spare-solar remap D12/D13.
- `backend/tests/mechanism_dataset.py`: stepped seed through the product writers; **input template** section
  (`TEMPLATE_DB`, `input_fingerprint`, `input_steps`, `tag_template`/`read_tag`/`check_tag`, `clone_template`,
  `derive_clone`, `drop_database`); `late_fill`, `grades`, `build_work`.
- `tools/mechanism_dataset.py`: `build --variant states|full [--budget 540] [--resume]`, `derive`, `status`, `drop`.
- L2m (`test_md0_mechanism_postgres.py`) never seeds: each test clones the template, derives, asserts, drops.

## Acceptance (MD0-S3 rulings)

| Ruling | Status | Evidence |
|---|---|---|
| Q1 template, inputs only, fingerprint tag | Done | `states` runs every step but `derive`; tag = DB comment `{schema, fingerprint, day_set, state}` written only after the last input step. Template has 0 `site_day_snapshot`, 0 `finding_thread` rows (queried). |
| Q1 clone + derive with branch code | Done | `clone_template` (`CREATE DATABASE … TEMPLATE`) then `seed_part([derive])` resumed from the tag state. |
| Q1 refusal on mismatch | Done, live | Pure L0 `test_check_tag_refuses_missing_and_stale`; Postgres `test_template_clone_refuses_untagged_and_stale_then_clones_a_current_one`; and live: after a harness edit the L2m setup raised `TEMPLATE_STALE: template inputs 8518c697410d != this checkout 99e30217a471`, then the template was rebuilt. |
| Q1 each pytest call < 600 s | Done | L0+L2m file run 211 s wall. |
| Q2 D-AW-3 unchanged, record kept | Done | See record below. |
| Q3 revert worker change; seam in harness | Done | `KoboSite.studies` passes `test_lease_clock=lambda: _db_now(engine)` to the opportunity worker only; no product file changed. |
| Q4 ACT-K1 25 vs 20 traced | Done | See below. Action value is `proposal["proposed_value"]` from the product recommendation; nothing chosen. |
| Q5 unbound requested-power | Done | Demo does not bind them; kept dropped. See below. |

## Timings (measured, this machine, 2026-11-04)

| Step | Time |
|---|---|
| Template build `states`, part 1 (create+migrate 5.5 s, begin..D14) | 488 s wall, exit 3 (resume) |
| Template build part 2 (`studies` 8.0 s + tag) | 14 s wall |
| Template seed total | 484.6 s (begin 0.3, D1 33.2, D2 36.3, D3 35.2, D4 38.3, D5 47.9, D10 41.9, D11 72.9, D12 58.5, D13 62.1, D14 50.0, studies 8.0) |
| An earlier identical build fit one part | 456.4 s seed (tag write then failed on bind parsing; fixed, `--resume` tagged it) |
| Clone (`CREATE DATABASE … TEMPLATE`) | 0.4 s |
| Derive on clone (step 10) | 40.9-41.8 s |
| L2m per test setup (clone + derive) | 41-45 s |
| L0 + L2m file (`test_md0_fixture.py` + `test_md0_mechanism_postgres.py`) | 211 s wall: 29 passed, 3 xfailed |
| L3m collect (in process, 40 requests all 200) | 148 s |
| L3m check | 1 s |
| `full` build | **not run** (context budget). Estimate: states 484.6 s + D6/D8/D9 at about 35-40 s each + derive about 45 s = **about 650 s, two parts**. |

Sizes: template 103,797,219 bytes (21,126 readings, 133 batches); derived L3m DB 107,090,403 bytes
(`pg_database_size`). The L3m DB was dropped after check; the template `assetops_mechanism_tpl_test` is kept
(fingerprint `99e30217a471…`).

## L3m check (`derive` from the template, `check --threads … --expect expected-mechanism.json`)

- COH-10 threads: 0 findings, 0 expected, 0 new (R9 passes).
- **2 new findings, exit 1**: COH-7a KOBO-001 week (summary Site window `[10-31, 11-01)` vs requested
  `[10-25, 11-01)`) and month (`[11-02, 11-03)` vs `[10-03, 11-03)`). Not GAP-K7 nor R4, so per the file's rule
  they are not added to `expected-mechanism.json` (still `[]`). The same rule on Cold/EV in `expected-today.json`
  is owned by CH-6. Architect to route.
- Fixed in this phase: the collector asked the Cold/EV action index although the story is Kobo only (6 × COH-0
  404). It now requests only the story's domain Sites (`chain_coherence.py` `Collector.domain_sites`).

## Product records (R7, verbatim from the final run)

- **D-AW-3:** `run_lifecycle` → `{"skipped": 0, "skipped_causes": [], "counts": {"ACTION_IN_HAND": 1,
  "CHANGE_APPLIED": 1}}`, generator thread CHANGE_APPLIED effective 2026-10-30. The D14 recurrence joins the thread
  (step b `ADDED`) and is **silently dropped: no event, no skip entry**. Lifecycle not changed (CH-6b owns it).
- Step b `{ADDED 3, ALREADY_PLACED 5, NEW_THREAD 2}`, `skipped_ineligible 1` (W1 not placed); headroom thread
  **OPEN** effective 2026-10-30 (MD-0-F3 now holds).
- Studies: K-W1 reconcile queued 1; `run_pending` ran 3 jobs DONE (LIMITED, UNKNOWN, LIMITED; the DB-trigger jobs
  included). K-W2 queued 0 (already queued by the triggers). **Studies recorded at build time** (R4 build-time
  fact → DD-1b R7: a story-time `available_at` on the DB-trigger enqueues).
- **MD-0-F1** GAP-K7 before fill: avoidable_gen_min NO_DATA, productive_kwh NO_DATA, noon_headroom_kw **PENDING**.
- **MD-0-F2 (material)** every non-noon delivered day is NO_DATA on all three Kobo measures (covered_seconds 0);
  noon days D12/D13 are LOW (covered 3600 of 86400). Likely cause, not proven: the normal-day rows are delivered as
  5-min point samples (s4 `reading_rules` shape) while the chain measures count interval coverage only; the noon
  remap rows are w4 interval readings. The Kobo story grades in §2.6 ("fully checked") are therefore not met.
- **MD-0-F4** D7 after the normal late fill: still NO_DATA (same cause as F2); invariants hold (no new Finding,
  thread states unchanged, a new D7 snapshot revision after `k_before`).
- **MD-0-F5 (material)** the late D7 overrun (2,016 readings, real decision clock) produced **0 Findings**, so the
  "D4, D7, D11" story order cannot be shown. Not investigated further (budget).

## ACT-K1: 25 vs reserve 20 (Q4 trace)

- `reserve-trial-1` proposes exactly `r − 5` for a pinned reserve `r` in [15, 90] (`B/actions/reserve_trial.py:7,265`).
  25 ⇒ the D11 Finding pinned **30**, and apply succeeded, so the current reserve also equalled 30.
- 30 is the demo configuration's value: `config/site-templates/kobo-mini-grid-60kw.yaml:100-101`
  (`reserve-state-of-charge: 30`), and the demo itself applies 30 → 25 (`d-verification-window-v2/v3.json`).
- 20 comes only from the fixture control copied from `s4-finding-cases-v1.json` setup (effective 10-03, recorded at
  install + 40 min). It does not reach the D4/D11 Findings: the demo `configure_at` revisions are effective later
  (install 10-12 + 10..27 min). Inferred from the rule and the outcome; the revision ordering was not queried.
- So the demo configuration gives 30, the product recommends 25, and 25 is applied. The 20 control is inert;
  removing it or keeping it is an Architect call (left unchanged).

## Unbound requested-power (Q5)

- The demo binds only `clinic-meter/requested-power` (roles-3 `kobo-001-s6-verification-demo-config.json`; roles-4
  adds `battery-pcs-controller/charge-requested-power`). `residential-meter` and `mill-meter` requested-power are
  bound only in `mg-w402-001-minigrid-roles-4.json` (another Site). Kept dropped (`manifest.noon_dropped`).
- Effect on `productive_kwh`: **none**. It reads `feeder_demand` (delivered) readings only
  (`chain/measure_impls.py:131`, `mini_depth/read.py:384-393`). The drop affects only the mini-depth service rows'
  requested evidence for those two feeders.

## Known deviations

- Cold/EV removed (MD0-S2); their cases read "on the DD-1 build".
- Noon channels dropped (above). Studies at build time (above). D14 is the recurrence day (builder's choice;
  MD0-S2 names none). `close` variant refused (MD-0b).
- **Template content.** "Inputs only" is read as everything before step 10: readings, configuration, controls,
  prices/objective, Actions, and also the per-day story-time assessment/Finding/depth outputs and the studies,
  because ACT-K1 needs the D11 Finding at story time. Chain-derived rows (snapshots, threads) are not in it.
- **Fingerprint coverage.** As MD0-S3 lists: evidence, sites, actions, work (domain intent), objectives,
  migrations, `backend/conversions`, contracts, publish/declare entry points, `action_api.py`,
  `domain_work_api.py`, the seed modules (whole `mechanism_dataset.py`, s2/s4/s6 test modules,
  `s6_action_records.py`), `tools/demo_combined_kobo.py`, `demo_story_days.py`, `w402_mini_depth_cases.py`.
  **Not covered:** analytics (assessment, Finding matcher), `mini_depth`, `mini_decisions`, whose outputs sit in
  the template. A slice changing those gets main's per-day Findings from the template (risk below). Any edit to
  `mechanism_dataset.py`, test-only parts included, forces a rebuild (conservative).
- The setup_cache `seed_database` op remains registered but the L2m no longer uses it.
- L2m fails (does not skip) when the template is missing or stale, so a full suite needs the template built.
- Workflow closeout (task `Status: in_review`, `ACTIVE_CONTEXT.md`, `CODE_STATE.md`) not done in this phase.

## DS-R1

`noon_headroom_kw` keeps its one-noon-hour basis (`chain/measures.py:47`, "DS-R1 keep"); MD-0 changes no measure.

## Checks run

- L0 `test_md0_fixture.py` 27 passed; tool tests `tools/checks/test_chain_coherence.py` 88 passed.
- L2m final run above (29 passed, 3 xfailed, 0 skipped, 0 failed) at `a4f6b2e38`.
- Guards: `check-architecture.ps1` passed; `check-agent-workflow.ps1` passed.
- No full backend suite run in this phase.

## Residual risk / review focus

1. F2 and F5: the dataset does not yet reach the §2.6 "fully checked" grades or the late-overrun Finding.
2. Template staleness outside the fingerprint (analytics / mini_depth / mini_decisions).
3. COH-7a ×2 on Kobo windows, unowned in `expected-mechanism.json`.
4. The `full` build is unmeasured (estimate only).
