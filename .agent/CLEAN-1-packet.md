# CLEAN-1 packet (lane A, branch task/CLEAN-1, from main f4850ee2c)

Task: cleanup card (revision 3 table row 5 plus gathered items). No product behaviour change except item 4's header.

## Delivered
1. `work/open_now.py:19` spacing `EARLIEST = datetime(...)` (one-line `sed -i`, a lane-rule slip, mechanical only).
2. DISP-1 Low: `test_disp1_money_eligibility_select_days.py::test_absent_run_in_the_bracket_equals_compose_and_kill_switch_equals_compose`
   (no DB, stub `basis_historical=True` snapshot, 2-day bracket: stored D + ABSENT_MARK D+1 via `coverage.dispatch_days`
   equals the `select_days=None` result; provider returning None equals it too).
3. FIX-AR3 Lows: `test_ar3_dispatch_day_rows.py::test_coverage_stored_pending_day_beside_an_absent_run` (stored dirty
   D2 + absent D3: one compose, PENDING_RECOMPUTE, days equal the compose oracle); `absent_day` docstring now says it is
   the compose-returned-nothing fallback; `period_read.absent_count` docstring states per-run units for dispatch.day.
   (The fix-ar3-parity.json no-revision Low is not changed: a recorded artifact.)
4. UQ-6a: `i18n/locale.py` `LocaleMiddleware` answers an unhandled exception (before response start) with Starlette's own
   500 body plus `Content-Language`, then re-raises (still logged). Test `test_uq6a_message_seam.py::test_an_unhandled_500_carries_content_language`;
   proven non-vacuous (fails with main's locale.py).
5. `test_ch5c2_real_composers_postgres.py` rerun (one file, `tools/run-host-tests.ps1`, default `assetops_test`):
   first run 5 passed / 1 failed (`test_f4_no_unlisted_read_over_every_stored_route`): 5 compose-path modules were missing
   from `config/chain/stored-composer-modules-v1.json` (`chain.dispatch_day_rows`, `chain.period_read`, `estate.period_rows`,
   `mini_depth.period_rows`, `work.open_now`, from AR-3/AR-4). Not connection exhaustion. Listed them; the clock guard then
   flagged `PeriodReader.__init__` default `datetime.now` (`period_read.py:373`), allow-listed in `test_ch5c2_clock_guard.py`
   with reason. Rerun: 6 passed in 145.5 s. Clock guard file: 8 passed.
6. F05 check: skipped (backlog per D-F05.1).

## Checks
- Targeted: disp1 + ar3 + uq6a + clock guard all pass (no-DB).
- check-all (revision 232d2f020): All 19 guards passed (estate guard self-tests 16 passed in 21m50s).

## Known deviations / risk
- The PY clock allowance for `PeriodReader.__init__` is my call; Architect to confirm (default only when `known_at` is None).
- Module list entries are guard registry only.
- Review focus: the middleware catch-and-reraise (a 500 is now sent from inside the middleware; the re-raise lets Starlette's
  outer handler find `response_started` and not send twice).
