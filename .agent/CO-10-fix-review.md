# CO-10 D-SR.81 review: ACCEPT WITH NOTES

Reviewer: fresh Claude reviewer, 2026-11-13. Diff `git diff 31984dbfa 45661fc1b` (branch fix/CO-10-ev-c1-status), ruling D-SR.81 (build-sheet-OWN-GAPS-2026-11-08.md), packet .agent/CO-10-fix-packet.md.

## Ruling conformance
- `CATEGORY` (ev_availability.py:28-32) is exactly the ruled map: AVAILABLE/UNPLUGGED/PLUGGED/AUTHORIZING/CHARGING -> AVAILABLE; FAULTED/DISABLED -> UNAVAILABLE; anything else falls to UNKNOWN via the unchanged lookup. Comment cites D-SR.81. No fourth category.
- `CALCULATION_VERSION` and module docstring bumped to `ev-availability/2`; `evDepthClient.ts:79,284` accept exactly `/2`; `EvAvailability.tsx:5` comment and `evDepth.test.tsx:90` updated.
- Version consumers: `grep -rI "ev-availability/1"` over the whole worktree (incl. ignored files, tools/, host/, frontend, contracts; excluding node_modules, .git, .agent history) returns nothing. No tools/demo_combined*.py row, fixture or prebuild/stored-route key names the version; stored routes key on code_version (auto-invalidated, per ruling).
- Must-not-change list: `REPORTED_STATES`, `status_spans`, grading, pb3/out_b3/out_c4_mini/out_c_rules/data4 tests, config, tools/ (incl. CO-10 row at demo_combined_finish.py:422-431) untouched in the diff.
- Changed assertions (test_w503 pure test) recomputed by hand: available 120+60=180, unavailable 60, unknown 3600-240, six spans with 08:30-08:31 AVAILABLE, known_time_ratio 180/240=0.750000, bounds 180/7200 and (180+3360+3600)/7200. Correct consequences, not weakened (the `full_lower` literal became `ratio(180, 7200)`, equivalent).
- evhb test 156-158 keeps the per-state check and adds a full seven-value map equality plus `set(CATEGORY) == set(EV_CONNECTOR_STATES)`; good.
- Client copy: "N of connector status is missing" (site_outcomes/ev.py:226-235) and the "unknown" part of CONNECTOR_OUT_OF_SERVICE (ev.py:440) derive from `unknown_seconds`, which now counts only gaps/unusable time, so they read truthfully. Availability page Unknown card note "No trustworthy state coverage" and the telemetry sentence stay true. Demo-script note added as ruled.
- Other self-check rows: no CO-*/EV/DATA-4 row reads `unknown_seconds` or the version except CO-10 (now passes as written per ruling) and CO-9 (asserts Assure/evidence state != UNKNOWN; more known time cannot push it toward UNKNOWN). DATA-4 uses scheduled_seconds and kWh. Value changes confined to the ruled client-visible effect.

## Findings
- Low (test strength), backend/tests/test_evhb_ev_window.py:169-182: the CO-10 shape test covers 08:00-08:17 (one FAULTED minute) rather than the ruled 08:00-08:16 Available / 08:16-16:00 Unavailable day, asserts totals rather than the 08:16 boundary, and classifies spans via `CATEGORY.get` by hand instead of through the calculation body that produces `unknown_seconds`. It still fails under the old map (16 min Unknown), so it is meaningful; optional tightening: assert the span boundary at 08:16 and/or call the calculation entry point.
- Low (process), branch name `fix/CO-10-ev-c1-status` differs from the ruled `task/CO-10-availability-mapping`; no effect.

## Checks run (reviewer)
- pytest (PYTHONPATH = this worktree, no DB URL): test_evhb_ev_window, test_w503_ev_availability_postgres, test_pb3_ev_status_grading, test_out_b3_cold_ev, test_out_c4_mini_ev, test_out_c_rules, test_data4_charger_use, host/tests/test_evhb_generated_days -> 99 passed, 7 skipped (Postgres), 0 failed, 2.8 s.
- vitest src/sites/__tests__/evDepth.test.tsx -> 17/17 passed (no separate EvAvailability test file exists). `tsc --noEmit` -> exit 0.

## Not verified (pending, coordinator)
- Postgres: persisted tests in test_w503_ev_availability_postgres.py (chain-based; assertions are inequalities/subsets, gap test asserts AVAILABLE neighbours, expected stable), test_out_c4_ev_warnings_postgres, test_w207/test_w503_ev_depth Postgres files. The packet's "1 failed" for test_out_c4_ev_warnings_postgres is a missing-DB-URL error, not a run.
- check-all; walk1113 prebuild/warm/self-check 54/54 and parity per the ruling's deploy steps.
