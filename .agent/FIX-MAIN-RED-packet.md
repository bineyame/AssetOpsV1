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
3. siteFoundationChange.test.tsx (FIXED). Cause: SR-1 (66a38d849) put the shared date-range button in the shell
   top bar; the "read-only, no button" check now excludes `[data-shared-range-button]` via `pageButtons()`. 18 passed
   (was 3 failed); tsc clean. Non-vacuity: the check still lists any other button's outerHTML.
4. test_ch5c2 `[listdir]` (NOT REPRODUCED). The test alone: 2 passed. Whole-file runs hit "too many clients" (shared
   Postgres sits ~110 of 200 connections from other work), so failures are environmental. Rerun when idle.

Scratch DB assetops_redfix_test dropped.
