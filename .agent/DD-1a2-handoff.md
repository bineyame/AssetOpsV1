# DD-1a2 handoff

## UPDATE after DD1a2-R2 (commit `281a2bd54` and later)
- G1 regenerated (`.agent/DD-1a2-g1.json`): `steady-before` 10-24 generator 04:00-06:00, 3.167 kWh exact, litres 0.973 (registered probe `B-early`, G0 test asserts it equals the committed handover); NECESSARY, window COMPLETE, 0 Findings; clinic requested = delivered on every reading with both values (288 a day; 2 per day have a missing value, none in 04-06); residential records no requested power. Recorded as a FAIL on "0 L", accepted by R2.
- v3 weekday L0 added (`test_demo_story_days.py`, 7 values of S). R25 probe `host/tests/test_dd1a2_r25_probe.py` PASSES (25 % reserve: steady-day STOPPED 18:00 and 24:00, 0 starts, night-early no generator, ends 31.16 %; non-vacuity assert on B-early passed).
- DONE after that: G2 PASS (VERIFIED 42 to 110 kWh), MONEY-A not vacuous and equal, add-day L2 (S-10 fill), scoped tests and guards A W N V M pass, packet `.agent/review-packet-DD-1a2.md` written. Remaining for the coordinator: task status/ACTIVE_CONTEXT/CODE_STATE, plan HTML text, R2 owner line. DBs dropped.
- (superseded) Next: G2 `mill3` (own DB `assetops_dd1a2a_test`, output `m3work/mill3.json` in scratch), then `story-only`, MONEY-A, add-day L2 (fill S-10 on the mill3 DB), stream probe, scoped tests, guards, packet.

## (older) State: STOPPED at G1 (`DD1a2-R` Q1, sheet `:751-752`). The Architect rules. No value changed.
Size 2.25. R25 probe, G2 (MILL-3), the L2 add-day test and the packet are NOT done: they follow G1 in the ruling's order. Nothing past the stop was run.

## The G1 result (registered KOBO-001, own `*_test` DB, one day of each profile; raw: `.agent/DD-1a2-g1.json`)

| Check | `steady-before-first` (10-23, S-13) | `steady-before` (10-24, S-12) | `steady` (10-28, S-8) |
|---|---|---|---|
| Runs | night-early, steady-before-mill, rest-before-mill | night-early-after-before-mill, steady-before-mill, rest-before-mill | night-early, steady-day, rest-mill |
| Generator (local) | 05:05-06:00 | **04:00-06:00** | 05:05-06:00 |
| Interval class | NECESSARY, window 1 / 0 / 0 | NECESSARY, window 1 / 0 / 0 | NECESSARY, window 1 / 0 / 0 |
| Starts 06:00-20:00 | 0 | 0 | 0 |
| Generator energy in evidence | 0 kWh | **3.167 kWh** | 0 kWh |
| Fuel (registered probe) | 0 L (`S-early`) | **0.973 L (`B-early`)** | 0 L (`S-early`) |
| Findings | 0 | 0 | 0 |
| `productive_kwh`, grade | 42.000, COMPLETE | 42.000, COMPLETE | 110.000, COMPLETE |
| **G1** | pass, money not measured | **FAIL on "0 L"** | pass, money not measured |

**Why it fails.** A `before` day ends at 45.26 % (86.32 % at 18:00), not 48.42 %, 3.16 pp lower. The states are measured; the likely reason is read from the windows only: its afternoon mill is 18 and 3 kW against the "after" pattern's 12 and 0 kW, so it draws 18 kWh more after the sun falls. From 45.26 % the night reaches 35 % at 04:00 and the 30 % reserve before 06:00, so the generator delivers energy. The pass line says 0 L. **7 days carry it:** S-19 to S-15, S-12, S-11, about 6.8 L in all by the per-day figure (not measured as a sum). The 06:00 start returns the tank to 300 L, so no chart shows it accumulating.

**Not measured: money.** `financial_consequence_revision` holds 0 rows on G1, but also 0 rows on the control build, which has 2 Findings. This path does not run the money worker, so "no money change" is unproven, not passed. The Finding check IS non-vacuous: the control (`.agent/DD-1a2-g1-control.json`, S-14 and S-7 story-only) finds 2 CANDIDATE_AVOIDABLE Findings with the same query. That is a control for G1, not G2's comparison.

