# 0K4e packet: `dispatch-3.3`, energy to solar cover

Branch `task/0K4e-candidate-energy` (worktree `/opt/assetecon/AssetOpsV1-0k4e`), base `main` `b96d5e978`. Spec rev 2,
rulings D-0K4.10, .11, .19, .23-.25. Builder: Claude, 2026-11-21. `USER_REVIEW_REQUIRED: true` (served candidate
litres and Findings move). Evidence: `/opt/assetecon/evidence/0K4e/`.

## Pre-flight

All R1-R5 and I1-I6 have answers (handshake.md, handshake-I.md, D-0K4.23-24). None were open before coding.

**1. W6 sweep (`git grep -n "dispatch-3\.2"` over backend/, frontend/src/, tools/)**

| Hit | Class | Action |
|---|---|---|
| `dispatch_v3.py` 1, 42, 515 (`MODEL_VERSION`, docstrings) | pins a version / prose | 3.3; version paragraph added |
| `claim_limit_read.py:39` `SUPPORTED_MODELS` | pins a version | `("dispatch-3.2", "dispatch-3.3")` |
| `claim_limit_read.py` 47, 55, 103; `stored_declaration.py` 10, 45, 139; `plain.py:40` | prose (the reader serves both) | "dispatch-3.2/3.3" |
| `stored_declaration.py:143` (through `SUPPORTED_MODELS`) | pins a version | follows the constant |
| `rows_mini_grid.py` 62, 65, 67 | pins a version (D-0K4.23 I6(c)) | 3.3; 67 is the one fingerprint swap |
| `structure/litres/inputs.py:5`, `rules.py` 5, 24, 50; `structure/sources.py` 48-49 | prose | the selected model, 3.3, or "3.2/3.3 strings" |
| `runs/replay_study.py:540` (6c study) | history | left |
| `tests/test_s3_dispatch_v3_analytic.py` 321-327 | pins a version | 3.3; 3.2 joins the refused versions |
| `tests/test_s3_claim_limit_vocabulary.py:14` | pins a version | 3.3 (3.3 adds no problem text) |
| `tests/test_s3_claim_limit_postgres.py:299` (`Broken` model) | pins a version (it stands for the live model) | 3.3 |
| `tests/test_s3_dispatch_read_postgres.py:212` | prose | "now `dispatch-3.3`" |
| `tests/test_s3_performance_cutover.py:166` (`model="dispatch-3.2"`: an other-model case) | history (still not the live model) | left |
| `tests/fixtures/*.json`, `test_ar3_dispatch_day_rows.py:48`, `test_s5_overview_read.py:86` | stored fixtures | left |
| `test_4d_litre_split.py:440`, `test_ap1_stored_declaration*.py` 4-5, 170, `test_lr01_money_eligibility_postgres.py:6` | history / prose of a passing test | left |
| `frontend/.../evidenceClaimLimit.test.tsx` 177, 184; `ap1StoredAnalytics.test.tsx:108` | stored fixtures (served strings) | left |
| `backend/tests/test_5c_deep_dive_view.py::test_4_h_kobo_litres` (named pin; on `task/5c-deep-dive-screen` only, not on `main`) | the 5c view's stub litre leaves (4d's KOBO-OCT test inputs; `test_4d_litre_split.py` is untouched by 0K4e) | **no literal change needed for 5c** (330 L, -$412.50, 730 L, -$37.50 stay) |

The sweep found no pin outside the spec's list.

**2. How the consumers select dispatch runs.** All three follow the default selection, and none uses a literal.
- `finding_service.py:52` uses `run_id = (r.get("selection") or {}).get("run_id")` from `self.read.window(...)`, then `plan_pass(..., self.model.MODEL_VERSION)` (:68).
- `structure/litres/inputs.py:126-129` uses `self._assessments.dispatch_spans(...)`, which is `select_dispatch_days_on` (`postgres_assessment_store.py:1064`). `day_state` analyses only a CURRENT selection.
- `financials/money_eligibility.py:225` uses `self.days.select_dispatch_days_on(c, ...)`, the S3 day selector, which fuel-cost-1 reads.

