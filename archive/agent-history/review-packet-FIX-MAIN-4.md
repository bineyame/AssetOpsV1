# FIX-MAIN-4 review packet
All three were stale tests after intended CH-6b1 product changes (7cc440771, 287e5ff6b); no product change.

| Failure | Cause commit | Fix (test only) | Result |
|---|---|---|---|
| test_ch6_claims::test_templates_are_the_a4_table | 7cc440771 added 4 income.* node templates | A4 table extended with the 4 income.* entries (exact text pinned) | pass |
| test_out_b1_board::test_board_imports_only_outcomes_and_stdlib | 287e5ff6b board.py imports stdlib `datetime.date` | `datetime` added to stdlib allow-list; outcomes/chain restrictions unchanged | pass |
| test_walk1_productive_sales (5 tests) | CH-6b1 `_month_reading` now returns (Reading, GradeCounts, window) | helper unpacks 3 values; assertions untouched | 5 pass |

Run: 60 passed (3 files); walk1 productive price/producer postgres via run-host-tests: 4 passed.