**The owner was told "about 0 litres"** (Question 1). 0.973 L a day on 7 days is small, and it still differs from that sentence and from the gate.

## For the Architect (facts, not a choice)
- **Accept about 1 L on the 7 days.** Already disclosed in the file's label, purpose and 04-06 source lines (`BEFORE_NIGHT_DISCLOSURE`). No file changes. The owner line needs correcting.
- **`steady-before-first` on every before day (fresh 48 % night).** 0 L, but a 00:00 step of 2.74 pp against R15's 0.5 pp, so `FULL_DAY_JOIN_BOUND` refuses it. It needs a ruling on the bound; a value reads as chosen. The kinds exist; only the list changes.
- **Branch B** ("not judged yet"), the ruling's stated route if a before day cannot be full. Owner decision.
- G0 passed, so this is the G1 line only. No RUNNING join is involved.

## Done (commits on the branch)
- `6a75592d2`, `4f41af404` (previous builder): Q7, Q8.4, Q4, Q6.
- `5a5211639`: `kobo-steady-before-mill`, `kobo-rest-before-mill`, `kobo-night-early-after-before-mill` (generated, in `--check`); `kobo-steady-day` un-held; disclosure on the three 06:00 start files (comment-only on `kobo-mill-midday`); `backend/conversions/demo-story-days-v3.json` per the table with `mill_change_day` and EV `S-14d`; `DEFAULT_FILE` = v3; `MILL_PROFILE_WRONG_SIDE`; `check_full_day_chains`; `plan_add_runs`; add-day delivers the runs; a `missing` day is fillable; `delivered_days` is Site-local.
- `3bd1893e8`: L0 on all of those.
- This commit: `tools/dd1a2_mill3_dry_run.py` fuel field replaced (no fuel signal reaches evidence; the first version reported a vacuous 0), G1 evidence, this handoff.

**G0: PASS on the registered Site** (`host/tests/test_dd1a2_registered_kobo.py`). `kobo-steady-day` 89.47 % at 18:00, 48.42 % at 24:00, STOPPED both (0.42 pp from `kobo-night-early`'s 48). `kobo-steady-before-mill` 86.32 %, then 45.26 %, STOPPED both. 0 starts 06:00-20:00. Registered equals the committed handover.

## Next, once ruled
1. Apply the ruling. Add G1 to `host/tests/test_dd1a2_registered_kobo.py` (`tools/dd1a2_mill3_dry_run.py g1` holds the report). If money must be measured, say which worker the gate means.
2. R25 probe on the Foundation with the 25 % reserve; L2 `add-day steady` end to end (`plan_add_runs`, `demo_combined.add_day`, `demo_combined_kobo.add_day` are built, none yet run end to end; the Site-local `delivered_days` query and the fill of a `missing` entry are untested against a DB).
3. G2: `tools/dd1a2_mill3_dry_run.py mill3 <work>` then `story-only` (keep-awake first, 40 min cap); write `.agent/DD-1a2-mill3-dry-run.json`. `mill3()` is unrun; R12's MG-5 and MG-4 guardrail days are not yet in its output.
4. Packet `.agent/review-packet-DD-1a2.md`, task status, `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md`. Replacement text for `client-demo-plan.html:781-782` is at sheet `:834-835`, for the coordinator.
5. After the v3 change `test_demo_combined_postgres.py:198` (`sd.load()`) reads v3; it is barred here and unchecked.

**Anchors**: `tools/demo_story_days.py` `check_mill_side`, `check_full_day_chains`, `plan_add_runs`; `tools/derive_steady_scenarios.py` `BEFORE_MILL`, `BEFORE_NIGHT_DISCLOSURE`, `RESET_NIGHTS`; `tools/probe_kobo_nights.py` `day_chains`, `FULL_DAY`, `full_days`.

**How to run**
- PYTHONPATH absolute Windows paths (`backend;contracts;tools;simulator;gateway;host;field;backend\tests;host\tests`). `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_dd1a2_test`, created and dropped around each run.
- G1 took 377 s (9 runs, 258 mini-depth jobs).

**Checks at this commit**: see the commit message and the final report. DBs and processes alive: none.