**3. 3.2 counts, labelled.** These cover the fixture's days, not 1-31 Oct. Database `assetops_ptf368bada5_main_test` (run-owned clone of `assetops_test`, dropped by the harness). The days are 10-06, 08, 09, 11, 13, 15, 19, 21, 23 and 24, using each S4 case's first delivery plus the planted night. On 3.2 there are **102 Candidate segments and 510 Candidate minutes**.

## What changed (spec §2)

- `dispatch_v3.py` (row 5b only):
  - `_battery_support` adds the energy test.
  - `_Index.energy_to_cover(t)` is the memoised per-slot recurrence (one argument). `held_value` is the interval fallback, with `interval_start < s <= interval_end`.
  - `cover_entry`, `Point.cover`, `Segment.covers` and `payload()` add `energy_cover` only when it is non-empty.
  - `_control_changes` takes both new keys.
  - `cover_message` maps an entry to `dispatch.energy_cover`.
- Nothing is added to `reasons` or `missing`. A Candidate keeps 3.2's reason byte for byte.
- `assessment_inputs.py`: two constants. `postgres_assessment_store._configuration` reads `battery-energy-capacity` and `pcs-conversion-efficiency`.
- `i18n/statements/en/dispatch.py` holds the two statements. `vocabulary.py` gains `dispatch_input` and `reading_problem`. `statement_cases/dispatch.py` has 7 hand-literal cases.
- `plain._segment` renders the lead entry. `finding_read.portion_cause(missing, cover=())` maps GAP or NOT_CONFIGURED to RECORD_GAP, and SHORT or NOT_REACHED to the cause fragment. Each portion carries `energy_cover`.
- The decision table gains a 3.2 row (historical) and a 3.3 row (current), plus a section, "Energy to solar cover".

**E1-E3 in words.**
- **E1:** the battery has 95 kWh above reserve (0.5 x 200 x 0.95). PV first covers the 10 kW load at 06:00, and 144 slots from 18:00 at 10 kW x 5/60 h need 120 kWh. 95 kWh is less than 132, so the result is Indeterminate `SHORT`.
- **E2:** at SOC 100 the battery holds 133 kWh, and 133 >= 132, so the result is Candidate `COVERED`, with 3.2's reason and margin.
- **E3:** at load 9.5 the need is 114 kWh. At SOC 96 the battery holds 125.4 kWh, exactly 1.1 x 114, so the result is Candidate. At SOC 95 it holds 123.5 kWh, so the result is Indeterminate.

**Fingerprint swap (D-0K4.19 item 5).** `rows_mini_grid.py:67`, `g:<module>:3349d495df46` became `g:<module>:0bae2f18559a`. The string diff is the token `3.2` to `3.3` only, and `git diff main -- tools/checks/` is that one line pair.

## Checks (real output)

| Check | Result |
|---|---|
| `pytest test_0k4e_energy_to_cover.py` (E1-E8b, E8) | 13 passed |
| `pytest test_0k4e_readers.py` (cases, E12-E14) | 18 passed |
| `test_s3_dispatch_v3_analytic.py` (E8) | 20 passed (version literals plus the four branch cases below) |
| Focused pure regression, rev `1440c39d2` (23 files, `-n 4`) | 323 passed, 2 failed; see Known deviations 4 |
| `test_0k4e_dispatch_33_postgres.py` (E9-E11), rev `8e9e4b5fb` | 1 passed in 16.96 s (`/opt/assetecon/evidence/0K4e/run4.log`, `run4/e9_e11.json`) |
| Postgres and consumer regression, rev `422384835` (21 files, `-n 4`, 103 s) | 289 passed, 2 failed (F05 in `test_s4_finding_store_postgres` and `test_s4_finding_read_postgres`: mid-build Q1) |
| F05 consumers after Q1's default, rev `422384835` + the F05 edit (12 files, `-n 4`, 210 s) | 85 passed, 1 xfailed, 5 errors: every md0 test is `TEMPLATE_STALE` (Known deviation 8) |
| `tools/checks/statement_catalogue.py` | `OK statement catalogue: load, coverage, legacy, scan (2 adopted), keys, imports` |
| check-all (fast), rev `8e9e4b5fb` | `All 42 guards passed (blocking; 0 advisory, 0 warned).` 175 s wall (32.2 s waiting for a slot) |
| `check-architecture.ps1`, `check-agent-workflow.ps1`, `check-decision-index.py` | `Architecture check passed.` / `Agent workflow check passed.` / `OK` |

