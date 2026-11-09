# C3 packet: two-tier board gap line (D-E4.6)

- `site_outcomes/mini.py` `finding_gap_line`: a gap day holding any COMPLETE/PARTIAL/LOW grade is counted as
  "{p} of the last {n} days {is|are} only partly checked" (`GAPS_PARTLY_CHECKED`); days with no counted measure keep
  `GAPS_NO_READINGS`. Both tiers join with " · " in the order no-readings, partly. Added to the vocabulary scan list.
- Pending branch (`GAPS_NOT_ASSESSED`) unchanged; tiers apply only when no gap day holds a PENDING row.
- Tests: new `test_gap_line_separates_no_readings_from_only_partly_checked` and vocabulary case in
  `test_idx_gaps_board.py`. Existing pins (test_idx_gaps_board, test_out_b2_mini, test_k10_declared_none_board) hold
  unchanged: their gap days carry no counted grade. test_idx_gaps_postgres not run (Postgres; its pins are
  all-NO_DATA days, unchanged by logic).
- Run: 52 passed (idx_gaps_board, out_b2_mini, out_b2_vocabulary, k10_declared_none_board); tools/checks
  fuel/mockup/vocab subset 26 passed.
- Capture change: none run. Kisiwa captures/IDX-GAPS index text would change on a fresh prepare (28 of 31 no-readings
  becomes only-partly-checked where critical_served is counted).
