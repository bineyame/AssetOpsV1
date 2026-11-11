# FIX-MAIN-RED packet

Branch `task/FIX-MAIN-RED` from main 626e3b94e.

1. test_ch9b1_origin_readers (FIXED). Cause: FX-COLD-LINKED (bcdf5389b, 1b0fdb61f) added two `a.origin_finding_id`
   reads in `site_outcomes/cold.py` over the Finding-only `domain_action_index` rows (linked-Finding resolution,
   start-action pick). Legitimate (class finding_fed, no opportunity origin), so the allowlist went 1 -> 3 with a
   justification comment. Guard not weakened. Proof: 9 passed (was 8 failed).
2. test_out_d5 estate (NOT FIXED, needs Architect ruling). Bisected on Postgres: passes at 502829266^1, fails at
   502829266 = merge task/DATA-12-coverage-local-days (D-E5.38; its packet says Postgres tests were not run). Coverage now
   counts Site-local graded days from stored chain day grades. The s602b `estate` fixture (tools/s602b_test_scoped_cases.py
   `estate_assertions`, 10-21 and 10-11 windows) stores no chain day grades, so each day is NO_READINGS, the Portfolio is
   PARTIAL, `withheld` True and F05 is withheld (0 rows). Windows cannot be shifted (INVALID_WINDOW unless UTC-aligned).
   Decision needed: (a) seed chain day grades in the estate fixture so F05 shows again (the placement/capture
   `data-portfolio-row` output depends on it), or (b) accept PARTIAL and rewrite the assertions (loses F05 placement).
   Follow-up (coordinator ruled (a), seed grades): NOT done, the premise does not hold for this fixture. The `estate`
   fixture deliberately has no readings: `test_out_b4_board_postgres.py` pins `S602B_CHAIN_DAY = {settled, readiness
   NONE, gaps 31}` and its line 542 comment says "estate 10-21 has no Finding rows while coverage is not current"
   (addendum 6, moved to the combined-dataset acceptance). Stored chain grades come only from readings
   (`performance_migration`, run AFTER `s602b.build`, where `estate_assertions` runs) plus backfill a-d and
   `chain_threads`. Making 10-11 and 10-21 COMPLETE means adding readings (changes the pinned readiness/gaps and board
   states on the same fixture) or hand-inserting chain rows and moving the assertions after the settle. Either changes
   what the fixture says. Needs a fixture-intent decision: readable on those two days, or (b) per addendum 6
   (PARTIAL, 0 rows).
   RESOLVED by coordinator ruling (b): `estate_assertions` in tools/s602b_test_scoped_cases.py now asserts, for 10-21 and
   10-11, status PARTIAL, exactly one NO_READINGS gap day, 0 rows, all-zero placement counts, plus the unchanged
   double-count / numeric-priority / one-page checks (comment cites D-E5.38 and addendum 6). Returns F05=None, rows={}.
   Proof (env var set, pg conns 123 < 150): test_out_d5_objectives_postgres 3 passed; test_out_b4_board_postgres
   5 passed, 1 xfailed (the existing strict BL-63 xfail), 0 skipped.
   Gaps for the Architect: (i) F05 placement is no longer asserted on this fixture; other Portfolio Finding-row
   placement coverage exists (grep: test_w303_selectors_postgres, test_w303_portfolio_scope_snapshot_postgres,
   test_s4_finding_index_postgres) but I did not verify they use a fixture with readings. (ii)
   tools/s602b-verification-evidence.mjs (lines ~292-301) captures the Portfolio F05 `data-portfolio-row` from the
   case file's `rows.F05`; it will find no row, so that capture needs the combined-dataset acceptance (not run).
3. siteFoundationChange.test.tsx (FIXED). Cause: SR-1 (66a38d849) put the shared date-range button in the shell
   top bar; the "read-only, no button" check now excludes `[data-shared-range-button]` via `pageButtons()`. 18 passed
   (was 3 failed); tsc clean. Non-vacuity: the check still lists any other button's outerHTML.
4. test_ch5c2 `[listdir]` (NOT REPRODUCED). The test alone: 2 passed. Whole-file runs hit "too many clients" (shared
   Postgres sits ~110 of 200 connections from other work), so failures are environmental. Rerun when idle.

Scratch DB assetops_redfix_test dropped.