**E8, the cases that reach row 5b.** Four cases reach it, each with PV 20 + PCS 20 kW against a 30 kW load: two_capability_candidate, minimum_runtime, inverted_span and capability_role_unbound. Their nights end at 06:15, so under 3.3 the walk meets a gap and each turns Indeterminate. Each now reads PV 40 kW (`PV_ALONE`, the PV-alone branch) and keeps testing its own rule. All their assertions are unchanged.

**E9 and E10, the model-change reconciliation (D-0K4.11).** Fixture days as above. These are not Kobo's October.

| | 3.2 | 3.3 |
|---|---|---|
| Candidate segments | 102 | 95 |
| Candidate minutes | 510 | 475 |
| Planted night, Candidate minutes (by hand: 60 then 25) | 60 | 25 |
| 4d split, planted day: `necessary_l` / `candidate_l` (L) | 207.000 / 9.000 | 212.250 / 3.750 |
| `assess()` time / calls | 0.046 s / 12 | 0.054 s / 26 |

- The 35 minutes that left Candidate are all from the planted night (SHORT). Before Q1's F05 edit, F05 also lost its 60 minutes: its readings stopped at 09:00, so the walk met a GAP at 09:10 (run 3 showed 83 segments and 415 minutes, `/opt/assetecon/evidence/0K4e/run3.log`).
- Total litres are unchanged at 216 L. The 3.2 runs and revisions keep the same md5 per row. Every head is 3.3.
- E11's reconcile enqueued exactly the 10 windows whose head was 3.2, and a second reconcile enqueued none.
- The claim-limit read answers for the 3.3 interval revision.

**Wall-time ratio.** Total `assess()` time is 1.17x (0.054 s against 0.046 s). Per call it is 0.54x (2.1 ms on 3.3 against 3.8 ms on 3.2). The 3.3 pass makes more calls because it reassesses every window. Either way it is below 2x, so it is not a mid-build question. E8b proves the bound: each (channel, asset, slot) is looked up once per assessment.

**Plants** (each applied, its test run, then reverted with `git checkout`):

| Plant | Result |
|---|---|
| P1 | E1 fails |
| P2 | E3 fails |
| P3 | E3 fails |
| P4 | E4 fails |
| P5 | E5 fails |
| P6 | E6 fails |
| P7 | E7 fails |
| P8 | E9 fails (Postgres) |
| P9 | E10 fails (the claim-limit read refuses 3.3) |
| P10 | E5b fails |
| P11 | E8b fails |
| P12 | E1 fails, and the statement guard reports `HAND_BUILT_NEW dispatch_v3.py:466 a:_battery_support:0fc4cb1d01da` |
| P13 | 6 of `test_0k4e_readers.py` fail |
| P14 | E13 fails |

## Known deviations

1. **E3's "one kWh less" is built as one SOC point less** (held 123.5 kWh, 1.9 kWh below the edge). At 95 % efficiency and 200 kWh, every held figure is (SOC - reserve) x 1.9 kWh, so a held figure exactly 1 kWh below the edge cannot be written as a decimal input. P2 and P3 still fail E3.
2. **E5's last quarter hour is three 5-minute means.** With 15-minute means aligned to the 18:00 point, the mean ending 06:00 also holds 05:50 and 05:55. The cover would then fall at 05:50, so E1's 120 kWh cannot come from 15-minute means alone. The rest of the night uses 15-minute means, and P5 fails E5.
3. **E10's litres cover the planted day only**, with a fixed 30 kW use and 0.3 L/kWh, through the real `month_litres` and the stored `dispatch_spans`. The CaseRunner world has no month of generator output or tank dips, so a real October figure would read `RUNNING_RECORD_GAP`.
4. **Pure regression: 2 failures, both from before this branch and not from 0K4e.** These are `test_w302_evidence_api.py::test_w302_evidence_authorized_scope_and_placeholders` ('Opens this range' against 'Current view') and `test_k7_kisiwa_story.py::test_8_add_day_kisiwa_options...` (`SystemExit` has no `error_code`).
   - w302 is a stale test on base `b96d5e978`. `main`'s `e9b9455ca` updates it to D-SR.73's view labels: it passes on `main` `e39a5d2fa` and fails on this branch alone (`/opt/assetecon/evidence/0K4e/main_two.log`, `branch_two.log`).
   - k7 `test_8` also fails on `main`. `ec8e64d3f` records it as environmental (it needs the heavy-slot pool).
   - Merging `main` brings w302's fix.
5. **The decision table had no 3.2 row**, because it stopped at 3.1. I added one in 3.1's words, marked historical.
6. **E9 reads the 3.2 phase before the deploy.** `dispatch_v3.MODEL_VERSION` is patched to 3.2 while 3.2 is assessed and read, as F07 does. Unpatched, the live 3.3 marks every 3.2 selection `STALE_PROJECTION` (asserted after the undo). The 3.2 model is the analytic at `b96d5e978`, loaded from git.
7. The branch name follows the dispatch (`task/0K4e-candidate-energy`), not spec §0 (`task/0K4e-dispatch-3-3`).

8. **`test_md0_mechanism_postgres.py`: not run.** It refuses with `TEMPLATE_STALE: template inputs a15afccd6b4c != this checkout 814cdbcd1767`. The rebuild (`tools/mechanism_dataset.py build --variant states --budget 540`) drops and prunes the shared `assetops_mechanism_*_test` templates that other lanes read, so it is left to the coordinator.

**Mid-build questions: 1, with its default applied (commit `8e9e4b5fb`, revertible on its own).**

**Q1.** F05 (`conversions/s4-finding-cases-v1.json`, "limitation-and-closure") is the only shared S4 fixture case that reaches row 5b: PV 29 + PCS 20 kW, SOC 50 %, reserve 20 %. Its readings stopped at 09:00, so under 3.3 the walk meets a gap and the case opens no Finding. That fails `test_s4_finding_store_postgres` and `test_s4_finding_read_postgres` (`('F05', [])`). The spec does not name this fixture.
- **Default applied:** F05's delivery goes on with load and PV to 09:45 (PV 29, then 40 kW from 09:35). The need is 19 slots x 1 kW x 5/60 h = 1.583 kWh against 57 kWh held, so the case still opens SUPPORTED. Its UNCONFIRMED step (runtime) and its NO_LONGER_SUPPORTED step (the reserve at 45 puts SOC 50 inside the 10-point headroom, a rule ahead of row 5b) are unchanged.
- **Ripple measured:** every F05 consumer passes, including the W3 estate goldens, the estate index, the SR5 range overview, the out-b4 board, S6 actions and the S4 power demo case.
- **Alternative:** the Architect rules F05 differently, and that commit is reverted.

## Downstream (spec §5, for the coordinator)

- 4d: `candidate_l` falls and `necessary_l` rises by the same litres.
- Findings re-derive on the next pass.
- A verification whose baseline days mix model versions refuses (`VERIFICATION_MODEL_NOT_COMPARABLE`) until the reconcile pass ends.
- After the reconcile, in-flight verification plans read their baseline as moved (it fails closed, and a new plan is needed). A new verification over stale 3.2 days refuses with `VERIFICATION_BASELINE_NOT_CURRENT`.
- Recency: a battery-support run whose post-run records have not arrived yet reads GAP, so its Finding opens late until a later delivery reassesses the window. A Finding-level case for this is queued as a backlog item.
- Residual risks (reviewer, round 1): the 6-hour read range decides evening points (an evening point is Candidate only if PV covers by 06:00 UTC, 09:00 at Kobo; otherwise `NOT_REACHED`); 15-minute cadence gives GAP at the second slot (the 15-minute fallback rescues interval means only); off-grid report times start their own slot grid, so memo sharing holds only for aligned times (cost stays bounded by points x slots).
- Readiness reads COVERED on an energy-cover Indeterminate (queued as Q10).
- No reassessment was run on any demo or walkthrough database. That is the coordinator's job.

## Review focus

- `_battery_support` and `energy_to_cover`'s backward fill.
- `held_value`'s fallback, only on MISSING.
- `plain._segment`'s guard: a legacy `missing` text wins.
- The four E8 fixture moves.
